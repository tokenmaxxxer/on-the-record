---
code_under_review:
  - on-the-record/hooks/directive.sh
  - gates/test_scope_option_directive.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

Subject: issue-1707

## What was done

Added a SCOPE-OPTION PROPOSAL block to `on-the-record/hooks/directive.sh`
(inserted between REQUIREMENT ELICITATION and VALIDITY CONSULT), and a
directive-content unit test, `gates/test_scope_option_directive.py`,
asserting the directive carries these obligations. Both committed at
8e35cd60.

The directive block states:

- The trigger subclass: asks that are BOTH design-bearing (no testable
  acceptance shape yet) AND scope-ambiguous (more than one plausible
  scope) — a strict subset of REQUIREMENT ELICITATION's (#1006 req#4)
  vague-ask catch. An explicit non-overlap statement: every other vague
  ask (design-bearing but scope-clear, or scope-ambiguous but not
  design-bearing) keeps the open-question path unchanged.
- The option-block form: exactly 2 or 3 options, ordered by ascending
  scope size (narrowest first), each carrying `scope:`, `cost:`, `risk:`,
  `non-goals:`, and `consult-trace:` fields.
- The verifiable neutrality rule: the literal token `recommended`
  (case-insensitive) MUST NOT appear anywhere in the option block —
  replacing the unverifiable "no preference" instruction the issue names.
- Each option's `consult-trace:` field cites the validity/risk consult
  ref the option's alternatives/tradeoffs were drawn from
  (scribe-not-inventor: options derive from consult output, not
  invented).

## Why

Issue #1707: for the dev-team-replacement program's gap 1, the orchestrator
currently returns every ambiguity to the operator as open questions
(#1006 req#4), leaving the product-judgment work on the operator. Consult
data showed consults reliably produce concrete alternatives/tradeoffs, so
for the narrow design-bearing-and-scope-ambiguous subclass the orchestrator
can propose bounded, neutral options instead and let the operator pick or
edit.

## Upstream / basis

Based on: docs/issue-1006/proposals/operator-experience-layer.md (the
existing REQUIREMENT ELICITATION / req#4 mechanism this directive narrows
against) and the issue-1707 body's own "Refinements from validity consult
(2026-08-17)" section, which supplied the threshold, verifiable form, and
non-overlap relation used verbatim above.

## Acceptance verification

canonical: acceptance: python3 gates/test_scope_option_directive.py — result: pass

Run this turn against the committed 8e35cd60 tree:

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

canonical: acceptance: python3 gates/test_scope_option_directive.py — result: pass

- check: directive defines the trigger subclass and the option-block form
  (2-3 options, scope/cost/risk/non-goals fields, ascending scope order,
  "recommended" token forbidden) — proven by
  `t_states_trigger_subclass`, `t_states_non_overlap_with_1006_req4`,
  `t_states_option_block_count_and_order`, `t_states_option_fields`,
  `t_states_neutrality_rule_forbids_recommended_token`.
- check: each option cites its consult trace — proven by
  `t_states_consult_trace_per_option`.
- empty state: precise asks and non-design-bearing vague asks are
  untouched — the REQUIREMENT ELICITATION block (unmodified) still gates
  all other vague asks; the new block only fires for the strict subclass.
  unverifiable: no live conversational fixture exists in this repo to
  execute the empty-state path end-to-end (directive.sh is a
  prompt-injection hook, not a callable function) — verified instead by
  reading the inserted text's own scope, which names the non-overlap
  explicitly (asserted by `t_states_non_overlap_with_1006_req4` above).

## Doc placement ladder

No env var/config key/new dep/migration/setup step, no library-or-format
choice over a named alternative, no changed public signature/wire format,
and no benchmark/investigation numbers — nothing placed on the doctrine
ladder.

## Open findings

None.

## What did not work

None.
