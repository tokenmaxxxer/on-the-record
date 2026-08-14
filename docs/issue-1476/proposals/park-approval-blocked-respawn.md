---
status: proposed
files:
  - gates/spawn_on_pr.py
  - spawn.py
  - tests/test_spawn_on_pr_park.py
---

## Request

spawn-on-pr's respawn gate keeps respawning a verification role whose only
blocker is an unresolved human-APPROVE state, wasting one full session per
tick to rediscover it (observed: issue-1163/conformance-review, 17
consecutive re-check PRs). Fix: park the respawn once the blocker is
confirmed unchanged since the prior tick, keyed off a structured signal
(never prose matching); re-arm on a real state change; keep parked entries
visible in watchdog output.

## Constraints

- Structured field only, never prose matching (issue's own consult-log
  risk note).
- Re-arm only on: new APPROVE comment, new commit on the role branch, or
  explicit unpark — never elapsed time alone.
- Watch-coverage inviolable: a parked entry must still surface in watchdog
  output, just labeled waiting-for-human instead of spawned.
- Existing watchdog test(s) asserting "every tick spawns" must be updated
  to account for parking.

## Rationale

Two structured signals were available to key the park decision on:

1. Read the role's own board-record frontmatter (`loop_state`/`blocker`
   field) — this is what a role that has already written a phase-2 record
   would carry. Rejected: for the reported case
   (`docs/issue-1163/reports/conformance-review.md`, non-existent per the
   survey) the blocked role never gets to write a record at all — the
   approval gate blocks the phase-2 write that would create the file. A
   signal that depends on a file the blocker itself prevents from existing
   can never fire.
2. Reuse `gates/ci.py:_approved_roles_on_issue()` (exact-string
   `APPROVE issue-<n>/<role>` comment scan, already the codebase's
   canonical structured approval signal) plus the role branch's current PR
   head commit sha, persisted per tick in a small JSON state file. Chosen:
   it needs no new comment-matching logic (reuses the existing exact-match
   scan), and it is available before any board record exists, which is
   exactly the state a parked role is stuck in.

## What will be done

- `gates/spawn_on_pr.py`: add a persisted park-state file
  (`runs/spawn_on_pr_parked.json`, `{"subject/role": {"blocker": str,
  "head_sha": str}}`). For each spawn-candidate pair, compute the current
  structured signal (`approved_roles = _ci._approved_roles_on_issue(...)`;
  blocked iff `role not in approved_roles`; `head_sha` = the pair's PR head
  commit). Park (skip spawn) iff a prior-tick entry exists with the same
  blocker and the same head_sha; otherwise spawn normally and persist the
  new signal. Any entry whose role is now in `approved_roles`, or whose
  head_sha changed, unparks and is removed/refreshed.
- `spawn.py`: the watchdog board-sweep print site (next to the existing
  `[watchdog] spawn-on-pr: N건 스폰` line) gains a line listing parked
  `subject/role` pairs as waiting-for-human, sourced from the same park
  state — no observation loss.
- `tests/test_spawn_on_pr_park.py`: the four Acceptance tests
  (`test_approval_blocked_respawn_parked`, `test_no_18th_spawn_on_replay`,
  `test_unpark_on_approve_comment`, `test_parked_entry_still_reported`),
  each driving the pure park-decision functions with injected/mocked
  inputs (no real `gh` calls).
- Any existing watchdog test asserting every tick produces spawn activity
  gets updated to reflect that a still-blocked pair now parks instead of
  respawning.

## Out of scope

- Changing `_approved_roles_on_issue()` itself or its exact-match
  semantics.
- Any change to the role-session approval protocol (contract v3 s19)
  itself — this only stops the *automatic watchdog spawn* from repeating
  when nothing has changed, not the approval flow.
- `backfill_closed()` / closed-issue debt path — untouched.

## Accumulation

The park-state file (`runs/spawn_on_pr_parked.json`) grows one entry per
distinct `(subject, role)` pair that has ever parked, not one line per
tick — repeated ticks on the same still-blocked pair update that one
existing entry in place (same key), they do not append. The file is
bounded by the number of PR-triggered roles (`PR_TRIGGERED_ROLES`, fixed at
2) times the number of open subjects with an open PR — the same order of
magnitude the board itself already is, not an unbounded log. An entry is
removed once its role re-arms (approved or head sha advances), so a
long-lived repo does not accumulate stale parked entries for resolved
roles.

## How you'll know it worked

- The four `tests/test_spawn_on_pr_park.py` tests pass.
- `test_no_18th_spawn_on_replay` specifically replays the issue-1163-shaped
  sequence (same blocker, same head sha, tick after tick) and asserts no
  further spawn occurs while unchanged.
- `test_parked_entry_still_reported` asserts the parked pair still shows up
  in the reporting path (not silently dropped).
- The pre-existing "every tick spawns" watchdog test is updated and still
  green.
