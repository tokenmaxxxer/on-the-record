# Survey — issue #1991: guidance-reflection rubric + multi-judge reflection scoring

## Write set surveyed

scripts/, gates/, docs/, tests/ (per issue scope). New artifacts:
scripts/measure_skill_reflection.py (the script named in Acceptance), a
new test module under gates/ or tests/ (name TBD in proposal), this
survey, and the phase-1 proposal — the last two land under this
session's own issue-1991 docs tree.

## Existing invocation-measurement lineage (docs/issue-1960)

canonical: scripts/measure_skill_invocation.py (read in full, this
session). Its shape: reads ~/.tokenmaxxxer/work/*.session*.log JSONL
transcripts, or explicit paths via sys.argv[1:]. Per session it scans
JSONL lines directly (no schema import): pulls the `mounted` skill list
from the `"subtype":"init"` line's `"plugins"` array (filtered to paths
containing /skill-registry/skills/), and a raw `skill_calls` count from
lines carrying `"name":"Skill"` + `"type":"tool_use"`. It prints one
json.dumps(...) line per session — status "measured" with
mounted/mounted_count/skill_calls, or status "unmeasurable" with a
reason (stat-failed, no-init-plugins-line). Every input log yields
exactly one output row; nothing is silently dropped.

canonical: docs/issue-1960/reports/execution-observation/baseline-measurement.md
and its sibling survey.md (read this session) — both confirm the
calling convention above: explicit log paths as argv, or the 40 most
recent deduplicated logs under WORK_DIR by default.

canonical: `find . -iname "test_measure_skill*"` (run this session, no
output) — no test module accompanies measure_skill_invocation.py today.
That script measures invocation only (mounted vs. called), not whether
guidance was actually followed. #1991 targets that harder, qualitative
question.

## Consult basis (issue #1978 deferral + 2026-08-22 requirements-engineering consult)

canonical: `tail -5 docs/reports/consult-log.md` (run this session) —
the shared log's latest row is 2026-08-21T22:16; the 2026-08-22 entry
the issue body cites is not present in this checkout (issue-scoped
consults route to a per-issue log instead, and #1991 has none yet). The
issue body's own paraphrase is what this survey works from: "S1
necessary-condition framing; multi-judge required; rubric-first." Read
as three constraints:

1. Rubric-first — the grading criteria (what "reflected" means, and the
   yes/no/partial boundary) are written down and stable before any
   judge call runs against them.
2. Multi-judge required — a single judge call carries self-grading-bias
   risk if the judge and the builder role share a lens; the issue body
   proposes 2-3 consult calls with distinct lenses, majority.
3. Necessary-condition (S1) framing — reflection is scored on whether
   the deliverable/record exhibits behavior a mounted skill's rules
   would require, not whether the session mentions the skill by name.

canonical: `grep -n -i "rubric\|deferred\|reflection"
docs/issue-1978/reports/implementation.md
docs/issue-1978/proposals/spawn-directive-single-phase-and-skill-trigger-lines.md`
(run this session, no output) — issue #1978's landed record delivered
the single-phase signal + per-skill trigger lines and carries no rubric
text. #1991's "guidance-reflection rubric #1978 deferred" phrase
describes a scope boundary #1978 declined to cross, not a pointer to
prose sitting somewhere in #1978's own tree; this proposal drafts the
rubric fresh.

## spawn.py consult mechanism (candidate judge-call substrate)

canonical: spawn.py:consult_cmd (source read this session, line 5658)
and the trace rows in docs/reports/consult-log.md above
(role=requirements-engineering / role=architecture entries) — this is
the existing one-shot judgment-only call shape: a role, a question, a
JSON judgment outcome, logged, no repository write. It is a plausible
substrate for "3 consult calls with distinct lenses" but is a live
subprocess call into a role session — expensive and non-deterministic
per call, which is why Acceptance requires "judges mockable": the new
script's judge-invocation must be swappable for a fake in tests, not
hard-wired to a live spawn.py consult subprocess call.

## No prior per-issue tree for #1991

canonical: `find docs -path "*1991*"` (run this session, before this
session created the tree) returned no rows — a fresh subject with no
earlier phase-1 or phase-2 record to reconcile against.

## Gap this proposal works from

canonical: the three canonical reads above (measure_skill_invocation.py
source, the #1978 grep, and the consult-log tail) taken together — no
rubric document exists, no multi-judge majority mechanism exists, and
none of this repo's judge call sites (spawn.py consult) are wrapped in
a mockable interface today. The new script needs its own thin
judge-call seam (default: shell to spawn.py consult; test-injectable
via a parameter) to satisfy "judges mockable" without duplicating
spawn.py's subprocess plumbing. No test module exists yet asserting
majority behavior over mocked judge votes. The empty-state rule ("a
session with zero mounted skills yields an explicit not-applicable
row, never an empty silent skip") mirrors measure_skill_invocation.py's
own "every input log produces exactly one output row" discipline — a
design constraint already validated by the sibling script's shape, not
a novel judgment call.
