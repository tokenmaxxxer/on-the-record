---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - tests/test_poll_watchdog_log.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_poll_watchdog_log.py -v (this session's own run, raw output below)
verdict: pass
loop_state: landed
---

## What was done

Added `_poll_watchdog_log_append()` in on-the-record/monitors/poll-heartbeat.sh:
rotates poll-watchdog.log to `.1` (overwriting any prior generation) when
its size exceeds `POLL_WATCHDOG_LOG_MAX_BYTES` (default 5MB) before an
append, non-fatally (`|| true` throughout, same pattern as the existing
append sites); then writes an ISO-8601 local-timestamp `[tick] ...`
header line followed by the tick's body, one header per tick. Applied at
both existing append call sites (due-tick watchdog report, poll-due
crashed path). Monitor stdout (`printed_text`/`diff_output` printf
calls) is untouched.

canonical: python3 -m pytest tests/test_poll_watchdog_log.py -v (this session's own run, raw output pasted below)

acceptance: python3 -m pytest tests/test_poll_watchdog_log.py -v — result: pass

```
$ python3 -m pytest tests/test_poll_watchdog_log.py -v
tests/test_poll_watchdog_log.py::test_tick_header_timestamp PASSED       [ 25%]
tests/test_poll_watchdog_log.py::test_rotation_at_threshold PASSED       [ 50%]
tests/test_poll_watchdog_log.py::test_rotation_failure_nonfatal PASSED   [ 75%]
tests/test_poll_watchdog_log.py::test_monitor_stdout_unchanged PASSED    [100%]
4 passed in 0.52s
```

canonical: python3 on-the-record/monitors/test_poll_heartbeat.py (this session's own before/after run, isolated with git stash / git stash pop around the "before" run; raw output pasted below)

Also ran the existing on-the-record/monitors/test_poll_heartbeat.py
suite (not part of this issue's Acceptance) before and after the change:

```
$ python3 on-the-record/monitors/test_poll_heartbeat.py   # (before, via git stash)
ok  t_heartbeat_arms_watchdog_when_due
FAIL t_heartbeat_attaches_on_board_repo: board target repo must get an alive marker
FAIL t_heartbeat_refuses_to_arm_on_non_git_root: poll tick: due, watchdog ran (rc=0, no output)
ok  t_heartbeat_respects_kill_switch
FAIL t_heartbeat_skips_attachment_on_non_board_repo: non-board target repo must not get a poll_heartbeat_last_state.json
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller
3/8 failed: ['t_heartbeat_attaches_on_board_repo', 't_heartbeat_refuses_to_arm_on_non_git_root', 't_heartbeat_skips_attachment_on_non_board_repo']

$ python3 on-the-record/monitors/test_poll_heartbeat.py   # (after, working tree)
ok  t_heartbeat_arms_watchdog_when_due
FAIL t_heartbeat_attaches_on_board_repo: board target repo must get an alive marker
FAIL t_heartbeat_refuses_to_arm_on_non_git_root: poll tick: due, watchdog ran (rc=0, no output)
ok  t_heartbeat_respects_kill_switch
FAIL t_heartbeat_skips_attachment_on_non_board_repo: non-board target repo must not get a poll_heartbeat_last_state.json
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller
3/8 failed: ['t_heartbeat_attaches_on_board_repo', 't_heartbeat_refuses_to_arm_on_non_git_root', 't_heartbeat_skips_attachment_on_non_board_repo']
```

Identical failure sets before and after — this change introduces no
regression in that pre-existing (unrelated) suite.

## Why

issue #1466: poll-watchdog.log has no per-line timestamps and no
rotation, making incident-time correlation impossible during the
2026-08-14 GraphQL rate-limit incident (#1459/#1461/#1462 root-cause
work).

## Upstream basis

docs/issue-1466/proposals/poll-watchdog-log-header-rotation.md

## Existing-parser check (req #4)

canonical: docs/issue-1466/reports/implementation/survey.md "Existing-parser check" section (rg sweep over the working tree, this session's own)

No existing tool parses poll-watchdog.log's current format — confirmed
in the phase-1 survey via an `rg` sweep across the working tree; the
only non-script hits (gates/test_poll_heartbeat_delta.py,
on-the-record/monitors/test_poll_heartbeat.py,
on-the-record/hooks/test_poll_rearm.py, plus a comment-only mention in
poll-rearm.sh) do not read this log file's on-disk contents back in.

## What did not work

None.

## Open findings

None.

## loop_state

landed
