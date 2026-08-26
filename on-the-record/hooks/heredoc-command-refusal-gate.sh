#!/usr/bin/env bash
# PreToolUse (Bash): deny-only, role-scoped refusal-message gate — issue
# #1976.
#
# Dogfooding observation (issue #1976): virtually every role session's
# first `git commit`/`gh pr create`/`gh issue create`/`gh pr comment`/
# `gh issue comment` attempt uses a heredoc-shaped message/body (`$(cat
# <<'EOF' ... EOF)`, or any other `<<` heredoc redirection anywhere in
# the command) and is refused by the host's default write-capable-command
# classifier as an un-analyzable shape, with no actionable next step —
# each session then burns 1-3 retries discovering the single-line `-m`/
# `--body-file` workaround independently.
#
# This hook does not change WHETHER a heredoc-shaped commit/PR command is
# refused (the host classifier already refuses it, and this gate refuses
# it again independently so the refusal is actionable even in an
# environment where the host classifier is absent, e.g. these tests) — it
# changes WHAT the refusal says: the sanctioned alternative, spelled out
# literally, every time.
#
#   git commit          -> two `-m` flags: `git commit -m "title" -m "body"`
#   gh issue/pr create   -> `--body-file <path>` instead of `--body "$(...)"`
#   gh issue/pr comment  -> `--body-file <path>` instead of `--body "$(...)"`
#
# Scope: role sessions only (`TOKENMAXXXER_SPAWNED` resolves non-empty via
# the same SessionStart-snapshot-first / live-env-var-fallback primitive
# gh-write-allow-gate.sh/merge-allow-gate.sh/spawn-allow-gate.sh already
# use — issue #2538: presence-only, no role name needed) — issue #1976's
# dogfooding note is specifically about role
# sessions, and gh-write-allow-gate.sh already owns the orchestrator's
# quoted-heredoc allow path for the five gh verbs it recognizes; this gate
# must never regress that by denying an orchestrator's already-working
# quoted-heredoc `gh issue/pr` call.
#
# Detection is intentionally shape-only and broad — any `<<` heredoc
# redirection token anywhere in a recognized git-commit/gh-write command —
# never content-based: this gate only ever needs to know THAT a heredoc is
# present, not what it says, so it can point at the sanctioned
# alternative. A command with no `<<` at all (i.e. already using the
# sanctioned two-`-m`/`--body-file` form) is untouched.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as every other gate here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, sys

def deny(msg):
    sys.stderr.write("heredoc-command-refusal-gate: %s\n" % msg)
    sys.exit(2)

try:
    e = json.loads(os.environ.get("HCRG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str) or not cmd.strip():
    sys.exit(0)

# --- identity: SessionStart snapshot first, live env var fallback ----------
# Identical primitive to gh-write-allow-gate.sh / merge-allow-gate.sh /
# spawn-allow-gate.sh.
spawned = bool(os.environ.get("TOKENMAXXXER_SPAWNED", ""))
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
        if isinstance(snapshot, dict) and "spawned" in snapshot:
            spawned = bool(snapshot["spawned"])
    except (OSError, ValueError):
        pass  # no snapshot yet — fall back to the live env var
if not spawned:
    sys.exit(0)  # orchestrator session — never this hook's target

if "<<" not in cmd:
    sys.exit(0)  # no heredoc redirection anywhere — already the sanctioned shape

_COMMIT_RE = re.compile(r"(?<![\w-])git\s+(?:-[^\s]+\s+)*commit\b")
_GH_WRITE_RE = re.compile(
    r"(?<![\w-])gh\s+(?:issue|pr)\s+(?:create|comment)\b"
)

if _COMMIT_RE.search(cmd):
    deny(
        "heredoc-shaped commit message body detected — the host's "
        "write-capable-command classifier refuses this shape as "
        "un-analyzable. Use two -m flags instead of a heredoc: "
        "git commit -m \"<title line>\" -m \"<body line>\" (one -m per "
        "paragraph; never a heredoc/$(cat <<EOF ...) body) — issue #1976."
    )

if _GH_WRITE_RE.search(cmd):
    deny(
        "heredoc-shaped --body detected — the host's write-capable-command "
        "classifier refuses this shape as un-analyzable. Use --body-file "
        "<path> instead of a heredoc body: write the body to a file first, "
        "then gh issue/pr create/comment ... --body-file <path> — issue "
        "#1976."
    )

sys.exit(0)
PY

HCRG_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
