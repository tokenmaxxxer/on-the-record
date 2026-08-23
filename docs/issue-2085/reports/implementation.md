---
code_under_review: HEAD
loop_state: landed
type: bugfix
breaking: false
verdict: pass
---

# issue-2085: acceptance-shape gate — collect all missing elements in one refusal

## What was done
Investigated `gates/acceptance_gate.py` function `check_issue_body` (the
module the issue's Acceptance names via `gates/`). It already collects ALL
three missing elements (check-grammar/prose-only, empty-state, provenance)
into one `bad` list and returns them together — this behavior was landed
by commit `b4fa617a` ("fix(issue-555): acceptance gate collects all format
violations in one refusal") and is exercised by the pre-existing test
`t_all_three_violations_reported_together` in
`gates/test_acceptance_gate.py`. `spawn.py` function `require_acceptance_gate`
joins that list into a single `sys.exit(...)` refusal message (one
spawn-time message, not one gh round-trip per element).

canonical: read gates/acceptance_gate.py:82-107 and spawn.py:709-717

Ran the existing suite live to confirm no regression and that behavior
matches the issue's acceptance criterion, then added
`t_issue_2085_all_three_named_in_single_refusal` to
`gates/test_acceptance_gate.py` — a regression test using this issue's own
number and driving an issue body missing all three elements at once,
asserting the single refusal list names all three.

```
$ python3 gates/test_acceptance_gate.py
ok - t_acceptance_heading_case_and_level_insensitive
ok - t_all_three_violations_reported_together
ok - t_artifact_reference_passes
ok - t_artifact_reference_without_empty_state_or_provenance_blocks
ok - t_empty_state_and_provenance_present_passes
ok - t_empty_state_not_applicable_passes
ok - t_gate_colon_line_passes
ok - t_gates_workflow_path_no_longer_passes
ok - t_issue_2085_all_three_named_in_single_refusal
ok - t_missing_acceptance_section_blocks
ok - t_only_reads_acceptance_section_not_whole_body
ok - t_prose_only_acceptance_blocks
ok - t_unverifiable_escape_passes
ok - t_unverifiable_exempts_empty_state_and_provenance
14/14 passed
```
canonical: python3 gates/test_acceptance_gate.py — pasted live run above (executed-unit)
acceptance: python3 gates/test_acceptance_gate.py — result: pass (full pasted run above shows every test, including t_issue_2085_all_three_named_in_single_refusal, which drives an issue body missing check-grammar, empty-state, and provenance and asserts the single returned list names all three).

## Why
The issue's reproduction (tm-dicequest#55, three separate spawn round-trips
each surfacing one lone missing element) predates the issue-555 fix that
already made `check_issue_body` collect-and-report-all. No source change
to the gate's logic was needed; the gap was that #2085's specific
acceptance wording (naming this issue's own regression test) had no test
tied to it yet, so the fix landed by #555 was undocumented against this
issue number.

## Upstream basis
b4fa617a (fix(issue-555): acceptance gate collects all format violations
in one refusal); gates/acceptance_gate.py; gates/test_acceptance_gate.py.

## What will be done
No behavior change to `gates/acceptance_gate.py`. Added one regression
test in `gates/test_acceptance_gate.py` that ties this issue's acceptance
wording to already-existing collect-all-violations behavior.

## What did not work
None.

## Skill verdicts
skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion threshold, accessor chain, or cross-module import direction involved; single pure function, no structural change.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision; the fix is a regex/list-collection function, not pattern-shaped.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure, algorithm, or communication-scheme choice; small fixed-size list of at most 3 strings.
skill-verdict: implementation-blueprint — not-applicable: single-file test addition, no multi-module structure decision, and the change is a bugfix/verification task, not new architecture.
skill-verdict: technical-feasibility-build-vs-buy-dependency-health — not-applicable: no dependency or vendor candidate involved.
skill-verdict: upstream-defect-report-convention — not-applicable: no upstream project defect being filed; this is an in-repo gate fix/verification.

## Open findings
None.
