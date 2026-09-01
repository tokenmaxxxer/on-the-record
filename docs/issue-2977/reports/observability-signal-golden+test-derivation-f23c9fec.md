---
issue: 2977
role: observability-signal-golden+test-derivation-f23c9fec
author: observability-signal-golden+test-derivation-f23c9fec
skills: observability-signal-golden (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/monitors/poll-heartbeat.sh
    sha: same-commit
  - path: on-the-record/monitors/test_poll_heartbeat.py
    sha: same-commit
---

# issue-2977 — observability-signal-golden+test-derivation-f23c9fec record

## What was done

Bounded the lock-reclaim logging in `on-the-record/monitors/poll-heartbeat.sh`'s
`_alive_stamp_write()` acquire loop so a contended lock cannot drive the
number of log lines past any output limit:

- Two new functions, `_reclaim_log_bounded(msg)` and `_reclaim_log_flush(lockfile)`,
  added right after `_poll_watchdog_log_append` — derived: `grep -c '^_reclaim_log_bounded()\|^_reclaim_log_flush()' on-the-record/monitors/poll-heartbeat.sh` — result: 2.
  The first collapsible reclaim event in a window logs immediately;
  further events in the same window are folded into a counter instead of
  each producing their own line; the counter is flushed into the next
  emitted line once the window elapses, and `_reclaim_log_flush` reports
  any remainder once the lock is finally acquired (so a run that ends
  mid-window still reports its count, never drops it).
- The `dead` branch and the `forming`/no-owner-recorded branch inside the
  acquire loop's retry `case` now call `_reclaim_log_bounded` instead of
  `_poll_watchdog_log_append` directly — derived: `grep -n '_reclaim_log_bounded "' on-the-record/monitors/poll-heartbeat.sh` — result:
  ```
  402:          _reclaim_log_bounded "$(printf '[alive-stamp-lock] stale lockfile %s (owner pid %s confirmed dead) reclaimed after %ss wait' ...
  410:            _reclaim_log_bounded "$(printf '[alive-stamp-lock] stale lockfile %s (no owner pid recorded after %ss wait) reclaimed' ...
  ```
  These are the two per-iteration branches that could turn a contended
  lock into a per-second (per contending process) log stream.
- The max-age force-reclaim valve and the release-skipped path are
  UNCHANGED — both still call `_poll_watchdog_log_append` directly,
  unbounded — derived: `grep -n '_poll_watchdog_log_append "\$(printf .\[alive-stamp-lock\]' on-the-record/monitors/poll-heartbeat.sh` — result:
  ```
  384:        _poll_watchdog_log_append "$(printf '[alive-stamp-lock] lockfile %s exceeded max wait %ss (owner pid %s) -- force-reclaimed independent of liveness check ...
  474:      _poll_watchdog_log_append "$(printf '[alive-stamp-lock] release skipped: lockfile %s no longer names this holder ...
  ```
  per the issue's must-not clause that the valve line is never suppressed
  under any rate bound.
- Two env-var overrides for test speed, both unset (defaults apply) in
  production: `POLL_HEARTBEAT_ALIVE_LOCK_RETRY_SLEEP` (replaces the
  acquire loop's two hardcoded `sleep 1`s, default `1`) and
  `POLL_HEARTBEAT_RECLAIM_LOG_WINDOW` (the collapse window in seconds,
  default `5`).
- `test_poll_heartbeat.py`: `_write_mutex_harness()` now also extracts
  `_reclaim_log_bounded`/`_reclaim_log_flush` (the real `_alive_stamp_write`
  body it splices now calls them) so the existing `t_alive_stamp_mutex_*`
  tests keep passing unmodified — derived: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -k mutex -q` — result: 4 passed.
  Added a standalone `_write_reclaim_log_harness()` (extracts the real
  `_poll_watchdog_log_append` plus the two new functions, HOME pointed at
  a tmp dir) plus new test functions, one per acceptance check —
  derived: `grep -c '^def t_.*_issue_2977' on-the-record/monitors/test_poll_heartbeat.py` — result: 3:
  `t_reclaim_output_bounded_issue_2977`,
  `t_reclaim_suppression_reports_count_issue_2977` (covers the N-events
  case and the zero-events empty state in one function),
  `t_force_reclaim_never_suppressed_issue_2977` (pins the call-site
  wiring, then drives repeated direct force-reclaim-style calls to prove
  none are ever collapsed).

## Why

test-derivation (skill, invoked this turn) routed the three acceptance
checks to a decision table on {event kind: dead, forming, max-age-valve}
x {volume}, plus boundary value analysis on the volume dimension. That
table is what the fix implements: the dead/forming branches collapse
under volume, the max-age-valve branch never does, and the report side
(event occurred, and how many) holds for both a collapsed run and the
zero-event run.

Bounding was implemented as a counter-plus-window collapse rather than
removing or disabling the reclaim logging outright (the issue's explicit
must-not), and rather than a pure count-based cap ("stop logging after N
events") — a pure cap would silently drop the count of events past N,
and the second acceptance check requires the count to still be reported
even when individual lines are suppressed. The window-based collapse
folds suppressed events into a running counter and reports that counter
the next time a line is emitted (or once the lock is acquired, via
`_reclaim_log_flush`), so no event's occurrence is ever dropped from the
count.

The max-age valve and the release-skipped path were deliberately left on
the direct, unbounded `_poll_watchdog_log_append` path: the valve because
the issue explicitly forbids suppressing it under any rate bound, and
the release-skipped path because it fires at most once per
`_alive_stamp_write` call (not per-iteration), so it is not the
per-iteration flood source this issue reports, and the acceptance
criteria do not require bounding it.

The fix does not assume the flood is caused by the other watchdog noise
defects filed separately (the issue's stated must-not) — it bounds the
per-iteration reclaim-log call sites directly, regardless of what else
may also be contributing to any observed volume.

## What did not work

None.

## Upstream basis

Both `sha:` entries are `same-commit`: the script fix and its tests land
in this same commit, per contract §1. No prior docs/issue-2977/ artifact
existed to build on — derived: `git log --oneline -- docs/issue-2977/` — result: empty (no prior commits touching this issue's docs tree).

## Open findings

None.

acceptance: `python3 -m pytest on-the-record/monitors/ -k reclaim_output_bounded -q` — result:
```
1 passed in 1.46s
```
acceptance: `python3 -m pytest on-the-record/monitors/ -k reclaim_suppression_reports_count -q` — result:
```
1 passed in 1.32s
```
acceptance: `python3 -m pytest on-the-record/monitors/ -k force_reclaim_never_suppressed -q` — result:
```
1 passed in 1.29s
```
acceptance: `python3 -m pytest on-the-record/monitors/ -q` (full module, regression check) — result:
```
40 passed in 24.22s
```

## Next steps

None — loop_state is terminal (landed).

skill-verdict: test-derivation — applied: invoked; used to route the 3
acceptance checks to a decision table (event kind x volume) plus
boundary value analysis on the volume dimension — derived: see the
decision table posted in-conversation this turn (6 feasible columns
enumerated) — the derived test functions directly implement that table.
skill-verdict: observability-signal-golden — not-applicable: this issue
is a bash monitor log-volume/rate-bounding fix, not a service-rollup
dashboard placing the four Golden Signals over aggregated children.
other mounted skills: not triggered

Closes #2977
