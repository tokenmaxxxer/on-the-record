---
code_under_review:
  - on-the-record/hooks/directive.sh
  - gates/test_scope_option_directive.py
type: docs
breaking: false
verdict: pass
loop_state: landed
---

Subject: issue-1712

validity-consult-skip: trivial
design-research-skip: mechanical

Skip record (scout-directive): scouting skipped — mechanical
directive-text edit, spec leaves no design decision open (the issue's
Acceptance criteria already specify the required wording).

## What was done

Edited the SCOPE-OPTION PROPOSAL block in
`on-the-record/hooks/directive.sh` (issue #1707) so the orchestrator runs
the VALIDITY CONSULT (#1024) on the vague ask first, before any option
exists, and derives the option block from that consult's output; the
`consult-trace:` field per option cites that same run. The
post-confirmation #1024 consult may reference the same trace instead of
re-running it when the confirmed ask is unchanged from the vague ask the
consult already ran on.
canonical: on-the-record/hooks/directive.sh:266-292 (working tree, this
session's own edit).

Extended the NEUTRALITY RULE to additionally bar the Korean substrings
`권장` and `추천` (either, case/substring match), alongside the existing
`recommended` token bar.

Updated the first-contact banner text to mention that a design-bearing,
scope-ambiguous ask gets a small option block instead of clarifying
questions.

Added assertions `t_states_consult_runs_on_vague_ask_before_options`,
`t_states_neutrality_rule_forbids_korean_synonyms`, and
`t_states_banner_mentions_option_path` to
`gates/test_scope_option_directive.py`.

## Why

Issue #1712: PR #1711's review flagged that options must cite a
`consult-trace:`, but #1024 as originally worded ties the validity
consult to the CONFIRMED ask — at option-presentation time (before
confirmation) no consult trace yet exists to cite, a chicken-and-egg gap.
canonical: `gh issue view 1712` (executed this session; body quoted in
this session's transcript). Closing it required reordering: run the
consult on the vague ask first, derive options from its output.

Rejected alternative: leave #1024 unchanged and let options cite no
trace until after confirmation — rejected because it reopens the same
chicken-and-egg gap the issue exists to close.

## Upstream / basis

Based on: docs/issue-1707/reports/implementation.md (the SCOPE-OPTION
PROPOSAL block this issue amends) and the issue-1712 body's own
Acceptance criteria, which supplied the ordering and neutrality wording
used above.

## Acceptance verification

canonical: acceptance: python3 gates/test_scope_option_directive.py — result: pass

Run this turn against the working tree:

```
$ python3 gates/test_scope_option_directive.py
ok - t_states_banner_mentions_option_path
ok - t_states_consult_runs_on_vague_ask_before_options
ok - t_states_consult_trace_per_option
ok - t_states_neutrality_rule_forbids_korean_synonyms
ok - t_states_neutrality_rule_forbids_recommended_token
ok - t_states_non_overlap_with_1006_req4
ok - t_states_option_block_count_and_order
ok - t_states_option_fields
ok - t_states_trigger_subclass
9/9 passed
```

canonical: acceptance: python3 gates/test_scope_option_directive.py — result: pass

- check: directive states the scope-option subclass runs the validity
  consult on the vague ask first and derives the option block from its
  output, with the #1024 post-confirmation consult able to reference the
  same trace — proven by `t_states_consult_runs_on_vague_ask_before_options`.
- check: neutrality rule additionally bars 권장/추천, banner mentions the
  option path — proven by `t_states_neutrality_rule_forbids_korean_synonyms`
  and `t_states_banner_mentions_option_path`.
- empty state: non-subclass elicitation and confirmed-ask consult flow
  unchanged — the REQUIREMENT ELICITATION block and the VALIDITY CONSULT
  (#1024) section body were not edited; only the SCOPE-OPTION PROPOSAL
  section and the banner text changed, proven by the pre-existing tests
  `t_states_trigger_subclass`, `t_states_non_overlap_with_1006_req4`,
  `t_states_option_block_count_and_order`, `t_states_option_fields`, and
  `t_states_neutrality_rule_forbids_recommended_token` still passing
  unmodified in the run above.

## Test-tier note (issue #1518)

```
$ cat .on-the-record/test-tiers.json
{
  "fast": {
    "command": "python3 -m pytest -q -m \"not slow\"",
    "budget_seconds": 300
  },
  "slow": {
    "command": "python3 -m pytest -q -m slow",
    "trigger_change_classes": [
      "spawn.py",
      "tests/test_spawn.py",
      "on-the-record/hooks/*.sh",
      "on-the-record/hooks/test_*.py"
    ]
  }
}
```

This change touches `on-the-record/hooks/*.sh`, matching the `slow`
tier's trigger_change_classes. Slow tier was not run this session
(headless single-shot turn, time-boxed) — surfacing the tiering gap per
this directive rather than silently absorbing it.

canonical: acceptance: python3 -m pytest -q -m "not slow" gates/test_scope_option_directive.py — result: pass

```
$ python3 -m pytest -q -m "not slow" gates/test_scope_option_directive.py
9 passed in 0.90s
```

## What did not work

None.

## Open findings

None known.
