# issue-997 current-state survey

## Scope in question
canonical: `gh issue view 997`
canonical: `gh issue view 586`
Issue #997 (batch 5 of `docs/issue-586/proposals/product-discovery.md`,
merged #995) asks to extend the "2-role seed fixture" so the judgment
gate renders a full 3+-role panel. Issue #997's acceptance text names
`gates/test_role_spec_shape.py`, but that file has no panel/judgment-gate
content at all.

derived: `grep -n panel gates/test_role_spec_shape.py`
```
(no output)
```

canonical: `gh issue view 586` acceptance section
The actual seed pair lives in
`on-the-record/hooks/test_delegated_judgment_gate.py`
(`ARCHITECTURE_ROLE` + `SECURITY_ROLE`, function
`t_multi_role_panel_quorum_and_unanimous_support_approves`), matching
issue #586's own acceptance criterion 3 verbatim: "check: extension of
test_delegated_judgment_gate.py with a multi-role fixture beyond the
seed pair." Issue #997's file reference reads as a paraphrase mismatch
against #586's own acceptance text; #586 is the requirement #997 cites.

## What exists today
canonical: on-the-record/hooks/delegated-judgment-gate.sh:615-712 (read in full this session)
`delegated-judgment-gate.sh` iterates `ROLES` (loaded from every
`roles/*.json` carrying `judgment_axes`/`write_scope`) with no hardcoded
pair assumption (`for role in ROLES`, `evaluating_roles` list
comprehensions). No script change is needed to support 3+ roles; only
the *test fixture* is still 2-role-only.

canonical: on-the-record/hooks/test_delegated_judgment_gate.py (read in full this session)
`test_delegated_judgment_gate.py` seeds `ARCHITECTURE_ROLE` (axis
`maintenance_complexity`) and `SECURITY_ROLE` (axis `attack_potential`),
used by `t_auto_approve_single_role` (1 role) and
`t_multi_role_panel_quorum_and_unanimous_support_approves` /
`t_partial_support_with_no_opinion_escalates_not_approves` (2 roles). No
3+-role case exists.

canonical: python3 -c "import json; [print(f, json.load(open(f)).get('judgment_axes')) for f in ['roles/architecture.json','roles/security-threat-model.json','roles/capacity-planning.json','roles/performance-engineering.json','roles/conformance-review.json']]" (executed this session)
```
roles/architecture.json ['maintenance_complexity']
roles/security-threat-model.json ['attack_potential']
roles/capacity-planning.json ['external_burden']
roles/performance-engineering.json ['performance']
roles/conformance-review.json ['alignment']
```
All 5 axes have exactly one owning role in this reading.

## Write set implied
Exactly one file: `on-the-record/hooks/test_delegated_judgment_gate.py`
— add a third seed-role dict (`PERFORMANCE_ROLE`, mirroring
`ARCHITECTURE_ROLE`/`SECURITY_ROLE`'s shape) and new test function(s)
exercising a 3-role panel.

canonical: on-the-record/hooks/delegated-judgment-gate.sh:615-712 (read in full this session)
No production code path changes are implied — the gate script already
handles N roles per the section read above; this is fixture-only,
matching the product-discovery batch-5 row's own complexity score
("scope is a single test file extension, well-specified by the existing
2-role seed fixture" — docs/issue-586/proposals/product-discovery.md
line 72).

## Scout-directive skip
canonical: on-the-record/hooks/test_delegated_judgment_gate.py (read in full this session, functions `t_auto_approve_single_role`, `t_auto_reject_with_finding_and_remediation`, `t_multi_role_panel_quorum_and_unanimous_support_approves`)
Skipped: the spec leaves no design decision open. The axis-to-role
assignment, the fixture's shape (role dict with `write_scope` +
`judgment_axes`, `_axis_block()` helper, `_run()`/`_stub_gh()` harness),
and the existing tests' expected outcomes are all fixed by the pattern
this extends. There is no product-facing surface or exemplar category
to scout against — this is an internal test-fixture extension of an
existing, already-designed harness.
