SKIP CONDITION APPLIES: the spec leaves no design decision open. Issue
#1510 names the exact three constants, their exact current/target values,
and the exact two test names/assertions to add — no architectural or
naming choice remains to research.

## Constants read this session

canonical: on-the-record/monitors/poll-heartbeat.sh:166 (read before edit)
- `sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-60}"` — absolute
  epoch-seconds sleep loop, no tick-count arithmetic elsewhere in the
  script.

canonical: on-the-record/hooks/directive.sh:180 (read before edit)
- `local threshold="${MONITOR_LIVENESS_STALE_SECONDS:-180}"` (= 3 ticks at
  the 60s default).

canonical: spawn.py:5661-5663 (read before edit)
- `MONITOR_ALIVE_TOUCH_CADENCE_SECONDS = 60` with
  `assert MONITOR_ALIVE_STALE_THRESHOLD_SECONDS > MONITOR_ALIVE_TOUCH_CADENCE_SECONDS`
  where `MONITOR_ALIVE_STALE_THRESHOLD_SECONDS = 7 * 24 * 3600` — unaffected
  by the 60->120 change, the assert still holds.

canonical: derived command below
```
$ grep -ni "concurrent\|MAX_SESSIONS\|MAX_PARALLEL\|semaphore\|throttl" spawn.py
21:import concurrent.futures
5390:    """동시-판정(concurrent judgment): ...
5409:        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
```
No count-based spawn gate present; the three hits are an unrelated
judgment-panel thread pool (max_workers=2, for two roles voting), not a
session-launch cap. `spawn_cmd()` (spawn.py:4790) builds argv/env only.

canonical: tests/test_spawn.py:6693 (read before edit)
- existing concurrency-related class is `RosterConcurrency`, covering a
  different invariant (lock-free roster writes, issue #139) — a new
  `NoConcurrencyCap` class was added rather than reused.

## Write set (frozen)

- on-the-record/monitors/poll-heartbeat.sh
- on-the-record/hooks/directive.sh
- spawn.py
- tests/test_heartbeat_cadence.py (new)
- tests/test_spawn.py
- docs/issue-1510/reports/implementation.md
