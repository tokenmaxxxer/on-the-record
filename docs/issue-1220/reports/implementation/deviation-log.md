canonical: python3 on-the-record/monitors/test_poll_heartbeat.py
derived: python3 on-the-record/monitors/test_poll_heartbeat.py
```
5/5 passed
```

2026-08-13T00:00:00Z inline on-the-record/monitors/test_poll_heartbeat.py:100-113 t_heartbeat_skips_watchdog_when_not_due asserted the old "poll tick: skipped (within TTL)" line, which the approved proposal's own plan for poll-heartbeat.sh drops that line entirely — updated the assertion to expect empty stdout on a non-due tick; mechanical, one-off, no design judgment, does not alter deliverable behavior.
