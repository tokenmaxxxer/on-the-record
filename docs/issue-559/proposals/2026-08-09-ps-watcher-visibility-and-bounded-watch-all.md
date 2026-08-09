---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - docs/issue-559/reports/implementation/survey.md
---

## Request

`spawn.py ps` shows nothing about whether a running session has an
attached watcher, so "watcher armed" and "watcher died / never armed" look
identical from outside — the human operator said, verbatim, "사용자가
모니터링이 지속되고 있는지 아닌지 알 방법이 없으니까 너무 헷갈리네". Also,
`spawn.py watch --all --follow` never returns even after every watched
session has ended, which stalled an orchestrator waiting to learn its
spawned sessions were done.

## Constraints

- No new dependency, no schema migration, no product-facing surface —
  scouting skipped per the survey (internal CLI ops tooling only).
- Reuse the existing dead-watcher check (`_watcher_looks_real`) rather than
  inventing a second liveness definition for `ps` vs. `watchdog`.
- After-proposal hunt (stance 0,
  docs/reports/2026-08-09-hunt-ps-watcher-visibility-and-bounded-watch-all.md)
  found `_watcher_looks_real(pid, issue)` checks only that `issue` appears
  in `/proc/<pid>/cmdline`, never `role` — a live watcher for a *different
  role* of the same issue is reported "real" for a sibling role's stale
  record. `ps` and `--until-idle` must not inherit this unchanged: the
  role check is added to `_watcher_looks_real` (it already has the role
  string available at every call site — spawn.py:1862 via
  `entry.get("issue")`, and the new `ps`/`until-idle` call sites will have
  the role from the same roster/workspace-index entry) rather than left
  issue-only.
- `ROSTER` and `WORKSPACE_INDEX` stay two separate registries (out of
  scope to merge them) — `ps` must join them by key the same way `_watch`
  already does (spawn.py:2806-2811), not restructure either store.
- The auto-armed watcher's spawn-time behavior (spawn.py:3997-4026) must
  keep failing the spawn when the watcher process can't start — this
  proposal only adds a timestamp field to what's already recorded there.

## Rationale

**For recording when a watcher was armed:** considered deriving
"armed-at" from the roster entry's existing `ts` field (session start
time) instead of adding a new `watcher_armed_at` field to the workspace
index. Rejected: the watcher is armed once per session by the auto-arm
path, but a session's `ps` `ts` is set at spawn time and does not
distinguish "watcher armed" from "session started" — they happen
microseconds apart for auto-arm today, but the issue's acceptance check
also wants a fixture with a live session and a *separately* recorded
watcher process, which only a dedicated timestamp field models correctly.
A new `watcher_armed_at` key alongside the existing `watcher_pid` key in
the workspace-index entry is the minimal correct model.

**For the bounded `--all` mode:** considered polling `roster`/process
liveness of the *sessions themselves* to decide when to stop, instead of
using the same `session-end` event tracking `_watch_all` already
maintains in `seen_end`. Rejected: `_watch` (singular) already treats
`session-end` in the events log as the authoritative per-session end
signal (spawn.py:2782-2788), not process liveness — process liveness for
the wrapper is explicitly documented as a *secondary*, crash-only signal
there (spawn.py:2800-2817) because of a post-processing tail where the
process can be legitimately gone before `session-end` is written. Reusing
`seen_end` keeps `_watch_all` consistent with `_watch`'s own definition of
"done" instead of introducing a second, weaker one.

## What will be done

- `spawn.py`: `_watcher_looks_real` gains a `role: str | None = None`
  parameter; when given (and `/proc/<pid>/cmdline` is readable), it
  additionally requires `role` to appear in argv, closing the
  after-proposal hunt finding above. Existing callers
  (`watchdog_check_one`) keep working unchanged since the new parameter
  defaults to `None` (issue-only check, current behavior) — `watchdog`
  already has `key` (`issue-<n>/<role>`) available to pass the role too,
  and this proposal passes it there as well while it's in the function.
- `spawn.py`: `_workspace_index_put` gains an optional `watcher_armed_at`
  parameter, stored in the entry when given; the auto-arm call site
  (spawn.py:4021-4022) passes `time.time()` alongside `watcher_pid`.
- `spawn.py`: `roster_ps()` is extended to, for each live roster entry,
  look up the matching `WORKSPACE_INDEX` entry (same bare-key ->
  repo-prefixed-key join `_watch` already does), and print one of:
  - a watcher line naming pid, armed-at (relative age, matching the
    existing minutes-ago style already used for the session line), and
    `follow` (always `True` for the auto-armed watcher, since it's always
    invoked with `--follow`) — when `watcher_pid` is present and
    `_watcher_looks_real` says it's alive;
  - a `워처: DEAD(...)` line naming the recorded pid — when `watcher_pid`
    is present but the process is gone (or pid-reused);
  - an explicit `워처: UNWATCHED` marker — when no `watcher_pid` was ever
    recorded for that session.
- `spawn.py`: `_watch_all` gains an `until_idle: bool = False` parameter.
  When true, after each full pass over the workspace index the loop checks
  whether every key currently in the index is already in `seen_end`
  (an empty index also counts as idle); if so, it returns 0 instead of
  sleeping and looping again.
- `spawn.py`: `main()` adds a `--until-idle` argparse flag to the `watch`
  subcommand (valid only with `--all`, mirroring the existing
  `--all`/`--issue` mutual-exclusion validation), threaded through to
  `_watch_all(until_idle=...)`.
- `test_spawn.py`: new tests near `WatcherAutoArm` asserting `roster_ps()`
  output names an alive watcher's pid/armed-at/follow, shows `UNWATCHED`
  for a session with no `watcher_pid` recorded, and shows a dead watcher
  as dead rather than omitting it (covers acceptance checks 1-2, using
  fixture roster+workspace-index tempdirs following the existing
  `WatcherAutoArm`/`Watchdog` `setUp` pattern). New tests near `WatchAll`
  asserting the `--until-idle` loop body exits once all fixture sessions'
  events show `session-end` (covers acceptance check 3), and that it does
  not exit early while a session is still live. A test near
  `WatcherAutoArm` asserts `_watcher_looks_real` rejects a pid whose
  `/proc/<pid>/cmdline` matches the issue but a *different* role
  (regression test for the after-proposal hunt finding).

## Accumulation

The touched shape is `roster_ps()` printing one more per-session status
line and `_workspace_index_put`/`_watch_all` gaining one more optional
field/parameter each — not a growing inline `subprocess`/`gh` call list
and not a `roles/*.json`-style repeated-file edit. If a future issue adds
another per-session status line (e.g. a third registry), the pattern to
follow is the same join `_watch` already established
(spawn.py:2806-2811) and this proposal reuses — N more such additions
converge on one shared join helper, not N independent inline lookups,
because there is exactly one bare-key -> repo-prefixed-key translation in
the codebase and every caller (`_watch`, now `ps`) already calls it the
same way rather than reimplementing it.

## Out of scope

- Merging `ROSTER` and `WORKSPACE_INDEX` into one registry.
- Changing the auto-arm failure behavior (spawn fails if the watcher can't
  start) — unaffected by this change.
- Non-Linux `/proc`-less watcher identity verification — `ps` reuses
  `_watcher_looks_real`'s existing platform degradation as-is.
- Any change to `watch` (singular) or `watchdog_check_one`'s own exit/
  reporting behavior beyond what's needed to add the `watcher_armed_at`
  field they read.

## How you'll know it worked

Committed tests in `test_spawn.py`, run via the project's existing
`python -m unittest` invocation, cover exactly the three acceptance
checks in the issue:
1. `ps` against a fixture with a live session + attached watcher record
   names the watcher (pid, armed-at, follow); a second fixture with no
   watcher shows `UNWATCHED`.
2. The auto-armed watcher's own record appears in the listing the same
   way, and a dead watcher (recorded pid not alive) shows as dead/
   UNWATCHED rather than being silently omitted.
3. `watch --all --until-idle` against a fixture index whose sessions have
   all ended exits instead of blocking.

All three fail against current `main` (no watcher output in `ps`, no
`--until-idle` flag) and pass on this branch.
