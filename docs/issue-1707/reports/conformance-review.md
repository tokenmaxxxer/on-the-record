---
kind: conformance-review
loop_state: closed
---

# Conformance review: issue #1707 (scope-option proposal duty)

## What was done
canonical: gh issue view 1707 (acceptance section); on-the-record/hooks/directive.sh and gates/test_scope_option_directive.py checked out from issue-1707/implementation commit 8e35cd60 into this branch.
Reviewed the implementation landed on `issue-1707/implementation`
(commit `e0d534ef089ac5281e548a4f6237dcdc48a8828a`) against issue #1707's
acceptance criteria and ran the shipped unit test to confirm it actually
asserts the stated obligations.

## Why
Board condition (issue-521 conformance-review role spec): an
implementation commit landed on the branch and no conformance-review
record existed yet for this commit sha.

## Upstream basis
- issue #1707 (subject issue)
- commit 8e35cd609a4a4ef572899e252036f30b7e5d6944 — feat(issue-1707): add scope-option proposal directive + unit test
- commit e0d534ef089ac5281e548a4f6237dcdc48a8828a — docs(issue-1707): implementation record for scope-option directive
- docs/issue-1707/reports/implementation.md (implementation role's own record, present on issue-1707/implementation)

code_under_review:
- on-the-record/hooks/directive.sh
- gates/test_scope_option_directive.py

## Verdicts

### check 1 — trigger subclass, non-overlap statement, option-block form, verifiable neutrality rule; asserted by a unit test

canonical: on-the-record/hooks/directive.sh lines 266-284 (quoted below)

```
- SCOPE-OPTION PROPOSAL (issue #1707): the trigger subclass is asks that
  are BOTH design-bearing (no testable acceptance shape yet) AND
  scope-ambiguous (more than one plausible scope) — a strict subset of
  the vague asks REQUIREMENT ELICITATION above already catches. Every
  other vague ask (design-bearing but scope-clear, or scope-ambiguous but
  not design-bearing) keeps REQUIREMENT ELICITATION's open-question path
  above unchanged; this check never fires for those. For the trigger
  subclass only, do not ask open questions — instead present an OPTION
  BLOCK of exactly 2 or 3 options, ordered by ascending scope size (the
  narrowest-scope option first), each carrying `scope:`, `cost:`,
  `risk:`, `non-goals:`, and `consult-trace:` fields (`consult-trace:`
  cites the validity/risk consult ref the option's alternatives/tradeoffs
  were drawn from — scribe-not-inventor: options must derive from consult
  output, not invented). NEUTRALITY RULE (verifiable, replacing an
  unverifiable "no preference" instruction): the literal token
  `recommended` (case-insensitive, any substring match) MUST NOT appear
  anywhere inside the option block. The operator picks or edits one
  option, which then becomes the confirmed requirement fed to issue
  drafting below.
```

This text states: the trigger subclass (design-bearing AND
scope-ambiguous), an explicit non-overlap statement ("Every other vague
ask ... keeps REQUIREMENT ELICITATION's open-question path above
unchanged"), the option-block form (exactly 2-3 options, ascending scope
order, scope/cost/risk/non-goals fields), and the neutrality rule
banning the literal token "recommended" case-insensitively.

`gates/test_scope_option_directive.py` carries
`t_states_trigger_subclass`, `t_states_non_overlap_with_1006_req4`,
`t_states_option_block_count_and_order`, `t_states_option_fields`, and
`t_states_neutrality_rule_forbids_recommended_token`, each asserting the
corresponding substring/ordering condition against the directive text.

derived: python3 gates/test_scope_option_directive.py
```
$ python3 gates/test_scope_option_directive.py
ok - t_states_consult_trace_per_option
ok - t_states_neutrality_rule_forbids_recommended_token
ok - t_states_non_overlap_with_1006_req4
ok - t_states_option_block_count_and_order
ok - t_states_option_fields
ok - t_states_trigger_subclass
6/6 passed
```
spec_ref: issue #1707 acceptance bullet 1 ("directive defines the trigger subclass ... and the option-block form ... A unit test asserts the directive carries these obligations.")
evidence: on-the-record/hooks/directive.sh:266-284 + gates/test_scope_option_directive.py, derived run above
verdict: Present

### check 2 — each option cites its consult trace (validity/risk consult ref), stated in the directive and asserted by the same test

canonical: on-the-record/hooks/directive.sh lines 275-279 (quoted above): "each carrying `scope:`, `cost:`, `risk:`, `non-goals:`, and `consult-trace:` fields (`consult-trace:` cites the validity/risk consult ref the option's alternatives/tradeoffs were drawn from ...)"

The test's `t_states_consult_trace_per_option` (in the derived run
above, first ok line) asserts the section between "SCOPE-OPTION
PROPOSAL" and "VALIDITY CONSULT" contains the literal fields
`` `consult-trace:` `` and the phrase "validity/risk consult ref".
derived: python3 gates/test_scope_option_directive.py (see run above)
spec_ref: issue #1707 acceptance bullet 2 ("each option cites its consult trace (validity/risk consult ref) — stated in the directive and asserted by the same test.")
evidence: on-the-record/hooks/directive.sh:275-279 + gates/test_scope_option_directive.py::t_states_consult_trace_per_option, derived run above
verdict: Present

## open findings
canonical: this record's own Verdicts section above (both checks Present, no open findings).
None.

## next steps
canonical: this record's own Verdicts section above (both checks Present, no open findings).
None — record is terminal (closed).
