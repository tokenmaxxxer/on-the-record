#!/usr/bin/env bash
# PreToolUse (Bash): deny-before-post gate on a "VIA DELEGATION" APPROVE
# citation — issue #707. Blocks a role-bound session (ANY role, not only the
# branch's own) from ever posting a delegation-citing APPROVE comment
# itself: only an orchestrator session (no CLAUDE_ROLE / no #698
# session-role-bind snapshot) may cite a delegation record as APPROVE
# provenance. This is the self-approval invariant's enforcement point for
# the delegation path — approval-gate.sh (the write-time gate) trusts
# whatever citation already exists in the issue's comment history; this
# hook is what keeps a self-authored citation from ever landing there in
# the first place, so approval-gate.sh never has to re-derive session
# identity from a GitHub comment that carries none.
#
# Positive check, not "role differs from branch role": the after-proposal
# hunt (docs/issue-707/reports/product-discovery/hunt-after-proposal.md)
# found the narrower differs-from-branch-role check insufficient — a
# session bound to an unrelated role on an unrelated issue would pass that
# narrower check without being the orchestrator at all. Absent CLAUDE_ROLE
# (and absent a bound snapshot) is this repo's own existing convention for
# "this is an orchestrator, not a role session" (session-role-bind.sh's own
# no-op condition), so that is the positive signal checked here — any
# bound role, matching or not, is refused.
#
# Fail-open on parse failure / no python3 on PATH — same fail-open posture
# every other Bash-matcher hook in this plugin already uses; what must
# never happen is silently allowing a positively-identified role-bound
# session to post the citation, matching approval-gate.sh's own asymmetry.
# Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, sys

def deny(msg, hint):
    sys.stderr.write("delegation-post-gate: %s\n" % msg)
    sys.stderr.write("delegation-post-gate: expected: %s\n" % hint)
    # greppable for the pre-registered guardrail metric (issue #707):
    # self_approval_violation_count counts these deny lines.
    sys.stderr.write("delegation-post-gate: metric self_approval_violation_count +1\n")
    sys.exit(2)

try:
    e = json.loads(os.environ.get("DPG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

if not re.search(r"\bgh\s+(issue\s+comment\b|api\b)", cmd):
    sys.exit(0)  # not a comment-posting command — not this hook's target

body = None
for pat in (
    r"--body(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)",
    r"-f\s+body=(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)",
    r"--raw-field\s+body=(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)",
):
    m = re.search(pat, cmd)
    if m:
        raw = m.group(1)
        if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
            raw = raw[1:-1]
        body = raw
        break
if body is None:
    sys.exit(0)  # no --body/-f body=/--raw-field body= — nothing to check yet

_CITE_RE = re.compile(r"^APPROVE issue-(\d+)/([\w-]+) VIA DELEGATION (\S+)$")
if not _CITE_RE.match(body.strip()):
    sys.exit(0)  # not a delegation citation — not this hook's target

# --- role identity: prefer the SessionStart-bound snapshot (issue #698) ---
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
    deny(
        "a role-bound session (role=%r) attempted to post a "
        "delegation-citing APPROVE comment (%r) — only an orchestrator "
        "session (no CLAUDE_ROLE bound) may cite a delegation record as "
        "APPROVE provenance, regardless of whether the cited delegation "
        "record is itself valid." % (role, body.strip()),
        "relay this citation from an orchestrator session with no "
        "CLAUDE_ROLE bound, never from a role session.",
    )
sys.exit(0)
PY

DPG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
trap - EXIT
exit "$rc"
