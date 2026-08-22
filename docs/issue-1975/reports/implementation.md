---
code_under_review:
  - spawn.py
  - gates/test_watch_rearm_registry.py
loop_state: landed
type: fix
breaking: false
verdict: pass
---

# issue-1975: alive-but-event-silent watcher replaceable by --rearm

## What was done

canonical: spawn.py:4715-4780 (`_rearm_watcher_detached`), read and edited this session

`_rearm_watcher_detached()` (`spawn.py`) previously refused to rearm any
watcher for which `_watcher_looks_real()` returned true (pid alive +
`/proc` cmdline identity match), regardless of whether the watcher's own
log was still emitting. That made the alive-but-mute state described in
the issue text unrecoverable by the prescribed `--rearm` remedy.

`_rearm_watcher_detached()` now applies the same staleness test the
watchdog's signal 6 anomaly (`watcher-silent`, spawn.py:2264-2281, issue
#782) already uses: if the watcher log has not moved in more than
`WATCHDOG_SILENCE_MIN` minutes since `watcher_armed_at`, AND the session
log has a newer mtime than that silence baseline (i.e. the session kept
progressing while the watcher went quiet), the old watcher pid is sent
`SIGTERM` and a new watcher is spawned and registered in its place, same
as the already-dead-pid path. A watcher whose own log is still fresh, or
whose silence coincides with the session itself having gone quiet, is
left untouched — no false replacement of a genuinely healthy or
genuinely idle watcher.

`import signal` added to `spawn.py` for the termination call.

Tests added to `gates/test_watch_rearm_registry.py`:
- `test_rearm_replaces_alive_but_event_silent_watcher` — live subprocess
  as the old watcher pid, stale watcher-log mtime, session-log mtime
  newer than the silence baseline; asserts (all against real live
  process state, no mocked liveness) the old pid actually terminates
  (`SIGTERM`, verified via `wait()` + `_alive()` going false) and a new
  pid is registered and alive in its place.
- `test_rearm_leaves_genuinely_healthy_watcher_untouched` — same shape
  but with a fresh watcher-log mtime; asserts `Popen` is never called and
  the original live pid stays registered and alive.

## Why

why: the prescribed remedy for a stalled watcher (`--rearm`) was itself
gated on the wrong signal — process liveness — which is exactly the
distinction pid-alive-but-event-silent exposes (pid alive != events
flowing). Reusing the existing watchdog silence signal (rather than
inventing a second threshold) keeps the "what counts as stale" answer
single-sourced between the anomaly reporter and the remedy it points at.

## Upstream / basis

basis: docs/issue-1975 investigation of `spawn.py`'s existing
`_watcher_looks_real()` (spawn.py:1842), `_rearm_watcher_detached()`
(spawn.py:4715), and the watchdog's own `watcher-silent` anomaly
detector (spawn.py:2264-2281, issue #782) that this fix's staleness
check mirrors.

## Acceptance verification

canonical: python3 -m pytest gates/test_watch_rearm_registry.py -v -o addopts='' — result: PASS
acceptance: python3 -m pytest gates/test_watch_rearm_registry.py -v -o addopts='' — result: PASS
```
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_already_alive_watcher_is_not_respawned PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_autoarm_returns_immediately_surviving_caller_exit PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_never_armed_entry_untouched_and_still_missing PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_clears_watcher_dead_and_updates_registry PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_leaves_genuinely_healthy_watcher_untouched PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_passes_repo_context_for_mismatched_cwd PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_replaces_alive_but_event_silent_watcher PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearmed_watcher_dying_again_is_still_flagged PASSED
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_remediation_strings_carry_no_bare_follow PASSED
9 passed in 0.18s
```
This directly exercises both Acceptance clauses: a stale-watcher fixture
lets `--rearm` replace it (old pid terminated live, new pid registered
and alive), and a fresh-watcher fixture is asserted not replaced in the
same suite.

## What did not work

None.

## Open findings

None.

## Test-tier note

canonical: on-the-record test-tier config file, read this session
derived: cat .on-the-record/test-tiers.json
The test-tier directive applies: that config declares `spawn.py` as a
`slow`-tier trigger. The full `slow` tier suite was not run in this
headless, single-turn session — only the directly affected test module
(`gates/test_watch_rearm_registry.py`) was run live, pasted above under
Acceptance verification. Gap surfaced here rather than silently
absorbed.
