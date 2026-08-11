#!/usr/bin/env bash
# PreToolUse (Write|Edit|MultiEdit): deny-only, role-session approval gate —
# issue #608 step 2. Closes the coverage hole step 1's fixture measurement
# confirmed: no deployed hook checked phase-2 approval state for a role
# session's own writes (its record file, src/, test/); the only two hooks
# that read an APPROVE comment (contract-guard.sh, pr-preflight.sh) are both
# Bash-matcher, gated on `gh pr` verbs only, never reached by a plain write.
#
# No-ops immediately unless CLAUDE_ROLE is set — orchestrator-authored
# writes are deliverable-guard.sh's job, not this hook's. Branch name is
# parsed as issue-<n>/<role> (same regex as pr-preflight.sh); an unparseable
# branch (detached HEAD, non-issue branch) fails open — accepted,
# pattern-consistent limitation, see the proposal's hunt note.
#
# Only the two phase-2-shaped targets are checked: the acting role's own
# record file (docs/issue-<n>/reports/<role>.md) or a src/test(s)/ path.
# Everything else (proposals, survey files, decisions, handbooks,
# docs/specs/approvers.md itself) is phase-1-legal and skipped.
#
# docs/specs/approvers.md absent -> deny with refuse-and-instruct
# (bootstrap offer), never a silent allow (the issue's explicit acceptance
# line, and the fix for step 1's Finding 1). approvers.md present -> check
# membership plus an exact "APPROVE issue-<n>/<role>" comment from a listed
# account (ported inline from pr-preflight.sh's identical check). A `gh`
# lookup failure fails open (consistent with pr-preflight.sh's own
# documented fail-open policy on infrastructure failures), with a stderr
# note that the check could not run.
#
# Fails closed on any other non-0/2 exit (trap), matching this plugin's
# house style. Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -n "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, posixpath, re, subprocess, sys

def deny(msg, hint):
    sys.stderr.write("approval-gate: %s\n" % msg)
    sys.stderr.write("approval-gate: expected: %s\n" % hint)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("AG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") not in ("Write", "Edit", "MultiEdit"):
    sys.exit(0)
ti = e.get("tool_input") or {}
p = ti.get("file_path") if isinstance(ti, dict) else None
if not isinstance(p, str) or not p:
    sys.exit(0)

# --- role identity: prefer the SessionStart-bound snapshot (issue #698) ----
# session-role-bind.sh snapshots CLAUDE_ROLE at SessionStart, before any
# session-controlled code runs, keyed by session_id, into a state file this
# session has no declared write path to. A later Bash-tool re-export of
# CLAUDE_ROLE can no longer change what this gate believes the role is,
# because the live env var is only a fallback for when no snapshot exists
# (e.g. session-role-bind.sh hasn't run yet, or its state dir was cleared).
role = os.environ.get("CLAUDE_ROLE", "")
session_id = e.get("session_id")
if isinstance(session_id, str) and session_id:
    state_dir = os.environ.get(
        "OTR_ROLE_BIND_STATE_DIR",
        os.path.join(os.environ.get("TMPDIR", "/tmp"), "otr-role-bind"),
    )
    safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
    snapshot_path = os.path.join(state_dir, safe_session + ".json")
    try:
        with open(snapshot_path, encoding="utf-8") as f:
            snapshot = json.load(f)
        if isinstance(snapshot, dict) and isinstance(snapshot.get("role"), str):
            role = snapshot["role"]
    except (OSError, ValueError):
        pass  # no snapshot yet — fall back to the live env var

n = posixpath.normpath(p.replace("\\", "/"))

# --- subject issue number off the current branch ---------------------------
try:
    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True, timeout=20)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
branch = r.stdout.strip()
bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
if not bm:
    sys.exit(0)  # unparseable branch — accepted fail-open, matches pr-preflight.sh/contract-guard.sh
issue = int(bm.group(1))
branch_role = bm.group(2)
if role != branch_role:
    sys.exit(0)  # branch doesn't match this role's own session — not this hook's target

# --- phase-2-shaped target check --------------------------------------------
record_path = "docs/issue-%d/reports/%s.md" % (issue, role)
is_record = n == record_path or n.endswith("/" + record_path)
is_src_test = re.search(r"(^|/)(src|tests?)/", n) is not None
if not (is_record or is_src_test):
    sys.exit(0)  # phase-1-legal path (proposal, survey, decisions, handbooks, approvers.md itself, ...)

# --- approvers.md presence: refuse-and-instruct, never silent allow --------
cwd = e.get("cwd") or os.getcwd()
approvers_path = os.path.join(cwd, "docs", "specs", "approvers.md")
if not os.path.isfile(approvers_path):
    deny(
        "docs/specs/approvers.md is absent — this phase-2-shaped write (%s) "
        "cannot be approval-checked, so it is refused rather than silently "
        "allowed." % n,
        "create docs/specs/approvers.md listing one GitHub login per line "
        "(e.g. '- octocat'), then have a listed approver post the required "
        "PR review Approve or an issue comment whose entire body is exactly "
        "'APPROVE issue-%d/%s'." % (issue, role),
    )

approvers = set()
for line in open(approvers_path, encoding="utf-8"):
    mm = re.match(r"^\s*-\s*(\S+)", line)
    if mm:
        approvers.add(mm.group(1))

# --- APPROVE comment / listed-account check ---------------------------------
if not any(os.access(d + "/gh", os.X_OK) for d in os.environ.get("PATH", "").split(os.pathsep) if d):
    sys.stderr.write("approval-gate: gh not found on PATH — cannot verify approval state, "
                      "failing open (infrastructure failure, not an approval-state failure).\n")
    sys.exit(0)

def gh_json(*args):
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None

comments = gh_json("issue", "view", str(issue), "--json", "comments", "-q", ".comments")
if comments is None:
    sys.stderr.write("approval-gate: gh issue view lookup failed — cannot verify approval state, "
                      "failing open (infrastructure failure, not an approval-state failure).\n")
    sys.exit(0)

needle = "APPROVE issue-%d/%s" % (issue, role)
approved = any(
    (c.get("body") or "").strip() == needle
    and (c.get("author", {}) or {}).get("login") in approvers
    for c in (comments or [])
)
if not approved:
    deny(
        "no matching 'APPROVE issue-%d/%s' issue comment from a "
        "docs/specs/approvers.md-listed account was found — this "
        "phase-2-shaped write (%s) needs phase-2 approval first." % (issue, role, n),
        "post an issue comment whose entire body is exactly "
        "'APPROVE issue-%d/%s', from an account listed in "
        "docs/specs/approvers.md." % (issue, role),
    )
sys.exit(0)
PY

AG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
trap - EXIT
exit "$rc"
