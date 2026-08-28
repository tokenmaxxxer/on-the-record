#!/usr/bin/env bash
# Stop: per-mounted-skill verdict obligation (issue #2039,
# docs/issue-2039/proposals/2026-08-22-per-skill-verdict-obligation.md).
#
# issue #2576: mounted-skill identity now comes straight from $MUSTER_SKILLS
# (pipeline.py:723, set on the spawned session's own process env from
# skill_dirs basenames) rather than scraping the two natural-language
# mounted-skill sentences spawn.py used to print into the first user
# message — that text is still shown to the model as a human-readable
# explanation, but was never a stable machine interface (a wording change
# at either assembly point silently emptied `mounted` here, with no
# error). $MUSTER_SKILLS is this Stop hook's own process env — it is a
# session-side signal same as before, not a gates.py CI-diff scan, just
# read directly instead of re-derived from prose. Delegates the actual
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
#
# issue #2681: #2153's narrowing has a floor at zero -- invoke one skill
# and you owe a verdict for it, invoke none and (before this change) you
# owed nothing AND produced nothing, byte-identical to the zero-mounted
# path below. A wrong-but-uninvoked skill was therefore invisible from
# every artifact this hook produces for the rest of the session. The
# zero_invocation_notice() below is the fix's entire surface: advisory
# only (additionalContext, never decision:"block" -- measured, issue's
# own "must not": the zero-invocation case is the minority on this
# machine's retained local session sample, 0/47 landed skill-composed
# records lacked a skill-verdict line, so a blocking gate would strand
# rare, hard-to-recover work for a signal that mostly wouldn't fire
# anyway), does not resurrect the per-mounted-skill verdict obligation
# #2153 removed (still no verdict line is owed), and makes no judgment
# about whether any mounted skill was appropriate -- it only makes the
# fact of non-use visible where it previously produced nothing.
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


def mounted_skill_names():
    """issue #2576: $MUSTER_SKILLS (pipeline.py:723) is this session's own
    process env, set from `skill_dirs` basenames at spawn time — the
    structured mounted-skill list, not the two natural-language sentences
    spawn.py prints for the model to read. Empty/unset (a session with
    zero matched skills, including zero always-on policy skills — an
    edge case, since policy skills like work-in-english are themselves
    task-triggered) yields an empty tuple, same as before."""
    raw = os.environ.get("MUSTER_SKILLS", "")
    return tuple(s for s in (p.strip() for p in raw.split(",")) if s)


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
        "filed, leaves exactly one entry appended to the path "
        "`spawn.py deviation-log-path --issue <n>` prints (issue #2348: "
        "sharded per session, role-scoped when $CLAUDE_ROLE is set; issue "
        "#803/#983/#2348, docs/handbooks/deviation-loop.md). "
        "(2) product capture — requirements/priorities/philosophy/goals "
        "the user stated this session are recorded into "
        "docs/reports/product/<category>.md before the session ends "
        "(issue #566; priorities is sharded per entry since issue #2637 -- "
        "`spawn.py priorities-path` prints where a new entry goes)."
    )


reminder = obligations_reminder(e.get("session_id"))

mounted = mounted_skill_names()


# issue #2681: distinguishes "mounted N skills, invoked zero" from
# "mounted zero skills" -- both used to be byte-identical (nothing, or at
# most the folded obligations reminder). Advisory only; never a
# requirement, never a judgment of appropriateness.
def zero_invocation_notice(mounted_names):
    return (
        "skill-verdict-guard: zero-invocation (issue #2681) -- this "
        f"session mounted {len(mounted_names)} skill(s) ("
        + ", ".join(mounted_names) + ") and invoked none of them via the "
        "Skill tool. Advisory only: no skill-verdict line is owed (issue "
        "#2153's narrowing stands) and this is not a judgment that any of "
        "them applied or didn't -- if one does apply, invoke it via the "
        "Skill tool before ending; if none do, no action is needed."
    )


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
# no skill-verdict line. issue #2681: that no longer means byte-identical
# to the zero-mounted path above -- the notice makes the zero-invocation
# fact visible without adding any new obligation.
if not invoked:
    finish(zero_invocation_notice(mounted), reminder)

if not gates_dir:
    sys.exit(2)
try:
    sys.path.insert(0, gates_dir)
    import record_lint
except ImportError:
    sys.exit(2)

# --- prefer the .on-the-record/role.json lease sidecar (issue #1814) -------
issue_n, role = None, None
try:
    with open(os.path.join(repo, ".on-the-record", "role.json"), encoding="utf-8") as f:
        sidecar = json.load(f)
    if (isinstance(sidecar, dict) and isinstance(sidecar.get("role"), str)
            and isinstance(sidecar.get("issue"), int)):
        issue_n, role = sidecar["issue"], sidecar["role"]
except (OSError, ValueError):
    pass

if role is None:
    branch_r = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo, capture_output=True, text=True, timeout=10,
    )
    branch = branch_r.stdout.strip() if branch_r.returncode == 0 else ""
    branch_m = re.match(r"^issue-(\d+)/([^/]+)$", branch)
    if not branch_m:
        finish(reminder)
    issue_n, role = int(branch_m.group(1)), branch_m.group(2)
rel = os.path.join("docs", f"issue-{issue_n}", "reports", f"{role}.md")

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
