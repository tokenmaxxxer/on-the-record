---
code_under_review:
  - spawn.py
  - tests/test_watchdog_freshness.py
type: feature
breaking: false
canonical: python3 -m pytest tests/test_watchdog_freshness.py -q
verdict: pass
loop_state: landed
---

## What was done

canonical: gh issue view 1456 (issue body, "Context" section)

Implemented all three requirements from issue #1456 in `spawn.py`, wired
into the `watchdog` CLI branch (`spawn.py` role dispatch, `if a.role ==
"watchdog"`). Issue #1456's Context section states #1360 recurred on
2026-08-14: a role-workspace watchdog kept pre-fix code in memory and
over-spawned against already-resolved issues (see the issue body for the
exact figures).

- `watchdog_canonical_guard()` — refuses to start when the watchdog's own
  file path resolves under the workspace-base tree (`~/.tokenmaxxxer/work/*`
  by default, `MUSTER_WORK_DIR` override), printing one guard line; skipped
  via `SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1`.
- `watchdog_lock_acquire()` — per-board single-instance lock at
  `STATE_ROOT/watchdog.lock`, storing `{pid, start_time}` where `start_time`
  is read from `/proc/<pid>/stat` field 22 (via `_proc_start_time()`).
  Liveness requires both pid-alive and start_time match, so a crashed
  process's lock (or a live pid that is a *different* process due to pid
  reuse) is reclaimed automatically. A second live instance exits with one
  line naming the pid and start_time.
- `watchdog_current_head()` / `watchdog_freshness_check()` — records the
  checkout HEAD the watchdog loaded code from before the tick runs; after
  the tick, re-fetches (`git fetch` + `merge --ff-only origin/HEAD`,
  advisory — failure doesn't block) and compares against the current HEAD.
  A mismatch prints one restart-required line; the CLI branch returns
  `WATCHDOG_STALE_CODE_SENTINEL` (non-zero) so the existing auto-respawn
  machinery relaunches on fresh code.

CLI wiring order in the `watchdog` branch: canonical guard → lock
acquire → record startup HEAD → run `roster_watchdog()` (the existing
tick) → freshness check → return. Three new reserved exit sentinels
(`WATCHDOG_LOCKED_SENTINEL=96`, `WATCHDOG_STALE_CODE_SENTINEL=95`,
`WATCHDOG_NONCANONICAL_SENTINEL=94`) sit alongside the existing
`WATCHDOG_CRASH_SENTINEL=97` (spawn.py:47) so none collide with
`roster_watchdog()`'s normal anomaly-count return (rc>=0).

Cost: the freshness check adds a fixed, small number of subprocess calls
(`git fetch`, `git merge --ff-only`, `git rev-parse HEAD`) per tick,
independent of board size — meets the constant-cost requirement (issue
#1320 lesson, folded into issue #1456's acceptance).

## Why

canonical: gh issue view 1456 (issue body)

#1360 recurred: a long-lived `spawn.py watchdog --auto-respawn` process
in a role workspace kept pre-fix code in memory after a hotfix merged.
The rearm mechanism only restarted the plugin Monitor, not this
independent workspace watchdog. Root lesson stated in the issue: merge ≠
deploy for long-lived processes. The three requirements close exactly
that gap: a process running from a non-canonical (role-workspace)
checkout should never have started; a running instance that is alone
should stay alone; and any instance, wherever started, should notice when
its own checkout has moved past the HEAD it loaded and restart itself.

## Upstream basis

docs/issue-1360/reports/consult-log.md @ 2026-08-14T06:25:36Z
(requirements-engineering consult cited in the issue body;
validity-consult line folds all three caveats into the requirements).

## What did not work

None.

## Doc-placement ladder

- No new env var beyond the one the issue itself specifies
  (`SPAWN_WATCHDOG_ALLOW_NONCANONICAL`), which is documented at the
  guard's docstring and CLI-line usage site — no separate handbook entry
  exists for `spawn.py` env knobs in this repo to extend, and this
  override is scoped to a single guard function's behavior, not a
  standing operational knob.
- No new dependency, migration, or public wire-format change — nothing
  else on the ladder applies.

## Test run

canonical: python3 -m pytest tests/test_watchdog_freshness.py -q (executed this turn, raw output pasted below)
acceptance: python3 -m pytest tests/test_watchdog_freshness.py -q — result: UNMEASURED-with-reason: no acceptance command on record for this target

```
$ python3 -m pytest tests/test_watchdog_freshness.py -q
........                                                                 [100%]
8 passed in 0.09s
```

Test cases, mapped to acceptance items (a)-(f): (a) second-instance
pointer line while first holds the lock; (b) stale lock with a dead pid
is reclaimed, and separately a live pid whose start-time mismatches
(pid reuse) is also reclaimed; (c) HEAD-mismatch tick reports non-fresh
with the restart-required line; (d) matching-HEAD ticks report fresh with
no line; (e) non-canonical path is refused, the override env var lets it
through, and a canonical path is allowed unconditionally; (f) empty
state — a fresh board with no lock file starts normally and creates the
lock. Every test docstring cites issue #1456.

## Open findings

None.
