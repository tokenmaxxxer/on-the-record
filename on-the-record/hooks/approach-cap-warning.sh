#!/usr/bin/env bash
# PreToolUse/PostToolUse pair: approach-cap warning — issue #2262.
#
# Six sessions died at the 200-turn `--max-turns` cap mid-action (spawn.py
# DEFAULT_SESSION_MAX_TURNS), killed with no warning to themselves and no
# terminal act (measured: issues 2173, 2186, 2193, 2204, 2208, 2240). The
# actual cap enforcement lives outside this repo (the `claude` CLI itself
# kills the process at `--max-turns`); the only lever available in-repo is
# to widen that CLI ceiling by a small wrap-up allowance
# (pipeline.py:spawn_cmd, `_resolve_wrap_up_allowance_turns`) and, before
# the padded turns run out, tell the session to converge — the SWE-agent
# autosubmit shape (issue body cites #2215's checkpointing precedent).
#
# Mode is selected by $1:
#   post -- fires on PostToolUse for every matched tool call and bumps a
#           per-session tool-call counter. Tool calls approximate turns
#           (a single turn can carry more than one parallel tool call, so
#           this slightly over-counts — acceptable for a warning, never
#           load-bearing the way the CLI's own turn count is).
#   pre  -- fires on PreToolUse, reads the counter, and — while remaining
#           turns (MUSTER_SESSION_MAX_TURNS_RESOLVED minus the counter)
#           is in (0, MUSTER_APPROACH_WARNING_TURNS] — emits
#           hookSpecificOutput.additionalContext telling the session to
#           converge: commit, open the PR, write the record with what it
#           has. Repeats on every tool call inside that window (not just
#           once) so the nudge cannot scroll out of context before the
#           session acts on it.
#
# No-op (both modes) when MUSTER_SESSION_MAX_TURNS_RESOLVED is unset or
# <= 0 — pipeline.py only sets it for a spawn with a resolved, capped
# budget (issue #2100 item 4); an uncapped/unresolved session has nothing
# to warn against, and this hook must never invent a cap the spawner
# didn't set. This is also the #2262 acceptance "empty state": a session
# that finishes naturally under the cap never crosses the remaining-turns
# window, so it sees no warning and no behavior change.
#
# Spawned-session identity (matches retry-loop-bound.sh, approval-gate.sh;
# issue #2538): resolves TOKENMAXXXER_SPAWNED from the #698
# session-role-bind snapshot with a live-env fallback — presence-only,
# never a role name, so this needs no role identity. Orchestrator sessions
# never carry MUSTER_SESSION_MAX_TURNS_RESOLVED in the first place
# (pipeline.py only sets it inside a role spawn's env), so this check is a
# second, independent no-op guard rather than the only one.
#
# Fails OPEN on any parse/state error or missing session_id — this hook
# only adds a warning on top of the existing turn budget, never instead
# of it.
#
# State: ${OTR_APPROACH_CAP_STATE_DIR:-$TMPDIR/otr-approach-cap}/<session_id>.json
trap 'exit 0' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac

MODE="${1:-}"
# Unlike the environment-gap fail-opens below, an unrecognized $1 is a
# wiring error (hooks.json only ever calls this with "pre" or "post") —
# distinct exit code so a registration typo doesn't silently masquerade
# as a normal no-op.
case "$MODE" in pre|post) ;; *) trap - EXIT; exit 1 ;; esac

# Cheap fast-path before touching python3/state: no resolved cap, no work.
case "${MUSTER_SESSION_MAX_TURNS_RESOLVED:-}" in ""|0|-*) trap - EXIT; exit 0 ;; esac

command -v python3 >/dev/null 2>&1 || { trap - EXIT; exit 0; }

PAYLOAD="$(cat 2>/dev/null || true)"
[ -n "$PAYLOAD" ] || { trap - EXIT; exit 0; }

STATE_DIR="${OTR_APPROACH_CAP_STATE_DIR:-${TMPDIR:-/tmp}/otr-approach-cap}"
mkdir -p "$STATE_DIR" 2>/dev/null || true

OTR_ACW_PAYLOAD="$PAYLOAD" OTR_ACW_MODE="$MODE" OTR_ACW_STATE_DIR="$STATE_DIR" \
  OTR_ACW_CAP="${MUSTER_SESSION_MAX_TURNS_RESOLVED:-}" \
  OTR_ACW_WARN_TURNS="${MUSTER_APPROACH_WARNING_TURNS:-20}" \
  python3 - <<'PY'
import json
import os
import re
import sys

payload_raw = os.environ.get("OTR_ACW_PAYLOAD", "")
mode = os.environ.get("OTR_ACW_MODE", "")
state_dir = os.environ.get("OTR_ACW_STATE_DIR", "")

try:
    cap = int(os.environ.get("OTR_ACW_CAP", "0"))
except ValueError:
    cap = 0
if cap <= 0:
    sys.exit(0)

try:
    warn_turns = int(os.environ.get("OTR_ACW_WARN_TURNS", "20"))
except ValueError:
    warn_turns = 20
if warn_turns < 0:
    warn_turns = 0

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

# --- spawned identity: same resolve-with-fallback pattern as
# retry-loop-bound.sh / approval-gate.sh --------------------------------
spawned = bool(os.environ.get("TOKENMAXXXER_SPAWNED", ""))
bind_state_dir = os.environ.get(
    "OTR_SKILL_BIND_STATE_DIR",
    os.path.join(os.environ.get("TMPDIR", "/tmp"), "otr-role-bind"),
)
snapshot_path = os.path.join(bind_state_dir, safe_session + ".json")
try:
    with open(snapshot_path, encoding="utf-8") as f:
        snapshot = json.load(f)
    if isinstance(snapshot, dict) and "spawned" in snapshot:
        spawned = bool(snapshot["spawned"])
except (OSError, ValueError):
    pass  # no snapshot yet — fall back to the live env var
if not spawned:
    sys.exit(0)  # no role bound — nothing this hook is scoped to warn


def _load():
    try:
        with open(state_path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def _save(data):
    try:
        tmp = state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, state_path)
    except OSError:
        pass


if mode == "post":
    data = _load()
    data["count"] = int(data.get("count", 0)) + 1
    _save(data)
    sys.exit(0)

# mode == "pre"
data = _load()
count = int(data.get("count", 0))
remaining = cap - count

if 0 < remaining <= warn_turns:
    ctx = (
        "approach-cap warning (issue #2262): about %d turns remain of "
        "this session's %d-turn budget. Converge now — commit what you "
        "have, open the PR, and write the record with what it has. A "
        "wrap-up allowance beyond this budget exists to land, not to "
        "keep exploring; do not start new exploration or open-ended "
        "investigation past this point."
        % (remaining, cap)
    )
    out = {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": ctx,
    }}
    sys.stdout.write(json.dumps(out))

sys.exit(0)
PY
rc=$?
trap - EXIT
exit "$rc"
