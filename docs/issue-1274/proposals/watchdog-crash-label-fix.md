---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - spawn.py
  - gates/test_poll_heartbeat_delta.py
  - on-the-record/monitors/test_poll_heartbeat.py
---

Skip condition: pure bugfix (scout-directive skip condition) — issue #1274 states `validity-consult-skip: trivial`, and the fix is fully specified by `roster_watchdog()`'s existing contract docstring plus the issue's own Requirements section. No design decision is open; scouting/full survey round skipped accordingly (survey.md still written, per survey-order-directive, to record the concrete write set).

## Request
poll-heartbeat.sh currently labels ANY nonzero watchdog exit code `[watchdog-crash]`, even though `roster_watchdog()`'s contract defines that exit code as an anomaly COUNT (0=clean, N=N anomalies), not a crash flag. Fix the monitor to only emit `[watchdog-crash]` for an actual crash (signal death, or a new reserved sentinel for an unhandled internal exception), and document the convention.

## Constraints
- Existing delta-suppression / always-emit line behavior (issue #1220) must keep working for whatever line is emitted.
- `roster_watchdog()`'s CLI return-as-exit-code contract (spawn.py:2684) stays unchanged for the normal (non-crashing) path — only the monitor's crash-label side and the previously-undefined "internal exception" path change.
- Hermetic tests only (existing fake-spawn.py harness), no live watchdog process.

## Rationale
Two ways to fix considered:
1. **Chosen**: keep `rc` as the anomaly count; change poll-heartbeat.sh's crash test to `rc >= 128` (signal death) or `rc == <reserved sentinel>`; add the sentinel by wrapping the watchdog CLI dispatch in spawn.py with a try/except that exits that sentinel on an unhandled exception instead of falling through to Python's default (which currently exits 1, colliding with anomaly_count==1).
2. **Rejected**: keep the crash signal out-of-band (e.g. write a marker file on crash, ignore rc entirely) — rejected because it adds a second signal-carrying channel between two already-coupled processes for no benefit; the rc-based contract already exists and is documented, it was simply misread by the monitor. Reusing and correctly respecting the existing rc contract is simpler and keeps the crash/anomaly distinction in the one place (`roster_watchdog`'s docstring) that already documents rc's meaning.

## What will be done
- `spawn.py`: define a reserved exit-code sentinel (e.g. 97) for a genuine internal crash; wrap the `watchdog` CLI branch in try/except so an unhandled exception exits with the sentinel (logging the traceback to stderr) instead of Python's default exit-1 behavior. Extend `roster_watchdog()`'s docstring to state the full convention: rc=0 clean, rc>0 anomaly count, sentinel or rc>=128 (signal death) = real crash.
- `on-the-record/monitors/poll-heartbeat.sh`: change the `[watchdog-crash]` condition from `watchdog_rc -ne 0` to `watchdog_rc -ge 128 || watchdog_rc -eq <sentinel>`.
- Add hermetic regression tests to the existing fake-spawn.py harness in `gates/test_poll_heartbeat_delta.py` and/or `on-the-record/monitors/test_poll_heartbeat.py`: rc=1 (anomaly) → no crash label; rc=137 (signal death, 128+9) → crash label; rc=sentinel → crash label; rc=0 → neither label (unchanged).

## Accumulation
This is a one-off condition fix (one `if` in poll-heartbeat.sh, one try/except in spawn.py's watchdog CLI branch) — not a repeated per-entry pattern like `roles/*.json`. If N more monitors grow their own ad hoc "any nonzero rc = crash" heuristic in the future, the fix is the same each time: read the called command's own documented exit-code contract instead of assuming rc!=0 means crash; no shared helper is warranted for a fix this localized (two call sites total: this monitor and spawn.py's own dispatch).

## Out of scope
- Changing `roster_watchdog()`'s anomaly-counting logic itself.
- Any change to `_auto_respawn_check()` or roster respawn behavior.

## How you'll know it worked
`python3 gates/test_poll_heartbeat_delta.py` and `python3 on-the-record/monitors/test_poll_heartbeat.py` pass, including the new cases; a manual read of `roster_watchdog()`'s docstring states the crash-vs-anomaly convention explicitly.
