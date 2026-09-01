---
issue: 3018
role: knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2
author: knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2
skills: knowledge-management-taxonomy-tagging (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: 56bf53c05338eaca83844015dcfb02fe012e6b0d (consult.py, spawn.py, tests/test_skill_candidates_signal.py, tests/test_skill_candidates_false_positive_rate.py)
type: fix
breaking: false
verdict: pass
loop_state: landed
upstream:
  - path: consult.py (rank_skills(), _SKILL_CANDIDATES_RELEVANCE_FLOOR, issue #2982)
    sha: 56bf53c05338eaca83844015dcfb02fe012e6b0d
  - path: docs/issue-2982/reports/adversarial-review-e63d3cd4.md (PR #3015, 10-query false-positive set)
    sha: 67ebda3b1d6b88b4fb7422d1b864db188309baeb
  - path: docs/issue-2982/reports/adversarial-review-fc5c800d.md (PR #3016, 3 additional quoted queries + 89% figure)
    sha: 1ff061bf15a3b4d158c67bad04804e1268419022
---

# issue-3018 — knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2 record

## What was done

Partial delivery on issue #3018's Direction (priority-ordered: trigger-document
expansion, then the haiku judge's operational timeout, then a local-embeddings
pilot, plus the load-bearing "stop forcing top-1" design change). This session
delivered only the design change and its measurement harness — trigger-document
expansion (270+ skills, explicitly "by priority group") and the judge timeout
fix are named in "Next steps" below, not attempted here.

**1. A signal beyond the raw BM25 score** (`56bf53c0:consult.py:106-134`,
`_SKILL_CANDIDATES_MARGIN_FLOOR = 0.1`): the top1-vs-top2 raw-score margin.
`rank_skills()` (the `use_judge=False` `--skill-candidates` preview path only —
scoped identically to the existing relevance floor) now reports
`outcome: "ambiguous"` instead of a confident `"bm25-only"` when the top
candidate clears `_SKILL_CANDIDATES_RELEVANCE_FLOOR` but does not clearly
separate from the runner-up (`56bf53c0:consult.py:893-909`). `ranked` stays
fully populated in that case (not suppressed the way `"no-candidates"` is) —
the near-tied candidates are real, plausible picks, so hiding them would
itself violate the issue's own must-not ("do not make `--skill-candidates`
select on the operator's behalf"). This is the design change the issue's
consult named as not optional: "stop forcing a top-1 return... say so
explicitly."

checked: `python3 -m pytest tests/ -k skill_candidates_signal -q` — result: 10 passed
checked: `python3 -m pytest tests/ -k skill_candidates_false_positive_rate -q` — result: 2 passed
checked: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result: 5 passed
checked: `python3 -m pytest tests/test_skill_candidates_floor.py -q` (full pre-existing file, no
regression) — result: 11 passed

**2. False-positive rate, measured live before/after against the current corpus**
(`56bf53c0:tests/test_skill_candidates_false_positive_rate.py`), over a fixed
13-query "unrelated" set drawn from two prior independent-verification records
(not authored by this session, per the issue's must-not):

derived: this session's own live run of the same computation the committed test
performs (`python3 -c "..."`, run against the corpus on disk at derivation time):
```
before=True after=True outcome=bm25-only    | fix an off-by-one error in the pagination loop
before=True after=True outcome=bm25-only    | add a retry with exponential backoff
before=True after=True outcome=bm25-only    | rename the internal variable foo to bar
before=True after=False outcome=ambiguous    | debug why the docker container exits immediately
before=True after=True outcome=bm25-only    | write a bash script that tails a log file
before=True after=True outcome=bm25-only    | convert this synchronous function to use asyncio
before=True after=True outcome=bm25-only    | investigate why the unit test for the parser is flaky
before=True after=True outcome=bm25-only    | update the changelog for the upcoming release
before=True after=True outcome=bm25-only    | fix a memory leak caused by an event listener
before=True after=False outcome=ambiguous    | reorder the columns in this CSV export
before=True after=True outcome=bm25-only    | fix this bug
before=True after=True outcome=bm25-only    | add a new feature
before=True after=True outcome=bm25-only    | clean this up

BEFORE: 13/13 = 100.0%
AFTER:  11/13 = 84.6%
```
This is a real but modest reduction (`13 - 11 = 2` of 13 queries newly flagged,
`2/13 = 15.4%`), honestly scoped to match the margin floor's own deliberately
conservative derivation — not a claim that the residual failure is solved.

canonical: `1ff061bf:docs/issue-2982/reports/adversarial-review-fc5c800d.md`
lines 130-156 (read this session) — the 89% baseline figure in the issue body
was measured there against a 35-query set generated by `/tmp/verify_noop_check*.py`
scripts; `git log --all --diff-filter=A -- '*verify_noop_check*'` returns empty,
confirming those scripts were never committed and the full 35-query text is not
recoverable from repository history. This session's 13-query set (10 from PR
#3015's record, verbatim, + the 3 example queries PR #3016's record quotes
verbatim) is the largest reproducible fixed set actually recoverable from
repository history, and is what both this test and
`tests/test_skill_candidates_signal.py` now pin down as the durable, re-runnable
fixture going forward (Direction: "the same two fixed query sets each time so
results are comparable across attempts").

**3. Alternatives measured, not asserted** (`56bf53c0:consult.py:107-134`
docstring, and `SkillCandidatesMarginMeasuredTest` in
`56bf53c0:tests/test_skill_candidates_signal.py`):
- Raising the relevance floor further: excluded by the issue's own must-not
  (measured twice already, fails both directions on this corpus).
- Judge/rerank as the signal: excluded because the judge's own operational
  timeout is not yet fixed (Direction priority 2, not attempted here) — "a
  reranker that is usually absent cannot be assessed as a reranker."
- Local embeddings: excluded, Direction scopes this to a future pilot.
- Top1/top2 raw-score margin (chosen): re-derived live this session against 7
  real operator-chosen picks (same issue/skill pairs as
  `SkillCandidatesFloorCalibratedTest.REAL_POSITIVE_TOP1_SCORES`,
  `tests/test_skill_candidates_floor.py:115-123`) and the 13-query unrelated
  set above — margin 0.185-3.139 for real picks, 0.021-5.219 for unrelated
  queries (both ranges quoted verbatim in
  `56bf53c0:tests/test_skill_candidates_signal.py`'s
  `REAL_POSITIVE_MARGINS`/`UNRELATED_QUERY_MARGINS`). Raw score alone overlaps
  completely between the two sets (pre-existing finding,
  `docs/issue-2982/reports/adversarial-review-e63d3cd4.md` lines 106-118);
  margin overlaps too at the high end (documented, not hidden — see
  `test_margin_alone_does_not_cleanly_separate_either_known_limitation` in the
  same test file) but every margin under 0.185 across both fixed sets was a
  negative, never a real pick — `_SKILL_CANDIDATES_MARGIN_FLOOR = 0.1` sits
  inside that unclaimed gap, same conservative posture as the relevance floor.

derived: `gh issue view 2906 --json title -q .title` (and the same command for
2874, 2924, 2511, 2626, 2892, 2894) — 7 titles retrieved live this session,
quoted verbatim in `56bf53c0:tests/test_skill_candidates_signal.py`'s
`REAL_POSITIVE_MARGINS` comments.

**4. Test derivation** (`test-derivation` skill, invoked this session):
`rank_skills()`'s judge-off outcome logic is a 4-column decision table
(candidates empty / top1 below relevance floor / top1-top2 margin below margin
floor / neither) evaluated in short-circuit priority order. All 4 feasible
columns are exercised — derived: `python3 -m pytest tests/ -k
skill_candidates_signal -q` plus `test/test_skill_candidates_ranking.py` (the
pre-existing empty-candidates case) together cover empty-candidates
(pre-existing), below-relevance-floor
(`test_below_relevance_floor_still_no_candidates_margin_not_reached`),
below-margin-floor (`test_close_top1_top2_reports_ambiguous_not_confident`),
and neither (`test_clear_margin_still_reports_bm25_only`,
`test_margin_just_above_floor_is_not_ambiguous`) — result: 10 passed (same run
already quoted under item 1 above). Boundary value analysis on the ordered
margin partition (single- vs. multi-candidate is the unordered partition,
marked N/A for BVA) covers the just-above-floor boundary explicitly.

## Why

The design change ("stop forcing a top-1 return") is the one piece of the
issue's Direction explicitly marked not optional, and is fully testable without
the judge fix or trigger-document work — the acceptance checks don't require
either of those. Scoping this session to that plus its measurement harness
(rather than spreading thin across all four Direction items) keeps every
delivered piece independently verifiable and honestly measured, matching the
issue's own repeated emphasis on re-deriving rather than asserting. The margin
constant's value (0.1) was chosen the same way `_SKILL_CANDIDATES_RELEVANCE_FLOOR`
was re-derived in issue #2982's follow-up: from the actual gap in measured data
(0.185 lowest real-pick margin, 0.057 highest sub-threshold negative-set margin),
not picked freehand.

## What did not work

- First boundary-value test asserted margin `== _SKILL_CANDIDATES_MARGIN_FLOOR`
  exactly (`top2 + 0.1`) stays `"bm25-only"`; failed with `'ambiguous' !=
  'bm25-only'` because `(7.0 + 0.1) - 7.0` evaluates to `0.09999999999999964` in
  IEEE-754 float arithmetic, landing just under the floor. Replaced with a
  margin clearly (not exactly) above the floor
  (`test_margin_just_above_floor_is_not_ambiguous`, committed at
  `56bf53c0:tests/test_skill_candidates_signal.py`) — the strict-`<` boundary
  semantics in `consult.py` are unchanged, only the test's chosen boundary
  value moved to avoid asserting on float equality at a computed
  floating-point boundary.

## Open findings

canonical: `1ff061bf:docs/issue-2982/reports/adversarial-review-fc5c800d.md`
(the 35-query/89% source record) and this session's own live measurement
(item 2 above) — both quoted/derived under "What was done", restated here as
open items rather than re-derived a second time.

- The 35-query set behind the issue's cited 89% figure is not reproducible
  from repository history (its generating scripts were never committed —
  derived: `git log --all --diff-filter=A -- '*verify_noop_check*'`, empty
  result, quoted under "What was done" item 2). This session's 13-query
  fixture is the largest reproducible subset and is now the one pinned down in
  committed tests. Resolution path: none needed for this issue; future
  re-measurement should extend this fixture rather than re-author a new one
  from scratch, to keep results comparable across attempts.
- The margin signal only catches near-zero top1/top2 ties — `2/13 = 15.4%` of
  the measured unrelated set (derived: item 2's before/after transcript above,
  same section). Most confidently-wrong-but-unambiguous top-1s (e.g.
  `"fix this bug"`, margin 0.364 per `tests/test_skill_candidates_signal.py`'s
  `UNRELATED_QUERY_MARGINS`) are untouched. Resolution path: named by the
  issue's own Direction as priority 1 (trigger-document expansion) and
  priority 3 (embeddings pilot) — neither attempted in this session.

## Next steps

`loop_state: landed` for the delivered piece (design change + measurement
harness); the issue overall remains open. Three items remain, in the order the
Direction specifies:

- Trigger-document expansion, by priority group — starting with skills most
  often surfaced as false top-1s in the measured unrelated set:
  `kubernetes-workload-probe-selection`,
  `release-engineering-changelog-entry-categorization`,
  `technical-feasibility-spike-report` (derived: item 2's before/after
  transcript above, "outcome=bm25-only" rows).
- The haiku judge's operational timeout fix. canonical:
  `56bf53c0:consult.py:206-233` (`_skill_judge_p90_cutoff()`,
  `_skill_judge_timeout()`) — read this session: concurrency is recorded per
  `skill_judge_perf` event (`56bf53c0:consult.py:637`,
  `"concurrency": concurrency`) but is not a factor in the adaptive p90
  timeout computed from those same events. This is a plausible mechanism for
  the Direction's observed "timed out at ~44s repeatedly" during bulk/
  concurrent evaluation, but this session had no live `runs/ledger.jsonl` with
  real haiku call timings to confirm it against — the timeout code path itself
  was read, not exercised live, so this is a code-reading hypothesis, not a
  reproduced finding.
- A local-embeddings pilot (Direction priority 3), gated on the first two
  being done first.

skill-verdict: knowledge-management-taxonomy-tagging — not-applicable: this
issue introduces a new API outcome value (`"ambiguous"`) and a measurement
signal, not a controlled-vocabulary term, tag merge, or SKOS broader/narrower
mapping.
skill-verdict: test-derivation — applied: invoked; routed `rank_skills()`'s
judge-off outcome logic as a 4-column decision table (Step 3) and the ordered
margin partition to boundary value analysis (Steps 4-5), checked all feasible
decision-table columns are exercised across new and pre-existing tests (item 4
above), and used the skill's BVA guidance to catch and replace a
float-precision boundary test before it landed (see "What did not work").
