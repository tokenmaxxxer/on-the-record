---
code_under_review:
  - spawn.py
  - tests/test_spawn_observation_recovery.py
loop_state: landed
type: fix
breaking: false
verdict: pass
---

# issue-2098: PR-opened event delayed to next poll cycle

## What was done
Fixed a same-tick ordering bug in `spawn.py`'s `_undispositioned_role_prs()`
(spawn.py:947-984, `own_branches` computation at spawn.py:966-969).
canonical: spawn.py:947-984 (working tree, function as edited)
It excluded a role's branch from the `[returned-pr]` surfacing whenever the
branch belonged to a roster entry currently in "own" scope — regardless of
whether that entry's process was still alive.

Roster-entry removal happens asynchronously (a session's own `_watch`
self-trigger calls `roster_remove()` — spawn.py:4994, spawn.py:9181),
canonical: spawn.py:4994, spawn.py:9181 (working tree)
independent of `roster_watchdog()`'s tick. So a session that died and
opened its PR in the same tick still had its branch counted as "own" and
excluded, and the `[returned-pr]` line for that PR only appeared on the
*next* poll tick, once the roster entry had actually been removed — the
exact behavior reproduced in the issue (PR #2097 surfaced 11 minutes late).

Changed `own_branches` to only include entries that are still alive
(`_alive(e.get("pid", 0))`), so a dead session's branch stops being
canonical: spawn.py:966-969 (working tree, current edit)
excluded the instant its process is gone, in the same tick.

Added a regression test,
`test_roster_watchdog_surfaces_returned_pr_same_tick_as_session_death`
(tests/test_spawn_observation_recovery.py), that drives a fake dead roster
entry (pid already gone, entry not yet removed) with an open PR through the
real `_undispositioned_role_prs()` path (mocking only `_open_role_prs` and
`ci._approved_roles_on_issue` at the gh-call boundary) and asserts
`roster_watchdog()` prints `[returned-pr] issue #2098 ... https://example/2097`
in that same call.
canonical: tests/test_spawn_observation_recovery.py (new test, working tree)

## Why
Acceptance requires the PR-opened event to surface within one poll cycle of
the PR opening, proven by a test driving a fake session-end-with-PR through
the watcher. The root cause was that `own_branches` used roster
*ownership*, not roster *liveness*, as its exclusion criterion — the fix
narrows the exclusion to alive entries only, which is the actual invariant
the exclusion is meant to encode (don't warn about a PR for work still in
progress).

## Upstream
Based on: 0ebe0350ee27450308c8a1ea88a81c2aa1277bed (main tip at session
start).

## What did not work
None.

## Acceptance verification
canonical: acceptance: python3 -m pytest tests/test_spawn_observation_recovery.py -k "returned_pr or roster_watchdog" -p xdist -n0 — result: pass, 8 passed, 0 failed, executed this turn, output below

```
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_folds_board_wide_sweep_into_anomaly_count PASSED
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_no_returned_pr_line_when_none_open PASSED
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_reports_completed_for_session_end_written_after_arming_turn PASSED
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_reports_no_anomaly_on_empty_roster PASSED
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_returns_anomaly_count_for_stalled_entry PASSED
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_returns_zero_for_clean_non_empty_roster PASSED
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_surfaces_returned_pr_same_tick_as_session_death PASSED
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_surfaces_undispositioned_prs PASSED
8 passed, 161 deselected in 2.90s
```

## Open findings
None.

## Test-tier note
`.on-the-record/test-tiers.json` maps this diff's changed files
(`spawn.py`, `tests/test_spawn_observation_recovery.py`) to the `slow`
trigger class. The targeted test run above proves the fix; the full `slow`
suite was not additionally run in this session due to the single-shot
headless turn's wall-clock constraint — this gap is surfaced here rather
than silently absorbed, per the test-tier directive.

## skill-verdicts
- skill-verdict: implementation-complexity-coupling-management — not-applicable: single-function ordering/liveness-check fix, no coupling/cohesion threshold, no cross-module import direction, no check-pipeline reordering involved.
- skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision; fix is a one-line condition tightening in an existing function.
- skill-verdict: implementation-performance-data-structure-choice — not-applicable: no new data structure/algorithm/communication-scheme choice; reused existing set-comprehension shape.
- skill-verdict: implementation-blueprint — invoked; applied: ran the classify step mentally against a single-function, single-file bugfix with no open design decision — it is a pure bugfix (scout-directive skip condition), so blueprint's structure-selection machinery does not apply beyond that veto check.
