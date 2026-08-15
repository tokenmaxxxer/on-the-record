---
status: proposed
files:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
---

Skip condition: pure bugfix to an existing classifier (`_MACHINE_BODY_RE`)
— extending a regex with one more fixed-format shape leaves no design
decision open, per the scout-directive's skip condition. Scouting was
skipped accordingly.

## Request

Extend pr-preflight's machine-comment classifier so the watchdog
`Judgment opened`/`Verdict: PR #? -> escalate` shapes (already covered)
and bare single-account approval strings (`APPROVE issue-N/role`, not yet
covered) are both classified machine/reconciliation-exempt, with a
hermetic unit test covering all three observed shapes plus a negative
case (#1552).

## Constraints

- Must not weaken the reconciliation gate for genuine operator comments —
  only the exact-match `APPROVE issue-<n>/<role>` token shape is exempt,
  never a prose comment that merely mentions approval.
- Must not touch the phase1/phase2 approval-detection logic itself
  (the hook's separate `APPROVE ` scan elsewhere in the file) — this
  proposal only changes what counts as a "machine comment" for the
  reconciliation-cursor block.

## Rationale

Considered folding the APPROVE-string exemption into the existing
`_MACHINE_LOGIN_RE` (login-based) check instead of `_MACHINE_BODY_RE`
(body-based). Rejected: the approval comment is posted by a real human
approver account (docs/specs/approvers.md), not a bot login, so a
login-based rule can never match it — the exemption has to key off the
comment's fixed body shape, same mechanism already used for the watchdog
templates.

## What will be done

- Add one alternative to `_MACHINE_BODY_RE` matching `^APPROVE
  issue-\S+/\S+\s*$` (exact-token shape only).
- Add a hermetic test (`test_pr_preflight.py`) that calls
  `_is_machine_comment`/`_MACHINE_BODY_RE` directly against the three
  observed shapes — `Judgment opened: ...`, `Verdict: PR #... -> escalate
  ...`, `APPROVE issue-N/role` — and asserts all three classify as
  machine/exempt, plus one non-templated human comment (e.g. "looks good,
  approving informally") that must still require reconciliation.

## Accumulation

`_MACHINE_BODY_RE` is a single regex with one alternative added per
exempted comment shape (issue #1310's original 7, this proposal's 1
more). If future issues keep adding one-off exempt shapes at this rate,
the regex stays a flat, readable alternation — no shared helper is
warranted until the alternative count grows large enough to obscure
intent (not yet, at 8 alternatives).

## Out of scope

- Any change to the phase1/phase2 approval-detection logic that already
  scans for the literal `APPROVE issue-<n>/<role>` string elsewhere in
  the hook.
- Any other watchdog/machine comment shape not named in the issue.

## How you'll know it worked

`python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q` passes,
including the new hermetic classifier test, with no regressions in the
existing suite.
