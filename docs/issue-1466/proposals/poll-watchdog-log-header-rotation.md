---
status: approved
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - tests/test_poll_watchdog_log.py
---

Spec leaves no design decision open (scout-directive skip condition 2) —
see docs/issue-1466/reports/implementation/survey.md. Approved via issue
comment "APPROVE issue-1466/implementation" from JiwonJung94
(docs/specs/approvers.md, single-account mode).

## Request

poll-heartbeat.sh appends each due tick's watchdog report to
poll-watchdog.log with no timestamp and no rotation, making incident-time
correlation impossible and the file grow unbounded.

## Constraints

- One tick-header line per tick (not per line) — must not disturb the
  line-keyed delta-diff suppression, which operates on Monitor stdout,
  not this log.
- Size-based rotation to exactly one `.1` predecessor generation;
  rotation failure must be non-fatal to the monitor loop.
- Monitor-channel stdout must stay byte-identical.
- Confirm no existing tool parses the current log format before landing.

## Rationale

Considered adding the timestamp per-line instead of per-tick-header, since
that's simpler to implement with a single `sed`-style transform. Rejected
because the issue explicitly requires one header per tick to avoid
touching the delta-diff suppression's line-keyed state, and per-line
timestamps would also bloat the log further, working against the
rotation goal.

Considered log rotation via `logrotate`-style external config. Rejected
as overkill and outside this script's existing self-contained bash
pattern (no external rotation infra exists in this repo) — a bash
size-check-and-rename before each append is consistent with the file's
existing non-fatal `|| true` append pattern.

## What will be done

- Add a bash helper in poll-heartbeat.sh that, before an append to
  poll-watchdog.log: (1) checks current file size against a bounded
  threshold and rotates the existing file to `poll-watchdog.log.1`
  (overwriting any prior `.1`) when over threshold, non-fatally; (2)
  prints an ISO-8601 local-timestamp tick-header line before the tick's
  body content.
- Apply this helper at both existing append sites (due-tick report path,
  poll-due-crashed path).
- Leave the Monitor stdout `printf` calls (printed_text / diff_output)
  completely untouched.
- Add tests/test_poll_watchdog_log.py with the four named tests plus the
  empty-state case (first-ever append to a missing log file).

## Out of scope

- Any change to Monitor stdout content or the delta-diff suppression
  logic.
- Compression of rotated `.1` files.
- Configurable rotation threshold via env var beyond what's needed to
  make the threshold testable.

## How you'll know it worked

`tests/test_poll_watchdog_log.py::test_tick_header_timestamp`,
`::test_rotation_at_threshold`, `::test_rotation_failure_nonfatal`, and
`::test_monitor_stdout_unchanged` all pass.
