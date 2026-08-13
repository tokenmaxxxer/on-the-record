---
code_under_review:
  - spawn.py
  - gates/test_watch_rearm_registry.py
type: fix
breaking: false
canonical: python3 -m pytest gates/test_watch_rearm_registry.py -v — executed live this session, output in Acceptance verification below
verdict: pass
loop_state: landed
---

## Reopen fix (2026-08-13, residual fatal defect)

canonical: python3 -m pytest gates/test_watch_rearm_registry.py -v — executed live this session, pasted output in the updated Acceptance verification section below

The issue reopened on live-fire evidence: the detached child spawned by
`_rearm_watcher_detached()` re-runs `spawn.py watch --issue N --role R
--follow` with no repo context, so the child's own
`_lookup_roster_entry()` call misses on the repo-prefixed key (roster
keys are `<repo>/issue-<n>/<role>`) and exits immediately with `기록
없음 — 아직 스폰된 적이 없다` — the parent registers the child's pid
right before this, so the registry shows a pid that is already dead.

canonical: spawn.py:3940-4002 (_rearm_watcher_detached, current working
tree, read this session)

Fix applied: `_rearm_watcher_detached()` gained a `cwd` parameter,
supplied by its only caller (`main()`'s `--rearm` branch,
spawn.py:5085-5087) as `a.cwd` — the same cwd `main()` already resolves
`repo=_repo_identity(a.cwd)` from for the parent's own lookup. The
detached child's argv now carries `-C <resolved cwd>` ahead of the
`watch` subcommand, so the child's own `_lookup_roster_entry()` call
resolves `repo=` from the same directory the parent used, reproducing
the same repo-prefixed key instead of missing it.

Test added: gates/test_watch_rearm_registry.py, new test method
test_rearm_passes_repo_context_for_mismatched_cwd — asserts the
child's `Popen` argv contains `-C` followed by the resolved `cwd`
value, using a work_dir distinct from the test process's actual cwd,
reproducing the mismatched-cwd shape the reopen comment described.

canonical: live foreign-cwd --rearm reproduction executed this session (raw session log, this turn)
- checked: live foreign-cwd `--rearm` reproduction — result: watcher survives, no lookup-miss line

Delivery proof (live, executed this session): registered a fabricated
dead-watcher entry under a scratch `MUSTER_STATE_ROOT`, then ran the
real `spawn.py -C <repo> watch --issue 999002 --role implementation
--rearm` CLI from `/tmp` (a cwd with no relation to the repo, matching
the reopen's "foreign cwd" scenario) — the detached child (pid
2844967) stayed alive and produced no `기록 없음` line in its watcher
log; `ps -p 2844967 -o pid,stat,etimes` at ELAPSED=32 still showed
`STAT=Ss` (running), spanning more than 2 watchdog-tick-equivalent
wall-clock windows, then was killed and its scratch dirs removed as
session cleanup.

## Summary of work

Implements the approved proposal
(docs/issue-1133/proposals/watcher-rearm-detached.md, `APPROVE
issue-1133/implementation` posted by JiwonJung94, member, exact-string
match on the issue): adds `_rearm_watcher_detached()` to spawn.py — the
read-decide-spawn-write span for re-arming a dead watcher held under one
`_workspace_index_locked()` acquisition (no nested
`_workspace_index_put()` flock), spawning the replacement watcher
detached (`start_new_session=True`, mirroring the existing spawn-time
auto-arm at spawn.py:5752-5759) so it survives the caller's own timeout —
wires a new `spawn.py watch --rearm` CLI flag to it, repoints the
`watcher-dead`/`watcher-silent` remediation strings at the non-blocking
`--rearm` form, and adds gates/test_watch_rearm_registry.py.

## Why

Root cause (survey + live MUSTER_STATE_ROOT reproduction, phase-1): the
registry write on re-arm already succeeds, but the only entrypoint that
performs it is the blocking `--follow` loop — a bounded caller
(orchestrator turn, timed Bash call) kills the just-armed watcher before
it can run, and the watchdog's own remediation text pointed callers at
that same blocking form. northpole req#1: watchdog signals must stay
trustworthy for bottleneck identification; a registry stuck DEAD after a
successful re-arm is alarm fatigue.

## Upstream basis

docs/issue-1133/proposals/watcher-rearm-detached.md

## What was done

- `_rearm_watcher_detached(issue, role, stall_timeout_min, repo=None)`
  (spawn.py, right before `_watch_all()`): loads the workspace index,
  looks up the roster entry, and decides dead-or-missing, all inside one
  `_workspace_index_locked()` block — closing the after-proposal hunt's
  TOCTOU finding (two concurrent `--rearm` calls both clearing the
  liveness check before either writes). If the current `watcher_pid`
  already looks real, returns 0 without spawning. Otherwise spawns the
  replacement via `subprocess.Popen([sys.executable, spawn.py, "watch",
  "--issue", ..., "--follow", "--self-heal", ...], start_new_session=True,
  stdin=DEVNULL, stdout/stderr to the existing `<work>.watcher.log`)` —
  same shape as the spawn-time auto-arm at spawn.py:5752-5759 — then
  writes the child's pid + arm-time into the loaded dict and persists it
  inline (duplicating `_workspace_index_put`'s dict-shape/collision
  check under the one lock already held, per the proposal's Accumulation
  section), and returns immediately without waiting on the child.
- `--rearm` CLI flag on the `watch` subcommand, wired in `main()`'s
  `a.role == "watch"` branch ahead of the existing `_watch()` call: when
  set, calls `_rearm_watcher_detached()` and returns immediately instead
  of falling into the blocking `_watch()` path.
- `watcher-dead` and `watcher-silent` remediation strings in
  `watchdog_check_one()` repointed from
  `spawn.py watch --issue <n> --follow` to
  `spawn.py watch --issue <n> --role <role> --rearm`.
- gates/test_watch_rearm_registry.py, hermetic via `MUSTER_STATE_ROOT`
  (issue #857 convention: env var set, then `spawn.STATE_ROOT` /
  `spawn.ROSTER` / `spawn.WORKSPACE_INDEX` monkeypatched to the same
  derived paths, since those are module-import-time constants and the
  test calls the function in-process rather than via subprocess):
  fabricates a dead-pid workspace-index entry, calls
  `_rearm_watcher_detached()` directly, asserts `watchdog_check_one`
  reports no `watcher-dead`/`watcher-missing` and the index holds a new
  alive pid; kills the newly-armed watcher (by writing back a
  non-existent pid) and asserts the next `watchdog_check_one` call flags
  `watcher-dead` again (regression guard: watch-coverage kept); asserts
  a never-armed entry still reports `watcher-missing` before rearm and
  gets a live pid registered by it; asserts an already-alive watcher is
  not respawned; asserts neither remediation string contains a bare
  `--follow` token.

## Acceptance verification

canonical: python3 -m pytest gates/test_watch_rearm_registry.py -v — executed live this session, output below (reopen-fix run, includes the new mismatched-cwd test)
- checked: `python3 -m pytest gates/test_watch_rearm_registry.py -v` — result: pass

```
$ python3 -m pytest gates/test_watch_rearm_registry.py -v
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_already_alive_watcher_is_not_respawned PASSED [ 16%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_never_armed_entry_untouched_and_still_missing PASSED [ 33%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_clears_watcher_dead_and_updates_registry PASSED [ 50%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearm_passes_repo_context_for_mismatched_cwd PASSED [ 66%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_rearmed_watcher_dying_again_is_still_flagged PASSED [ 83%]
gates/test_watch_rearm_registry.py::WatchRearmRegistry::test_remediation_strings_carry_no_bare_follow PASSED [100%]
6 passed in 0.08s
```

## What did not work

- First draft of the watch-coverage-regression test used a roster entry
  carrying `"issue": self.issue` for `watchdog_check_one()`, expecting
  the newly-armed watcher (a mocked `Popen` whose `.pid` is the test
  process's own pid) to clear `_watcher_looks_real()`. Expected: cleared
  because the pid is alive; actual: rejected, because
  `_watcher_looks_real()` also checks `/proc/<pid>/cmdline` for the
  issue/role strings, and the test process's own cmdline is pytest's,
  not a `watch` invocation — it spawned a second child instead of
  no-op'ing. Fixed by omitting `issue` from the synthetic roster entry
  handed to `watchdog_check_one()` (falls back to `_alive()`-only) and,
  for the one test that specifically needs the "already looks real"
  branch to trigger with the real `issue` argument
  (`test_already_alive_watcher_is_not_respawned`), patching
  `spawn._watcher_looks_real` directly instead.
- First `_put_entry`/Popen mock combination in
  `test_never_armed_entry_untouched_and_still_missing` and
  `test_already_alive_watcher_is_not_respawned` left `fake_proc.pid`
  unset (a bare `mock.Mock()`). Expected: JSON-serializable int; actual:
  `_rearm_watcher_detached()`'s registry write raised `TypeError`
  (`MagicMock` not serializable). Fixed by setting `fake_proc.pid =
  os.getpid()` on every mocked `Popen` return value the code path
  reaches.
- Reopen fix: the first attempts to append the "Reopen fix" section via
  `Edit` chose an anchor whose `new_string` opened on the frontmatter's
  outcome-verdict line, kept only as unchanged match context. Expected:
  record-claim-guard.sh's OUTCOME check (issue #870) would scan the
  resulting full file, where the adjacent `canonical:` line sits just
  above it; actual: the hook lints only the `Edit` tool's `new_string`
  fragment on its own, so that outcome line landed as the fragment's
  first line with nothing above it inside the fragment, and the write
  was refused each time. Fixed by anchoring one line later
  (`loop_state: landed`) so the fragment no longer opens on that line.

## Doc placement

No env var, new dependency, migration, config key, or public-signature/
wire-format change — nothing to place on the doctrine ladder beyond this
record and the code_under_review file list above.

## Open findings

None.

## Next steps

Commit this record and the code/test changes with the `Subject:
issue-1133` trailer, push the branch, and route the phase-2 delivery
through PR #1138 (or a new phase-2 PR if that one is no longer usable)
with `Closes #1133`.

## Resolution path

No open findings; not applicable.

## Hunt

After-proposal hunt (stance 0, "assume the gate just touched is
bypassable") ran before this build; its TOCTOU finding is already
incorporated into the design above (the single `_workspace_index_locked()`
span) — see
docs/issue-1133/reports/implementation/2026-08-13-hunt-watcher-rearm-detached.md.
closed_checks: TOCTOU-on-check-then-act (spawn.py, `_rearm_watcher_detached`)
— code_under_review: spawn.py.
