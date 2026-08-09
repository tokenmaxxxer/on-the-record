---
code_under_review:
  - spawn.py
  - test_spawn.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal
(`docs/issue-559/proposals/2026-08-09-ps-watcher-visibility-and-bounded-watch-all.md`)
exactly, in `spawn.py` and `test_spawn.py`:

- `_watcher_looks_real(pid, issue, role=None)` gained the `role` parameter
  named in the proposal's Constraints section (after-proposal hunt finding)
  — when given, `/proc/<pid>/cmdline` must also contain `role`, not just
  `issue`. `watchdog_check_one`'s call site now passes the role derived
  from its own `key` (`issue-<n>/<role>`).
- `_workspace_index_put` gained `watcher_armed_at: float | None = None`,
  stored in the entry when given. The auto-arm call site (`spawn.py:4037`)
  now passes `time.time()` alongside `watcher_pid`.
- `roster_ps()` now, for each live roster entry, joins the matching
  `WORKSPACE_INDEX` entry via the same bare-key -> repo-prefixed-key join
  `_watch`/`watchdog_check_one` already use, and prints one of: watcher
  pid + armed-at (minutes ago) + `follow=True`; `워처: DEAD(pid ...)`; or
  `워처: UNWATCHED`.
- `_watch_all(stall_timeout_min, until_idle=False)`: when `until_idle` is
  true, after each full pass over the workspace index it returns 0 once
  every key in the index is already in `seen_end` (empty index counts as
  idle), instead of sleeping and looping forever.
- `main()`: new `--until-idle` argparse flag on `watch`, valid only with
  `--all` (mirrors the existing `--all`/`--issue` exclusion check),
  threaded to `_watch_all(until_idle=...)`.
- `test_spawn.py`: new `WatcherPs` class (UNWATCHED / alive-watcher fields
  / dead-watcher-shown-dead, matching acceptance check 1), new tests in
  `WatchAll` covering `--until-idle` exit-on-idle, non-exit-while-live,
  empty-index, and CLI flag rejection without `--all` (acceptance check
  2), and a regression test in `WatcherAutoArm` for the role-aware
  `_watcher_looks_real`.

## Why

Issue #559: the human operator has no way to tell "watcher armed" from
"watcher died / never armed" by looking at `spawn.py ps`, and
`watch --all --follow` blocks forever even after every watched session
has ended, stalling an orchestrator waiting to learn its spawned sessions
are done.

## Upstream / basis

docs/issue-559/proposals/2026-08-09-ps-watcher-visibility-and-bounded-watch-all.md

## What did not work

None.

## Doc-placement ladder

- No new env var, config key, dependency, or migration — nothing to add
  to a handbook.
- No library/format choice over a named alternative and no changed public
  wire format — the two alternatives considered (deriving armed-at from
  roster `ts`; polling process liveness instead of `seen_end` for
  `--until-idle`) are recorded in the proposal's own `## Rationale`
  section, not a new decision doc, since neither was adopted.
- No benchmark/investigation numbers to report.

## Hunt

Before-landing hunt (stance: assume this change and another plugin's rule
cancel each other) ran against the diff and found nothing — see
`docs/reports/2026-08-09-hunt-ps-watcher-visibility-and-bounded-watch-all.md`.

closed_checks:
- before-landing-hunt-stance1 (code_under_review: spawn.py, test_spawn.py): NO FINDING

## Verification run (this session)

`python3 -m pytest test_spawn.py -k "watcher_ps or until_idle" -q` — 7
passed. `python3 -m pytest test_spawn.py -q` — 343 passed (full suite,
issue's acceptance check 3).

## Open findings

None.
