#!/usr/bin/env bash
# PreToolUse (Bash): plugin-only default-on orchestrator gh-write-allow gate
# — issue #856, the unbuilt half of #810 SCOPE EXTENSION 2.
#
# Grants `hookSpecificOutput.permissionDecision: "allow"` for the five gh
# issue/pr write verbs the orchestrator needs to run the on-the-record loop
# at all (requirements -> issues, relaying decisions) but that a fresh
# install's host permission classifier denies by default (measured #855:
# "every gh call ... is denied by the permission mode in this session"):
#   gh issue create, gh issue comment, gh pr comment, gh issue close,
#   gh pr close
#
# Same three-part design as merge-allow-gate.sh (#816) and
# spawn-allow-gate.sh (#823):
#   (a) CLAUDE_ROLE resolves empty — orchestrator only, never a role
#       session (identical SessionStart-snapshot-first identity read).
#   (b) the whole, unstripped command tokenizes (shlex.shlex(posix=True,
#       punctuation_chars=True) — issue #824/#834's strict command-shape
#       design) to exactly one of the five recognized verb shapes, or that
#       shape prefixed by `cd DIR &&`, with no other chaining/substitution
#       operator token anywhere else in the list. Keyed on command SHAPE
#       only — no token past the verb's own subcommand name is inspected,
#       so a `--body`/comment-text argument carrying sensitive-looking
#       literals (issue #810 SCOPE EXTENSION 2's live failure mode) can
#       never flip this decision either way.
#   (c) no readiness/content predicate at all — these are non-destructive
#       forge writes (create/comment/close, not merge), so unlike
#       merge-allow-gate.sh there is no landing_readiness.py call.
#
# Any other shape (unresolvable command, role session, unrecognized verb)
# falls through to plain `exit 0` with no JSON — no change from today's
# classifier/manual-grant behavior. This hook only ever ADDS a permission
# signal; it never emits `"deny"` itself, so an existing deny gate on the
# same command (e.g. a role-scoped gate, or a future gh-write deny rule)
# still wins when both fire — the same safe composition proven for #816.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, shlex, sys

try:
    e = json.loads(os.environ.get("GWAG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str) or not cmd.strip():
    sys.exit(0)

# --- identity: SessionStart snapshot first, live env var fallback ----------
# Identical primitive to merge-allow-gate.sh / spawn-allow-gate.sh.
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

# --- strict command-shape validation (issue #824/#834 design) --------------
# The whole command must tokenize to exactly one recognized verb shape, or
# that shape prefixed by `cd DIR &&`, with no chaining/substitution
# operator token anywhere else in the list. No token past the verb itself
# is ever inspected — the decision is keyed on shape, never on argument
# text (issue #856's own stated requirement).
#
# issue #868 exception: `$(cat <<'DELIM' ... DELIM\n)` — a command
# substitution whose ENTIRE content is a `cat` heredoc with a QUOTED
# delimiter. A quoted heredoc delimiter (`<<'EOF'`/`<<"EOF"`) is a shell
# primitive that disables ALL expansion of its body by construction — the
# shell never looks for `$(...)`, backticks, or variables inside it,
# regardless of what text the body contains. So `cat`'s stdout (the
# multi-line body, verbatim) is the only thing this substitution can ever
# produce; it cannot execute anything hidden. This is the real shape a
# session emits for `gh issue create --body "$(cat <<'EOF' ... EOF)"`
# (see docs/issue-868/reports/implementation/survey.md). Only this exact
# shape is special-cased; any other `$(...)`/backtick/newline still exits
# untouched below.
_HEREDOC_SUB_RE = re.compile(
    r"\$\(\s*cat\s*<<\s*(?P<q>['\"])(?P<delim>[A-Za-z_][A-Za-z0-9_]*)(?P=q)"
    r"\s*\n(?P<body>.*?)\n(?P=delim)[ \t]*\n?\s*\)",
    re.DOTALL,
)
_subs = list(_HEREDOC_SUB_RE.finditer(cmd))
if len(_subs) == 1 and cmd.count("$(") == 1 and "`" not in cmd:
    # Exactly one substitution, of the provably-benign shape, and nothing
    # else in the command needs `$(` at all — collapse it to an inert
    # single-token placeholder so the rest of the command (the actual gh
    # verb and its other flags) can be shape-checked as normal below.
    cmd = cmd[: _subs[0].start()] + '"__OTR_QUOTED_HEREDOC_BODY__"' + cmd[_subs[0].end():]

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


VERB_SHAPES = (
    ("gh", "issue", "create"),
    ("gh", "issue", "comment"),
    ("gh", "pr", "comment"),
    ("gh", "issue", "close"),
    ("gh", "pr", "close"),
)


def _match_shape(toks):
    for shape in VERB_SHAPES:
        n = len(shape)
        if len(toks) >= n and tuple(toks[:n]) == shape:
            return toks[n:]
    return None


if tokens[:1] == ["cd"] and len(tokens) >= 2 and tokens[2:3] == ["&&"]:
    tail = _match_shape(tokens[3:])
elif tokens:
    tail = _match_shape(tokens)
else:
    tail = None

if tail is None:
    sys.exit(0)  # not one of the five recognized verb shapes — unreached

if any(_is_operator_token(t) for t in tail):
    sys.exit(0)  # a chaining/substitution operator survives outside the
    # one tolerated `&&` of a recognized `cd DIR &&` prefix

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": (
            "gh-write-allow-gate: orchestration session (CLAUDE_ROLE unset) "
            "invoking a recognized gh issue/pr write verb with no unquoted "
            "shell chaining — issue #856."
        ),
    }
}))
sys.exit(0)
PY

GWAG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
