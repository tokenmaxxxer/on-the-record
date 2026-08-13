---
status: proposed
files:
  - spawn.py
  - gates/test_watch_rearm_registry.py
---

## Request

Issue #1154: the watcher a spawn auto-arms at spawn time still dies
with its caller — the same lifetime failure #1133 diagnosed and #1149
verified fixed for `spawn.py watch --rearm`, reopened for the sibling
auto-arm path in `_spawn_one()`. Field observation across 8 spawns
(the issue's own count) is initial watchers dying, re-armed watchers
surviving. Root-cause the detachment shape difference against
`_rearm_watcher_detached()`, fix it, and extend the existing rearm gate
test with an auto-arm survival case.

## Constraints

- Must not change `_rearm_watcher_detached()`'s existing, field-proven
  behavior — this issue's write set touches the auto-arm block only.
- Must not weaken `--no-wait`'s existing contract (spawn returns
  immediately, session keeps running, watcher already armed) — the fix
  should make the *default* (non-`--no-wait`) path match that survival
  property, not repurpose `--no-wait` itself.
- New gate-test case must run hermetically via `MUSTER_STATE_ROOT`
  (issue #857 convention), matching the existing cases in
  `gates/test_watch_rearm_registry.py`, not against real `runs/` state.
- Stay clear of the consult-trace region (issue-1134 phase-2 in
  flight) — the write set above is exhaustive.

## Rationale

Considered leaving the Popen/`start_new_session=True` call itself
unchanged and instead adding `-C <cwd>` to the auto-arm's watcher argv
(mirroring PR #1149's literal diff). Rejected as the primary fix:
survey found `_lookup_roster_entry()` already has a role-suffix
fallback when `repo` is `None` (spawn.py:3754-3760), so a missing `-C`
only breaks lookup when the same issue+role is armed across two repos
at once — it does not explain the reported 100%-of-single-repo-spawns
death pattern. It stays in scope as a secondary hardening item (closes
a real gap for multi-repo fleets) but not as the fix for the reported
symptom.

The primary fix targets the one place the two paths' code actually
diverges: `_rearm_watcher_detached()` returns immediately after
registering the watcher; the auto-arm path, unless `--no-wait` is
passed, falls through into a blocking `_await_bounded()` wait
(spawn.py:5943-5944) that keeps the un-`setsid`'d arming process alive
inside the same bounded orchestrator call the watcher needs to
outlive — the forked session-runner child three lines below detaches
itself via `os.setsid()` for exactly this reason, but the arming
parent branch never does the same. Survey's own local reproduction of
the shared `start_new_session=True` shape did not reproduce a death in
this session's sandbox, so the exact OS-level teardown mechanism the
orchestrator's harness uses is not independently confirmed here — but
making the default auto-arm path return immediately, the same way
`--rearm` already does, removes the one structural difference between
a path with 8/8 reported deaths and a path with 3/3 reported
survivals, without depending on that confirmation.

## What will be done

- In `_spawn_one()`'s auto-arm block (spawn.py, the `if child_pid > 0:`
  branch), after the watcher `Popen()` and `_workspace_index_put()`
  registration succeed, return immediately (print the existing
  "워처 자동 무장" line, then return 0) instead of falling through into
  `_await_bounded(...)` when `no_wait` is false — i.e., make the
  watcher-registered-then-return behavior the default, matching
  `_rearm_watcher_detached()`'s shape, rather than gating it behind
  `--no-wait`. Callers that want the existing bounded progress wait
  keep it available as an explicit follow-up `spawn.py watch --issue
  <n> --role <role>` call (the same remediation path already printed
  and already used elsewhere in this file), not as the default
  auto-arm return path.
- Pass `-C <resolved cwd>` in the auto-arm's watcher argv, mirroring
  PR #1149's fix, closing the secondary multi-repo lookup gap named in
  Rationale.
- Extend `gates/test_watch_rearm_registry.py` with a spawn-time
  auto-arm case: simulate the arming caller exiting/being killed right
  after the watcher is spawned and registered, assert the watcher
  process is still alive and the registry's `watcher_pid` still
  resolves live across a simulated watchdog re-check (mirrors the
  existing rearm test's dead-pid-then-live-pid assertions).
- Live delivery proof (issue's Acceptance check 2): a real
  `spawn.py role spawn ...` invocation from a bounded background Bash
  call, observed alive across 2+ watchdog ticks after that call
  returns/is bounded out.

## Out of scope

- Any change to `_rearm_watcher_detached()` itself, `--rearm`'s CLI
  wiring, or the watchdog remediation strings (all already correct per
  #1133/#1149).
- The consult-trace landing path (issue-1134, phase-2 in flight) —
  untouched by this write set.
- Confirming the exact OS-level mechanism (process-group signal vs.
  cgroup/namespace teardown) the orchestrator harness uses to end a
  bounded call — the fix is structural (match the proven-safe shape),
  not conditioned on that confirmation.

## How you'll know it worked

- `python3 -m pytest gates/test_watch_rearm_registry.py -v` passes,
  including the new auto-arm survival case.
- A live `spawn.py role spawn ...` bounded-background invocation's
  auto-armed watcher is observed alive (registry `watcher_pid` +
  `_watcher_looks_real()`) across at least 2 subsequent watchdog ticks
  after the spawning call itself has returned/ended.
