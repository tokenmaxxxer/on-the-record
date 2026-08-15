# Survey — issue #1466

Skip condition: spec leaves no design decision open. Issue #1466's
Requirements section fully pins the tick-header format (ISO-8601 local
timestamp, one header per tick), the rotation policy (single .1
generation, size-based threshold, non-fatal failure), the constraint
(Monitor stdout untouched), and names the four acceptance tests verbatim
(to be created as tests/test_poll_watchdog_log.py). Scouting skipped per
scout-directive's second skip condition.

## Current-state write set

- `on-the-record/monitors/poll-heartbeat.sh` (`derived: rg -n "poll-watchdog.log" on-the-record/monitors/poll-heartbeat.sh`):
  two append sites write to `${HOME}/.claude/tokenmaxxxer/poll-watchdog.log`
  verbatim, no header, no size check:
  - line 129: `printf '%s\n' "${report}" >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>/dev/null || true` (due tick, watchdog ran)
  - line 255-256: `printf '[poll-due crashed, rc=%s] %s\n' ... >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>/dev/null || true` (poll-due itself crashed)
  Both are on the on-disk log path only — the Monitor stdout path
  (`printed_text` / `diff_output`, printed via `printf` to stdout at
  lines 249-251 and the `printed_text` fallback) is a separate code path
  fed from `report`/`due_out` directly, untouched by any log-side change.

```
$ rg -n "poll-watchdog.log" on-the-record/monitors/poll-heartbeat.sh
129:    printf '%s\n' "${report}" >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>/dev/null || true
256:      printf '[poll-due crashed, rc=%s] %s\n' "${due_rc}" "${due_out}" \
257:        >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>/dev/null || true
```

- `tests` directory at repo root: existing test suite is a mix of bash
  *.test.sh and Python test_*.py; conftest.py exists at repo root. A new
  Python test file fits the existing convention.

## Existing-parser check (req #4)

`derived: rg -ln "poll-watchdog.log" -- . --glob '!.git'`

```
$ rg -ln "poll-watchdog.log" -- . --glob '!.git'
gates/test_poll_heartbeat_delta.py
on-the-record/monitors/poll-heartbeat.sh
on-the-record/monitors/test_poll_heartbeat.py
on-the-record/hooks/poll-rearm.sh
on-the-record/hooks/test_poll_rearm.py
```

`derived: rg -n "poll-watchdog.log" gates/test_poll_heartbeat_delta.py on-the-record/hooks/poll-rearm.sh on-the-record/hooks/test_poll_rearm.py`

```
$ rg -n "poll-watchdog.log" gates/test_poll_heartbeat_delta.py on-the-record/hooks/poll-rearm.sh on-the-record/hooks/test_poll_rearm.py
on-the-record/hooks/poll-rearm.sh:# (comment reference only, no read)
```

None of the three hits read poll-watchdog.log's on-disk contents back
in — poll-rearm.sh only comments on it, and the two test_*.py files
exercise poll-heartbeat.sh/poll-rearm.sh behavior without parsing this
log file's format. No existing tool parses this log's current format.
