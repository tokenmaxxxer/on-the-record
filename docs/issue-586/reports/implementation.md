---
code_under_review:
  - roles/conformance-review.json
  - roles/capacity-planning.json
  - roles/performance-engineering.json
  - gates/role_spec_shape.py
  - gates/test_role_spec_shape_batch9.py
  - docs/handbooks/architecture-methodology.md
  - docs/decisions/2026-08-10-judgment-axis-matrix.md
type: feature
breaking: false
verdict: pass
loop_state: committing
---

# Record — issue #586 step 2: realize the axis matrix (implementation, batch 1)

## Summary of work
Realizing batch 1 of `docs/issue-586/proposals/implementation.md` (approved
via `APPROVE issue-586/implementation`): assign `judgment_axes` on
conformance-review/capacity-planning/performance-engineering, extend
`check_axis_ownership` to flag zero-owner axes, wire the three axis-check
functions into `gates/role_spec_shape.py`'s `main()` via a new
`--roles-dir` mode, add tests, ship the handbook template section and the
ADR.

## Why
Closes the dead-code gap the after-proposal hunt found on the merged
architecture proposal (PR #590) and completes the 5-axis ownership matrix
per that proposal's section 1 assignment table.

## Upstream / basis
docs/issue-586/proposals/implementation.md

## What did not work
- `test_batch9_axis_ownership_passes_for_seeded_roles` and
  `test_batch9_axis_ownership_rejects_duplicate_owner` (pre-existing,
  written before the zero-owner extension) broke once
  `check_axis_ownership` started flagging zero-owner axes, because both
  passed partial-role dicts that legitimately have unowned axes outside
  what they meant to assert. Fixed by scoping their assertions to the
  specific failure mode each test targets instead of requiring an empty
  reasons list.

## Open findings
None.

## Next steps
Land this batch's edits, run the full suite, commit, push, open PR.

## Resolution path
N/A — no open findings.
