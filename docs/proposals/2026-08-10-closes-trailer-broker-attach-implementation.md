---
status: approved
files:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_contract_guard.py
  - docs/issue-653/reports/implementation.md
---

## Intent
Implement the revised, approved #653 ADR (`docs/issue-653/proposals/
2026-08-10-closes-trailer-preflight-hardening.md`, architecture branch,
`APPROVE issue-653/architecture`): `contract-guard.sh` attaches/corrects
`Closes #<issue>` on a phase-2 merge's PR body via `gh pr edit` before
allowing the merge, instead of denying outright; deny remains only as the
fallback when that write itself fails.

## Constraints
- Change only `contract-guard.sh`'s existing deny-branch for a missing/
  wrong `Closes #<issue>` on a phase-2 merge — no new hook, no new
  install/CI surface, per the ADR.
- Reuse the existing round-scoped phase-2 signal (#577) unchanged.
- Red/green test coverage in `test_contract_guard.py` must demonstrate the
  ADR's judgment criterion directly: a session that never writes the
  trailer still produces a correctly-closing merged PR body, and a write
  failure still denies (never silently waves the merge through).

## Rationale
Alternative considered and rejected: keep denying and only strengthen
`pr-preflight.sh`'s pre-create refusal (the prior, now-superseded
direction of this same issue). Rejected because the orchestrator's
relayed evidence (5 same-day recurrences, one spawn-and-respawn producing
0 fixes) shows a refusal only helps a session capable of self-correcting,
which the evidence says doesn't hold — a stronger refusal is still a
refusal. Auto-attach at the merge broker removes the dependency instead
of tightening a gate around it.

## What will be done
- `contract-guard.sh`: replace the immediate `deny(...)` for a missing/
  wrong `Closes #<issue>` with: build the corrected body (append the
  trailer if absent; fix the digit if a wrong `#<m>` is present), call
  `gh pr edit <pr> --body <corrected> [-R <repo>]`, and only `deny(...)`
  if that call's exit code is non-zero. A successful edit falls through to
  `sys.exit(0)` (merge proceeds).
- `test_contract_guard.py`: extend the fake `gh` shim to handle `pr edit`
  (logs the call, and can be made to fail via a per-repo `edit_fails`
  fixture flag), update the four existing tests that asserted deny-on-
  missing-trailer so they instead assert the broker attached the trailer
  and allowed the merge (green: auto-attach path), and add new tests for:
  wrong-issue-number correction, and the `edit_fails` fallback-to-deny
  path (red: write failure still blocks).
- Write `docs/issue-653/reports/implementation.md` per the record-shape
  directive.

## Out of scope
- `pr-preflight.sh` changes — the ADR defers these explicitly.
- Any new hook, CI job, or install step.
- Round-scoping logic itself (#577) — reused, not modified.

## How you'll know it worked
`pytest on-the-record/hooks/test_contract_guard.py` passes, including new
cases proving: (a) a phase-2 merge with no `Closes` trailer at all still
merges, with the broker's `gh pr edit` call carrying the corrected body
(green — the deadlock the issue reports cannot occur); (b) a wrong
`Closes #<m>` gets corrected in place; (c) when the `gh pr edit` write
itself fails, the merge is still denied (red — auto-attach must not
silently wave through an unfixed body).

## Accumulation
This is a single hand-edit to one hook file's one deny-branch and one
matching test file, not a repeated-pattern change across a list of
similar files (contrast: `roles/*.json` mass edits). If a similar
broker-attach-at-merge need arises for another trailer/field in the
future, it composes by adding another corrected-body branch in this same
function rather than duplicating the `gh pr edit` call site — there is
exactly one call site today and this change does not multiply it.

## What did not work
(none yet — appended live if something breaks during the build)
