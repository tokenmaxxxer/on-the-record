---
role: conformance-review
subject: issue-322
loop_state: scope-proposed
---

## Request

Audit the merged implementation of issue #322 (PR #351,
`issue-322/implementation`, commit `abd6e712`, merge `99fac8e2`:
`ledger/decisions.py` + `ledger/test_decisions.py`) against issue #322's
Acceptance section and the approved phase-1 proposal
`docs/issue-322/proposals/2026-08-07-decision-mining.md`. Working from
the artifact and the spec only, not builder intent.

## What will be done (phase 2, on Approve)

Produce `docs/issue-322/reports/conformance-review.md`: a per-requirement
verdict (Present | Surface | Absent | Incorrect | Unverifiable) against
the proposal's four `## What will be done` items, its `## Constraints`
block (mining surfaces only, never installs/asserts a rule), its
`## Out of scope` list (no CI wiring, no `gh api` mining, no LLM
matching, no retroactive backfill), and its `## How you'll know it
worked` acceptance line (`python3 ledger/test_decisions.py` passes),
each verdict citing exact `ledger/decisions.py`/`ledger/test_decisions.py`
line ranges or a live command result as evidence. No fixes applied to
the target artifact — findings addressed to the `implementation` role
only.

## Out of scope

- Editing `ledger/decisions.py`, `ledger/test_decisions.py`, or any other
  code — this role never fixes, only classifies.
- Judging code quality, style, or the merits of the mechanical-substring
  design choice itself (already argued in the proposal's own
  `## Rationale`) — only spec-vs-artifact conformance.
- Filing or confirming the live recurring-correction candidates the
  detector itself surfaces when run against real history — a separate,
  out-of-scope action per the source proposal's own Out of scope.
