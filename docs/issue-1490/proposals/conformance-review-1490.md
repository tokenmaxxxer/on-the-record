---
status: proposed
files:
  - docs/issue-1490/reports/conformance-review.md
---

## Request

Run conformance review for issue #1490 against whatever lands on
`issue-1490/implementation` — check each of the issue's 4 stated
Requirements and 4 Acceptance items for Present/Surface/Absent/
Incorrect/Unverifiable, sourced from the build artifact and the issue
text only (not from the implementation role's stated intent).

## Constraints

- Per role directive: never render a holistic code-quality judgment,
  never fix anything found — findings hand off to the implementation
  role.
- Per contract v3 s19: this role's record file
  (`docs/issue-1490/reports/conformance-review.md`) is phase-2 output,
  gated on a human Approve for this proposal.
- Verdicts must be checkable against real artifacts (file contents,
  command output), not against the implementation role's own claims of
  what it did.

## What will be done (on Approve)

1. Re-check `issue-1490/implementation` for a phase-2 commit (code
   changes to `pytest.ini`, `conftest.py`, `requirements-dev.txt`,
   `tests/*.py`, `docs/handbooks/operations.md`,
   `docs/issue-1490/reports/implementation.md`).
2. If a phase-2 commit exists: read the diff and the delivery record,
   run the two Acceptance commands
   (`python3 -m pytest -q --ignore=bench -m "not slow"` and
   `python3 -m pytest -q --ignore=bench`) myself where feasible, and
   write one verdict per Requirement (1-4) and per Acceptance item (4)
   into `docs/issue-1490/reports/conformance-review.md`, each verdict
   citing the file/line or command output it is based on.
3. If still no phase-2 commit exists at re-check time: do not write
   the record file yet — this proposal itself documents that condition
   (see survey.md) and this role's session ends without a record,
   leaving the board unspawned for this sha until phase-2 lands.

## Out of scope

- Fixing or building anything the review finds Absent/Incorrect — those
  become findings addressed to the implementation role.
- Judging the phase-1 proposal document's design quality (that's the
  implementation role's own phase-1 approval gate, already covered by
  the `APPROVE issue-1490/implementation` comment on the issue).

## Accumulation

Not accumulation-shaped: one review record per implementation-commit
sha, produced once phase-2 lands. No repeated pattern to track here
beyond the normal one-record-per-landed-commit cadence the role
directive already describes.

## How you'll know it worked

`docs/issue-1490/reports/conformance-review.md` exists, carries one
verdict per Requirement/Acceptance item with a citation each, and
`review-traceability`/`review-record-norm` checks on that record pass.
