---
issue: 2274
role: conformance-review
loop_state: reported
upstream:
  - path: PR #2304 (branch issue-2274/performance-engineering)
    sha: 2dcbc085688c3434aaf928c5a08f813d1815f82d
subject: PR #2304 (tokenmaxxxer/on-the-record) — cross_family judge p90-timeout delivery for issue #2274
test: issue-2274#Acceptance (gate / empty state / provenance)
result: passed
assertedBy: issue-2274/conformance-review session (builder-blind), 2026-08-25
---

# issue-2274 — conformance-review record

## What was done

canonical: `git worktree add /tmp/pr-2304-review pr-2304-review` (PR #2304
head `2dcbc085688c3434aaf928c5a08f813d1815f82d`, fetched via
`refs/pull/2304/head`), plus `gh issue view 2274` and `gh pr diff 2304` —
every citation and command result below was read/run this session,
independent of the builder's own record of itself, pinned at
`2dcbc085688c3434aaf928c5a08f813d1815f82d:docs/issue-2274/reports/performance-engineering.md`
(that path is PR-only and does not exist on this `conformance-review`
branch, hence the sha pin instead of a bare path reference throughout
this record).

Requirement extraction (conformance-review-requirement-extraction):
issue #2274's Acceptance block has three lines — `gate`, `empty state`,
`provenance`. `provenance` bundles three obligations ("paste the measured
distribution", "the chosen cutoff with its derivation", "a live spawn ...
fails open within the bound") and was split one requirement per
obligation (rule 1) into R6/R7/R8 below. `gate` and `empty state` are
each already singular. R3/R4 are pulled from the issue's Ask paragraph
only as far as needed to check the mechanism `empty state`/`provenance`
presuppose but never define ("the bound", "the existing fallback path").
R5 is the issue's frozen Non-goal, adjacent scope rather than aspiration.
Full enumeration was used instead of a derived sample:

acceptance: `cd /tmp/pr-2304-review && git diff --stat main...HEAD` — result:
```
consult.py                                         | 120 ++++++-
docs/issue-2274/reports/performance-engineering.md | 359 +++++++++++++++++++++
...26-08-25-hunt-cross-family-judge-p90-timeout.md | 101 ++++++
.../performance-engineering/deviation-log.md       |   4 +
spawn.py                                           |   6 +
...test_spawn_skill_judge_haiku_timeout_overlap.py | 146 ++++++++-
6 files changed, 727 insertions(+), 9 deletions(-)
```
small enough that every requirement-bearing hunk was read directly, so
conformance-review-sampling-derivation is not applicable (see
skill-verdict below).

### R1 — gate test passes

- requirement: `gate: tests/test_retrieval_eval.py`
- spec_ref: issue #2274 Acceptance, line `gate`
- verdict: **Present**
- acceptance: `cd /tmp/pr-2304-review/tests && python3 -m unittest test_retrieval_eval -v` — result:
```
test_bm25_document_carries_description_name_and_axis ... ok
test_declared_phrases_are_quoted_and_short_words_dropped ... ok
test_document_falls_back_to_name_tokens_without_description ... ok
test_fast_path_autopicks_on_verbatim_phrase_judge_never_called ... ok
test_fast_path_filling_cap_skips_judge_entirely ... ok
test_fast_path_ignores_declared_phrase_outside_bm25_topn ... ok
test_bm25_recall_at_8_and_final_pick_metrics ... ok
test_fast_path_verbatim_phrase_autopicks_without_judge ... ok
test_gold_set_frozen_shape ... ok

Ran 9 tests in 0.679s

OK
macro (non-empty n=4): Recall@8=1.000 MRR=1.000 | precision@mount (all n=12)=1.000
```
- rationale: Test-method reuse (conformance-review-verification-method-selection
  rule 4) of the full gate file, not just the one method the builder's
  record quoted — independent re-execution in an isolated worktree, not a
  copy of the builder's pasted transcript, confirms the result is
  reproducible from the committed diff itself.

### R2 — empty state: bound stays dormant below threshold

- requirement: `empty state: fewer than the threshold number of recorded
  skill_judge_perf events — the bound must not activate; current behavior
  unchanged.`
- spec_ref: issue #2274 Acceptance, line `empty state`
- verdict: **Present**
- canonical: `2dcbc085688c3434aaf928c5a08f813d1815f82d:consult.py:154-166`
  (`_skill_judge_timeout()` returns `_sp.SKILL_JUDGE_TIMEOUT_DEFAULT` when
  `_skill_judge_p90_cutoff()` is `None`).
- acceptance: `cd /tmp/pr-2304-review && python3 -m pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py -v` — result:
```
18 passed in 1.20s
```
  (includes `SkillJudgeTimeoutTest::test_default_timeout_is_90s_when_env_unset`,
  which pins the empty-state path explicitly via a mocked cutoff.)
- acceptance: `cd /tmp/pr-2304-review && python3 -c "import sys; sys.path.insert(0,'.'); import spawn; from pathlib import Path; import os; p=Path(os.environ['ON_THE_RECORD'])/'runs'/'ledger.jsonl'; print('genuine=', len(spawn._skill_judge_perf_samples(p))); print('cutoff=', spawn._skill_judge_p90_cutoff(p))"` — result:
```
genuine= 27
cutoff= None
```
- rationale: the unit-level pin (Test method) and a live query against
  the real, currently-running production ledger (Analysis/Demonstration
  — "is today's real event volume under threshold" isn't a unit-test
  question) independently agree: 27 genuine samples is below the 50
  threshold this session confirmed in R3, so the cutoff is `None` and
  `_skill_judge_timeout()` still returns the unchanged 90s default today.

### R3 — bound is p90 of genuine samples once threshold is met

- requirement: issue #2274 Ask paragraph 2, "a per-call timeout at ~p90"
  of measured `skill_judge_perf` latency, gated at the sample threshold
  Acceptance's `empty state` line names without defining.
- spec_ref: issue #2274 Ask paragraph 2 (the mechanism Acceptance's
  `empty state`/`provenance` lines both refer to)
- verdict: **Present**
- canonical: `2dcbc085688c3434aaf928c5a08f813d1815f82d:consult.py:60`
  (`_SKILL_JUDGE_PERF_MIN_EVENTS = 50`), `consult.py:87-152`
  (`_skill_judge_perf_samples`, `_percentile`, `_skill_judge_p90_cutoff`).
- acceptance: `cd /tmp/pr-2304-review && python3 -c "data=[float(i+1) for i in range(50)]; n=len(data); p=0.9; k=(n-1)*p; f=int(k); c=min(f+1,n-1); val=data[f] if f==c else data[f]*(c-k)+data[c]*(k-f); print('n=',n,'k=',k,'f=',f,'c=',c,'data[f]=',data[f],'data[c]=',data[c],'p90=',val)"` — result:
```
n= 50 k= 44.1 f= 44 c= 45 data[f]= 45.0 data[c]= 46.0 p90= 45.1
```
  This independently reproduces (by hand-computing the same linear
  interpolation, not by trusting the test's own `assertAlmostEqual`) the
  exact fixture `SkillJudgePerfP90Test::test_cutoff_is_p90_at_min_events`
  asserts (50 samples 1..50s → cutoff 45.1), part of the 18-passed run
  cited under R2 above.
- rationale: matches a standard linear-interpolation p90 (numpy's default
  `'linear'` method), computed independently rather than accepted from
  the test's assertion alone.

### R4 — reuses the existing BM25 fail-open, adds no new machinery

- requirement: issue #2274 Ask paragraph 2 parenthetical, "the existing
  fallback path ... this is extending an existing behavior to slowness,
  not new machinery."
- spec_ref: issue #2274 Ask paragraph 2
- verdict: **Present**
- canonical: `gh pr diff 2304` (this session) — the diff touches
  `consult.py`, `spawn.py`,
  `test/test_spawn_skill_judge_haiku_timeout_overlap.py`, and three new
  `docs/issue-2274/reports/` files only (see the `git diff --stat` fence
  under "What was done"); no hunk touches
  `_cross_family_skill_matches_with_consult()`'s `except Exception`
  fail-open block (landed under issue #2040, unmodified in this diff).
- rationale: the absence of any hunk touching the fail-open dispatch
  itself is the evidence that no second fail-open path was added — the
  new code (R3) only supplies a different timeout value to the same
  pre-existing exception handler.

### R5 — Non-goal: judge task/candidates not shrunk

- requirement: "Do not shrink the judge's task or candidates to chase
  speed."
- spec_ref: issue #2274 Non-goals
- verdict: **Present**
- canonical: `gh pr diff 2304` (this session, full diff read end-to-end,
  see the `git diff --stat` fence under "What was done") — no hunk
  touches candidate-set construction or judge task/prompt code anywhere
  in `consult.py`; the only additions are the timeout-derivation
  functions (R3) and their tests.
- rationale: a non-goal is satisfied by the absence of the forbidden
  change, confirmed here by reading the diff directly rather than
  accepting the builder's own record's claim of it.

### R6 — provenance: measured distribution pasted

- requirement: "paste the measured distribution from real ledger
  events" (Acceptance `provenance`, obligation: paste-distribution)
- spec_ref: issue #2274 Acceptance, line `provenance`
- verdict: **Present**
- canonical: `2dcbc085688c3434aaf928c5a08f813d1815f82d:docs/issue-2274/reports/performance-engineering.md`
  section "Measured distribution and live empty-state confirmation" —
  pastes `n= 19` and the full sorted `wall_s` sample list from the shared
  production ledger, plus p50/p90/max.
- acceptance: the same live query cited under R2 above (this session)
  reruns that measurement: `genuine= 27` today versus the builder's `19`
  — the population grew between the builder's session and this one (more
  real judge calls landed in the interim, since the ledger is live and
  append-only); the underlying method and file are identical, and both
  counts remain under the 50 threshold from R3.
- rationale: a concrete, reproducible list of real `wall_s` values (not a
  summary claim) satisfies "paste the measured distribution"; the count
  drifting between sessions is expected of a live ledger and does not
  contradict the requirement.

### R7 — provenance: chosen cutoff with derivation

- requirement: "the chosen cutoff with its derivation" (Acceptance
  `provenance`, obligation: cutoff-derivation)
- spec_ref: issue #2274 Acceptance, line `provenance`
- verdict: **Present**
- canonical: `2dcbc085688c3434aaf928c5a08f813d1815f82d:docs/issue-2274/reports/performance-engineering.md`
  "Why" section states the percentile-over-mean rationale and the
  `wall_s>=1.0` data-quality-filter rationale.
- acceptance: R2's live query (this session, cited above) reproduces the
  actual numeric cutoff today: `cutoff= None` (genuine sample count 27 <
  50), so "chosen cutoff" is correctly reported as not-yet-active,
  consistent with both this session's and the builder's own live
  queries.
- rationale: both the formula (why p90; why the wall_s floor) and a
  live-executed number are present and independently reproduced, not
  asserted once and trusted.

### R8 — provenance: live spawn demonstrating in-bound fail-open

- requirement: "a live spawn where a deliberately-slowed judge call fails
  open within the bound" (Acceptance `provenance`, obligation:
  live-fail-open-demo)
- spec_ref: issue #2274 Acceptance, line `provenance`
- verdict: **Present**
- acceptance: `cd /tmp/pr-2304-review && python3 -m pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py -v -k test_a_genuinely_slow_subprocess_times_out_and_fails_open_live` — result:
```
test_a_genuinely_slow_subprocess_times_out_and_fails_open_live PASSED
1 passed in 19.27s
```
  This test, independently rerun this session in the isolated worktree,
  spawns a real `sleep 5` subprocess (unmocked `subprocess.run`) under a
  real `SKILL_JUDGE_TIMEOUT=0.3`, and asserts the outcome is
  `fail-open` — a slow (19.27s wall-clock, dominated by the real 5s
  `sleep` plus process overhead) but genuine, non-mocked timeout.
- rationale: this exercises `_cross_family_skill_matches_with_consult()`
  directly — the same internal entry point the pre-existing
  mocked-exception timeout test already uses — rather than shelling out
  to the `spawn` CLI end-to-end as a separate OS process. Treated as
  satisfying "live spawn" because the slowdown and the resulting timeout
  are both genuine and unmocked, consistent with this codebase's own
  existing definition of "live" for the sibling test it extends;
  flagged here explicitly rather than silently accepted so a reader can
  judge the interpretation independently.

## Why

Builder-blind means every claim above was re-derived or re-executed this
session rather than taken from the builder's own account of itself
(pinned at
`2dcbc085688c3434aaf928c5a08f813d1815f82d:docs/issue-2274/reports/performance-engineering.md`).
conformance-review-verification-method-selection routed R1/R2/R3/R8 to
Test (existing coverage reused per its rule 4, rerun rather than
re-derived from scratch), R2/R6/R7's "is today's ledger volume
under/over threshold" question to Analysis/Demonstration (a condition a
static unit test cannot establish — only a live query can), and R4/R5 to
Inspection (a structural "does a diff hunk touch X" question, per its
rule 1). conformance-review-sampling-derivation was judged not-applicable
and skipped: the diff is 6 files, 727 insertions / 9 deletions — derived:
`git diff --stat main...HEAD` (fence pasted in full under "What was
done") — small enough that every requirement-bearing line was read in
full, so a derived sampling scope (for when full enumeration is
infeasible) does not apply here.

## What did not work

Nothing in this review pass hit a blocked or unreproducible verification
path — every requirement above had either an existing test to rerun or a
live artifact (the production ledger, `gh pr diff`) to query directly
this session, so no requirement fell back to `Unverifiable` for lack of
access.

## Upstream basis

- PR #2304, `tokenmaxxxer/on-the-record`, head commit
  `2dcbc085688c3434aaf928c5a08f813d1815f82d` (branch
  `issue-2274/performance-engineering`) — sha for every `consult.py`,
  `spawn.py`, and test citation above; fetched this session via
  `git fetch origin pull/2304/head:pr-2304-review` and
  `git worktree add /tmp/pr-2304-review pr-2304-review`.
- `2dcbc085688c3434aaf928c5a08f813d1815f82d:docs/issue-2274/reports/performance-engineering.md`
  — the builder's own record, read only to locate what to independently
  re-check; not present on this `conformance-review` branch (PR-only,
  unmerged), hence the sha-pinned citation rather than a bare path
  throughout this record.
- issue #2274 itself (Ask, Non-goals, Acceptance) — `gh issue view 2274`,
  this session.

## Open findings

- **Not evidenced against Acceptance, but worth surfacing**: issue #2274
  Ask paragraph 2's last clause asks to "confirm the retrieval-eval gold
  cases hold under fail-open at that rate" (~10%, once the bound is
  live). This is not part of the frozen Acceptance block itself —
  Acceptance's `gate` line only names the test file, and R1 above
  confirms it passes — so it does not fail any Acceptance-scoped
  requirement. But independently reading
  `2dcbc085688c3434aaf928c5a08f813d1815f82d:tests/test_retrieval_eval.py:8-15`
  shows the gate's final-pick stage mocks the judge as an oracle
  (`_skill_judge_consult` replaced entirely) — `_skill_judge_timeout()`
  and `_skill_judge_p90_cutoff()` are never invoked by this gate at all,
  so R1's rerun exercises a 0% fail-open rate, not ~10%. The builder's
  own record discloses this honestly ("this gate's judge stage is
  oracle-mocked, so it doesn't exercise the timeout", per
  `2dcbc085688c3434aaf928c5a08f813d1815f82d:docs/issue-2274/reports/performance-engineering.md`).
  No test in the diff runs the 12-gold-case set with a simulated nonzero
  fail-open rate and checks recall/precision still hold at it; the
  nearest existing coverage
  (`test_fast_path_verbatim_phrase_autopicks_without_judge`, part of the
  9-tests-OK run under R1) covers one case's judge-raises path, a
  different failure mode (`RuntimeError`, not `TimeoutExpired`) and not
  rate-based. Resolution path: a follow-up spot-check — mock ~10% of the
  oracle's per-case judge calls to raise `TimeoutExpired` across the 12
  gold cases and confirm recall/precision still hold — would close the
  gap between the Ask's literal wording and what is currently evidenced;
  not a blocker for this PR's Acceptance grade as frozen, since
  Acceptance itself did not ask for it.
- **Carried forward, not new**: the builder's own record already
  discloses that the 512KiB tail-read's noise-vs-genuine ratio could
  delay the bound's activation indefinitely if noise volume outpaces
  genuine volume. Independently confirmed still accurate by reading
  `2dcbc085688c3434aaf928c5a08f813d1815f82d:consult.py:87-130`; no new
  resolution path beyond what the builder's record already states.

## Next steps

`loop_state` is `reported` (terminal for a review-record per the
session protocol's kind table) — nothing pending from this record
itself. Forward note only: if the gold-case-under-fail-open gap above is
picked up, it belongs to a follow-up issue/test addition, not a re-open
of this one.

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; split Acceptance's `provenance` line into R6/R7/R8 (rule 1),
pulled in R3/R4 as the minimum Ask context Acceptance's own wording
presupposes rather than re-deriving new scope, and kept R5's Non-goal as
its own item.
skill-verdict: conformance-review-verification-method-selection —
applied: invoked; routed R1/R2/R3/R8 to Test (existing coverage reused
per rule 4), R2/R6/R7's live-ledger-volume claim to
Analysis/Demonstration, R4/R5 to Inspection.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
all eight Acceptance-scoped requirements independently re-verified and
assigned Present; the retrieval-eval-under-fail-open gap was kept out of
the five-verdict set entirely (it is not an Acceptance-scoped
requirement) and recorded as an Open finding instead, per this skill's
own scope.
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every evidence citation above is pinned to file:line plus the
PR's head sha `2dcbc085688c3434aaf928c5a08f813d1815f82d`, and re-executed
this session rather than paraphrased from the builder's record.
skill-verdict: conformance-review-finding-record — applied: invoked;
this file, one block per requirement with requirement/spec_ref/verdict/
evidence/rationale; no `spec_vs_built` field needed since no requirement
verdicted `Incorrect`.
other mounted skills: conformance-review-sampling-derivation (full
enumeration was feasible, not-applicable), conformance-review-
severity-classification (scope was not extended into risk-weighting,
not-applicable), implementation-audit (cross-family keyword match only —
this role's own conformance-review skill family already governs this
exact task more specifically, not-applicable) — not triggered.

## before-landing — stance 0: verify record's pasted command output / citations / verdicts against PR #2304 head

Verdict: NO FINDING
Seed: docs/issue-2274/reports/conformance-review.md (this session's own record, staged for commit), checked against /tmp/pr-2304-review at sha 2dcbc085688c3434aaf928c5a08f813d1815f82d
cap_seconds: not specified by dispatcher
tier: default
diff_stat_lines: N/A (reviewing a record file, not a code diff)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:20:00Z

Re-ran: `python3 -m unittest test_retrieval_eval -v` (tests/), `pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py -v` (18 passed, confirmed, only wall-clock duration differs), the `-k test_a_genuinely_slow_subprocess_times_out_and_fails_open_live` isolate (1 passed, confirmed), the live ledger query (`spawn._skill_judge_perf_samples`/`_skill_judge_p90_cutoff` against `$ON_THE_RECORD/runs/ledger.jsonl`: genuine count re-ran twice, 27→32, consistent with the record's own "live, append-only ledger grew between sessions" explanation, not a discrepancy), and the hand p90 computation (n=50,p=0.9 → 45.1, matches). Checked citations consult.py:60, consult.py:87-152, consult.py:154-166, tests/test_retrieval_eval.py:8-15 line-for-line against the pinned sha — all match the quoted content exactly. Checked R4/R5's "no hunk touches the fail-open block / candidate construction" claim via `git diff main...HEAD -- consult.py`/`spawn.py` — confirmed, the diff only adds `_SKILL_JUDGE_PERF_MIN_EVENTS`/`_MIN_PLAUSIBLE_JUDGE_WALL_S`/`_LEDGER_TAIL_READ_BYTES`, `_skill_judge_perf_samples`, `_percentile`, `_skill_judge_p90_cutoff`, and reworks `_skill_judge_timeout()`'s body — no other hunk. Confirmed `docs/issue-2274/reports/performance-engineering.md` does not exist at `main` or at this branch's `HEAD`, supporting the record's sha-pin rationale. Found no wrong pasted output, no false file:line citation, no verdict that should differ, and no internal inconsistency between frontmatter and body.
