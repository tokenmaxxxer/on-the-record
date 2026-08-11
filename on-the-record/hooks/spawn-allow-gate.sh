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
#   (b) the command-shape check is strict, not a substring/remainder
#       search — the entire tool_input.command must tokenize (via
#       shlex.shlex(posix=True, punctuation_chars=True), the only
#       tokenizer that tracks bash's real quote/escape state instead of
#       hand-rolling a prefix-strip-then-regex — see issue #824's
#       docs/issue-824/proposals/strict-merge-allow-validation.md, ported
#       here per issue #834) to exactly ["python3"|"python", SPAWN_PATH,
#       ...args] or ["cd", DIR, "&&", "python3"|"python", SPAWN_PATH,
#       ...args], SPAWN_PATH ending in "spawn.py", with no other
#       chaining/substitution operator token anywhere else in the list —
#       closing the bypass where a command-substitution payload with no
#       internal whitespace hid inside the old `cd DIR &&` prefix's
#       unbounded directory slot and was stripped away before the
#       operator search ever ran (issue #834). A backtick, `$(`, or a
#       literal newline anywhere in the raw command is rejected outright,
#       before any tokenizing.
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
import json, os, re, shlex, sys

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

# --- strict command-shape validation (issue #834, porting issue #824) ------
# The whole command must tokenize to exactly one of the two recognized
# shapes below, with no other chaining/substitution operator token
# anywhere else in the list — a stripped-prefix-then-regex check is not
# enough, since a command-substitution payload with no internal whitespace
# can hide inside the `cd DIR &&` prefix's directory slot and vanish before
# a remainder-only check ever inspects it (this issue's exact bypass).
if "`" in cmd or "$(" in cmd or "\n" in cmd:
    sys.exit(0)  # no legitimate invocation needs substitution or a newline

try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)  # unbalanced quoting — unreached, same fail-open posture as today

# shlex's own `punctuation_chars` omits `;` (it is still split into its own
# token, just not tracked in that attribute) — add it explicitly so every
# shell control operator this hook must catch is covered.
OPERATOR_CHARS = set(_lexer.punctuation_chars) | {";"}


def _is_operator_token(tok):
    return bool(tok) and all(c in OPERATOR_CHARS for c in tok)


PYBINS = ("python3", "python")

if len(tokens) >= 2 and tokens[0] in PYBINS and tokens[1].endswith("spawn.py"):
    spawn_path = tokens[1]
    tail = tokens[2:]
elif (len(tokens) >= 5 and tokens[0] == "cd" and tokens[2] == "&&"
      and tokens[3] in PYBINS and tokens[4].endswith("spawn.py")):
    spawn_path = tokens[4]
    tail = [tokens[1]] + tokens[5:]  # DIR, then everything after SPAWN_PATH
else:
    sys.exit(0)  # not one of the two recognized shapes — unreached

if any(_is_operator_token(t) for t in tail):
    sys.exit(0)  # a chaining/substitution operator survives outside the
    # one tolerated `&&` of a recognized `cd DIR &&` prefix

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
