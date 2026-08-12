---
proposal: docs/issue-1043/proposals/2026-08-12-watcher-dead-follow-attribution.md
---

# Hunt record — watcher-dead-follow-attribution

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — a second follow watcher (e.g. a human running `spawn.py watch --follow` manually while the auto-armed watcher is still alive) unconditionally overwrites `watcher_pid` in the workspace index with its own pid via `_workspace_index_put()`; once that manual watcher exits, the real auto-armed watcher becomes structurally invisible and `watchdog_check_one`/`_watcher_looks_real` report watcher-dead even though the real watcher is still alive and running — the exact false-positive the proposal is meant to fix, reintroduced by the fix itself composing with a second concurrent follow.
Kind: composition
Seed: docs/issue-1043/proposals/2026-08-12-watcher-dead-follow-attribution.md — planned call `_workspace_index_put(issue, role, work, log, watcher_pid=os.getpid(), watcher_armed_at=time.time())` at follow-watcher start in `_watch()` (spawn.py)
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only proposal, no code diff yet)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
python3 - <<'PY'
import os, sys, time, json, subprocess, tempfile
sys.path.insert(0, ".")
import spawn
tmp = tempfile.mkdtemp()
spawn.WORKSPACE_INDEX = spawn.Path(tmp) / "workspace_index.json"
work, log = "/tmp/some-work", "/tmp/some-work.log"

# 1. auto-arm registers the real, long-lived watcher (this process, alive for the whole test)
real_watcher_pid = os.getpid()
spawn._workspace_index_put(1043, "implementation", work, log,
                            watcher_pid=real_watcher_pid, watcher_armed_at=time.time())

# 2. per the proposal, a second (manual) `watch --follow` self-registers at start, overwriting
p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.3)"])
spawn._workspace_index_put(1043, "implementation", work, log,
                            watcher_pid=p.pid, watcher_armed_at=time.time())
p.wait()  # manual watcher exits (Ctrl-C / terminal closed)
time.sleep(0.1)

idx = spawn._workspace_index_load()
ws_entry = idx[f"{spawn._repo_identity(work)}/issue-1043/implementation"]
recorded_pid = ws_entry["watcher_pid"]
print("looks_real:", spawn._watcher_looks_real(recorded_pid, 1043, "implementation"))
print("real watcher still alive:", spawn._alive(real_watcher_pid))
PY
```

### Observed
```
looks_real: False
real watcher still alive: True
```
`watchdog_check_one` reads `watcher_pid` from the workspace index, finds it dead (the second, manual follow watcher already exited), and flags `watcher-dead` — even though the real, still-running auto-armed watcher exists and is doing its job. The index has no way to hold or reconcile two live watcher pids; `_workspace_index_put()`'s entry is rebuilt each call and the last writer always wins, with no ownership/identity check that the caller is the same watcher the index currently trusts.

### Expected
A watcher registering itself should not be able to silently clobber another watcher's registration that is still alive and valid (or the code should structurally prevent/detect two follow watchers for the same issue/role coexisting), so that a manual `watch --follow` invocation cannot make a live auto-armed watcher look dead.

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the read-before-write guard in `_watch()` (spawn.py ~3772-3779) reads `entry.get("watcher_pid")` and calls `_watcher_looks_real()` entirely outside `_workspace_index_locked()`, so two concurrent `--follow` processes can both observe "no live watcher" and both call `_workspace_index_put()`, with the second write silently clobbering the first's watcher claim (same TOCTOU class as the earlier unconditional-overwrite finding, just narrowed to a race window instead of always).
Kind: composition
Seed: spawn.py +13 (read-before-write guard in `_watch`, ~line 3772-3779), tests/test_spawn.py +38
cap_seconds: 120
tier: default
diff_stat_lines: 51
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:02:00Z

### Reproduce
```python
import sys, threading, time
sys.path.insert(0, ".")
import spawn
from pathlib import Path

tmp = Path("/tmp/ws_index_race.json")
if tmp.exists(): tmp.unlink()
spawn.WORKSPACE_INDEX = tmp

issue, role, work, log = 999, "implementation", "/tmp/work-race", "/tmp/log-race"

def read_then_write(fake_pid, results, i):
    idx = spawn._workspace_index_load()
    key = f"{spawn._repo_identity(work)}/issue-{issue}/{role}"
    entry = idx.get(key, {})
    current_watcher_pid = entry.get("watcher_pid")
    looks_real = (current_watcher_pid is not None and
                  spawn._watcher_looks_real(current_watcher_pid, issue, role))
    time.sleep(0.05)  # the TOCTOU window between read and _workspace_index_put's lock
    if not looks_real:
        spawn._workspace_index_put(issue, role, work, log,
                                    watcher_pid=fake_pid, watcher_armed_at=time.time())
    results[i] = looks_real

results = [None, None]
t1 = threading.Thread(target=read_then_write, args=(11111, results, 0))
t2 = threading.Thread(target=read_then_write, args=(22222, results, 1))
t1.start(); t2.start(); t1.join(); t2.join()

print("both saw looks_real=False:", results)
final = spawn._workspace_index_load()
key = f"{spawn._repo_identity(work)}/issue-{issue}/{role}"
print("final entry:", final.get(key))
```

### Observed
```
both saw looks_real=False: [False, False]
final entry: {'work': '/tmp/work-race', 'log': '/tmp/log-race', 'watcher_pid': 22222, 'watcher_armed_at': 1786512664.8812113}
```
Both simulated `_watch()` calls independently decided "no live watcher, I should claim it" (the read of `entry.get("watcher_pid")` and the `_watcher_looks_real()` check happen with no lock held), and the second `_workspace_index_put()` call silently overwrote the first's `watcher_pid`/`watcher_armed_at` — exactly the clobber the guard was added to prevent, just requiring a race window instead of the previous unconditional-overwrite path.

### Expected
The read (current `watcher_pid` + liveness check) and the write (claiming `watcher_pid=os.getpid()`) should be a single atomic check-and-set under `_workspace_index_locked()` (or equivalent), so that only one of two concurrently-arriving `--follow` processes can win the claim; the loser should detect the other's claim and skip registering itself.
