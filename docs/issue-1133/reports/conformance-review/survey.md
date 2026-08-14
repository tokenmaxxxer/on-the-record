---
kind: current-state-survey
subject: issue-1133
code_under_review:
  - spawn.py
  - gates/test_watch_rearm_registry.py
---

# Current-state survey — conformance review of issue #1133's landed fix

## Board condition

canonical: gh issue view 1133, read this session — issue closed, Requirements/Acceptance section intact.

derived: `gh pr list --search "1133" --state all --limit 20`, run this session:
```
1143	issue-1133: non-blocking watcher --rearm (detached, TOCTOU-safe)	issue-1133/implementation	MERGED	2026-08-13T02:26:35Z
1138	issue-1133: watcher re-arm registry staleness — phase-1 proposal	issue-1133/implementation	MERGED	2026-08-13T02:13:36Z
1149	issue-1133: pass repo context into rearm's detached child argv	issue-1133/implementation	MERGED	2026-08-13T02:42:22Z
```
derived: `git merge-base --is-ancestor b1cd3f38645ef1c142f2521bc7772abe56971871 origin/main && echo ancestor-yes`, run this session:
```
ancestor-yes
```
derived: `ls docs/issue-1133/reports/`, run this session:
```
implementation
implementation.md
```
canonical: same three outputs above, run this session — PR #1149's merge commit (latest of the three implementation PRs touching spawn.py) is on main, and the report tree carries no conformance-review file yet.

## Skip record (scout-directive)

derived: `gh issue view 1133`, read this session:
```
## Requirements

1. Re-arm (watch) updates the same registry/roster entry the watchdog
2. watcher-dead's remediation text names a non-blocking form
3. Regression guard: watch-coverage inviolable
```
canonical: same excerpt above, read this session — the issue text already lists its own discrete checks verbatim, leaving no open design choice for a reviewer to steer toward. Scouting skipped on this ground alone.

## Requirement source for the phase-1 proposal

derived: `gh issue view 1133`, read this session, full Requirements + Acceptance text (verbatim, quoted into the proposal below):
```
1. Re-arm (watch) updates the same registry/roster entry the watchdog
   reads, so a successfully re-armed watcher clears the watcher-dead
   signal on the next tick.
2. watcher-dead's remediation text names a non-blocking form (no --follow,
   or an explicit note to background it).
3. Regression guard: watch-coverage inviolable — the fix must not reduce
   observation (watchdog keeps flagging genuinely dead watchers).

Acceptance:
- check: new gate test in gates/ (e.g. test_watch_rearm_registry.py):
  arm a watcher, kill it, re-arm via the watch code path, assert the
  watchdog scan reports no watcher-dead for that entry and the registry
  holds the new pid
- check: the watcher-dead message string in the watchdog code contains no
  bare --follow instruction (or carries an explicit background note);
  asserted by the same gate test
```

## Code-location scan

derived: `grep -n "watcher-dead\|watcher-silent\|--rearm\|def _rearm_watcher_detached\|def watchdog_check_one" spawn.py`, run this session (excerpted):
```
2231:def watchdog_check_one(key: str, entry: dict, now: float | None = None,
2325:                f"watcher-dead: 워처 pid {watcher_pid} 가 죽어 있거나(또는 다른 "
2327:                f"<n> --role <role> --rearm 로 재무장하라 (non-blocking)")
2342:                        f"watcher-silent: 워처 pid {watcher_pid} 는 살아 있지만 "
2344:                        f"spawn.py watch --issue <n> --role <role> --rearm 로 "
4077:def _rearm_watcher_detached(issue: int, role: str | None, stall_timeout_min: float,
```
canonical: spawn.py:4077-4139 (`_rearm_watcher_detached`), read this session — the read-decide-spawn-write span is held under one `_workspace_index_locked()` acquisition; the registry write at spawn.py:4136-4139 sets `d[key] = {"work":..., "log":..., "watcher_pid": wproc.pid, "watcher_armed_at": ...}`, the same field shape `_workspace_index_put()` (spawn.py:3687-3719) writes on initial arm.

canonical: spawn.py:2231-2338 (`watchdog_check_one`), read this session — signal 5 re-loads `_workspace_index_load()` fresh on every call (spawn.py:2308) rather than caching, so a rearm's registry write is visible on the watchdog's very next tick.

Scope note (not pre-judged; left to phase-2): `entry.get("issue")` used at spawn.py:2323's `_watcher_looks_real()` call reads from the ROSTER entry (`entry`, keyed `issue-<n>/<role>`), not from the WORKSPACE_INDEX entry `_rearm_watcher_detached()` writes — cross-read against spawn.py:1958-1983 (ROSTER definition) and spawn.py:3687-3719 (`_workspace_index_put`, which also never writes an `"issue"` key). The rearm write's omission of `"issue"` from the WORKSPACE_INDEX entry matches the pre-existing initial-arm shape.

Scope note (left to phase-2): two other "다시 spawn.py watch --follow 로 재무장하라" strings remain at spawn.py:3995-3996 and spawn.py:4072-4073, inside `_watch()`'s own non-self-heal stall/wall-clock branches — a different code path from "the watchdog's remediation text" the Acceptance section names. Whether requirement 2's scope reaches these is a phase-2 verdict question, not decided here.

## Gate test presence

derived: `ls gates/test_watch_rearm_registry.py`, run this session:
```
gates/test_watch_rearm_registry.py
```
derived: docs/issue-1133/reports/implementation.md's pasted transcript (that file's own Acceptance verification section, read this session):
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
canonical: both outputs above (implementation.md's own pasted transcript, not re-executed by this survey) — the named test file exists and includes a regression-guard-shaped test (`test_rearmed_watcher_dying_again_is_still_flagged`) and a remediation-string-shaped test (`test_remediation_strings_carry_no_bare_follow`), matching the two Acceptance checks by name. Re-execution of this suite is deferred to the phase-2 record.

## What did not work

None.
