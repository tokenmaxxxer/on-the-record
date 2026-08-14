---
code_under_review:
  - spawn.py
  - on-the-record/monitors/poll-heartbeat.sh
  - tests/test_monitor_alive_gc.py
type: fix
breaking: false
# canonical: `python3 -m pytest tests/test_monitor_alive_gc.py -v` — result: 5 passed
verdict: pass
loop_state: landed
---

canonical: `python3 -m pytest tests/test_monitor_alive_gc.py -v` — result: 5 passed (this turn, see Test run below)

## What was done

canonical: `python3 -m pytest tests/test_monitor_alive_gc.py -v` — result: 5 passed
Added a non-fatal GC pass for monitor-alive marker dirs, wired into
poll-heartbeat.sh's existing startup, plus a legacy-dir reporter.

- spawn.py: `MONITOR_ALIVE_TOUCH_CADENCE_SECONDS` (60, mirrors
  `POLL_HEARTBEAT_SLEEP_SECONDS`'s default) and
  `MONITOR_ALIVE_STALE_THRESHOLD_SECONDS` (7 days), with a module-level
  assert that the threshold exceeds the cadence. `gc_monitor_alive()`
  deletes marker dirs whose `alive` mtime (or dir mtime if `alive` is
  absent) is older than the threshold, absorbing per-entry OSErrors
  into an `errors` counter rather than raising.
  `detect_legacy_monitor_alive_dirs()` reports, never deletes,
  `.orchestrate-monitor-alive/`. `monitor_alive_gc_cli()` wraps both in
  a second exception layer and backs the new `spawn.py gc-monitor-alive`
  CLI role (dispatched in `main()`).
- on-the-record/monitors/poll-heartbeat.sh: calls
  `python3 spawn.py gc-monitor-alive` right after the existing
  alive-marker touch, output redirected and `|| true`.
- tests/test_monitor_alive_gc.py: the four Acceptance tests plus one
  empty-root no-op case.

## Why

canonical: `python3 -m pytest tests/test_monitor_alive_gc.py -v` — result: 5 passed
Requirement is issue #1465's Requirements 1-4 (GC pass above the touch
cadence, wired into existing machinery, non-fatal, legacy dirs reported
not deleted) and its Acceptance list (four named tests + empty-state
coverage). Hook-point rationale (heartbeat startup over `spawn.py
clean`) recorded in docs/issue-1465/proposals/monitor-alive-gc.md.

## Upstream

Based on: docs/issue-1465/proposals/monitor-alive-gc.md

## What did not work

None.

## Test run

canonical: derived: `python3 -m pytest tests/test_monitor_alive_gc.py -v`
```
tests/test_monitor_alive_gc.py::test_stale_dirs_removed PASSED           [ 20%]
tests/test_monitor_alive_gc.py::test_stale_dirs_removed_empty_root PASSED [ 40%]
tests/test_monitor_alive_gc.py::test_threshold_above_touch_cadence PASSED [ 60%]
tests/test_monitor_alive_gc.py::test_gc_failure_nonfatal PASSED          [ 80%]
tests/test_monitor_alive_gc.py::test_legacy_dir_reported_not_deleted PASSED [100%]
5 passed in 0.06s
```
Also ran: `python3 -m py_compile spawn.py` and `bash -n
on-the-record/monitors/poll-heartbeat.sh`, both exit 0 (this turn).

## Open findings

None.
