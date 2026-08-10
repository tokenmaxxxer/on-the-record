#!/usr/bin/env bash
# Stop: nudge the orchestrator session to record requirements/priorities/
# philosophy/goals stated during the conversation into
# docs/product/<category>.md, when a category was flagged in this
# session's user turns but the corresponding doc file gained no new line.
# Issue #566, carrying architecture's design
# (docs/issue-566/proposals/architecture.md, merged PR #569) verbatim:
# hook name, transcript-walk payload, four-category EN+KO vocabulary,
# git-diff cross-check, bootstrap-on-first-flag, advisory-only output.
#
# Reads transcript_path off the raw Stop event JSON (additive to the
# existing *_PAYLOAD-env convention other Stop hooks here use) and walks
# the transcript JSONL for type=="user" entries with plain-string content
# (tool-result entries are also type:"user" but carry structured content,
# not authored text, and are skipped).
#
# Same kill-switch/fail-closed skeleton as decision-queue-stopgate.sh:
# no-op on CLAUDE_ROLE set, honors ORCHESTRATE_OFF, trap-based exit-code
# remap to 2 on unexpected failure. Advisory only
# (hookSpecificOutput.additionalContext), never decision:"block" —
# architecture's cross-check section states this explicitly.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
payload="$(cat 2>/dev/null || true)"

command -v python3 >/dev/null 2>&1 || exit 2

REPO="$(pwd -P)"

IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, re, subprocess, sys

try:
    e = json.loads(os.environ.get("STOP_PAYLOAD", ""))
except ValueError:
    sys.exit(2)
if not isinstance(e, dict):
    sys.exit(2)

transcript_path = e.get("transcript_path")
if not isinstance(transcript_path, str) or not transcript_path:
    sys.exit(0)
if not os.path.isfile(transcript_path):
    sys.exit(0)

repo = os.environ.get("PRODUCT_CAPTURE_REPO", "")

CATEGORIES = {
    "requirements": (
        re.compile(
            r"(이\s*프로젝트|이\s*시스템|the (project|system|app|service)|"
            r"we (need|must|should build))",
            re.IGNORECASE,
        ),
        re.compile(
            r"(must|should|need(s)? to|해야|필요합니다|required|requirement)",
            re.IGNORECASE,
        ),
    ),
    "priorities": (
        re.compile(
            r"(더\s*중요|우선순위|prioriti(z|s)e|more important than|"
            r"comes first|먼저\s*처리|takes precedence)",
            re.IGNORECASE,
        ),
        None,
    ),
    "philosophy": (
        re.compile(
            r"(철학은|원칙은|the (point|philosophy|principle) is|"
            r"우리는\s*.*라고\s*믿|we believe|기본적으로\s*.*지향)",
            re.IGNORECASE,
        ),
        None,
    ),
    "goals": (
        re.compile(
            r"(목표는|goal is|aim(ing)? (for|to)|achieve|달성하고자|"
            r"success looks like)",
            re.IGNORECASE,
        ),
        None,
    ),
}

SENT_SPLIT = re.compile(r"[.!?\n]")


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


flagged = {cat: [] for cat in CATEGORIES}

try:
    with open(transcript_path, "r", encoding="utf-8", errors="replace") as fh:
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
            content = message.get("content")
            text = flat_text(content)
            if not text:
                continue
            for sentence in SENT_SPLIT.split(text):
                sentence = sentence.strip()
                if not sentence:
                    continue
                for cat, (anchor_re, modal_re) in CATEGORIES.items():
                    if not anchor_re.search(sentence):
                        continue
                    if modal_re is not None and not modal_re.search(sentence):
                        continue
                    flagged[cat].append(sentence)
except OSError:
    sys.exit(0)

active = {cat: sents for cat, sents in flagged.items() if sents}
if not active:
    sys.exit(0)

unrecorded = []
for cat, sents in active.items():
    doc_path = os.path.join(repo, "docs", "product", f"{cat}.md")
    if not os.path.isfile(doc_path):
        os.makedirs(os.path.dirname(doc_path), exist_ok=True)
        title = cat.capitalize()
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(f"# {title}\n\nAppend-only, newest entry last.\n")

    rel = os.path.join("docs", "product", f"{cat}.md")
    added_lines = 0
    for args in (
        ["git", "diff", "--unified=0", "--", rel],
        ["git", "log", "-1", "--format=", "-p", "--", rel],
    ):
        try:
            r = subprocess.run(
                args, cwd=repo, capture_output=True, text=True, timeout=10
            )
        except (OSError, subprocess.SubprocessError):
            continue
        for out_line in r.stdout.splitlines():
            if out_line.startswith("+") and not out_line.startswith("+++"):
                added_lines += 1
    if added_lines == 0:
        excerpt = sents[0][:120]
        unrecorded.append((cat, excerpt))

if not unrecorded:
    sys.exit(0)

parts = [f"{cat}.md (e.g. \"{excerpt}\")" for cat, excerpt in unrecorded]
out = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": (
            "product-capture-stopgate: statements matching these categories "
            "were not reflected in docs/product/: " + "; ".join(parts) + ". "
            "Record them as structured entries before ending the turn."
        ),
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

STOP_PAYLOAD="$payload" PRODUCT_CAPTURE_REPO="$REPO" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
