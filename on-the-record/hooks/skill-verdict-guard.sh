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
# issue #2138 (gate retirement): this hook is the MERGED OBLIGATIONS
# Stop gate — deviation-log-guard.sh (issue #803/#983, no-traceless-
# deviation) and product-capture-stopgate.sh (issue #566, product-
# statement capture) were demoted from standalone Stop hooks and their
# normative content folded here as a once-per-session advisory reminder
# (additionalContext, never blocking), keyed on the Stop payload's
# session_id under ~/.claude/tokenmaxxxer/obligations-noted/.
#
# Zero mounted skills -> the skill-verdict check is skipped (byte-inert
# per the proposal's Constraints); the folded obligations reminder can
# still emit once. Refuses via hookSpecificOutput.additionalContext,
# never decision:"block" -- same house style as deviation-log-guard.sh.
# Same fail-closed trap / ORCHESTRATE_OFF kill switch as its sibling hooks.
#
# issue #2153: the required set narrows from "every mounted skill" to
# "every skill this session actually invoked via the Skill tool" -- a
# mounted-but-never-invoked skill needs no skill-verdict line at all (a
# 'not-applicable' row for it answered no audit question; see the issue's
# live measurement). Invocation is detected by scanning the FULL
# transcript (not just the first user message) for assistant tool_use
# blocks named "Skill", intersected against the mounted-name set so a
# stray/typo'd tool call can't manufacture a new requirement.
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


_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def extract_names(line_body):
    """`line_body` is everything after the assembly point's own colon
    (e.g. "이슈 #1742/#1774): a, b (...), c — Use ...trigger., ...").

    Issue #2057: a naive split on every comma fragments a skill's own
    trigger sentence -- spawn.py:8318-8361 joins entries with ", " but
    each entry's optional trigger is itself free text that commonly
    contains internal commas (e.g. "Use when a class's coupling ...
    crosses a threshold, a caller chains ..."). spawn.py's own trigger
    regex (`_SKILL_USE_SENTENCE_RE = r"(Use\\b[^.]*\\.)"`) guarantees a
    trigger never contains a literal "." except its own terminating one,
    so a trigger's internal commas can be told apart from a real
    top-level, entry-separating comma: only split on a comma that sits
    outside both parens (depth 0) AND outside an unterminated "Use ..."
    trigger sentence.
    """
    # Drop the leading "이슈 #.../..): " citation clause before the
    # actual comma-joined name list, if present.
    m = re.match(r"^[^:]*:\s*(.*)$", line_body)
    body = m.group(1) if m else line_body
    # spawn.py's role-mapping line inserts a literal "스킬 " label before
    # the actual comma-joined name list (the --skills line has no such
    # label) -- strip it so it isn't parsed as part of the first name.
    body = re.sub(r"^스킬\s+", "", body)

    parts = []
    depth = 0
    in_use = False
    start = 0
    n = len(body)
    i = 0
    while i < n:
        ch = body[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif not in_use and depth == 0 and body[i:i + 4] == "Use ":
            in_use = True
        elif in_use and ch == ".":
            in_use = False
        elif ch == "," and depth == 0 and not in_use:
            parts.append(body[start:i])
            start = i + 1
        i += 1
    parts.append(body[start:])

    names = []
    for item in parts:
        item = item.strip()
        if not item:
            continue
        item = re.split(r"\s+—\s+|\s+\(", item, maxsplit=1)[0].strip()
        # A real skill name is a bare identifier token -- discard any
        # split remainder still carrying spaces/parens/prose (e.g. the
        # trailing "(skill-repository <sha>) 가이던스만 붙는다 ..." tail
        # and cross-family parenthetical, which name no new skill).
        if item and _NAME_RE.match(item):
            names.append(item)
    return names


# issue #2153: only a skill actually invoked via the Skill tool this
# session owes a skill-verdict line. Scans every assistant transcript
# entry (not just the first user message) for a tool_use block named
# "Skill", pulling the invoked name out of its input.skill argument.
def invoked_skill_names(path, mounted_set):
    names = []
    seen = set()
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
                if not isinstance(entry, dict) or entry.get("type") != "assistant":
                    continue
                message = entry.get("message")
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use" or block.get("name") != "Skill":
                        continue
                    tool_input = block.get("input")
                    if not isinstance(tool_input, dict):
                        continue
                    name = tool_input.get("skill")
                    if (isinstance(name, str) and name in mounted_set
                            and name not in seen):
                        seen.add(name)
                        names.append(name)
    except OSError:
        return []
    return names


# issue #2138: folded obligations reminder (deviation-log #803/#983 +
# product-capture #566, both demoted from standalone Stop hooks). Emitted
# at most once per session, advisory only.
def obligations_reminder(session_id):
    if not isinstance(session_id, str) or not session_id:
        return None
    import hashlib
    marker_dir = os.path.expanduser("~/.claude/tokenmaxxxer/obligations-noted")
    marker = os.path.join(
        marker_dir,
        hashlib.sha256(session_id.encode("utf-8", "surrogatepass")).hexdigest()[:24],
    )
    if os.path.exists(marker):
        return None
    try:
        os.makedirs(marker_dir, exist_ok=True)
        with open(marker, "w") as fh:
            fh.write("noted")
    except OSError:
        return None
    return (
        "obligations (advisory, issue #2138 merged Stop gate): "
        "(1) no traceless deviation — every mid-task deviation, inline or "
        "filed, leaves exactly one line in the deviation log "
        "(docs/issue-<n>/reports/deviation-log.md, or "
        "docs/reports/deviation-log.md with no issue; issue #803/#983, "
        "docs/handbooks/deviation-loop.md). "
        "(2) product capture — requirements/priorities/philosophy/goals "
        "the user stated this session are recorded into "
        "docs/reports/product/<category>.md before the session ends "
        "(issue #566)."
    )


reminder = obligations_reminder(e.get("session_id"))

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

def finish(*parts):
    parts = [p for p in parts if p]
    if not parts:
        sys.exit(0)
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": "\n".join(parts),
        }
    }))
    sys.exit(0)


if not mounted:
    finish(reminder)

invoked = invoked_skill_names(transcript_path, set(mounted))

# issue #2153: a mounted skill this session never actually invoked owes
# no skill-verdict line -- byte-unaffected same as the zero-mounted path.
if not invoked:
    finish(reminder)

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
    finish(reminder)
role = branch_m.group(2)
rel = os.path.join("docs", f"issue-{branch_m.group(1)}", "reports", f"{role}.md")

record_file = os.path.join(repo, rel)
record_text = ""
if os.path.isfile(record_file):
    with open(record_file, "r", encoding="utf-8-sig", errors="replace") as fh:
        record_text = fh.read()

violations = record_lint.skill_verdict_reason_check(record_text, invoked)

verdict_text = None
if violations:
    verdict_text = (
        "skill-verdict-guard: 이 세션에서 실제로 호출한(invoked) 스킬 "
        + ", ".join(invoked) + " 마다 " + rel + " 에 "
        "`skill-verdict: <name> — applied: ... | not-applicable: ...` "
        "줄이 하나씩 필요하다 (마운트만 되고 호출하지 않은 스킬은 이 "
        "줄이 필요 없다 — 이슈 #2153) -- " + " / ".join(violations) + " "
        "-- 자세한 형태는 docs/handbooks/skill-verdict-obligation.md 참고."
    )
finish(verdict_text, reminder)
PY

SVG_PAYLOAD="$payload" SVG_REPO="$REPO" SVG_GATES_DIR="$gates_dir" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
