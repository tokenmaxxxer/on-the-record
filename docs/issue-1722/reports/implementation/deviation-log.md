## Deviation log

- 2026-08-17T10:46:18Z, `filed`, canonical: docs/issue-1722/reports/implementation/2026-08-17-hunt-suppress-quiet-patrol-poll-summary.md
  (read directly) — the pre-phase-2-completion warrant hunt found that
  this proposal's quiet-tick summary-line gate in
  `on-the-record/monitors/poll-heartbeat.sh` regresses
  `gates/test_poll_heartbeat_patrol.py`, a pre-existing, independent
  sibling test suite (issue #1598) that drives the same patrol block and
  still pins the pre-#1722 always-print contract on a quiet, no-crash
  tick. derived: `python3 gates/test_poll_heartbeat_patrol.py` (run with
  this diff applied) ->
  ```
  ok  t_kill_switch_suppresses_and_traces
  FAIL t_no_board_role_zero_side_effects:
  FAIL t_patrol_invoked_only_on_nth_tick:

  2/3 failed: ['t_no_board_role_zero_side_effects', 't_patrol_invoked_only_on_nth_tick']
  ```
  That file is outside this proposal's approved write set
  (`on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/test_poll_heartbeat.py` only) and updating its
  pinned assertions to match the new behavior is a judgment call a
  reviewer should weigh (rewrite in place vs. retire in favor of the
  newly-added coverage in `on-the-record/monitors/test_poll_heartbeat.py`).
  Per SCOPE-EXCEEDED: finishing what this proposal covers (already built
  and tested) and reporting the now-stale sibling suite for the next
  issue/role to resolve, not building it inline. Reported, not spawned.
