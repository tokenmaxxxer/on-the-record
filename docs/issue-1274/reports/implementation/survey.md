# Survey — issue #1274

Write surfaces:
- `on-the-record/monitors/poll-heartbeat.sh` (around line 89) — `watchdog_rc -ne 0` unconditionally appends `[watchdog-crash]`. `roster_watchdog()`'s own docstring (spawn.py:2684) already documents rc as anomaly count, 0=clean, >0=count — never a crash signal. Bug: the monitor never read its own contract.
- `spawn.py` — `roster_watchdog()` return value is `sys.exit()`'d as-is by `main()` (spawn.py:6781). An unhandled exception inside the watchdog path currently falls through to Python's default traceback handling, exiting 1 — indistinguishable from `anomaly_count == 1`. No reserved sentinel exists yet for a genuine internal crash; needs one, per Acceptance ("simulated signal death DOES" — but a Python-level exception path also needs an unambiguous, non-collidable code).
- Tests: `gates/test_poll_heartbeat_delta.py` and `on-the-record/monitors/test_poll_heartbeat.py` both stub `spawn.py` via a fake-spawn.py harness (`FAKE_WATCHDOG_REPORT` env var, `sys.exit(0)` on the watchdog branch) run through `bash on-the-record/monitors/poll-heartbeat.sh`. Same harness pattern is reused for the new cases, adding a fake exit code lever.

Skip condition: pure bugfix (issue itself states `validity-consult-skip: trivial`) — the label taxonomy is fully specified by the issue's Requirements section and roster_watchdog's own existing contract docstring; no product/architecture decision is open. Scout/full proposal round skipped per scout-directive's bugfix skip condition.
