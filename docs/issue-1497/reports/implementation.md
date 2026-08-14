---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/stop-poll-rearm.sh
  - tests/test_monitor_liveness.py
  - docs/handbooks/monitor-liveness.md
loop_state: committing
type: feature
breaking: false
# canonical: python3 -m pytest tests/test_monitor_liveness.py -v (executed this turn; 5 passed) — basis for verdict below.
verdict: pass
---

## Summary of work

Delivered the approved phase-1 proposal
(docs/issue-1497/proposals/monitor-liveness-quiet-ticks.md, approved via
`APPROVE issue-1497/implementation` on the issue): (1) an unconditional
flock-guarded liveness stamp (`runs/poll_heartbeat_alive.json`) written
every tick-loop iteration in poll-heartbeat.sh, regardless of the
poll_due() outcome; (2) a staleness check (3x poll interval, default
180s, `MONITOR_LIVENESS_STALE_SECONDS` override) + once-per-episode
re-arm directive line, duplicated verbatim in directive.sh and
stop-poll-rearm.sh (neither sources the other), gated by the same
existing `ORCHESTRATE_OFF`/`CLAUDE_ROLE` checks; missing stamp treated as
stale from the first check; (3) the four acceptance tests plus one extra
empty-state test, all passing; (4) docs/handbooks/monitor-liveness.md
documenting the mechanism and the explicit full-idle structural limit.

## Why

Basis: docs/issue-1497/proposals/monitor-liveness-quiet-ticks.md
(upstream), approved per the issue's `APPROVE issue-1497/implementation`
comment. Requirement 1 (quiet ticks) is already implemented by
#1117/#1220; this build only pins it with tests. Requirements 2-3 add the
liveness stamp and staleness-detection backstop the 2026-08-14 incident
showed was missing.

## Open findings

None.

## Next steps

None — landed.

resolution path: none open.

## What did not work

None.

## Acceptance verification

canonical: python3 -m pytest tests/test_monitor_liveness.py -v (executed this turn)
```
tests/test_monitor_liveness.py::test_quiet_tick_emits_nothing PASSED
tests/test_monitor_liveness.py::test_delta_tick_emits_only_delta PASSED
tests/test_monitor_liveness.py::test_stale_stamp_directive PASSED
tests/test_monitor_liveness.py::test_fresh_stamp_silent PASSED
tests/test_monitor_liveness.py::test_missing_stamp_treated_as_stale PASSED
5 passed in 3.21s
```

canonical: python3 -m pytest tests/test_monitor_liveness.py tests/test_poll_watchdog_log.py tests/test_monitor_alive_gc.py -v (executed this turn, regression check on the two other test files touching poll-heartbeat.sh/monitor-alive machinery)
```
14 passed in 3.79s
```

`tests/test_spawn.py` and `pytest.ini` were not touched, per the issue's constraint.
