---
status: proposed
files:
  - spawn.py
  - on-the-record/monitors/poll-heartbeat.sh
  - tests/test_monitor_alive_gc.py
---

Skip condition (survey-order-directive): pure bugfix / spec leaves no
design decision open. Issue #1465's Requirements + Acceptance sections
already pin the shape (target dir, threshold-derivation rule, hook
point, four test names) — this proposal fills in the mechanical
implementation, not a design choice.

## Request

Marker dirs under `~/.claude/tokenmaxxxer/monitor-alive/` accumulate
without bound because nothing ever deletes old ones (183 observed
stale). Add a non-fatal GC pass, wired into existing machinery, that
deletes stale marker dirs above a threshold derived from
poll-heartbeat.sh's own touch cadence, and separately reports (never
deletes) legacy `.orchestrate-monitor-alive/` dirs left over from before
the #947/#1280 relocation.

## Constraints

- Threshold must be asserted greater than poll-heartbeat.sh's touch
  cadence (Acceptance test #2).
- No new daemon — hook into heartbeat startup or `spawn.py clean`.
- GC failure must never be fatal to the monitor loop.
- Legacy `.orchestrate-monitor-alive/` dirs are reported, never deleted.

## Rationale

Two viable hook points existed: (a) `spawn.py clean` (human-invoked,
already the safe-deletion precedent via `roster_clean()`), or (b)
poll-heartbeat.sh startup (runs once per Monitor session, i.e. far more
often than a human runs `clean`). Considered and rejected (a) as the
sole hook: `spawn.py clean` is opt-in and human-cadence, and the
accumulation problem is session-count-driven (one new hash dir per
distinct workspace root per session), so relying only on a human-invoked
command would still let the dir count grow unbounded between manual
runs — GC needs to run at least as often as dirs are created to
actually bound growth. Chose (b), heartbeat startup, instead. `spawn.py
clean` was also considered as an ADDITIONAL second call site and
rejected for this proposal, to keep the write set to one hook point per
the issue's "no new daemon" constraint and avoid duplicating the same GC
logic at two call sites for no behavioral gain — the GC function itself
lives in spawn.py either way, so a `spawn.py clean` caller can be added
later without re-deriving the threshold.

## What will be done

- `spawn.py`: `MONITOR_ALIVE_STALE_THRESHOLD_SECONDS` (7 days) and
  `MONITOR_ALIVE_TOUCH_CADENCE_SECONDS` (60, mirroring
  `POLL_HEARTBEAT_SLEEP_SECONDS`'s default) as a module-level assertion;
  `gc_monitor_alive()` walks `~/.claude/tokenmaxxxer/monitor-alive/*`,
  deletes dirs whose `alive` mtime (or dir mtime if absent) exceeds the
  threshold, absorbing per-entry `OSError`s into an `errors` counter;
  `detect_legacy_monitor_alive_dirs()` reports (not deletes)
  `.orchestrate-monitor-alive/`; `monitor_alive_gc_cli()` wraps both in
  a second exception layer and is exposed as `spawn.py gc-monitor-alive`.
- `on-the-record/monitors/poll-heartbeat.sh`: call
  `python3 spawn.py gc-monitor-alive` right after the existing
  alive-marker touch, output redirected and `|| true`.
- `tests/test_monitor_alive_gc.py`: the four Acceptance tests plus an
  empty-root no-op case.

## Out of scope

- Periodic re-touch of the alive marker during the tick loop (unrelated
  to the accumulation defect).
- Deleting legacy `.orchestrate-monitor-alive/` dirs (explicitly
  forbidden by the issue).
- Wiring GC into `spawn.py clean` as a second call site.

## Accumulation

`spawn.py main()`'s `if a.role == "...":` dispatch chain gains one more
branch (`gc-monitor-alive`), following the exact shape every existing
role (`poll-due`, `watchdog`, `reconcile`, ...) already uses — this is
the established CLI-dispatch pattern, not a new one. If N more `spawn.py`
CLI roles are added the same way, the chain grows by N lines with no
change in shape or risk; each branch is independently readable and the
pattern already scales to the ~15 roles present today. No shared helper
extraction is warranted at this size — extracting one now for a single
added branch would be premature.

## How you'll know it worked

`python3 -m pytest tests/test_monitor_alive_gc.py -v` passes all five
tests (the four Acceptance-named tests plus the empty-root no-op case).
