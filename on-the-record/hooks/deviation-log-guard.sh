#!/usr/bin/env bash
# Stop: no-traceless-deviation invariant for issue #803's deviation loop
# (docs/issue-803/proposals/2026-08-11-self-driven-deviation-loop.md,
# docs/issue-803/proposals/2026-08-12-implementation-deviation-loop.md).
#
# Same fail-closed trap / ORCHESTRATE_OFF kill switch / CLAUDE_ROLE-unset
# orchestrator-only gate as stop-gate.sh's skeleton — but stop-gate.sh's
# own check mechanism (last_assistant_message text only, no file/git
# access) cannot maintain a "no matching deviation-log append this turn"
# fact (warrant hunt finding,
# docs/issue-803/reports/implementation/2026-08-12-hunt-implementation-deviation-loop.md,
# stance 3). This guard instead follows product-capture-stopgate.sh's
# mechanism: reads transcript_path off the raw Stop event JSON, scans the
# transcript for a recognized-deviation marker, and separately checks via
# git diff / git log -p against the deviation-log path(s) whether a
# matching append actually landed.
#
# Deviation-log path split mirrors consult-log.md's existing split exactly
# (docs/issue-<n>/reports/deviation-log.md when issue-scoped, else
# docs/reports/deviation-log.md).
#
# Refuses via hookSpecificOutput.additionalContext, never decision:"block"
# — matching stop-gate.sh's own house-style rationale that a heuristic
# misfire on unusual phrasing should not discard the whole turn.
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

repo = os.environ.get("DEVLOG_GUARD_REPO", "")

# Recognized-deviation marker: the assistant's own turn text stating one
# of the deviation-loop's classification outcomes (inline/filed) for a
# concrete deviation — mirrors the RECOGNIZE/CLASSIFY vocabulary in
# directive.sh's injected paragraph and docs/handbooks/deviation-loop.md.
MARKER_RE = re.compile(
    r"(deviation[^.\n]{0,80}(inline-fix|file-as-issue|inline fix|filed as"
    r"\s+(an\s+)?issue)|"
    r"(inline-fix|file-as-issue)[^.\n]{0,80}deviation)",
    re.IGNORECASE,
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


marker_found = False
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
            if not isinstance(entry, dict) or entry.get("type") != "assistant":
                continue
            message = entry.get("message")
            if not isinstance(message, dict):
                continue
            text = flat_text(message.get("content"))
            if not text:
                continue
            if MARKER_RE.search(text):
                marker_found = True
                break
except OSError:
    sys.exit(0)

if not marker_found:
    sys.exit(0)

branch_r = subprocess.run(
    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    cwd=repo, capture_output=True, text=True, timeout=10,
)
branch = branch_r.stdout.strip() if branch_r.returncode == 0 else ""
branch_m = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
if branch_m:
    rel = os.path.join("docs", f"issue-{branch_m.group(1)}", "reports", "deviation-log.md")
else:
    rel = os.path.join("docs", "reports", "deviation-log.md")

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

if added_lines > 0:
    sys.exit(0)

out = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": (
            "deviation-log-guard: this turn's transcript names a recognized "
            "deviation (inline-fix or file-as-issue) but " + rel + " gained "
            "no new line. Append the deviation-log entry (timestamp, "
            "inline/filed/resolved, description, and for filed/resolved the "
            "issue number/role/PR) before ending the turn — see "
            "docs/handbooks/deviation-loop.md."
        ),
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

STOP_PAYLOAD="$payload" DEVLOG_GUARD_REPO="$REPO" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
