---
code_under_review:
  - docs/specs/enforcement-boundary.md
type: docs
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #573 boundary-spec follow-up (phase 2)

## Summary of work

Added the two missing verdict rows to
`docs/specs/enforcement-boundary.md`'s `on-the-record/hooks/*.sh
(plugin-shipped)` table, per the approved phase-1 proposal
(`docs/issue-573/proposals/boundary-spec-followup.md`):

- `delegated-judgment-gate.sh` — verdict `contract` (issue #573).
- `product-capture-stopgate.sh` — verdict `contract` (issue #566).

No hook behavior, `hooks.json`, or other spec file was touched — write
set matched the proposal exactly.

## Why

`gates/test_boundary.py` (test `t_all_gates_modules_recorded`) was red on
`main` because both hooks shipped (PR #583 for #573, PR #569 for #566)
without their required verdict rows. The prior delivery record's own
"Resolution path" named this exact follow-up as the next unit.

## Upstream / basis

docs/issue-573/proposals/boundary-spec-followup.md (approved via issue
comment `APPROVE issue-573/implementation`, single-account mode).

## Test output

```
$ python3 gates/test_boundary.py
ok - t_a_new_unrecorded_module_is_caught
ok - t_all_gates_modules_recorded
ok - t_class_b_disposition_rows_cited
ok - t_gate_porting_rows_are_ported_or_justified
ok - t_gates_docstring_states_retroactivity_rule
ok - t_issue_492_reconcile_pieces_present
ok - t_run_md_references_unenforced_clauses
ok - t_run_md_streaming_landing_is_default_norm
ok - t_spec_records_the_operator_boundary_decision
ok - t_unenforced_clauses_file_matches_spec_exactly
ok - t_ci_supplement_or_out_of_scope_rows_are_cross_referenced
ok - t_every_deleted_workflow_has_migration_row
ok - t_workflows_dir_absent_or_empty
13/13 passed
```

## What did not work

None.

## Open findings

None.
