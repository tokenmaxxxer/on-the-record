#!/usr/bin/env bash
# PreToolUse (Bash): plugin-only default-on orchestrator git-fetch-allow gate
# — issue #894 finding #1's fix (docs/issue-894/reports/security-threat-model.md).
#
# The resumed-orchestrator turn (spawn.py::_resume_orchestrator_session,
# harness/driver.py::resume_orchestrator_session) used to run under
# `--permission-mode bypassPermissions` to get past the host's default-deny
# on Bash calls it needs (`gh pr merge`, `spawn.py`, `git fetch`) — but
# bypassPermissions also removes the host default-deny fallback for every
# OTHER Bash shape, since merge-allow-gate.sh/spawn-allow-gate.sh/
# gh-write-allow-gate.sh only ever emit "allow", never "deny" (issue #886
# hunt). #894's mitigate disposition: drop bypassPermissions, and instead
# cover `git fetch` (the one resume-needed shape none of the other three
# hooks recognize) with this narrow sibling hook — same discipline as
# merge-allow-gate.sh (issue #810/#824):
#   (a) CLAUDE_ROLE resolves empty — orchestrator only, never a role
#       session (identical SessionStart-snapshot-first identity read).
#   (b) the whole, unstripped command tokenizes (shlex.shlex(posix=True,
#       punctuation_chars=True)) to exactly `git fetch [<remote>]
#       [<refspec>...]`, or that shape prefixed by `cd DIR &&`, with no
#       other chaining/substitution operator token anywhere else in the
#       list. Keyed on shape only — no token past `fetch` is inspected for
#       content, matching the other three hooks' own stated invariant.
#   (c) no readiness predicate — `git fetch` only updates local
#       remote-tracking refs, it does not change any ref a human/reviewer
#       would see as "landed" (unlike `gh pr merge`), so unlike
#       merge-allow-gate.sh there is no landing_readiness.py call.
#
# Any other shape (unresolvable command, role session, unrecognized verb,
# any operator token) falls through to plain `exit 0` with no JSON — no
# change from today's classifier/manual-grant behavior. This hook only
# ever ADDS a permission signal; it never emits `"deny"` itself, so an
# existing deny gate on the same command still wins when both fire — the
# same safe composition the other three hooks already rely on.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, sys

try:
    e = json.loads(os.environ.get("GFAG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str) or not cmd.strip():
    sys.exit(0)

# --- identity: SessionStart snapshot first, live env var fallback ----------
# Identical primitive to merge-allow-gate.sh / spawn-allow-gate.sh /
# gh-write-allow-gate.sh.
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

# --- strict command-shape validation (issue #824 design, ported per #894) --
# The whole command must tokenize to exactly ["git", "fetch", ...tail] or
# ["cd", DIR, "&&", "git", "fetch", ...tail], with no chaining/substitution
# operator token anywhere else in the list. No token past "fetch" is ever
# inspected for content — the decision is keyed on shape, never on argument
# text, matching the other three hooks' own stated invariant.
if "`" in cmd or "$(" in cmd or "\n" in cmd:
    sys.exit(0)  # no legitimate invocation needs substitution or a newline

try:
    _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    _lexer.whitespace_split = True
    tokens = list(_lexer)
except ValueError:
    sys.exit(0)  # unbalanced quoting — unreached, same fail-open posture as today

OPERATOR_CHARS = set(_lexer.punctuation_chars) | {";"}


def _is_operator_token(tok):
    return bool(tok) and all(c in OPERATOR_CHARS for c in tok)


if len(tokens) >= 2 and tokens[0] == "git" and tokens[1] == "fetch":
    tail = tokens[2:]
elif (len(tokens) >= 5 and tokens[0] == "cd" and tokens[2] == "&&"
      and tokens[3] == "git" and tokens[4] == "fetch"):
    tail = [tokens[1]] + tokens[5:]  # DIR, then everything after "fetch"
else:
    sys.exit(0)  # not one of the two recognized shapes — unreached

if any(_is_operator_token(t) for t in tail):
    sys.exit(0)  # a chaining/substitution operator survives outside the
    # one tolerated `&&` of a recognized `cd DIR &&` prefix

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": (
            "git-fetch-allow-gate: orchestration session (CLAUDE_ROLE unset) "
            "invoking `git fetch` with no unquoted shell chaining — issue #894."
        ),
    }
}))
sys.exit(0)
PY

GFAG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
