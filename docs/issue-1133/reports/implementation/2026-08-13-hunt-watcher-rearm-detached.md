---
proposal: docs/issue-1133/proposals/watcher-rearm-detached.md
---

# Hunt record — watcher-rearm-detached

## after-proposal — stance 0: assume the gate/mechanism just proposed is bypassable — find the bypass

Verdict: FINDING — concurrent `--rearm` calls double-spawn a detached watcher because the proposal's check-then-act sequence ("looks up the current ... entry; if the recorded watcher_pid is missing or fails `_watcher_looks_real`, spawns ... then calls `_workspace_index_put`") is only lock-protected at the final write, not across the read-decide-spawn span, so the losing call's detached `--self-heal` child is never recorded anywhere and, per the proposal's own note that `--self-heal` "loops until session-end" instead of returning on stall, runs forever untracked, invisible to `spawn.py ps`/the workspace index, and outside the very coverage/regression-guard the proposal's gate test checks (which only exercises a single re-arm call).
Kind: composition
Seed: docs/issue-1133/proposals/watcher-rearm-detached.md — "What will be done" (`_rearm_watcher_detached`), cross-checked against the real primitives it says it reuses: `_workspace_index_load`/`_workspace_index_put`/`_workspace_index_locked` (spawn.py:3497-3560ish) and `_watcher_looks_real` (spawn.py:1941-1969), and against the existing spawn-time auto-arm Popen shape at spawn.py:5744-5766 that the proposal says it mirrors.
cap_seconds: 120
tier: default
diff_stat_lines: proposal doc only (~150 lines, no code yet)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:15:00Z

### Reproduce
Reimplemented the proposal's own described algorithm verbatim (read current `watcher_pid`, decide via `_watcher_looks_real`, spawn a detached child with `start_new_session=True`, then `_workspace_index_put` the new pid) against the real `spawn.py` primitives, fired twice concurrently against a fabricated dead-pid entry, hermetically under `MUSTER_STATE_ROOT`:

```
python3 /tmp/repro_rearm.py
```
(script imports `spawn`, sets `MUSTER_STATE_ROOT=/tmp/rearm_repro/state`, seeds a workspace-index entry with `watcher_pid=999999` (dead), then runs two threads that each: load the index, check `_watcher_looks_real` on the current `watcher_pid`, `subprocess.Popen(["sleep","300"], start_new_session=True, ...)` as a stand-in for the detached `watch --follow --self-heal` child, and `spawn._workspace_index_put(..., watcher_pid=child.pid, ...)`)

### Observed
```
spawned children pids: [2716917, 2716919]
workspace index tracked pid: 2716919
orphaned (untracked, still running) pids: [2716917]
  pid 2716917 alive=True
```
Both concurrent `--rearm` invocations decided (correctly, given the state each read) that no live watcher existed, so both spawned a detached child; `_workspace_index_locked()` only serializes the two `_workspace_index_put` writes, so the second write silently clobbers the first — one live detached process (`2716917`) is left running with no entry in the workspace index pointing at it, no roster entry, and no code path that will ever notice or kill it.

### Expected
The read-decide-spawn-write sequence needs to be atomic (e.g. take `_workspace_index_locked()` for the whole check-then-act, or use a compare-and-swap on the recorded `watcher_pid`) so a second concurrent `--rearm` call that races an in-flight one either blocks/no-ops instead of spawning, or the losing spawned child is killed before the call returns — otherwise every concurrent double-invocation (plausible for the exact orchestrator-retry scenario the proposal was written to fix) leaks a permanently running, permanently untracked `--self-heal` process.
