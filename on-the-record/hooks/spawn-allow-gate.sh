#!/usr/bin/env bash
# PreToolUse (Bash): plugin-only default-on orchestrator spawn-allow gate —
# issue #810 SCOPE EXTENSION 2, extending merge-allow-gate.sh's pattern from
# `gh pr merge` to the plugin's own spawn.py role-spawn/watch/consult
# invocations.
#
# Live evidence that motivated this (issue #810 comment "SCOPE EXTENSION 2"):
# a legitimate spawn.py invocation was denied by the host permission
# classifier purely because its task-description TEXT contained
# sensitive-looking literals — rewording the task unblocked the identical
# command. The block was text-driven, not action-driven, so this gate's
# allow decision is keyed ONLY on (a) orchestrator identity and (b) the
# invoked command resolving to this checkout's own spawn.py — never on any
# word inside the command's arguments.
#
# Scoped the same three ways merge-allow-gate.sh already established:
#   (a) CLAUDE_ROLE resolves empty — orchestrator only, never a role
#       session. Same SessionStart-snapshot identity read as
#       merge-allow-gate.sh / approval-gate.sh.
#   (b) the command, after stripping an optional leading `cd DIR &&`, is a
#       single `python3 <path-ending-in-spawn.py> ...` invocation with no
#       further shell chaining (&&, ;, |) or command/process substitution
#       ($(...), `...`, <(...), >(...)) reachable outside single-quoted
#       spans — only single quotes fully neutralize those in bash; double
#       quotes still let $(...) and `...` execute, so double-quoted spans
#       are NOT stripped before this check — so this hook never
#       blanket-allows an arbitrary command merely because "spawn.py"
#       appears in it somewhere.
#   (c) the resolved spawn.py path exists on disk inside a resolvable
#       on-the-record checkout (reuses merge-allow-gate.sh's
#       `_checkout_resolve`) — a path that does not resolve to a real file
#       is left unreached, not allowed.
#
# Any other shape falls through to plain `exit 0` with no JSON — no change
# from today's classifier/manual-grant behavior. This hook only ever ADDS a
# permission signal; it never emits `"deny"` itself.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0

# --- locate the on-the-record checkout, same probe as merge-allow-gate.sh --
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
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, sys

try:
    e = json.loads(os.environ.get("SAG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str) or not cmd.strip():
    sys.exit(0)

# --- identity: SessionStart snapshot first, live env var fallback ----------
# Identical primitive to merge-allow-gate.sh (path:on-the-record/hooks/
# merge-allow-gate.sh lines 79-101) — this hook only ever fires for the
# orchestrator (empty role).
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
    sys.exit(0)  # a role session — never this hook's target

# --- command-shape resolution: strip an optional `cd DIR &&` prefix --------
rest = cmd.strip()
cd_m = re.match(r"^cd\s+\S+\s*&&\s*(.*)$", rest, re.DOTALL)
if cd_m:
    rest = cd_m.group(1).strip()

# --- reject if any shell-chaining/substitution operator is reachable -------
# The task text an orchestrator passes to spawn.py is free-form and may
# legitimately contain &&, ;, | as literal characters — but ONLY inside
# single quotes are those (and $(...) / `...`) neutralized by the shell;
# double quotes still let $(...) and `...` command-substitution execute.
# So: strip single-quoted spans only (fully inert), then check the
# remainder — which still includes double-quoted text — for any chaining
# or substitution operator, since all of those stay live there.
stripped = re.sub(r"'[^']*'", "", rest)
if re.search(r"&&|;|\||\$\(|`|<\(|>\(", stripped):
    sys.exit(0)

# --- must be exactly a `python3 <...spawn.py> ...` invocation --------------
m = re.match(r"^python3?\s+(\S*spawn\.py)(?:\s|$)", rest)
if not m:
    sys.exit(0)
spawn_path = m.group(1)

checkout = os.environ.get("SAG_CHECKOUT", "")
resolved = spawn_path
if not os.path.isabs(resolved):
    resolved = os.path.normpath(os.path.join(checkout, resolved))
checkout_spawn = os.path.normpath(os.path.join(checkout, "spawn.py"))
if os.path.normpath(resolved) != checkout_spawn or not os.path.isfile(checkout_spawn):
    sys.exit(0)  # doesn't resolve to this checkout's own spawn.py — unreached

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": (
            "spawn-allow-gate: orchestration session (CLAUDE_ROLE unset) "
            "invoking this checkout's own spawn.py with no unquoted shell "
            "chaining — issue #810 SCOPE EXTENSION 2."
        ),
    }
}))
sys.exit(0)
PY

SAG_PAYLOAD="$payload" SAG_CHECKOUT="$CHECKOUT" python3 -c "$GUARD"
rc=$?
exit "$rc"
