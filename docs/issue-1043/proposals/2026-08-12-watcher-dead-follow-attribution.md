---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

## Request

Fix the watcher-dead false-positive: the roster watchdog flags
`watcher-dead`/`watcher-missing` from a stale/absent auto-armed watcher pid
even when an orchestrator's own `spawn.py watch --issue <n> --follow` is
actively covering the same session. Attribute watcher liveness across
*any* live watcher for the session (auto-armed or follow), and clear
stale pids from the roster entry when a watcher is replaced.
Requirement linkage: R001.

## Scout skip record

Pure bugfix per scout-directive's skip condition — see
`docs/issue-1043/reports/implementation/survey.md` "Scope skip condition".
No design/exemplar decision is open; scouting was skipped on that ground.

## Constraints

- No new dependency, no new env var, no schema/migration (per survey).
- Must not change `_watcher_looks_real()`'s existing identity semantics
  (liveness + `/proc/<pid>/cmdline` match on `"watch"` + issue + role) —
  reuse it, don't fork it.
- Must not weaken `watcher-missing`/`watcher-dead` detection for the
  genuinely-uncovered case (no watcher at all, auto-armed or follow).
- `_workspace_index_put()`'s existing collision guard (same key, different
  `work` -> `RuntimeError`, issue #533) must keep firing; the follow
  registration must pass the same `work` the entry already carries.

## Rationale

Two approaches were considered:

1. **(Chosen) Have `_watch()` register its own pid as the watcher when
   entering follow mode**, via the existing `_workspace_index_put(...,
   watcher_pid=os.getpid(), watcher_armed_at=time.time())` call already
   used by auto-arm. `_workspace_index_put()` already replaces the entry
   wholesale each call (survey: spawn.py:3523, `entry = {"work": work,
   "log": log}` rebuilt fresh, extra fields added only if supplied) — so
   this single call both (a) makes the live follow watcher visible to
   `watchdog_check_one()` under the *same* `watcher_pid` field it already
   reads, with no new field or code path in the watchdog, and (b)
   satisfies "clear stale pids on replacement" for free, since the old
   (possibly dead) auto-armed pid is dropped by the same overwrite.

2. **(Rejected) Add a second field (`follow_watcher_pid`) and OR the two
   liveness checks in `watchdog_check_one()`.** Rejected because it
   requires the watchdog to track and reconcile two independently-stale
   pids instead of one, doubles the surface `_watcher_looks_real()` must
   be called against per tick, and does not get "clear stale pids on
   replacement" for free — a separate cleanup step would be needed for
   the dead auto-armed pid, which is exactly the bug this issue reports
   living on.

Option 1 reuses `_workspace_index_put()`'s existing single-writer,
whole-entry-replace contract instead of adding a second liveness source
the watchdog has to merge — smaller diff, no new field, no new decision
about "which pid wins" (there is only ever one `watcher_pid` value: the
most recent registrant, auto-arm or follow, whichever is currently
covering the session).

## What will be done

- In `_watch()` (spawn.py, `follow=True` branch), immediately before the
  follow loop starts, resolve the role from the already-computed `key`
  (`re.search(r"issue-\d+/([^/]+)$", key)`, falling back to the `role`
  parameter). Read the current `watcher_pid` already on the workspace
  index entry (if any) and check it with the existing
  `_watcher_looks_real(watcher_pid, issue, follow_role)`. Only when that
  check is `False` (no watcher recorded, or the recorded one is dead/not
  a real watcher) call `_workspace_index_put(issue, follow_role, work,
  str(log_path), watcher_pid=os.getpid(), watcher_armed_at=time.time())`
  to register this follow process as the watcher. When the check is
  `True` (a live watcher — auto-armed or an earlier follow — already
  covers the session), this `_watch()` invocation does not overwrite it;
  it still runs the follow loop normally, it just does not claim watcher
  ownership away from the process that already holds it.
  This runs once per `_watch(..., follow=True)` invocation, before
  `_await_bounded()` is first called — the follow process is alive for
  the whole loop, so a single check-and-maybe-register at entry is
  sufficient for `_watcher_looks_real()`'s liveness check to hold for the
  loop's duration.
- **Guards the after-proposal hunt finding**
  (docs/issue-1043/reports/implementation/hunt-2026-08-12-watcher-dead-follow-attribution.md,
  stance 0, composition): an earlier draft of this proposal had `_watch()`
  unconditionally overwrite `watcher_pid` on every follow entry. The
  hunter reproduced that a second, short-lived manual `watch --follow`
  invocation would then clobber a live auto-armed watcher's registration;
  once the manual watcher exited, the (still-alive) auto-armed watcher
  would itself be flagged `watcher-dead` — reintroducing the exact bug
  this issue reports, via composition with a second concurrent follow.
  The read-before-write guard above closes it: registration only ever
  moves from "no live watcher" to "a live watcher", never from "a live
  watcher" to a different one, so a transient follow process can no
  longer make an already-live watcher look dead once it exits.
- Add two regression cases to `tests/test_spawn.py` (under the existing
  `WatchFollow` class, whose `setUp()` already wires a synthetic
  `WORKSPACE_INDEX` + roster + events log), named to satisfy the
  acceptance's `-k watcher_dead` filter:
  - a stale dead auto-armed `watcher_pid` is pre-registered, then
    `spawn._watch(180, "implementation", 5.0, follow=True)` runs to
    completion (session-end) — assert the workspace index's
    `watcher_pid` is now `os.getpid()` and `watchdog_check_one()` raises
    neither `watcher-dead` nor `watcher-missing`.
  - a companion control case with no watcher registered at all —
    `watchdog_check_one()` still raises `watcher-missing`/`watcher-dead`,
    guarding against the fix accidentally being too permissive.

## Out of scope

- Signal 6 (`watcher-silent`, spawn.py:2261-2276) — unaffected; the follow
  registration reuses `watcher_armed_at`, which already feeds that check
  correctly for an auto-armed watcher and will do the same for a
  follow-registered one.
- Any change to `_watcher_looks_real()` itself.
- Making `watch --all --follow` (`_watch_all()`) register per-session —
  out of scope for this issue, which only mentions `watch --follow`.
- Periodic re-registration/heartbeat while the follow loop runs — a
  single registration at entry is sufficient because liveness is judged
  by pid + cmdline, not by a freshness timestamp, for as long as this
  same follow process is the one running.

## Accumulation

This change adds one more `_workspace_index_put()` call site (`_watch()`
follow-entry), alongside the existing auto-arm call site
(`_spawn_one()`). Both call sites already share the single helper
`_workspace_index_put()` — there is no inline/duplicated subprocess or
`gh` call being accumulated, and no `roles/*.json`-style repeated-file
edit. If a future issue adds more watcher-registration call sites (e.g. a
`watch --all` per-session variant), it would call the same shared helper
too; the helper's whole-entry-replace contract (spawn.py:3497-3529) is
what keeps N call sites from needing N separate "clear stale pid"
implementations, so this does not compound into per-site logic that
would need factoring out later.

## How you'll know it worked

`python3 -m pytest tests/test_spawn.py -k watcher_dead` runs and its
result is pasted into the phase-2 record once the fix and its two new
regression cases are built, covering both the stale-pid-with-live-follow
(no flag) and no-watcher-at-all (flag fires) cases named in the issue's
acceptance.
