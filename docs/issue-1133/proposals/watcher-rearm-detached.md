---
status: proposed
files:
  - spawn.py
  - gates/test_watch_rearm_registry.py
---

## Request

Watcher re-arm (`spawn.py watch --follow`) does write a fresh
`watcher_pid` into the workspace-index registry the watchdog reads, but
the only entrypoint that performs that write is a blocking, foreground
`--follow` loop — so any bounded caller (an orchestrator turn, a timed
Bash call) kills the just-armed watcher, and the registry is left
holding a dead pid again. Separately, the watchdog's own
`watcher-dead`/`watcher-silent` remediation text names that same
blocking form as the fix, walking every caller who follows it straight
into the same failure. Add a non-blocking re-arm path and repoint the
remediation text at it.

## Constraints

- Must not weaken watch-coverage: a watcher that is genuinely dead and
  never re-armed must keep being flagged `watcher-dead` by
  `watchdog_check_one` (issue's Acceptance, "regression guard").
- Must not change `_watch()`'s existing blocking `--follow` semantics
  for its current callers (spawn-time auto-arm, `--role`-bearing
  interactive follows) — only add a new path, not alter the old one.
- New gate test must run hermetically via `MUSTER_STATE_ROOT` (issue
  #857), not against the real `runs/` state.

## Rationale

Considered just editing the remediation message to add a "background
it yourself" note (e.g. append `&`/`nohup`) without adding any new code
path. Rejected: the survey's live reproduction showed the write itself
already succeeds at follow-start — the actual failure is that the
process carrying that write dies with its caller. A caller told to
background a `--follow` invocation from inside its own bounded
process group still ties the watcher's lifetime to that group in
several orchestration harnesses (the reported failure was itself an
orchestrator's own bounded call). Only a first-class detached
entrypoint — spawned with `start_new_session=True` the same way the
existing spawn-time auto-arm already does at spawn.py:5744-5766 —
actually survives the caller's own timeout, and it gives the required
gate test a concrete call to make and assert on instead of asserting
on wording alone.

## What will be done

- Add `_rearm_watcher_detached(issue, role, work, log_path,
  stall_timeout_min)` to spawn.py, next to `_watch()`, with its entire
  read-decide-spawn-write span wrapped in one acquisition of the
  existing `_workspace_index_locked()` context manager
  (spawn.py:3496-3511) — after-proposal hunt (stance 0) found that
  leaving only the final registry write lock-protected lets two
  concurrent `--rearm` calls both pass the "is it dead" check before
  either writes, so the losing call's detached child is spawned but
  never recorded (a leaked, permanently untracked watcher process).
  To hold the lock across the whole check-then-act span without
  deadlocking, this function does NOT call the separate
  `_workspace_index_put()` helper (which acquires its own,
  non-reentrant `flock` on the same lock file) — instead, inside its
  own single `_workspace_index_locked()` block it loads the index,
  decides whether the current `watcher_pid` is missing or fails
  `_watcher_looks_real`, and if so spawns
  `[sys.executable, spawn.py, "watch", "--issue", ..., "--role", ...,
  "--follow", "--self-heal", "--stall-timeout", ...]` via
  `subprocess.Popen` with `start_new_session=True`,
  `stdin=subprocess.DEVNULL`, stdout/stderr redirected to the existing
  `<work>.watcher.log` path (same shape as spawn.py:5744-5766), writes
  the child's pid + arm-time directly into the loaded dict and
  persists it (duplicating `_workspace_index_put`'s dict-shape/collision
  check inline, under the one lock already held), then returns
  immediately (no wait). If the current watcher already looks real, it
  reports that and returns without spawning a second one — still
  inside the same lock, so no other `--rearm` call can interleave a
  spawn in between.
- Add a `--rearm` CLI flag to the `watch` subcommand (mutually distinct
  from `--follow`): `spawn.py watch --issue <n> --role <role> --rearm`
  calls the function above and returns immediately — never blocks the
  calling process.
- Update the `watcher-dead` (spawn.py:2259-2261) and `watcher-silent`
  (spawn.py:2278) remediation strings to name
  `spawn.py watch --issue <n> --role <role> --rearm` instead of the
  bare `--follow` form.
- Add `gates/test_watch_rearm_registry.py`: using `MUSTER_STATE_ROOT`
  pointed at a temp dir, register a roster entry + a workspace-index
  entry with a fabricated already-dead `watcher_pid`, call the new
  re-arm function directly (not via subprocess, to keep the gate fast
  and deterministic), then:
  - assert `watchdog_check_one` reports no `watcher-dead`/`watcher-missing`
    for that entry, and the workspace index holds a new, alive pid;
  - kill the newly-armed watcher process, assert the next
    `watchdog_check_one` call *does* report `watcher-dead` again
    (regression guard: watch-coverage inviolable);
  - assert an entry that was never armed (`watcher_pid` absent) is
    untouched by the re-arm function and still reports
    `watcher-missing` (empty-state case);
  - assert neither the `watcher-dead` nor `watcher-silent` message
    string contains a bare `--follow` token.

## Accumulation

This adds a second inline `subprocess.Popen([sys.executable, spawn.py,
"watch", ...], start_new_session=True, ...)` call site alongside the
existing one at spawn.py:5744-5766 (spawn-time auto-arm), rather than
factoring a shared helper — the two call sites differ in when they run
(spawn-time vs. post-hoc re-arm) and in what triggers them, but build
the identical child argv/Popen shape. If a third caller needs to spawn
a detached watcher, that third addition should factor both existing
call sites into one `_popen_detached_watcher(issue, role, work,
log_path, stall_timeout_min)` helper instead of adding a third inline
copy — two near-identical inline copies is an acceptable one-off, three
is the accumulation line. This proposal does not do that extraction now
because there are only two sites after this change and no third caller
exists yet.

## Out of scope

- Folding watcher lifecycle into `roster_watchdog --auto-respawn`
  (survey's rejected alternative).
- Changing `_watch()`'s existing blocking `--follow` behavior or its
  callers (spawn-time auto-arm keeps calling the blocking form exactly
  as today — it already runs detached via its own Popen).
- Any change to `spawn.py watch --all` / `_watch_all`.

## How you'll know it worked

`python3 -m pytest gates/test_watch_rearm_registry.py -v` passes, and
manually: with `MUSTER_STATE_ROOT` isolated, fabricate a dead-pid entry,
run `spawn.py watch --issue <n> --role <role> --rearm`, confirm the
command returns immediately (not a hang) and
`workspaces.json` now holds a live pid that `watchdog_check_one`
accepts.
