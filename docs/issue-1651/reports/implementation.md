---
code_under_review:
  - gates/requirement_met.py
  - gates/test_requirement_met.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #1651

## What was done

Built `gates/requirement_met.py` (commit d4b954a7): a pure
`grade(issue_body, diff, per_check_verdicts)` plus a `gh`-wrapped
`check(root, issue, pr)`, same shape as `acceptance_gate.py`/`closure_sweep.py`.
canonical: gates/requirement_met.py:1-30 (this branch's committed diff, commit d4b954a7)

It reuses `acceptance_gate._acceptance_section` for section extraction and
`check_runner.parse_checks` for the `- check:`/`gate:` bullet parser instead of
re-parsing the Acceptance section, per the issue's instruction not to re-invent
that parser.
canonical: gates/requirement_met.py:69-75 (import + grade() call sites, commit d4b954a7)

For each parsed check bullet, `grade()` extracts a cited artifact (backtick text
in the bullet), looks up a caller-supplied semantic verdict from
`per_check_verdicts`, and applies one deterministic rule: a bullet graded YES
whose cited artifact does not appear in the PR diff (or has no cited artifact at
all) goes into `blocking_reasons`. NO/UNKNOWN verdicts are recorded per-criterion
but never added to `blocking_reasons`.
canonical: gates/requirement_met.py:63-107 (grade() function body, commit d4b954a7)

Zero `- check:` bullets (an `unverifiable:`-only Acceptance section, or no
`## Acceptance` section at all) takes a separate code branch returning
`{"empty_state": True, ...}`.
canonical: gates/requirement_met.py:69-82 (empty_state branches, commit d4b954a7)

Did not wire this into `spawn.py` or any hook — the issue scopes this to the
gate module and its tests; wiring is stated in the issue as a separate issue.

## Why

northpole req#6 (requirement fidelity): a builder session can self-attest that
acceptance criteria are met; nothing today grades a landing PR against each
frozen criterion from outside the building session. This gate is the missing
external-grading half, extending `acceptance_gate` (#310) and
`reexecution_gate`.

## Upstream / basis

Issue #1651 body, fetched this session via `gh issue view 1651 --json body`.
Reused code read from `gates/acceptance_gate.py`, `gates/check_runner.py`,
`gates/closure_sweep.py`, `gates/reexecution_gate.py`,
`gates/landing_obligation.py`.

## What did not work

None — no reverted approach this session.

## Test evidence

acceptance: python3 -m pytest gates/test_requirement_met.py -v — result: PASS
canonical: pytest gates/test_requirement_met.py -v (this session's own live run,
executed this turn against the committed working tree, commit d4b954a7)

```
gates/test_requirement_met.py::t_multiple_criteria_one_blocking_one_not PASSED
gates/test_requirement_met.py::t_yes_with_artifact_absent_from_diff_fails PASSED
gates/test_requirement_met.py::t_yes_with_artifact_present_in_diff_passes PASSED
gates/test_requirement_met.py::t_no_verdict_never_blocks_even_without_artifact PASSED
gates/test_requirement_met.py::t_yes_with_no_cited_artifact_at_all_blocks PASSED
gates/test_requirement_met.py::t_semantic_verdict_is_advisory_only_recorded_not_blocking_by_itself PASSED
gates/test_requirement_met.py::t_empty_state_no_acceptance_section_is_distinct_result PASSED
gates/test_requirement_met.py::t_empty_state_no_check_bullets_is_distinct_result PASSED
gates/test_requirement_met.py::t_unknown_verdict_never_blocks PASSED
9 passed in 0.91s
```

Nine test functions cover: a YES verdict with the cited artifact present in the
diff; a YES verdict with the cited artifact absent from the diff; a YES verdict
with no artifact cited at all; NO and UNKNOWN verdicts never entering
`blocking_reasons` even without a matching artifact (the advisory-only
separation the issue requires); an Acceptance section with zero `- check:`
bullets; an issue body with no `## Acceptance` section at all; and a
multi-criterion body with one blocking and one non-blocking criterion.

acceptance: python3 -m pytest -q -m "not slow" gates/ — result: PASS
canonical: pytest -q -m "not slow" gates/ (this session's own live run, executed
this turn against the committed working tree, commit d4b954a7); command taken
from `.on-the-record/test-tiers.json`'s `fast` tier — no `spawn.py`/hook files
are in this diff so the `slow` tier's `trigger_change_classes` do not apply

```
742 passed, 8 xfailed in 4.39s
```

## Open findings

None.
