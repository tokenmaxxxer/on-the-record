---
status: proposed
subject: issue-2241
stage: 0
files:
  - spawn.py
  - skills.py
  - docs/handbooks/spawn-cli.md
  - test/test_spawn_skill_invocation.py
---

# Stage 0 — introduce skill-based spawn alongside the existing path

## Request

Add a skill-based invocation path to `spawn.py`'s CLI, callable
alongside `spawn.py <role> "<task>"`, with zero behavior change to the
existing role path. This is stage 0 of the seven-stage program in
`docs/decisions/2026-08-25-retire-role-axis-staging.md` retiring the
role axis (issue #2241).

## Constraints

- Enforcement stays core-only (frozen decision
  `single-enforcement-surface`); no skill-side hooks introduced.
- No design may reintroduce a role-shaped concept under a new name
  (frozen decision `single-skill-axis`) — the new path must resolve
  skills, never a role manifest by another name.
- The record contract must not break mid-flight: every currently
  in-flight `issue-<n>/<role>` branch must keep working unmodified.
- This stage must not touch `roster.py`'s claim/lease logic, board-gate,
  or `merge_gate.py` — those are stages 1, 3, and 5.

## Rationale

Chosen: an additive CLI surface, both paths live simultaneously,
nothing existing changes shape. Rejected alternative: replace the
`role` positional argument outright in this stage (a hard cutover of
the CLI surface itself) — rejected because every session invoked via
the existing role path (including any script or automation calling
`spawn.py <role> ...` today) would break immediately with no migration
window, and this is stage 0 of 7; the issue's own staging defers any
cutover to stage 4, after the new concepts (stage 1) are proven.

## What will be done

- `spawn.py` gains a new optional invocation shape (e.g. `spawn.py
  --skill <skill-name> "<task>" --issue <n>`) that resolves guidance via
  `skills.resolve_role_source`-equivalent logic already in place for
  the role path (per survey finding 5, guidance resolution is already
  unconditionally skill-repo), but takes a skill name directly instead
  of deriving it from a role→skill table.
- The existing `spawn.py <role> "<task>"` invocation is untouched:
  same branch naming, same claim/lease behavior, same board writes.
- `docs/handbooks/spawn-cli.md` documents both invocation shapes and
  states plainly that the skill-based path does not yet affect
  concurrency, write-scope, or observer verification — those land in
  later stages.
- A regression test asserts the two paths produce equivalent
  guidance-resolution output for a role/skill pair that map 1:1 today.

## Out of scope

- Any change to branch naming, the spawn claim, the TTL lease, board
  write-scope, or `merge_gate`'s observer check — those are stages 1,
  3, 4, and 5.
- Deleting or deprecating the role path — it stays fully functional
  through stage 3.

## How you'll know it worked

- `spawn.py <role> "<task>"` invocations behave byte-identically to
  before this stage (existing test suite for the role path passes
  unmodified).
- The new skill-based invocation successfully resolves guidance for at
  least one skill with no corresponding role name, proving the new
  path is not merely a renamed role lookup.
- `test/test_spawn_skill_invocation.py` passes, exercising both paths
  side by side.

## Rollback

Revert the `spawn.py`/`skills.py`/handbook changes in one commit; the
role path was never modified, so rollback carries zero risk to
existing sessions or in-flight branches.

## Accumulation

`spawn.py` already carries 13 inline `subprocess`/`gh` call sites (a
pre-existing shape, not introduced by this stage) — this stage adds
one new CLI branch that reuses existing call sites rather than adding
new ones. If a future stage needed to add per-skill special-casing to
`spawn.py` N more times, the right move is a shared dispatch helper
(one function keyed by skill, called once) rather than N more inline
`if role == ...`/`if skill == ...` branches; this stage's own new
branch is written as one such dispatch entry, not a repeated
copy-pasted block, so it does not itself add to the accumulation.
