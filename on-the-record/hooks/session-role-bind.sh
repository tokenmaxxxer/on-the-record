#!/usr/bin/env bash
# SessionStart hook: snapshot CLAUDE_ROLE into a session_id-keyed state file
# before any session-controlled code can run. Issue #698 — approval-gate.sh
# (and any future consumer) reads this snapshot instead of trusting a later,
# session-influenced read of the live CLAUDE_ROLE env var, which the model
# can re-export via Bash.
#
# At SessionStart, CLAUDE_ROLE is still exactly what spawn.py set at process
# launch — no session-controlled code has run yet, so this is the one point
# in the session lifecycle where reading the env var is trustworthy.
#
# State: ${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}/<session_id>.json
# containing {"role": "<value>"}. First-observation wins: a later
# SessionStart replay within the same session_id never overwrites an
# existing snapshot, so a role can't rebind itself mid-session via a replay.
#
# No-ops (exit 0) when CLAUDE_ROLE is unset (orchestrator session) or the
# payload carries no session_id — same fail-open shape as
# retry-loop-bound.sh's missing-session_id handling.
trap 'exit 0' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -n "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }

PAYLOAD="$(cat 2>/dev/null || true)"
[ -n "$PAYLOAD" ] || { trap - EXIT; exit 0; }

STATE_DIR="${OTR_ROLE_BIND_STATE_DIR:-${TMPDIR:-/tmp}/otr-role-bind}"
mkdir -p "$STATE_DIR" 2>/dev/null || true

OTR_RB_PAYLOAD="$PAYLOAD" OTR_RB_ROLE="$CLAUDE_ROLE" OTR_RB_STATE_DIR="$STATE_DIR" \
  python3 - <<'PY'
import json
import os
import re
import sys

payload_raw = os.environ.get("OTR_RB_PAYLOAD", "")
role = os.environ.get("OTR_RB_ROLE", "")
state_dir = os.environ.get("OTR_RB_STATE_DIR", "")

try:
    payload = json.loads(payload_raw)
except ValueError:
    sys.exit(0)
if not isinstance(payload, dict):
    sys.exit(0)

session_id = payload.get("session_id")
if not isinstance(session_id, str) or not session_id:
    sys.exit(0)

safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
state_path = os.path.join(state_dir, safe_session + ".json")

if os.path.exists(state_path):
    # first-observation wins — a replayed SessionStart never rebinds.
    sys.exit(0)

tmp = state_path + ".tmp"
try:
    with open(tmp, "w") as f:
        json.dump({"role": role}, f)
    os.replace(tmp, state_path)
except OSError:
    pass
sys.exit(0)
PY
trap - EXIT
exit 0
