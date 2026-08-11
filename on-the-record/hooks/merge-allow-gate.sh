#!/usr/bin/env bash
# PreToolUse (Bash): plugin-only default-on orchestrator merge-allow gate —
# issue #810, candidate 4 of docs/issue-810/proposals/technical-feasibility.md.
#
# Grants `hookSpecificOutput.permissionDecision: "allow"` for a `gh pr merge`
# call, scoped three ways per the proposal's Safety argument:
#   (a) CLAUDE_ROLE resolves empty — orchestrator only, never a role session.
#       Identity read reuses session-role-bind.sh's SessionStart snapshot,
#       exactly the way approval-gate.sh already does (path:on-the-record/
#       hooks/approval-gate.sh lines 72-92) — a later in-session re-export of
#       CLAUDE_ROLE cannot flip this hook's belief about who is running.
#   (b) the command is `gh pr merge` against a resolvable, explicit PR
#       number — reuses contract-guard.sh's target-repo resolution
#       (path:on-the-record/hooks/contract-guard.sh lines 66-79) so no bare
#       `gh pr merge` (implicit "current PR") is ever auto-allowed.
#   (c) gates/landing_readiness.py's `classify` (path:gates/landing_readiness.py
#       line 31), invoked via its own CLI entrypoint against the target
#       checkout, reports that exact PR as READY with no reason suffix.
#
# Any other shape (unresolvable command, role session, PR not exactly READY,
# lookup failure) falls through to plain `exit 0` with no JSON — no change
# from today's classifier/manual-grant behavior. This hook only ever ADDS a
# permission signal; it never emits `"deny"` itself, and per the phase-2
# empirical check recorded in docs/issue-810/reports/implementation.md, an
# existing deny gate's exit-code-2 on the same `gh pr merge` call still wins
# over this hook's JSON `"allow"` when both fire — this hook cannot make a
# bad merge easier, only a good one faster.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v gh >/dev/null 2>&1 || exit 0

# --- locate the on-the-record checkout, for `gates/landing_readiness.py` ---
_checkout_resolve() {
  if [ -n "${TOKENMAXXXER_CHECKOUT:-}" ] && [ -f "${TOKENMAXXXER_CHECKOUT}/spawn.py" ]; then
    printf '%s' "${TOKENMAXXXER_CHECKOUT}"; return 0
  fi
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  probe="$d"
  for _ in 1 2 3 4; do
    probe="$(dirname "$probe")"
    if [ -f "$probe/spawn.py" ]; then printf '%s' "$probe"; return 0; fi
  done
  mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer"
  if [ -f "$mk/spawn.py" ]; then printf '%s' "$mk"; return 0; fi
  own="$HOME/.claude/tokenmaxxxer/on-the-record"
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  old="$HOME/.claude/tokenmaxxxer/muster"
  if [ -f "$old/spawn.py" ]; then printf '%s' "$old"; return 0; fi
  mkdir -p "$(dirname "$own")" 2>/dev/null
  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] || exit 0
[ -f "$CHECKOUT/gates/landing_readiness.py" ] || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, subprocess, sys

try:
    e = json.loads(os.environ.get("MAG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)
if not re.search(r"\bgh\s+pr\s+merge\b", cmd):
    sys.exit(0)

# --- identity: SessionStart snapshot first, live env var fallback ----------
# Same primitive approval-gate.sh already trusts (path:on-the-record/hooks/
# approval-gate.sh lines 72-92) — this hook only ever fires for the
# orchestrator (empty role), the mirror image of approval-gate.sh's
# role-session-only trigger.
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
if role:
    sys.exit(0)  # a role session — never this hook's target, contract v3 s10 unchanged

# --- target-repo / explicit-PR-number resolution ----------------------------
# Ported from contract-guard.sh's already-hardened resolution
# (path:on-the-record/hooks/contract-guard.sh lines 66-79): only the forms
# that resolve to an explicit PR number are handled; a bare `gh pr merge`
# with an implicit "current PR" is left unreached (no allow, no deny).
target_cwd = None
target_repo_flag = None

cd_m = re.match(r"^\s*cd\s+(\S+)\s*&&", cmd)
if cd_m:
    target_cwd = cd_m.group(1)

rest = re.split(r"\bgh\s+pr\s+merge\b", cmd, maxsplit=1)[1]

url_m = re.search(r"github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)", rest)
repo_flag_m = re.search(r"(?:-R|--repo)[= ]([^\s/]+/[^\s/]+)", rest)

if url_m:
    pr = url_m.group(2)
    target_cwd = None
    target_repo_flag = url_m.group(1)
elif repo_flag_m:
    num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
    if not num_m:
        sys.exit(0)
    pr = num_m.group(1)
    target_cwd = None
    target_repo_flag = repo_flag_m.group(1)
else:
    num_m = re.search(r"(?<!\S)(\d+)(?!\S)", rest)
    if not num_m:
        sys.exit(0)  # implicit "current PR" — cannot resolve without a checkout
    pr = num_m.group(1)

if target_repo_flag and target_cwd is None:
    # -R/--repo or a full URL with no local `cd` checkout: landing_readiness.py
    # needs a local checkout (docs/specs/approvers.md, docs/issue-<n>/reports/)
    # to compute has_record/has_approval — not fetchable, explicit unreached.
    sys.exit(0)

run_cwd = target_cwd or e.get("cwd") or os.getcwd()

# --- call the existing READY predicate, not a reimplementation -------------
checkout = os.environ.get("MAG_CHECKOUT")
script = os.path.join(checkout, "gates", "landing_readiness.py")
try:
    r = subprocess.run(
        [sys.executable, script, "--repo", run_cwd],
        capture_output=True, text=True, timeout=60,
    )
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)  # lookup failure — fail-open, same posture as contract-guard.sh

ready_line = re.compile(r"^PR #%s: READY\s*$" % re.escape(pr), re.MULTILINE)
if not ready_line.search(r.stdout):
    sys.exit(0)  # not exactly READY (blocked, or a reason suffix) — no allow

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": (
            "merge-allow-gate: PR #%s is landing_readiness=READY "
            "(gates/landing_readiness.py) and this is the orchestration "
            "session (CLAUDE_ROLE unset) — issue #810." % pr
        ),
    }
}))
sys.exit(0)
PY

MAG_PAYLOAD="$payload" MAG_CHECKOUT="$CHECKOUT" python3 -c "$GUARD"
rc=$?
exit "$rc"
