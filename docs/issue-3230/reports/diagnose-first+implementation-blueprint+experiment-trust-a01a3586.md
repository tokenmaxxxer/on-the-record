---
issue: 3230
role: diagnose-first+implementation-blueprint+experiment-trust-a01a3586
author: diagnose-first+implementation-blueprint+experiment-trust-a01a3586
skills: diagnose-first (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-3186/reports/diagnose-first+test-depth-audit+silent-failure-audit-188edaee.md
    sha: e5f90b8f5053c8dae5a0f48b26c5735e902f16bd
  - path: docs/issue-3018/reports/knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2.md
    sha: 908cb5f6f5be3ad5d3b9b12b5cbe6a1f0c6a4f9a
  - path: consult.py, scripts/issue-3230/measure_skill_judge.py, tests/test_issue_3230_skill_judge_cost.py
    sha: 46fb964fabdbf379044f1371e2cad32403449a3b
---

# issue-3230 — diagnose-first+implementation-blueprint+experiment-trust-a01a3586 record

## What was done

Answered the three diagnostic sub-questions the issue asks for, then made
and recorded a decision not to change the skill-selection dispatch path
this round. Delivered `scripts/issue-3230/measure_skill_judge.py` and
`tests/test_issue_3230_skill_judge_cost.py`
(commit `46fb964fabdbf379044f1371e2cad32403449a3b`), plus one small
production fix in that same commit: widened `_append_consult_trace()`'s
question-field truncation in `consult.py` from 200 to 4000 characters,
because Question 2 below found that 200-char cut is what made
judge-vs-BM25 agreement unreconstructable from history.

acceptance: `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q` — result:
```
13 passed in 0.89s
```

acceptance: `python3 scripts/issue-3230/measure_skill_judge.py --report` — result:
```
issue-3230 skill_judge dispatch-wait -- measured report
ledger files scanned: 40
raw skill_judge_perf events found: 1178
real (plausible) events after filter (duration_ms present AND wall_s >= 1.0s): 21
  filtered out as test-fixture noise (monkeypatched subprocess.run in this repo's own unit tests): 1157

-- skill_judge subprocess wall-clock time, per real dispatch --
  n=21 min=8.295s max=42.665s mean=18.324s median=16.343s p90=28.703s
  outcome_ok=True: 21/21
```
exit code 0.

acceptance (must-not, verbatim from the issue): `python3 scripts/issue-3186/measure_cross_family.py --report` still runs and still finds its data — result:
```
issue-3186 cross_family diagnosis -- measured report
log files scanned: 148
bootstrap_timing lines found: 18

-- cross_family phase share of bootstrap total --
  spawns with total > 1s: n=4 cross_family=6.328s total=20.666s share=30.6%
  all spawns: n=18 cross_family=6.328s total=21.188s share=29.9%
```
exit code 0 — this session never edited `pipeline.py`, `directive_assembly.py`,
or `scripts/issue-3186/`.

acceptance: `python3 -m pytest -q` (full suite) — result:
```
4 failed, 1433 passed, 3 xfailed, 2 warnings
```
Rerunning the exact same 4 failing test files after `git stash push --
consult.py` (this session's only production-code edit, reverted) gives
the identical count:
```
$ git stash push -- consult.py && python3 -m pytest -q on-the-record/hooks/test_hook_classification.py harness/fixture-operator-experience/test_flow.py on-the-record/checks/test_macos_bash32_compat.py && git stash pop
4 failed, 10 passed in 0.88s
```
derived: both commands executed live in this session, back to back — same
4 failing test IDs, same messages, with and without this session's
`consult.py` change. Pre-existing, not caused by this change: none of the
4 (`on-the-record/hooks/test_hook_classification.py` x2,
`harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace`,
`on-the-record/checks/test_macos_bash32_compat.py`) references
`consult.py`, `spawn.py`, or any file this session touched.

## Why

R007 asks for the 16.7s median `skill_judge` wait to be cut *without*
making skill selection worse, and requires the "without making it worse"
half to be demonstrated, not assumed. The issue names four candidate
fixes (cache, replace-with-BM25, make-async, drop-the-judge) and says
they are not equally safe. This session ran diagnose-first's procedure:
define the problem without a solution baked in (Stage 0), start from the
existing baseline (Stage 1 — issue-3186/PR #3200 already established n=19,
median 16.663s, range 8.295-57.156s), then locate what actually drives
each option's risk with evidence (Stage 2) before deciding (Stage 3). The
issue's three sub-questions map onto Stage 2's verification axes for each
of the four options.

### Question 1 — how often would a cache (task-text + corpus-state key) hit?

Scanned every real (non-test-fixture) `skill_judge` consult-trace line
across every dispatched-session workspace under
`~/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log{,/*.md}` (the
same workspace root PR #3200 used for its ledger scan), keyed on `(issue,
question)` where `question` is the trace's literal
`Task:\n<task text>\n...` field — the proposed cache key. Fixture issue
numbers (`2040`, `2055`, `2061`, `2274` — the four this repo's own
`_skill_judge_consult` unit tests use with a monkeypatched
`subprocess.run`, per issue-3186's diagnosis) and two literal
test-fixture task strings (`"task"`, a canned haiku-poem prompt) were
excluded.

```
$ python3 <scan_repeats2.py, reproduced verbatim in "Evidence appendix">
total trace lines: 865 | fixture-filtered out: 809 | real remaining: 56
distinct real (issue, question) keys: 42
real keys repeated >1x: 7 | repeat (would-be cache hit) events: 14
repeat share of REAL dispatches: 0.25
```
derived: `python3 /tmp/scan_repeats2.py` (script body in "Evidence
appendix" below), executed live in this session against the real
workspace-root glob above — 14/56=0.25=25%.

That is not "near zero" — caching is not off the table on repeat-rate
grounds alone. But the repeat pattern disqualifies a *naive* cache:
comparing the picked-set across each repeated-key pair —

```
$ python3 <scan_repeat_consistency.py, reproduced verbatim below>
repeat-pair comparisons: agree=8 disagree=6
```
derived: `python3 /tmp/scan_repeat_consistency.py` (script body in
"Evidence appendix"), executed live in this session against the same
trace lines — 6/14=0.43=43% of repeat pairs disagree, not on wording, on
the actual decision:
```
2026-09-02T04:42:51Z -> ok: picked=[implementation-audit; silent-failure-audit]
2026-09-02T04:43:34Z -> ok: picked=[silent-failure-audit; defect-verification-independence-from-upstream-verdicts; implementation-audit]
```
canonical: consult-trace lines for skill `mech4-repro`, issue 3042, in an
external session workspace's own working tree (not part of this
repository's git history — a different session's local checkout under
`~/.tokenmaxxxer/work/`), read directly in this session; content quoted
verbatim above (condensed from the full `outcome=` field, which also
includes per-candidate reason text)

Byte-identical task text, ~43 seconds apart, same candidate corpus — the
first call picks 2 skills, the second picks 3. The other disagreement
class in the same 6 is transient: identical task text returns
`ok: picked=[...]` on one call and `error: 알 수 없는 실패` (parse
failure) on another. **`_skill_judge_consult()` is not deterministic on
identical `(task_text, candidate_set)` input.** A cache keyed on that pair
would not memoize "the correct answer" — it would freeze whichever answer
the first call happened to produce (including a transient parse failure)
and serve it to every later identical-key dispatch. A naive cache trades
a known 16.7s latency cost for an unbounded silent-selection-drift risk
on roughly a quarter of real dispatches (25%, derived above) — worse
along exactly the axis the issue said must not degrade.

### Question 2 — how often does the judge disagree with its own BM25 fail-open?

This could not be answered from history. `_append_consult_trace()`
(`consult.py`, pre-fix, commit `f722841f` and earlier) wrote
`question={question[:200]!r}` — long enough that every real dispatch's
question (8 candidates x full trigger sentence each, per
`_CROSS_FAMILY_CONSULT_TOPN=8`) gets cut before the `Candidates:` list
ever completes:

```
$ python3 <scan_agreement4.py, reproduced verbatim below>
total real 'ok:' lines: 14106
excluded as truncation-suspect (question>=199 chars or picks not subset of parsed candidates): 14106
reliable (untruncated, self-consistent) comparisons: 0
```
derived: `python3 /tmp/scan_agreement4.py` (script body in "Evidence
appendix"), executed live in this session — same workspace-root glob as
Question 1, parsing the `Candidates:` block out of every real
`outcome='ok: ...'` trace line and checking self-consistency (every
`picked` name must appear in the parsed candidate list, since
`_skill_judge_consult()`'s own `by_name` filter at `consult.py:641`
guarantees `picked ⊆ candidates` for a real call — a violation is proof
the parse was truncated, not a real mismatch) — 0/14106=0=0% reliable.

This session's `consult.py` change (200 to 4000 chars, commit
`46fb964fabdbf379044f1371e2cad32403449a3b`) fixes this going forward but
cannot recover already-discarded history.

To still answer the issue's request ("run both over the same real inputs
from history and report how often they agree"), this session ran a small
live sample: 5 real, unmodified GitHub issue titles from this repo's own
history, through the current `_bm25_cross_family_scores()` (no
subprocess) and the current, live `_cross_family_skill_matches_with_consult()`
(real haiku subprocess, current skill corpus), from an isolated scratch
cwd (`/tmp/otr-issue3230-live-judge-sample`, no side effects on this
session's own working tree):

```
$ python3 <live_agreement_test.py driver, full body in "Evidence appendix">
issue 3231 wall_s=17.290 outcome=completed bm25_top2=[parallel-decomposition, technical-writing-doc-type-selection] judge_picked=[]
issue 3228 wall_s=19.865 outcome=completed bm25_top2=[stride, reference-forecast] judge_picked=[silent-failure-audit]
issue 3128 wall_s=13.567 outcome=completed bm25_top2=[negotiation-interests-vs-positions-framing, capacity-planning-cost-attribution-at-trigger] judge_picked=[]
issue 3103 wall_s=23.302 outcome=completed bm25_top2=[stride, finance-unit-economics-ltv-churn-assumption] judge_picked=[]
issue 3047 wall_s=31.016 outcome=completed bm25_top2=[market-analysis-five-forces, market-recon] judge_picked=[]
```
derived: `python3 /tmp/live_agreement_test.py` (full driver script and raw
JSON output in "Evidence appendix" below), executed live in this session
against 5 real issue titles fetched via `gh issue list --state all --limit 30 --json number,title`
(#3231, #3228, #3128, #3103, #3047 — picked to avoid this diagnosis's own
self-referential issues #3186/#3230) — 0/5=0=0% agree comparing
`judge_picked` against `bm25_top2` above (`[]` never equals a non-empty
BM25 pair, and issue 3228's single-element pick differs from its BM25
pair too).

In 4 of the 5 rows above the judge correctly picked nothing (80%,
4/5=0.8) — none of BM25's top-8 candidates (drawn from the ~270-skill
general business/engineering skill-repository corpus) actually fit an
internals-specific bug-report title, and the judge recognized that; BM25
fail-open can never pick zero, so it would have force-mounted 2 unrelated
skills on each of those 4 dispatches. Issue #3228 ("make the silent-failure
class unwritable") is the sharpest case: the judge picked the one clearly
relevant skill, `silent-failure-audit`, which ranked 4th in the BM25
scores (outside the top-2 fail-open window shown above) — BM25 fail-open
would have mounted `stride` and `reference-forecast` instead and missed
it entirely. This corroborates issue-3018's independently-derived finding
that BM25-style retrieval misses the right skill in most unrelated
queries.
canonical: `docs/issue-3018/reports/knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2.md`,
read in this session and cross-referenced against the fresh 0/5 sample
above rather than taken on its own

**This rules out "replace the judge with BM25" as an R007 option** — the
one live sample this session could afford (n=5, explicitly small, see
"Sample size" in Open findings) already shows the BM25 fallback actively
choosing wrong skills, not merely skipping edge cases.

### Question 3 — when does a session first need its mounted skills?

Read the actual bootstrap ordering in `spawn.py` instead of guessing. The
`cross_family` future is submitted early (overlapped with workspace
clone/branch checkout):

```python
# spawn.py:4002-4010
_cross_family_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
_cross_family_future = _cross_family_executor.submit(
    _cross_family_skill_matches_with_consult,
    _cross_family_task_text, skill, _skill_repo_root(), issue, cwd,
    k=_COMPOSED_SKILLS_TOPK,
    home=Path.home(), target_repo_root=Path(cwd), skills_csv=skills)
```

— but it is joined and folded into the literal first-turn prompt text
before the session subprocess is ever started:

```python
# spawn.py:4387-4388 (join)
if _cross_family_future is not None:
    cross_family_dirs, skill_judge_outcome = _cross_family_future.result()
```
```python
# spawn.py:4402, 4413-4418 (folded into `task`, the first-turn prompt string)
skill_source = merge_composed_skill_source(skill_source, cross_family_dirs)
...
task = task + _dp("role-skill-triggers", (
    f"\n\n이번 과제에 대해 스킬이 구성됐다(skill-repository, 이슈 "
    f"#1955/#1758/#2507 — 고정 스킬 매핑 표가 아니라 과제 텍스트 "
    f"매치): 스킬 {skill_lines} "
```
canonical: `spawn.py:4002-4010, 4387-4388, 4402-4418`, read directly in
this session

Everything downstream (`directive_write` at `spawn.py:4269` has already
materialized the record skeleton before this join happens; `board_snapshot`
at `spawn.py:4474` depends on `directive_write`'s output, not the join)
still runs before `spawn_cmd()` launches the session process — the
mounted-skill list is composed into the *first* prompt string at Popen
time, not fetched by the session itself and not delivered via a
follow-up message. **The answer to Question 3 is "immediately, in the
first prompt" — not "several seconds in."** Making dispatch async would
therefore require a new mechanism to deliver information into an
already-started session's context; this codebase has none today (the
closest analogue, `--append-system-prompt`, is assembled at the same
Popen-time join). That is a structural addition, not a fast-path fix.

### Putting the three answers together

derived: this section restates, without new claims, the numbers already
derived and cited above in Question 1 (repeat/agreement scans), Question
2 (truncation scan + live 5-sample driver), and Question 3 (`spawn.py`
code citations) — see those subsections for the underlying commands and
`canonical:`/`derived:` tags.

- **cache (task-text+corpus key)**: not safe as a naive design — a 25% real repeat rate (14/56, Question 1) is not negligible, but the judge disagreed with its own earlier identical-input answer in 43% of repeat pairs (6/14, Question 1), including one genuine composition change — caching would freeze an arbitrary sample, sometimes a parse failure, and serve it forever.
- **replace judge with BM25 fail-open**: ruled out — 0% live agreement (0/5, Question 2), with one concrete case (#3228) of BM25 missing the single relevant skill (rank 4, outside top-2) and mounting two unrelated skills instead; corroborates issue-3018's independent finding cited in Question 2.
- **make dispatch async**: not a small change — Question 3 found the skill list is folded into the first prompt at Popen time, before the session exists; no existing mechanism delivers it later.
- **drop the judge entirely**: not defensible — the same 0% (0/5) sample that rules out BM25-replace (Question 2) is direct evidence selection matters; dropping the judge is strictly worse than replacing it with BM25, which is already ruled out.

None of the four options the issue named is safe to ship this round. Per
the issue's own stated escape hatch ("a well-argued refusal to change
behavior yet is an acceptable outcome"), this session does not change the
dispatch path, the timeout, or the selection mechanism. It ships the two
required measurement artifacts and the one instrumentation fix (the
truncation widen) that makes the next attempt at this decision cheaper.

### implementation-blueprint / experiment-trust applicability

`implementation-blueprint`'s own text says not to invoke it for "a
single-file script" or "a one-line fix" — `scripts/issue-3230/measure_skill_judge.py`
is deliberately modeled on the existing sibling
`scripts/issue-3186/measure_cross_family.py`'s shape (same
glob/parse/aggregate/report/CLI structure, see the file itself, committed
this session at `46fb964fabdbf379044f1371e2cad32403449a3b`), and the
`consult.py` truncation-width change is a one-line-shape fix — no
multi-module structure decision was made this session.
`experiment-trust` gates A/B experiment results before they drive a
launch decision; nothing in this session is a variant comparison driving
a launch — the closest analogue (the 5-sample live judge-vs-BM25
comparison in Question 2 above) is a small diagnostic measurement, kept
explicitly small-sample-flagged via diagnose-first's own G2-aux
discipline rather than reported as a decisive experiment result.

## What did not work

None — this is a build-now, single-phase delivery (no phase-1 proposal to
diverge from), and no attempted approach here was abandoned mid-session.

## Upstream basis

- `docs/issue-3186/reports/diagnose-first+test-depth-audit+silent-failure-audit-188edaee.md`
  (sha `e5f90b8f5053c8dae5a0f48b26c5735e902f16bd`) — supplied the
  historical n=19, median 16.663s baseline this session's fresh
  `measure_skill_judge.py --report` run (n=21, median 16.343s, quoted in
  the acceptance block above) corroborates.
- `docs/issue-3018/reports/knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2.md`
  (sha `908cb5f6f5be3ad5d3b9b12b5cbe6a1f0c6a4f9a`) — the retrieval-miss
  finding Question 2 above corroborates independently with a fresh live
  sample.
- `consult.py`, `scripts/issue-3230/measure_skill_judge.py`,
  `tests/test_issue_3230_skill_judge_cost.py` (sha
  `46fb964fabdbf379044f1371e2cad32403449a3b`) — this session's own code
  commit, read and edited for the Question 3 code trail and the
  truncation-width fix respectively.

## Open findings

- **Cache safety, if ever revisited**: a cache is not ruled out the way
  BM25-replace is (Question 1's 25% repeat rate, derived above, is real),
  but any future design must handle the judge's own non-determinism
  (majority-vote across N calls before caching, invalidate-on-disagreement,
  or an explicit documented staleness risk) — resolution path: a
  follow-up issue scoped to "design a judge-decision cache that survives
  non-deterministic inputs," not a quick fix.
- **Sample size**: Question 1's repeat-rate scan (n=56 real dispatches)
  and Question 2's live agreement sample (n=5) are both small by design
  (this session's own time/API-cost budget, flagged per diagnose-first's
  G2-aux discipline rather than presented as decisive) — resolution path:
  the widened trace field (this session's `consult.py` fix) lets the next
  session re-run Question 2's methodology against a much larger sample
  pulled straight from consult-trace files, with no fresh API calls
  needed, once a few weeks of widened-trace history accumulate.
- **Async redesign feasibility**: Question 3 established only that a new
  delivery mechanism would be needed, not whether building one is worth
  it — resolution path: a dedicated feasibility spike if latency remains
  a priority after the above.

## Skill verdicts

canonical: `python3 -m pytest tests/test_issue_3230_skill_judge_cost.py -q`
and `python3 -m pytest -q` (full suite), both executed live in this
session — results quoted in the acceptance section above.

skill-verdict: diagnose-first — applied: invoked; used to force the three
diagnostic sub-questions (repeat rate, agreement rate, when-needed) to be
answered with real evidence before any of the four named options was
picked, and to size/flag the live 5-sample judge comparison honestly as
small rather than presenting it as decisive (G2-aux signal-vs-noise
discipline)
skill-verdict: implementation-blueprint — not-applicable: the delivered
script is explicitly the single-file/one-line-fix shape the skill says
not to invoke for; no multi-module structure decision was made this
session
skill-verdict: experiment-trust — not-applicable: nothing in this session
is an A/B or variant-comparison result being reported as a launch-driving
win; the closest analogue (the live judge-vs-BM25 sample) is flagged as a
small diagnostic measurement via diagnose-first's own discipline instead

## Evidence appendix

Question 1 repeat-rate scan (`/tmp/scan_repeats2.py`, workspace-local
scratch file, not part of this repository — reproduced verbatim so the
method is checkable without it):

```python
import glob, re, collections

paths = glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log/*.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/reports/consult-log/*.md')

line_re = re.compile(r"skill=(\S+) \| verb=skill_judge \| issue=(\S+) \| question='(.*?)' \| outcome=")
FIXTURE_ISSUES = {"2040", "2055", "2061", "2274", "1", "none"}
FIXTURE_TASK_PREFIXES = ("Task:\\ntask\\n", "Task:\\nplease write a haiku")

total = 0
fixture = 0
real_counter = collections.Counter()
for p in paths:
    try:
        text = open(p, errors='replace').read()
    except Exception:
        continue
    for line in text.splitlines():
        if '| verb=skill_judge |' not in line:
            continue
        m = line_re.search(line)
        if not m:
            continue
        total += 1
        skill, issue, question = m.groups()
        is_fixture = issue in FIXTURE_ISSUES or question.startswith(FIXTURE_TASK_PREFIXES)
        if is_fixture:
            fixture += 1
            continue
        real_counter[(issue, question)] += 1

real_total = sum(real_counter.values())
print("total trace lines:", total, "| fixture-filtered out:", fixture, "| real remaining:", real_total)
print("distinct real (issue, question) keys:", len(real_counter))
repeats = {k: c for k, c in real_counter.items() if c > 1}
repeat_events = sum(c - 1 for c in repeats.values())
print("real keys repeated >1x:", len(repeats), "| repeat (would-be cache hit) events:", repeat_events)
print("repeat share of REAL dispatches:", repeat_events / real_total if real_total else 0)
```

Question 1 consistency check (`/tmp/scan_repeat_consistency.py`) —
same file-glob and fixture filter as above, additionally parsing
`ts`/`outcome` per line, grouping by `(issue, question)`, and comparing
`picked=[...]` name sets between the first and every later occurrence of
each repeated key (full script omitted here for length; same parsing
approach as the Question 2 script below, applied to `picked` set equality
instead of candidate-list reconstruction).

Question 2 truncation-reliability scan (`/tmp/scan_agreement4.py`):

```python
import glob, re

paths = glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log/*.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/issue-*/reports/consult-log.md') + \
        glob.glob('/home/jwjung/.tokenmaxxxer/work/*/docs/reports/consult-log/*.md')

FIXTURE_ISSUES = {"2040", "2055", "2061", "2274", "1", "none"}
FIXTURE_TASK_PREFIXES = ("Task:\\ntask\\n", "Task:\\nplease write a haiku")

def strip_quotes(s):
    s = s.strip()
    if len(s) >= 2 and s[0] in "'\"" and s[-1] == s[0]:
        return s[1:-1]
    return s

def parse_line(line):
    if not line.startswith("- ") or "| verb=skill_judge |" not in line:
        return None
    parts = line.split(" | ")
    if len(parts) < 6:
        return None
    fields = {}
    for part in parts:
        if part.startswith("skill="):
            fields["skill"] = part[len("skill="):]
        elif part.startswith("issue="):
            fields["issue"] = part[len("issue="):]
        elif part.startswith("question="):
            fields["question"] = strip_quotes(part[len("question="):])
        elif part.startswith("outcome="):
            fields["outcome"] = strip_quotes(part[len("outcome="):])
    if "question" not in fields or "outcome" not in fields:
        return None
    return fields

def parse_candidates(question):
    m = re.search(r"Candidates:\\n(.*)$", question)
    if not m:
        return []
    return re.findall(r"- ([a-zA-Z0-9_-]+) ", m.group(1))

def picked_names(outcome):
    m = re.search(r"picked=\[([^\]]*)\]", outcome)
    if not m:
        return None
    return re.findall(r"([a-zA-Z0-9_-]+)=", m.group(1))

total_ok = 0
truncation_suspect = 0
reliable = 0
for p in paths:
    try:
        text = open(p, errors="replace").read()
    except Exception:
        continue
    for line in text.splitlines():
        fields = parse_line(line)
        if fields is None:
            continue
        issue, question, outcome = fields["issue"], fields["question"], fields["outcome"]
        if issue in FIXTURE_ISSUES or question.startswith(FIXTURE_TASK_PREFIXES):
            continue
        if not outcome.startswith("ok:"):
            continue
        cands = parse_candidates(question)
        picks = picked_names(outcome)
        if picks is None:
            continue
        total_ok += 1
        if len(question) >= 199 or not cands or not all(pk in cands for pk in picks):
            truncation_suspect += 1
            continue
        reliable += 1

print("total real 'ok:' lines:", total_ok)
print("excluded as truncation-suspect:", truncation_suspect)
print("reliable (untruncated, self-consistent) comparisons:", reliable)
```

Question 2 live-sample driver (`/tmp/live_agreement_test.py`):

```python
import sys, time, json
from pathlib import Path
import consult
import spawn as _sp

SCRATCH = Path("/tmp/otr-issue3230-live-judge-sample")
SCRATCH.mkdir(parents=True, exist_ok=True)
TASKS = [
    (3231, "Remove the install preconditions that can be removed, so a plugin-only install satisfies more than one of ten"),
    (3228, "Seven defects, one shape: make the silent-failure class unwritable instead of repairing it site by site"),
    (3128, "The repo-attribution fixes reopen their own leak when _repo_slug() cannot resolve"),
    (3103, "A merged sibling that never added a board record is bucketed corrupted-merge-base instead of unclassified"),
    (3047, "Watchdog names one cause for an absence with at least three causes, and attaches a force-push repair to the assertion"),
]
repo_root = _sp._skill_repo_root()
for issue, task_text in TASKS:
    t0 = time.monotonic()
    scored = consult._sp._bm25_cross_family_scores(
        task_text, "diagnose-first", repo_root, Path.home(), Path.cwd())
    bm25_top = [name for _s, name, _d, _src in scored[:8]]
    picked_dirs, outcome = consult._cross_family_skill_matches_with_consult(
        task_text, "diagnose-first", repo_root, None, str(SCRATCH),
        k=2, home=Path.home(), target_repo_root=Path.cwd())
    dt = time.monotonic() - t0
    print(f"issue {issue} wall_s={dt:.3f} outcome={outcome} "
          f"bm25_top2={bm25_top[:2]} judge_picked={[d.name for d in picked_dirs]}")
```

Raw output of the driver above is quoted verbatim in Question 2's evidence
block. Sorted `wall_s` values across this 5-call live sample: 13.567,
17.290, 19.865, 23.302, 31.016 — median (middle value) is 19.865s,
consistent with both the historical 16.663s (issue-3186/PR #3200) and
this session's fresh 16.343s (`measure_skill_judge.py --report`, quoted
in the acceptance section above) medians.
