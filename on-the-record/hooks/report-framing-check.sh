#!/usr/bin/env bash
# Stop: checks a PR/board report turn's last_assistant_message for the
# four semantic-effect framing elements (issue #320) — resolved problem,
# prior cost, newly possible, still broken — plus, since issue #2044, a
# fifth skills-utilization element when the closed issue's own session(s)
# mounted >=1 skill. Detects a report turn by the run.md step-5 header
# (1단계/2단계) or the Mission Board line shape (`[이슈 #<n>] ... · <stage>
# → <next>`). Not a report turn -> no-op.
#
# This checks the live reply directly, complementing the grep-based
# instruction-text check in gates/test_report_framing_check.py (which
# only verifies run.md still carries the instruction, not that a given
# reply complied with it).
#
# Mounted-skill detection (issue #2044): the orchestrator's own reply
# carries no mounted-skill list of its own — that only ever exists in a
# ROLE session's transcript (skill-verdict-guard.sh's territory, issue
# #2039). What the orchestrator DOES have is the role's landed record,
# which carries one `skill-verdict: <name> — applied: ... |
# not-applicable: ...` line per mounted skill (issue #2039). So: pull
# every `이슈 #<n>` cited in this reply, and if any
# docs/issue-<n>/reports/**/*.md file under the repo root already carries
# a skill-verdict line, this report is for a >=1-mounted-skill delivery
# and must itself carry a skills-utilization element. A zero-skill
# delivery (no skill-verdict line anywhere under the cited issue's
# reports/) is unaffected — same shape-only, never-judges-content
# posture as skill-verdict-guard.sh.
#
# Fails closed (trap remaps non-0/2 exit to 2), matching stop-gate.sh's
# house style. Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

command -v python3 >/dev/null 2>&1 || exit 2

REPO="$(pwd -P)"

IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, re, sys

try:
    e = json.loads(os.environ.get("REPORT_FRAMING_PAYLOAD", ""))
except ValueError:
    sys.exit(2)
if not isinstance(e, dict):
    sys.exit(2)

# Issue #1725: honor the Stop-hook contract's stop_hook_active field --
# the harness treats ANY Stop additionalContext/decision:"block" as
# inject-and-resume, so a forced-retry turn must emit nothing at all.
# Mirrors #1718's decision-queue-stopgate.sh placement: before any other
# field of e is read.
if e.get("stop_hook_active"):
    sys.exit(0)

msg = e.get("last_assistant_message")
if not isinstance(msg, str) or not msg:
    sys.exit(0)

REPORT_TRIGGER = re.compile(
    r"(1단계|2단계|\[이슈\s*#\d+\].*·.*→)",
)
if not REPORT_TRIGGER.search(msg):
    sys.exit(0)

ELEMENTS = {
    "resolved problem": re.compile(
        r"(해결|제거|고쳐|fix(ed|es)?|resolv(ed|es)|no longer)", re.IGNORECASE),
    "prior cost": re.compile(
        r"(비용|지장|치렀|겪었|used to|cost|previously|고통)", re.IGNORECASE),
    "newly possible": re.compile(
        r"(새로 가능|이제.*가능|newly possible|now (possible|can)|가능해)",
        re.IGNORECASE),
    "still broken": re.compile(
        r"(남았|아직.*(안|못)|여전히|still (broken|open|missing|todo)|"
        r"not (yet|done))", re.IGNORECASE),
}

# issue #2044: a fifth element, gated on whether any issue this reply
# cites already has a mounted-skill record (a skill-verdict: line under
# docs/issue-<n>/reports/**, issue #2039). Repo-scan errors (no repo,
# unreadable dir, ...) degrade to "not mounted" -- this hook never
# refuses a report over its own scan failure.
_SKILL_VERDICT_LINE = re.compile(
    r"(?i)^\s*[-*]?\s*skill-verdict\s*:\s*.+?\s*—")
_ISSUE_NUM = re.compile(r"이슈\s*#(\d+)")

repo = os.environ.get("REPORT_FRAMING_REPO", "")
mounted_delivery = False
if repo:
    for n in set(_ISSUE_NUM.findall(msg)):
        reports_dir = os.path.join(repo, "docs", f"issue-{n}", "reports")
        if not os.path.isdir(reports_dir):
            continue
        for dirpath, _dirnames, filenames in os.walk(reports_dir):
            for fn in filenames:
                if not fn.endswith(".md"):
                    continue
                try:
                    with open(os.path.join(dirpath, fn), "r",
                              encoding="utf-8-sig", errors="replace") as fh:
                        text = fh.read()
                except OSError:
                    continue
                if any(_SKILL_VERDICT_LINE.match(line)
                       for line in text.splitlines()):
                    mounted_delivery = True
                    break
            if mounted_delivery:
                break
        if mounted_delivery:
            break

if mounted_delivery:
    ELEMENTS["skills-utilization"] = re.compile(
        r"스킬.{0,120}(적용|not-applicable|해당\s*없|미해당|사용)",
        re.IGNORECASE | re.DOTALL)

missing = [name for name, pat in ELEMENTS.items() if not pat.search(msg)]

if not missing:
    sys.exit(0)

reason = (
    "report-framing-check: this PR/board report is missing framing "
    "element(s): " + "; ".join(missing) + ". Per issue-320, frame the "
    "change as resolved problem, prior cost, newly possible, and "
    "still broken — not just an address-only enumeration."
)
if "skills-utilization" in missing:
    reason += (
        " This delivery mounted >=1 skill (issue #2039's skill-verdict "
        "lines found under docs/issue-<n>/reports/) -- per issue #2044, "
        "also state which skills were mounted, applied where/how, or "
        "judged not-applicable and why, sourced from those skill-verdict "
        "lines."
    )

out = {
    "decision": "block",
    "reason": reason,
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

REPORT_FRAMING_PAYLOAD="$payload" REPORT_FRAMING_REPO="$REPO" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
