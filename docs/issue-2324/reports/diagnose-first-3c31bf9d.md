---
issue: 2324
role: diagnose-first-3c31bf9d
author: diagnose-first-3c31bf9d
skills: diagnose-first (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
code_under_review: same-commit (docs/issue-2324/_assets/measure_batching_headroom.py, tests/test_directive_diet_2135.py)
type: diagnostic
breaking: false
verdict: headroom-below-threshold-no-directive-change
upstream:
  - path: directive_assembly.py (`_TURN_BUDGET_PROSE`, issue #2262)
    sha: 90d1c5a7c7dc3197cb2b43e9baa2b1c53a2e7238
  - path: docs/issue-2262/reports/implementation.md
    sha: 90d1c5a7c7dc3197cb2b43e9baa2b1c53a2e7238
  - path: docs/issue-2837/reports/adversarial-review-de1e46b2.md (re-aiming evidence, PR #2841)
    sha: 81a628df4bdcb8b00524c418f17c4f6063654c65
  - path: docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md
    sha: a7a7417aeadaa9e37fcc3d509834f1e37a840dd0
---

# issue-2324 — diagnose-first-3c31bf9d record

## What was done

Per this issue's explicit step ordering ("do not skip step 2"), measured
batching headroom on 10 real session transcripts under
`$MUSTER_WORKSPACE_ROOT` BEFORE touching any directive text, using a
committed instrument, `docs/issue-2324/_assets/measure_batching_headroom.py`.

- derived (headline number):
```
python3 docs/issue-2324/_assets/measure_batching_headroom.py <10 transcript
paths, full table below> | python3 -c "
rows=[(18,2,10,5),(67,0,16,3),(50,15,15,4),(36,1,8,2),(53,5,14,5),
      (77,6,19,7),(123,0,34,7),(70,0,20,4),(101,3,25,5),(118,5,51,15)]
total=sum(r[0] for r in rows); pairs=sum(r[3] for r in rows)
print(f'{pairs}/{total} = {100*pairs/total:.2f}%')
"
```
  result: `57/713 = 7.99%` — 57 of 713 turns show an adjacent pair of
  single-small-tool-call turns with no detected dependency between them
  (full per-transcript table and exact command below). This is below
  the 10-15% threshold set in advance (see "Why") for treating headroom
  as worth a directive rewrite, so per the issue's own STOP-AND-REPORT
  clause this is reported as a finding: **no edit was made to any
  directive file** (`directive_assembly.py`, `on-the-record/directive/*.md`,
  `.on-the-record/directive/*.md`) or to issue #2262's approach-cap
  machinery — acceptance: `git diff origin/main --stat -- directive_assembly.py
  on-the-record/ .on-the-record/` — result: empty.

skill-verdict: diagnose-first — applied: invoked; the skill's Amdahl
check ("what share of the whole does this cause carry") is the
reasoning this record's stop decision rests on, and its Stage-3
reversible/two-way-door test (not editing the directive is a two-way
door, so it does not need a heavy weighted-option comparison) is why
this record does not build a decision matrix for the near-threshold
7.99% number — canonical: this session's own Skill-tool invocation of
`diagnose-first` (visible in this session's own transcript), read
before this record was assembled.

skill-verdict: work-in-english — applied: invoked; this record, the
commit, and the PR are in English throughout (the issue body and some
surrounding instructions were in Korean).

skill-verdict: hypothesis-testing — not-applicable: this is a measured
technical diagnostic with a threshold stated ahead of measurement, not
a product/feature go-kill-pivot decision with a pre-registered
falsifiable hypothesis in the sense that skill targets.

skill-verdict: flow-metrics — not-applicable: no per-item WIP/lead-time
entry-exit data or Little's-law question is in scope; this is a
per-turn tool-call-batching measurement, not a kanban/flow-boundary
measurement.

### Investigation methodology (headroom measurement)

10 transcripts were selected from `$MUSTER_WORKSPACE_ROOT` — the
on-the-record-repo session logs with the largest, most-complete
`.session.*.log` files among sessions whose last write predates this
measurement's own wall-clock time by >15 minutes (i.e. not
concurrently in-flight) — derived: `ls -la
$MUSTER_WORKSPACE_ROOT/*.session.*.log` sorted by size, cross-checked
with `stat -c '%y %n' <candidate>` against `date -u` (both run in
`$MUSTER_WORKSPACE_ROOT`/this session) to exclude sessions whose log
`mtime` was within ~1-3 minutes of the check (still live).

A first parsing attempt treated each JSONL line in the log as one
"turn" and measured zero multi-tool-call turns across all 10
transcripts — contradicted by `_TURN_BUDGET_PROSE`'s own existence (a
directive telling sessions to batch tool calls should have SOME
observable effect), so it was investigated rather than accepted; root
cause and fix are in "What did not work" below. The committed script
(`docs/issue-2324/_assets/measure_batching_headroom.py`) groups by
`message.id` before counting `tool_use` blocks per turn.

Definitions used (heuristic, disclosed per PR #2841's caution — canonical:
`docs/issue-2837/reports/adversarial-review-de1e46b2.md` — that magnitude
is method-sensitive):
- **turn**: one assistant API response (one `message.id`), which may
  itself carry >=1 `tool_use` block — >1 IS the "batched in one
  message" case this issue asks for more of.
- **small call**: `Grep`/`Glob`/`Read`, or an atomic (non-`&&`/`|`/`;`)
  `Bash` command.
- **batchable adjacent pair**: two consecutive turns that are each a
  single small call, where no >=15-character token from the first
  call's `tool_result` text appears verbatim in the second call's
  input (the empty-state dependency check).

### Headroom table (10 real transcripts, `$MUSTER_WORKSPACE_ROOT`)

- derived:
```
python3 docs/issue-2324/_assets/measure_batching_headroom.py \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2827-diagnose-first-6c16a19d.session.20260830T135512.515671.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2749-adversarial-review-28904fd2.session.20260830T115728.3966889.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2847-diagnose-first-50e013fd.session.20260830T134944.497939.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2830-diagnose-first-7c274fa6.session.20260830T120848.4170669.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2814-test-authoring-isolation-and-fixture-strategy-49df91ca.session.20260830T094015.3166892.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2749-adversarial-review-71d5dd92.session.20260830T133435.407894.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2811-technical-writing-style-guide-compliance-ea5a2771.session.20260830T093054.3136489.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2798-adversarial-review-99b10ef0.session.20260830T080603.2662095.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log" \
  "$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2749-silent-failure-audit-e9b54ddf.session.20260830T131031.176660.log"
```
  result (tab-separated, one row per transcript):

| # | transcript (issue-role) | total turns | multi-tool turns | single-small-call turns | batchable-adjacent-pairs |
|---|---|---|---|---|---|
| 1 | 2827-diagnose-first | 18 | 2 | 10 | 5 |
| 2 | 2749-adversarial-review-28904fd2 | 67 | 0 | 16 | 3 |
| 3 | 2847-diagnose-first | 50 | 15 | 15 | 4 |
| 4 | 2830-diagnose-first | 36 | 1 | 8 | 2 |
| 5 | 2814-test-authoring | 53 | 5 | 14 | 5 |
| 6 | 2749-adversarial-review-71d5dd92 | 77 | 6 | 19 | 7 |
| 7 | 2811-technical-writing-style-guide | 123 | 0 | 34 | 7 |
| 8 | 2798-adversarial-review | 70 | 0 | 20 | 4 |
| 9 | 2135-diagnose-first+minimalism-scoping | 101 | 3 | 25 | 5 |
| 10 | 2749-silent-failure-audit-e9b54ddf | 118 | 5 | 51 | 15 |
| | **sum** | **713** | **37 (5.19%)** | **212 (29.73%)** | **57 (7.99%)** |

- derived (sum row arithmetic):
```
python3 -c "
rows=[(18,2,10,5),(67,0,16,3),(50,15,15,4),(36,1,8,2),(53,5,14,5),
      (77,6,19,7),(123,0,34,7),(70,0,20,4),(101,3,25,5),(118,5,51,15)]
total=sum(r[0] for r in rows); multi=sum(r[1] for r in rows)
single=sum(r[2] for r in rows); pairs=sum(r[3] for r in rows)
print(total, multi, single, pairs, f'{100*multi/total:.2f}%', f'{100*single/total:.2f}%', f'{100*pairs/total:.2f}%')
"
```
  result: `713 37 212 57 5.19% 29.73% 7.99%`

**Headroom number: 7.99% (batchable-adjacent-pairs / total turns) — this
is the decision number for STOP-AND-REPORT below.** The looser
"single-small-call-turns / total" figure (29.73%, derived above) is
reported per the issue's requested table shape but is not the decision
number: it does not account for adjacency or dependency, so most of
that 29.73% either has no adjacent partner or is a genuine serial
dependency — the issue's own empty-state case (see the empty-state test
in `tests/test_directive_diet_2135.py`, function name
`test_empty_state_serial_dependent_pair_is_not_forced_batchable`).

The `multi_tool_turns` figure (37/713 = 5.19%, derived above) is
independent confirmation that `_TURN_BUDGET_PROSE` is not inert:
sessions already batch >1 tool call into a single turn some of the
time. What is left after that (7.99%) is below this delivery's own bar
for another directive round.

### STOP-AND-REPORT: no directive change made

7.99% (derived above) is below the 10-15% threshold set in "Why" below.
Investigating why headroom is already this low — rather than assuming
and moving on — found the reason: issue #2262's `_TURN_BUDGET_PROSE`
already mandates most of this issue's Ask #1 — canonical:
```
directive_assembly.py lines 153-179 (`_TURN_BUDGET_PROSE`), read this
session — key sentences (Korean original, translated here): "(1)
bundle several related greps into one Bash call with && or | and run
them in one turn ... (2) delegate wide exploration to 3-4 parallel
Explore-type subagents via the Task tool — a foreground batch running N
explorations in one turn keeps those turns for editing/verification
instead of spending them serially ... (operator directive, issue #2262
comment: run_in_background workers are banned in headless spawns — the
parent turn's death kills them — but foreground Task batching is
allowed)."
```
This covers three of this issue's four Ask-#1 bullets verbatim:
mandate parallel tool calls where independent (item 2, subagent
fan-out), compound bash over serial (item 1), and prefer the #2262
subagent fan-out for wide exploration (item 2, by name). The fourth
(MultiEdit over serial Edit) is not separately stated in
`_TURN_BUDGET_PROSE` today — see "Open findings" #1 for why that alone
was not judged to cross the 10-15% action threshold.

### Re-aiming check (PR #2839/#2841 evidence)

canonical: `docs/issue-2837/reports/adversarial-review-de1e46b2.md`
(quoted in full in this delivery's task brief) — investigation/other is
the largest single time-bucket in a session (42.0%/30.2% of two
measured sessions in PR #2839, re-confirmed 3.06x-4.53x across three
sessions and two classification methods in PR #2841's independent
re-check) — batching pays off in investigation, not editing. The
existing #2262 directive is already aimed there: both its guidance
items (grep batching, subagent fan-out) are investigation-phase moves,
and this measurement's own `single_small_call_turns` figures are
`Grep`/`Read`/`Bash` calls (investigation tools) by definition (see
"small call" above), not `Edit`/`Write`. No re-aiming was needed
because the existing directive was never mis-aimed at editing in the
first place.

## Why

Chose the 10-15% threshold before measuring (diagnose-first's "no
improvement talk before measurement" — stated here, before the headroom
number above was computed in this session) as a proportionate bar:
below it, a directive rewrite's realistic yield is a few percent of
turns on an already-small share of session wall-clock — canonical:
`docs/issue-2837/reports/adversarial-review-de1e46b2.md` (editing is
5.2-17.9% of a session in PR #2839's own two-session measurement,
record+landing and investigation are the two largest buckets) — not
worth the risk of a systemic, no-side-effects-required change touching
every consumer session's context (this issue's own operator-frozen
constraint) for a gain this issue's own Ask #2 already anticipated
might not clear. 7.99% measured (derived above) is below that bar, so
this delivery stops at the measurement per the issue's own
STOP-AND-REPORT clause rather than writing a directive change to
manufacture a bigger number.

The corrected transcript-parsing bug (see "What did not work") is
itself evidence for why measuring first mattered: the wrong parser's
headline number (0% multi-tool turns, i.e. "the #2262 directive has
zero effect") would have argued for a much larger rewrite than the
corrected number (5.19% already batching, 7.99% residual headroom,
both derived above) supports.

## Upstream basis

- `directive_assembly.py` `_TURN_BUDGET_PROSE` (issue #2262, sha
  `90d1c5a7c7dc3197cb2b43e9baa2b1c53a2e7238`) — the directive this
  delivery's finding rests on and does not modify.
- `docs/issue-2262/reports/implementation.md` (same sha) — canonical:
  that file (read this session) documents the original measurement
  motivating `_TURN_BUDGET_PROSE`: six 2026-08-24/25 sessions all hit
  the 200-turn cap, and one of them (issue #2240) ran 69 grep commands
  serially, 68 of them distinct — quoted verbatim inside
  `_TURN_BUDGET_PROSE` itself (see the STOP-AND-REPORT codeblock above).
- `docs/issue-2837/reports/adversarial-review-de1e46b2.md` (sha
  `81a628df4bdcb8b00524c418f17c4f6063654c65`) — the re-aiming evidence
  this delivery's task brief required incorporating.
- `docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md`
  (sha `a7a7417aeadaa9e37fcc3d509834f1e37a840dd0`) — a sibling
  measurement-only delivery in this same repo/day, cross-checked for
  the "measurement-only, no source touched, human decides on closure"
  delivery shape this record follows.
- `tests/test_directive_diet_2135.py` (this commit) — the gate named in
  issue #2324's own Acceptance section. derived: `git log --all -S
  test_directive_diet_2135 --oneline | head -1` → `a555e169
  issue-2525: retire the plugin's own test suite (#2528)` — a file of
  this name existed under issue #2135/#2262's original work and was
  removed only by issue #2525's blanket plugin-test-suite retirement
  (`tests/*.py`, `gates/test_*.py`, `on-the-record/hooks/test_*.py`,
  `conftest.py`), not for cause specific to this content — and new
  narrow files have continued to land under `tests/` since that
  retirement (`tests/test_tmp_resource_gc.py` from issue #2468,
  `tests/test_cross_checkout_prune_liveness.py` from issue #2492, both
  present in `git ls-files tests/`), so authoring a new, narrow file at
  this name does not conflict with the #2525 retirement decision.

## Open findings

1. The MultiEdit-over-serial-Edit guidance (this issue's Ask #1, fourth
   bullet) is not present in `_TURN_BUDGET_PROSE` today — not added in
   this delivery, since editing is a small time-share (5.2-17.9% —
   canonical: `docs/issue-2837/reports/adversarial-review-de1e46b2.md`)
   and this issue's own measurement targets investigation-phase
   batching, where MultiEdit does not apply. Resolution path: a
   follow-up could add one sentence to `_TURN_BUDGET_PROSE` if a future
   measurement shows editing-phase serial-Edit turns are themselves a
   non-trivial share — not measured in this delivery, so not asserted
   here.
2. This delivery's "5 comparable issues, before/after" table (below)
   compares 5 current (post-#2262) transcripts against each other, not
   against a pre-#2262 baseline — derived: `ls
   $MUSTER_WORKSPACE_ROOT/*.events.jsonl | wc -l` → `33`; `stat -c '%y'
   $MUSTER_WORKSPACE_ROOT/*.events.jsonl | sort | head -1` → earliest
   mtime is still 2026-08-30 (no pre-2026-08-25 session logs present in
   this environment). `docs/issue-2262/reports/implementation.md`
   documents its pre-change problem (200-turn-cap deaths, serial greps)
   but not a controlled wall-clock before/after table, so a true
   pre/post-#2262 wall-clock comparison is not reproducible here.
3. The dependency heuristic (>=15-char token overlap between a prior
   `tool_result` and the next call's input) is crude and will both
   over- and under-count real dependencies — disclosed in the script's
   own docstring and covered by two unit tests, acceptance: `python3 -m
   pytest tests/test_directive_diet_2135.py -q` — result: `7 passed`
   (includes both the batchable-pair and empty-state-dependency tests)
   — but not validated against a hand-labeled sample of the 10
   transcripts. A tighter headroom number would need that hand-labeling.

## What did not work

A first version of the headroom-measurement script parsed the
stream-json session log one JSONL line at a time, treating each line as
its own "turn." This produced `multi_tool_turns = 0` across all 10
transcripts, which contradicted `_TURN_BUDGET_PROSE`'s own existence.
Investigating the contradiction found the cause: the log format streams
one JSON line per assistant content block (`thinking`/`text`/
`tool_use`), with several lines sharing one `message.id` when they are
the same logical turn — derived:
```
python3 -c "
import json
from collections import Counter
p='$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2749-silent-failure-audit-e9b54ddf.session.20260830T131031.176660.log'
ids=[]
with open(p) as f:
    for l in f:
        d=json.loads(l)
        if d.get('type')=='assistant':
            ids.append(d['message']['id'])
c=Counter(ids)
print('assistant JSONL lines:', len(ids), 'duplicate message ids:', sum(1 for v in c.values() if v>1))
"
```
result: `assistant JSONL lines: 218 duplicate message ids: 93` — proving
the one-line-per-turn assumption was wrong (93 of 218 lines shared an
id with at least one other line). The corrected script (committed,
`docs/issue-2324/_assets/measure_batching_headroom.py`) groups by
`message.id` first; its own module docstring documents this pitfall for
reuse. No other approach was abandoned in this delivery.

## Before/after: turn count and wall clock, 5 comparable issues

Per Open finding #2, no pre-#2262 baseline was available in this
environment, so this table reports the current, post-#2262
(unchanged-by-this-delivery) state for 5 comparable, completed
transcripts — the "after" state this issue's step 5 asks for, since
this delivery made no further change to produce a distinct new "after."
Wall clock is `session-log mtime − the start timestamp embedded in the
log's own filename`; each file's mtime was confirmed >15 minutes stale
relative to this measurement's own wall-clock time (not still being
written) — derived: `stat -c '%y %n'` on each file vs `date -u`, both
run in `$MUSTER_WORKSPACE_ROOT`/this session.

- derived:
```
python3 -c "
import os, re, datetime
files = [
 'on-the-record-issue-2749-adversarial-review-71d5dd92.session.20260830T133435.407894.log',
 'on-the-record-issue-2811-technical-writing-style-guide-compliance-ea5a2771.session.20260830T093054.3136489.log',
 'on-the-record-issue-2798-adversarial-review-99b10ef0.session.20260830T080603.2662095.log',
 'on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log',
 'on-the-record-issue-2749-silent-failure-audit-e9b54ddf.session.20260830T131031.176660.log',
]
for f in files:
    m = re.search(r'\.session\.(\d{8}T\d{6})\.', f)
    start = datetime.datetime.strptime(m.group(1), '%Y%m%dT%H%M%S')
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
    print(f.split('.session.')[0], f'{(mtime-start).total_seconds()/60:.1f} min')
"
```
  (run in `$MUSTER_WORKSPACE_ROOT`) result:
```
on-the-record-issue-2749-adversarial-review-71d5dd92 13.6 min
on-the-record-issue-2811-technical-writing-style-guide-compliance-ea5a2771 23.4 min
on-the-record-issue-2798-adversarial-review-99b10ef0 12.3 min
on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0 24.6 min
on-the-record-issue-2749-silent-failure-audit-e9b54ddf 21.0 min
```

| issue-role | turns (before = after, no change made) | wall clock |
|---|---|---|
| 2749-adversarial-review-71d5dd92 | 77 | 13.6 min |
| 2811-technical-writing-style-guide | 123 | 23.4 min |
| 2798-adversarial-review | 70 | 12.3 min |
| 2135-diagnose-first+minimalism-scoping | 101 | 24.6 min |
| 2749-silent-failure-audit-e9b54ddf | 118 | 21.0 min |

"Before" and "after" are identical here by construction (no directive
edit was made this delivery) — this table satisfies the issue's
requested shape and gives a human maintainer a current baseline; it
does not claim a measured improvement.

## Acceptance verification

- gate: acceptance: `python3 -m pytest tests/test_directive_diet_2135.py -v`
  — result: `7 passed`.
- empty state (issue's own clause: a task needing serial dependent
  calls — no forced batching): the test named
  `test_empty_state_serial_dependent_pair_is_not_forced_batchable`
  inside `tests/test_directive_diet_2135.py` fixtures a Grep-then-Read
  of the exact path Grep found, and asserts `batchable_adjacent_pairs
  == 0` — acceptance: `python3 -m pytest tests/test_directive_diet_2135.py -k test_empty_state_serial_dependent_pair_is_not_forced_batchable -q` — result: `1 passed`.
- (a) retired-role-axis check: acceptance: `grep -n -iE "\brole\b"
  docs/issue-2324/_assets/measure_batching_headroom.py
  tests/test_directive_diet_2135.py` — result: no match (exit 1),
  confirming the retired `role` noun (issue #2741) is not reintroduced
  in either new file.
- (b) no new bug: acceptance: `git diff origin/main --stat` — result:
  empty (no tracked file changed; only new untracked
  `docs/issue-2324/**` and `tests/test_directive_diet_2135.py`).
  Full-suite failing-test-name sets, this branch vs `origin/main` (via
  a detached `origin/main` worktree, since removed), both `python3 -m
  pytest test/ tests/ -q`:
```
branch (462 passed, 15 failed, 3 xfailed):
FAILED test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
FAILED test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
FAILED test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
FAILED test/test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo

origin/main worktree (455 passed, 15 failed, 3 xfailed): same 15 names,
diffed with `diff <(sort branch_failed.txt) <(sort main_failed.txt)` —
empty diff. The 462-vs-455 delta is exactly the 7 new passing tests in
tests/test_directive_diet_2135.py, which does not exist on origin/main.
```
- (c) no overhead increase: acceptance: `git diff origin/main --stat --
  directive_assembly.py .on-the-record/directive/ on-the-record/directive/`
  — result: empty (0 lines) — zero byte/line/token change to any
  directive file or the assembly code that builds them, since nothing
  there was touched.
- (d) monitor/watch machinery: derived: `git ls-files | grep -iE
  "watchdog|watch|monitor" | grep -v docs/` — result: `watchdog.py`,
  `on-the-record/directive/monitor-mode.md`,
  `on-the-record/monitors/monitors.json`,
  `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/poll_heartbeat_delta.py`,
  `on-the-record/monitors/test_poll_heartbeat.py`,
  `test/test_watchdog_heartbeat_noise.py`. acceptance: `git diff
  origin/main --stat -- watchdog.py on-the-record/monitors/` — result:
  empty (untouched). acceptance: `python3 -m pytest
  test/test_watchdog_heartbeat_noise.py
  on-the-record/monitors/test_poll_heartbeat.py -q` — result: `36
  passed`.

## Next steps

No pending code change remains queued for this delivery: derived: `git
status --short` — result: this record file plus
`docs/issue-2324/_assets/measure_batching_headroom.py` and
`tests/test_directive_diet_2135.py` are the only new/modified paths.

Per "Open findings," a human maintainer could decide to: (1) close
issue #2324 on the basis that its Ask #1 directive is already
substantially landed under #2262 and remaining headroom (7.99%,
derived above) is below a reasonable action threshold, mirroring how
issue #2135's composition-breakdown record left closure to a human
maintainer; or (2) file a narrower follow-up specifically for the
MultiEdit-over-serial-Edit sentence (Open finding #1) if a future
measurement shows it matters. This delivery does not pick or file that
follow-up itself.
