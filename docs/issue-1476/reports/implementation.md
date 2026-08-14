---
code_under_review:
  - gates/spawn_on_pr.py
  - spawn.py
  - tests/test_spawn_on_pr_park.py
type: fix
breaking: false
verdict: pass  # canonical: python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q — 18 passed, 0 failed (this turn)
loop_state: landed
---

canonical: `python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q` — 18 passed, 0 failed (fenced output below, this turn's run)

## What was done

Implemented the park/re-arm mechanism from
`docs/issue-1476/proposals/park-approval-blocked-respawn.md`:

canonical: gates/spawn_on_pr.py (this turn's edit, see `code_under_review`)
- `spawn_missing_for_pr()` now, per candidate `(subject, role)` pair,
  checks a persisted park state (`runs/spawn_on_pr_parked.json`, per
  `root`). A pair only gets checked for park when a prior-tick entry
  exists AND the current PR number (already computed via
  `spawn._pr_open_or_merged_for_branch`, no new gh call for that part)
  matches the prior one — i.e. no new commit landed. Only then does it
  call `is_approval_blocked()` (new function, wraps a call structurally
  equivalent to `gates/ci.py`'s `_approved_roles_on_issue` — the
  codebase's existing exact-string `APPROVE issue-<n>/<role>` comment
  scanner, structured, never prose matching). `should_park()` is a pure
  function combining these into the park/no-park verdict. A first-time
  candidate (no prior park entry) always spawns, unchanged from before —
  no new gh calls on that path, so existing tests needed no mocking
  changes.
- Added `parked_report(root)` (lists currently-parked `(subject, role)`
  pairs) and `unpark(root, subject, role)` (explicit re-arm, requirement
  2's third trigger) plus a `spawn_on_pr.py unpark --subject --role` CLI
  subcommand.
- `spawn.py`: the watchdog board-sweep print site (next to the existing
  `[watchdog] spawn-on-pr: N건 스폰` line) now also prints
  `[watchdog] spawn-on-pr: waiting-for-human N건: [...]` when
  `parked_report()` is non-empty — parked pairs stay visible instead of
  silently dropping out of watchdog output (requirement 3).
- `tests/test_spawn_on_pr_park.py`: the four Acceptance tests plus three
  supporting tests (pure `should_park()` truth table, explicit `unpark()`,
  and an empty-state case confirming a never-before-seen pair spawns
  without any gh approval lookup).

## Why

canonical: docs/issue-1476/reports/implementation/survey.md (written this
turn) — the survey found no existing structured per-role blocker field
usable before a role has ever written a board record (the exact state a
human-approve-blocked role is stuck in), so the park signal is built from
two already-existing structured primitives instead: the exact-match
APPROVE-comment scanner already present in the codebase, and the
PR-number lookup `spawn_missing_for_pr()` already performs every tick.

## Upstream

Based on: docs/issue-1476/proposals/park-approval-blocked-respawn.md

## Test run

canonical: python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q — this turn's run, fenced below
```
$ python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q
..................                                                       [100%]
18 passed in 0.34s
```

canonical: python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q — same run as above
The four Acceptance tests (`test_approval_blocked_respawn_parked`,
`test_no_18th_spawn_on_replay`, `test_unpark_on_approve_comment`,
`test_parked_entry_still_reported`) are inside that pytest run.

## What did not work

None.

## Open findings

None.
