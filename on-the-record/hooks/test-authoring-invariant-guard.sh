#!/usr/bin/env bash
# PreToolUse (Bash): standing test-authoring invariant — issue #896 step 2
# (REFRAME: invariant-first, not spawn-when). "A new or changed code path
# that ships without a covering test cannot land." No spawn, no cost
# decision — this is an always-on, cheap, default-on gate, the same shape
# as credential-record-guard.sh (standing security invariant) and
# deliverable-guard.sh (standing delegation invariant).
#
# Scope: intercepts `git commit` the same way pr-preflight.sh intercepts
# `gh pr create/edit` — regex on tool_input.command, since the commit
# boundary (not per-edit Write/Edit) is where "this change, as a whole,
# has no test" is actually decidable: a source file and its test routinely
# land in separate, independently-ordered tool calls within one commit.
#
# Escape hatch: a commit message line matching `^Test-N/A: .+` (a non-empty
# reason) exempts the commit — for a change with no testable code path.
# This is not a rubber stamp: the reason is required, mirroring
# record-claim-guard.sh's existing "no bare claim without a reason"
# pattern already enforced on every record write in this repo.
#
# No command allow/deny lists: classification is by staged file
# path/extension, never by inspecting or blocking specific shell commands.
#
# Fail-open: no python3, not a git repo, not a `git commit` invocation,
# unparseable payload, or an empty staged diff all pass through (exit 0).
# The only path that exits 2 is a positive, evidence-backed determination
# that code changed with no test change and no N/A escape.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as the other hooks here).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

IFS='' read -r -d '' GUARD <<'PY' || true
import json, os, re, subprocess, sys

def deny(msg):
    sys.stderr.write("test-authoring-invariant: %s\n" % msg)
    sys.stderr.write(
        "test-authoring-invariant: add a covering test to the staged "
        "change, or add a commit-message line 'Test-N/A: <reason>' if "
        "this change has no testable code path.\n"
    )
    sys.exit(2)

try:
    e = json.loads(os.environ.get("TAI_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

if not re.search(r"(^|[;&|]\s*)git\s+commit\b", cmd):
    sys.exit(0)
if re.search(r"--no-verify\b", cmd):
    sys.exit(0)  # not this gate's business to fight --no-verify usage

# --- commit message: -m "..." or -F <file> or a --body-style heredoc ------
def _extract_message(cmd):
    m = re.search(
        r"-m(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)", cmd
    )
    if m:
        raw = m.group(1)
        if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
            raw = raw[1:-1]
        return raw
    heredoc = re.compile(
        r"-m\s+\"\$\(\s*cat\s+<<(-?)\s*(['\"]?)(\w+)\2\s*\n(.*?)\n(?(1)[ \t]*)\3[ \t]*\n?\)\"",
        re.DOTALL,
    )
    m = heredoc.search(cmd)
    if m:
        return m.group(4)
    m = re.search(r"-F(?:=|\s+)(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\S+)", cmd)
    if m:
        raw = m.group(1)
        if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
            raw = raw[1:-1]
        try:
            with open(raw, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return None
    return None

message = _extract_message(cmd) or ""
if re.search(r"^Test-N/A:\s*\S.*$", message, re.MULTILINE):
    sys.exit(0)  # reasoned N/A escape present

# --- staged diff -------------------------------------------------------
def _diff(args):
    try:
        r = subprocess.run(["git"] + args, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return [l for l in r.stdout.splitlines() if l.strip()]

paths = _diff(["diff", "--cached", "--name-only", "--diff-filter=ACM"])
if not paths:
    # nothing staged (e.g. `git commit -a`): fall back to the working
    # tree vs HEAD, the set -a would actually commit.
    paths = _diff(["diff", "--name-only", "--diff-filter=ACM", "HEAD"])
if not paths:
    sys.exit(0)  # nothing to classify, or git diff unavailable — fail open

CODE_EXT = (
    ".py", ".js", ".jsx", ".ts", ".tsx", ".sh", ".go", ".rb", ".java",
    ".rs", ".c", ".cpp", ".h", ".hpp", ".kt", ".swift", ".m", ".cs",
)
TEST_SEGMENTS = ("test", "tests", "spec", "specs")

def is_test(path):
    lower = path.lower()
    segs = re.split(r"[/\\]", lower)
    if any(s in TEST_SEGMENTS for s in segs[:-1]):
        return True
    base = segs[-1]
    return bool(re.match(r"^test_.+|.+_test\.[^.]+$|.+\.spec\.[^.]+$|.+\.test\.[^.]+$", base))

def is_code(path):
    lower = path.lower()
    if lower.startswith("docs/") or lower.endswith(".md"):
        return False
    return any(lower.endswith(ext) for ext in CODE_EXT)

code_paths = [p for p in paths if is_code(p) and not is_test(p)]
test_touched = any(is_test(p) for p in paths)

if code_paths and not test_touched:
    deny(
        "code path(s) changed with no covering test in the same commit: "
        + ", ".join(code_paths[:5])
        + (" ..." if len(code_paths) > 5 else "")
    )
sys.exit(0)
PY

TAI_PAYLOAD="$payload" python3 -c "$GUARD"
rc=$?
exit "$rc"
