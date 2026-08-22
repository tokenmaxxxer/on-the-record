#!/usr/bin/env bash
# Stop: per-mounted-skill verdict obligation (issue #2039,
# docs/issue-2039/proposals/2026-08-22-per-skill-verdict-obligation.md).
#
# Mirrors deviation-log-guard.sh's mechanism exactly: the mounted-skill
# list only ever exists in the spawned session's own first-user-message
# text (spawn.py:8143-8182's two assembly points), never in a file the
# target repo's git tree or CI can read independently — so this is
# necessarily a session-side Stop hook, not a gates.py CI-diff scan.
# Reads transcript_path off the raw Stop event JSON, scans the
# transcript's first user message for the two known mounted-skill line
# prefixes, extracts the skill name set (union, no double-count for a
# skill named by both assembly points), and delegates the actual
# shape check to gates/record_lint.py's record_skill_verdicts_in (the
# same canonical function a future gates.py/CI caller would use).
#
# Zero mounted skills -> exit 0 immediately, no output (byte-inert per
# the proposal's Constraints). Refuses via hookSpecificOutput.additionalContext,
# never decision:"block" -- same house style as deviation-log-guard.sh.
# Same fail-closed trap / ORCHESTRATE_OFF kill switch as its sibling hooks.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"

command -v python3 >/dev/null 2>&1 || exit 2

REPO="$(pwd -P)"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gates_dir=""
if [ -d "$script_dir/../gates" ]; then
    gates_dir="$(cd "$script_dir/../gates" && pwd)"
elif [ -d "$script_dir/../../gates" ]; then
    gates_dir="$(cd "$script_dir/../../gates" && pwd)"
fi

IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, re, subprocess, sys

try:
    e = json.loads(os.environ.get("SVG_PAYLOAD", ""))
except ValueError:
    sys.exit(2)
if not isinstance(e, dict):
    sys.exit(2)

# Issue #1725 Stop-hook contract: a forced-retry turn must emit nothing.
if e.get("stop_hook_active"):
    sys.exit(0)

transcript_path = e.get("transcript_path")
if not isinstance(transcript_path, str) or not transcript_path:
    sys.exit(0)
if not os.path.isfile(transcript_path):
    sys.exit(0)

repo = os.environ.get("SVG_REPO", "")
gates_dir = os.environ.get("SVG_GATES_DIR") or ""

# The two mounted-skill line prefixes spawn.py assembles
# (spawn.py:8143-8151 and spawn.py:8152-8182). Each line is a
# comma-joined "name (...)"/"name — ..." list; a skill name is the text
# up to the first " (" or " — " token.
_PREFIXES = (
    "마운트된 스킬(--skills",
    "이 역할은 skill-repository(",
)


def flat_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text")
                if isinstance(t, str):
                    parts.append(t)
        return "\n".join(parts) if parts else None
    return None


def first_user_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(entry, dict) or entry.get("type") != "user":
                    continue
                message = entry.get("message")
                if not isinstance(message, dict):
                    continue
                text = flat_text(message.get("content"))
                if text:
                    return text
    except OSError:
        return None
    return None


def extract_names(line_body):
    """`line_body` is everything after the assembly point's own colon
    (e.g. "이슈 #1742/#1774): a, b (...), c — ..."). Split on top-level
    commas, then take each item's leading name token before its first
    "(" or " — "."""
    # Drop the leading "이슈 #.../..): " citation clause before the
    # actual comma-joined name list, if present.
    m = re.match(r"^[^:]*:\s*(.*)$", line_body)
    body = m.group(1) if m else line_body
    # spawn.py's role-mapping line inserts a literal "스킬 " label before
    # the actual comma-joined name list (the --skills line has no such
    # label) -- strip it so it isn't parsed as part of the first name.
    body = re.sub(r"^스킬\s+", "", body)
    names = []
    for item in body.split(","):
        item = item.strip()
        if not item:
            continue
        item = re.split(r"\s+—\s+|\s+\(", item, maxsplit=1)[0].strip()
        if item:
            names.append(item)
    return names


text = first_user_text(transcript_path)
mounted = []
seen = set()
if text:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        for prefix in _PREFIXES:
            if line.startswith(prefix):
                for name in extract_names(line[len(prefix):]):
                    if name not in seen:
                        seen.add(name)
                        mounted.append(name)
                break

if not mounted:
    sys.exit(0)

if not gates_dir:
    sys.exit(2)
try:
    sys.path.insert(0, gates_dir)
    import record_lint
except ImportError:
    sys.exit(2)

branch_r = subprocess.run(
    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    cwd=repo, capture_output=True, text=True, timeout=10,
)
branch = branch_r.stdout.strip() if branch_r.returncode == 0 else ""
branch_m = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
if not branch_m:
    sys.exit(0)
role = branch_m.group(2)
rel = os.path.join("docs", f"issue-{branch_m.group(1)}", "reports", f"{role}.md")

record_file = os.path.join(repo, rel)
record_text = ""
if os.path.isfile(record_file):
    with open(record_file, "r", encoding="utf-8-sig", errors="replace") as fh:
        record_text = fh.read()

violations = record_lint.skill_verdict_reason_check(record_text, mounted)

if not violations:
    sys.exit(0)

out = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": (
            "skill-verdict-guard: 이 세션에 마운트된 스킬 "
            + ", ".join(mounted) + " 마다 " + rel + " 에 "
            "`skill-verdict: <name> — applied: ... | not-applicable: ...` "
            "줄이 하나씩 필요하다 -- " + " / ".join(violations) + " "
            "-- 자세한 형태는 docs/handbooks/skill-verdict-obligation.md 참고."
        ),
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

SVG_PAYLOAD="$payload" SVG_REPO="$REPO" SVG_GATES_DIR="$gates_dir" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
