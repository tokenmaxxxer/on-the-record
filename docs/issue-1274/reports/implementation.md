---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - spawn.py
  - gates/test_poll_heartbeat_delta.py
type: fix
breaking: false
verdict: unverifiable
loop_state: landed
---

## What was done
Fixed `on-the-record/monitors/poll-heartbeat.sh`'s `[watchdog-crash]` labeling: it previously labeled ANY nonzero `roster_watchdog()` exit code as a crash, but the rc is an anomaly COUNT by contract (0=clean, N=N anomalies), not a crash flag. Changed the crash condition from `watchdog_rc -ne 0` to `watchdog_rc -ge 128 || watchdog_rc -eq 97` (signal death, or a new reserved sentinel). Added `WATCHDOG_CRASH_SENTINEL = 97` in `spawn.py`, wrapped the `watchdog` CLI dispatch branch in try/except so an unhandled internal exception exits with that sentinel (with a traceback to stderr) instead of Python's default exit-1 (which would collide with `anomaly_count == 1`). Extended `roster_watchdog()`'s docstring to state the full rc convention explicitly. Added four hermetic regression tests to `gates/test_poll_heartbeat_delta.py` using the existing fake-spawn.py harness (extended with a `FAKE_WATCHDOG_RC` lever): rc=1 anomaly → no crash label, rc=137 (signal death) → crash label, rc=97 (sentinel) → crash label, rc=0 clean → neither label.

## Why
requirement: northpole req#4 (observability signals must be truthful) — docs/specs/northpole.md. False crash alarms fired on every tick with even one benign anomaly (e.g. spawn-coverage gh read failure), making the crash label diagnostically worthless.

## Upstream
Based on: docs/issue-1274/proposals/watchdog-crash-label-fix.md

## Acceptance verification
canonical: `python3 gates/test_poll_heartbeat_delta.py` and `python3 on-the-record/monitors/test_poll_heartbeat.py` — this session's own live run, output below
checked: both suites — result: pass

```
$ python3 gates/test_poll_heartbeat_delta.py
13/13 passed
$ python3 on-the-record/monitors/test_poll_heartbeat.py
5/5 passed
```

verdict: unverifiable — the acceptance-relevant paths (anomaly rc vs. signal-death/sentinel rc) are covered by the hermetic tests above; no live watchdog process was exercised, per the issue's own Acceptance which asks for hermetic tests only.

## What did not work
None.

## Open findings
None.

## closed_checks
- name: anomaly-rc-no-crash-label
  code_sha: HEAD (working tree at time of test run)
- name: signal-death-and-sentinel-produce-crash-label
  code_sha: HEAD (working tree at time of test run)
