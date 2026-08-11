# Hunt record — issue #707, after-proposal dispatch

proposal: docs/issue-707/proposals/product-discovery.md
transition: after-proposal
stance taken: assume the mechanism the proposal specifies is bypassable as specified (rotation
index derived below, `.warrant-hunt.count` was absent before this dispatch so the count started at
zero).

derived: `cat .git/warrant/.warrant-hunt.count` (before this dispatch, file absent -> count 0)

## Placement note

The canonical hunt-record path per the warrant directive would be a hunt-record file for this
proposal, keyed by issue since the proposal path carries an issue segment. The dispatched hunter
could not write that path — this session's board-gate restricts a `product-discovery`-bound session
to `product-discovery.md`/`product-discovery/**` paths, and a hunt-record path under
`docs/issue-707/reports/` reads as another role's file under that rule. Rather than lose the
finding, it is recorded here, inside this role's own write scope, with the attribution and
reproduction the hunter produced. Whoever owns hunt-record placement next (architecture/
implementation, when they touch this issue) should relocate this section to its canonical path.

## Finding (CONFIRMED reproducible against the deployed gate code — this is phase-1 spec work, no
new code exists yet for this proposal itself)

The proposal's delegation-citation identity check (`docs/issue-707/proposals/product-discovery.md`,
"Spec-or-kill verdict" / open question 2) reads: a delegated APPROVE is refused "if the snapshot's
role matches the branch's own role." But `on-the-record/hooks/session-role-bind.sh` snapshots only
`{"role": <CLAUDE_ROLE>}` keyed by `session_id` — no issue number and no branch field is captured at
all — and `on-the-record/hooks/approval-gate.sh` only ever compares `role != branch_role`, a bare
role-name string match:

```
$ grep -n "\"role\"\|session_id\|json.dump" on-the-record/hooks/session-role-bind.sh
$ grep -n "branch_role\|role != branch_role" on-the-record/hooks/approval-gate.sh
```

Reusing this exact mechanism for delegation citation means the check can only answer "does this
session's role name equal the target branch's role name" — it cannot answer "is this session
actually the orchestrator relaying the operator's delegation" (the orchestrator's own convention
across every hook in this repo is *no* `CLAUDE_ROLE` set / no snapshot at all — `approval-gate.sh`
itself no-ops unless `CLAUDE_ROLE` is set).

**Consequence**: a role session bound to `implementation` on an unrelated issue could post `APPROVE
issue-707/docs-only VIA DELEGATION <scope>` on issue-707's branch, and the identity check as
specified would pass (`"implementation" != "docs-only"`) — even though that session is neither
issue-707's orchestrator nor its bound acting role, just some other role session whose name happens
to differ. The invariant this issue exists to protect ("the ACTOR can never approve its own
change") would hold in this exact scenario only by accident, not because the check actually verifies
orchestrator identity.

## Disposition

This sharpens open question 2 in `docs/issue-707/proposals/product-discovery.md` from "check against
#698's snapshot" (as currently specified) to: **the delegation-citation check must positively verify
the citing session is the orchestrator (absent `CLAUDE_ROLE` / no snapshot, this repo's existing
convention) — not merely that its role name differs from the branch's own role.** Carried forward
as a named open finding for step 2 (implementation) to resolve before wiring the check; not fixed
here, since this proposal's write set is phase-1 docs only and contains no gate code.
