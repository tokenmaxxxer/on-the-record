---
issue: 3018
role: adversarial-review-533b82da
author: adversarial-review-533b82da
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: b4cba7ddf3b792d14d940bf51fc328cbce6cc96d (PR #3036: consult.py, spawn.py, tests/test_skill_candidates_signal.py, tests/test_skill_candidates_false_positive_rate.py)
type: fix
breaking: false
verdict: pass
loop_state: landed
upstream:
  - path: docs/issue-3018/reports/knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2.md
    sha: b4cba7ddf3b792d14d940bf51fc328cbce6cc96d
  - path: consult.py (rank_skills(), _SKILL_CANDIDATES_MARGIN_FLOOR)
    sha: b4cba7ddf3b792d14d940bf51fc328cbce6cc96d
---

# issue-3018 — adversarial-review-533b82da record

## What was done

Independent verification of PR #3036 (issue #3018, top1/top2 margin signal).
Fetched the PR head into an isolated worktree (`git fetch origin
pull/3036/head:pr-3036-review && git worktree add /tmp/pr-3036-review
pr-3036-review`), re-ran the three acceptance checks there unmodified, audited
the diff against the issue's must-not list, traced the provenance of the
evaluation queries, and ran my own independently-authored 15-query measurement
against the PR's shipped code (not the PR's own fixture) to check the actual
effect on the issue's headline 89%-wrong-top-1 complaint.

checked: `python3 -m pytest tests/ -k skill_candidates_signal -q` (in
/tmp/pr-3036-review, PR head b4cba7dd) — result: 10 passed
checked: `python3 -m pytest tests/ -k skill_candidates_false_positive_rate -q`
(same worktree) — result: 2 passed
checked: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q`
(same worktree; this maps to the pre-existing
`b4cba7dd:tests/test_skill_candidates_floor.py`, confirmed via `derived: grep
-rl skill_candidates_regression_cases tests/` in the worktree, which returned
that one path) — result: 5 passed

acceptance: `python3 -m pytest tests/ -k skill_candidates_signal -q` — result: 10 passed
acceptance: `python3 -m pytest tests/ -k skill_candidates_false_positive_rate -q` — result: 2 passed
acceptance: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result: 5 passed

All three of the issue's acceptance checks pass, independently re-run in an
isolated worktree, not trusted from the PR's own claimed test-plan numbers.

**Must-not audit** (all four checked against the diff, not asserted):
- Relevance floor not raised — derived: `git diff main...HEAD -- consult.py |
  grep -n RELEVANCE_FLOOR` (run in /tmp/pr-3036-review) — the only match is
  the unchanged context line `_SKILL_CANDIDATES_RELEVANCE_FLOOR = 4.0`; the
  diff adds a new, separate `_SKILL_CANDIDATES_MARGIN_FLOOR = 0.1` constant
  alongside it and never touches the relevance-floor value or its comparison
  site (`b4cba7dd:consult.py:108`).
- Evaluation queries not authored by the delivering session — derived: `grep
  -n "off-by-one\|exponential backoff\|rename the internal\|docker container
  exits\|tails a log file\|asyncio\|parser is flaky\|changelog\|memory
  leak\|CSV export\|fix this bug\|add a new feature\|clean this up"
  docs/issue-2982/reports/adversarial-review-e63d3cd4.md
  docs/issue-2982/reports/adversarial-review-fc5c800d.md` — all 10 of the
  10-query set and 3 additional queries ("fix this bug" / "add a new
  feature" / "clean this up") from
  `b4cba7dd:tests/test_skill_candidates_signal.py` and
  `b4cba7dd:tests/test_skill_candidates_false_positive_rate.py` appear
  verbatim in those two prior-issue records (session `adversarial-review-
  e63d3cd4`, PR #3015, and session `adversarial-review-fc5c800d`, PR #3016).
  canonical: `b4cba7dd:docs/issue-3018/reports/knowledge-management-taxonomy-
  tagging+test-derivation-66e9bdc2.md` frontmatter, `role:
  knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2` — a third,
  different session from either query source, and the one that authored
  PR #3036. This is the correct shape; issue #2982's first derivation
  failure (self-authored eval queries) is not repeated here.
- `--skill-candidates` does not select on the operator's behalf — canonical:
  `b4cba7dd:spawn.py:2501-2522` (the `a.skill_candidates` CLI branch), read
  in the worktree: it calls `rank_skills()` and prints the raw JSON result,
  no post-processing. canonical: `b4cba7dd:consult.py` diff hunk around
  `rank_skills()` — the new `"ambiguous"` branch returns `{"ranked": ranked,
  "outcome": "ambiguous", "picked": []}`; `picked` stays empty and `ranked`
  stays fully populated (unlike `"no-candidates"`, which clears `ranked`).
  The caller sees every candidate and the tie; nothing is pre-selected.
- Landed floor not removed without measuring — same derived grep as the
  first bullet confirms the floor is untouched, not removed; nothing needed
  re-measuring on this axis.

**Independent effect measurement** (my own 15 queries, authored for this
verification and checked by grep against every fixture already in the repo
to confirm none overlap — full list and per-query output below): run live
against PR head via `spawn._bm25_cross_family_scores`/`spawn.rank_skills` in
the isolated worktree.

derived: `python3 /tmp/my_own_query_check.py` run in `/tmp/pr-3036-review`
(PR head b4cba7dd) — result:
```
BEFORE (confident top1, raw floor only): 15/15 = 100.0%
AFTER  (confident top1, margin signal):  14/15 = 93.3%
before=True  after=True  outcome=bm25-only    margin=0.5345000744267496   top1=html5-game-rendering-loop | upgrade the postgres driver to the async version
before=True  after=True  outcome=bm25-only    margin=0.13157359483927866  top1=secure-coding-input-validation-injection-defense | add input validation to the signup form
before=True  after=True  outcome=bm25-only    margin=0.354179743795239    top1=refactoring-legacy-characterization-test-scope | profile why the batch job is slow on large inputs
before=True  after=True  outcome=bm25-only    margin=1.0042192273145405   top1=code-architecture | write a Dockerfile for the worker service
before=True  after=True  outcome=bm25-only    margin=3.021317176777414    top1=parallel-decomposition | split this monolithic function into smaller pieces
before=True  after=True  outcome=bm25-only    margin=0.32607364603352007  top1=diagnose-first | fix the flaky CI step that times out intermittently
before=True  after=True  outcome=bm25-only    margin=3.8022944458838968   top1=api-design-payload-design | add a health check endpoint to the API
before=True  after=True  outcome=bm25-only    margin=1.2567833228951688   top1=release-engineering-readiness-checklist | migrate the config loader from yaml to toml
before=True  after=True  outcome=bm25-only    margin=0.18628322611215786  top1=product-discovery-hypothesis-testing | deduplicate the rows before writing to the output file
before=True  after=True  outcome=bm25-only    margin=0.48415751817225505  top1=finance-unit-economics-proposal-shape | add unit tests for the new pricing calculator
before=True  after=True  outcome=bm25-only    margin=0.6476836609494612   top1=architecture-module-boundary-definition | resolve the merge conflict in the auth module
before=True  after=False outcome=ambiguous    margin=0.03210782922193722  top1=sales-objection-handling | cache the results of this expensive database query
before=True  after=True  outcome=bm25-only    margin=3.195412260315634    top1=legal-compliance-vendor-dpa | handle the null pointer exception in the payment flow
before=True  after=True  outcome=bm25-only    margin=2.5673448520991418   top1=secure-coding-cryptography-secrets-management | set up a cron job to rotate the log files nightly
before=True  after=True  outcome=bm25-only    margin=9.576674371167275    top1=observability-signal-use | increase the thread pool size for the worker queue
```

Only 1 of 15 queries converted from a confident wrong top-1 to `"ambiguous"`
(margin 0.032 — a razor-thin near-tie). The other 14 have margins ranging
0.13 to 9.58 — most far above the 0.1 margin floor — and pass through
completely unaffected. This is consistent with the PR's own disclosed number
on its own fixture (2/13 = 15.4% conversion, canonical:
`b4cba7dd:docs/issue-3018/reports/knowledge-management-taxonomy-
tagging+test-derivation-66e9bdc2.md` "What was done" item 2 transcript): on
two independently-sourced query sets, the margin signal converts roughly one
in ten to one in fifteen confidently-wrong top-1s, and leaves the large
majority completely untouched.

## Why

Two judgment calls the task specifically assigned to this session, not to a
checklist:

**(1) Scope — defensible slice or inversion?** canonical: `gh issue view
3018` "Direction" section, read this session — the issue's Direction ordered
three cost-ranked interventions at the vocabulary-mismatch root cause
(trigger-document expansion first, "attacks that directly"; haiku-judge
timeout fix second; embeddings pilot third, gated on a measurement pilot) and
named the top1/top2-margin design change ("stop forcing a top-1 return")
separately, as something the consult called "not optional" regardless of
which recall intervention lands — i.e., additive on top of a recall fix, not
a substitute for one. PR #3036 (canonical: `gh pr view 3036` body, read this
session) ships only the design change and skips both recall-facing
priorities, stating this openly as "a deliberate partial delivery." Per the
letter of the issue's must-not list and the Direction's own text, this is not
a forbidden move — the design change is explicitly named, nothing here
contradicts an explicit constraint, and the PR's own record is unusually
candid that this is a partial slice with the recall-facing work still
outstanding. But in substance this is closer to an inversion than a
defensible first step: the two items the consult explicitly ordered *first*,
specifically because they address the measured cause (vocabulary mismatch
means the correct skill is never retrieved, so no reordering of what was
retrieved can fix it), remain untouched, while the delivered piece only
changes how an already-wrong top-1 is *reported* on a narrow slice of
near-tie cases. Calling this "priority 3" in the verification-task framing is
generous — it isn't priority-ordered at all relative to Direction items 1–2,
and shipping it alone, first, does not advance toward the root cause the
issue exists to fix. My verdict: an inversion in substance, defensible only
in the narrow sense of not violating an explicit constraint.

**(2) Effect — does this touch the 89% number?** No, not meaningfully. My own
independently-sourced 15-query set (derived above) shows 93.3% still
confidently wrong after the fix, against 100% before — a ~7-point drop, from
one razor-margin conversion. The PR's own honestly-disclosed number on its
own fixture (100% → 84.6%, canonical: `b4cba7dd:docs/issue-3018/reports/
knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2.md` "What was
done" item 2) is larger but still leaves the large majority of wrong top-1s
untouched, and both records converge on the same qualitative finding: the
margin signal only catches near-zero ties, and most confidently-wrong-but-
unambiguous top-1s (the actual bulk of the issue's 89% complaint) sail
through with comfortable margins, several above 1.0 and one above 9.5 in my
own run. acceptance: `python3 -m pytest tests/ -k
skill_candidates_false_positive_rate -q` — result: 2 passed — the acceptance
checks pass because they were written to require only "the rate must move,
not... be left where PR #3011 left it," a strictly-less-than assertion, not a
magnitude requirement (canonical: `b4cba7dd:tests/
test_skill_candidates_false_positive_rate.py`, `assertLess(len(after),
len(before), msg)`). Passing tests here is real but is not equivalent to
closing, or substantially narrowing, the gap the issue names in its title.

## Upstream basis

- canonical: `b4cba7dd:docs/issue-3018/reports/knowledge-management-taxonomy-
  tagging+test-derivation-66e9bdc2.md`, read in full in the worktree — the
  delivering session's own record (same commit as PR #3036's head
  `b4cba7dd`); its own "Open findings" section states "The margin signal only
  catches near-zero top1/top2 ties — 2/13 = 15.4% of the measured unrelated
  set... Most confidently-wrong-but-unambiguous top-1s... are untouched" and
  names trigger-document expansion and the judge timeout fix as the
  remaining Direction items — consistent with my independent finding above,
  not contradicted by it.
- canonical: `docs/issue-2982/reports/adversarial-review-e63d3cd4.md` (PR
  #3015) and `docs/issue-2982/reports/adversarial-review-fc5c800d.md` (PR
  #3016), both read in this checkout (pre-existing on `main`, not part of PR
  #3036's diff) to confirm query provenance by the grep quoted under
  "Must-not audit" above.
- derived: `git diff main...HEAD --stat` and `git diff main...HEAD --
  consult.py spawn.py` in `/tmp/pr-3036-review` (base `a6b5ecdb`, head
  `b4cba7dd`): `consult.py` (+65 lines: the margin constant and the
  `"ambiguous"` branch), `spawn.py` (+1 line: re-exports the new constant),
  plus `b4cba7dd:tests/test_skill_candidates_signal.py` and
  `b4cba7dd:tests/test_skill_candidates_false_positive_rate.py` (new test
  files, not present on `main`).
- My own 15-query set (verbatim, for reproducibility — none overlap any
  fixture already in the repo, checked by grep before use): "upgrade the
  postgres driver to the async version", "add input validation to the signup
  form", "profile why the batch job is slow on large inputs", "write a
  Dockerfile for the worker service", "split this monolithic function into
  smaller pieces", "fix the flaky CI step that times out intermittently",
  "add a health check endpoint to the API", "migrate the config loader from
  yaml to toml", "deduplicate the rows before writing to the output file",
  "add unit tests for the new pricing calculator", "resolve the merge
  conflict in the auth module", "cache the results of this expensive database
  query", "handle the null pointer exception in the payment flow", "set up a
  cron job to rotate the log files nightly", "increase the thread pool size
  for the worker queue". Full per-query before/after/margin/top1 output
  quoted verbatim under "What was done" above (`derived:` block).

## Open findings

- The issue's actual complaint (89% confident-wrong-top-1 on unrelated
  queries) remains almost entirely unaddressed after PR #3036 — derived:
  both measurements quoted above (the PR's own 15.4% conversion, my own 6.7%
  conversion) agree the margin signal only reaches near-zero ties. Not a
  defect in PR #3036 itself (it does what it says, honestly, and violates no
  must-not per the "Must-not audit" above), but the issue should not be
  considered materially progressed toward its own acceptance-line problem
  statement by this PR alone. Resolution path: Direction priority 1
  (trigger-document expansion) is the intervention the consult said "attacks
  that directly" — still not started, per `b4cba7dd:docs/issue-3018/reports/
  knowledge-management-taxonomy-tagging+test-derivation-66e9bdc2.md` "Next
  steps".
- No code-correctness defect found in the delivered margin-signal logic
  itself — derived: `python3 -m pytest tests/ -k skill_candidates_signal -q`
  (10 passed) plus the `b4cba7dd:consult.py` diff reading under "Must-not
  audit" above; the decision-table logic, boundary handling, and scoping
  (`use_judge=False` preview path only) all check out.

## Next steps

loop_state: landed — derived: `python3 -m pytest tests/ -k
skill_candidates_signal -q` (10 passed), `python3 -m pytest tests/ -k
skill_candidates_false_positive_rate -q` (2 passed), `python3 -m pytest
tests/ -k skill_candidates_regression_cases -q` (5 passed), all three re-run
in /tmp/pr-3036-review and quoted under "What was done" above; the must-not
audit and both judgment calls are complete, this verification record is
terminal. Recommend to whoever picks up issue #3018 next: prioritize
Direction item 1 (trigger-document expansion) over further tie-breaking
refinements to the margin signal, since that is the only intervention on
record, per both PR #3036's own consult and two independent measurements
(canonical: both quoted under "Why" item 2 above), that acts on the actual
retrieval-recall cause rather than on how an already-wrong top-1 gets
reported.

skill-verdict: adversarial-review — applied: invoked; used to structure this
PR as a deliverable to audit independently of its own claimed test-plan
results — isolated worktree, re-run acceptance checks, diff audit against the
issue's must-not list, and an independently-sourced effect measurement rather
than trusting the PR's fixture or its stated before/after numbers.
