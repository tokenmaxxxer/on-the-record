---
status: proposed
files:
  - docs/issue-745/reports/conformance-review.md
---

# Proposal — issue #745 conformance-review: Item 3 three-axis skip-eligibility

## Intent

Board condition holds (see
docs/issue-745/reports/conformance-review/current-state.md): implementation
commit 22e162ed landed on main and no conformance-review record exists yet
for it. This proposal is phase 1 only — it fixes the requirement list
phase 2 will check against, not any verdict.

## Constraints

- Verdicts are per-requirement (Present/Surface/Absent/Incorrect/
  Unverifiable), never a holistic code-quality judgment, and never a fix
  — findings route to the implementation role, addressed_to
  issue-745/implementation.
- Phase 2 works from the artifact (docs/issue-745/reports/implementation.md,
  commit 22e162ed) and the spec
  (docs/issue-745/proposals/item3-execution-observation-conditioning.md)
  only, deliberately without relying on the implementation record's own
  narration of what it did.

## What will be done (phase 2, once approved)

Check each of the seven requirements listed in the current-state survey
against the actual code in gates/skip_eligibility.py,
gates/spawn_on_pr.py, and the test files, then write one verdict row per
requirement into docs/issue-745/reports/conformance-review.md.

## Out of scope

- Editing gates/skip_eligibility.py, gates/spawn_on_pr.py, or any other
  implementation file — findings are reported, not fixed, by this role.
- Re-scoring the proposal's own RICE table or its pre-registered
  measurement design — that was product-discovery's call, already
  approved.

## How you'll know it worked

docs/issue-745/reports/conformance-review.md exists, carries one verdict
row per requirement in the current-state survey's "What phase 2 will
check" list, cites its evidence with file:line or a derived: command
reproduction per requirement, and every non-Present verdict is
addressed_to issue-745/implementation.
