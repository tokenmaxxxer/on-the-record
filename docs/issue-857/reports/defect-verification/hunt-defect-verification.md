---
proposal: docs/issue-857/proposals/defect-verification.md
---

# Hunt record — defect-verification

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — `WORKSPACE_INDEX` (`_workspace_index_put`, spawn.py:3060) does load-mutate-save with no locking at all, unlike `ROSTER` which is wrapped in `_roster_locked()` (fcntl flock, spawn.py:1760-1770). Concurrent same-process-tree writers (e.g. an observing session and a fixture session it spawns, both hitting the same WORKSPACE_INDEX file) race and silently lose entries — the "refuse to overwrite silently" collision guard in `_workspace_index_put` (spawn.py:3077-3081) only protects same-key collisions visible within one load; it does nothing for the classic read-modify-write race where two processes both load, both mutate distinct keys, and whichever saves last wins, discarding the other's key entirely.
Kind: silent-failure
Seed: docs/issue-857/proposals/defect-verification.md, docs/issue-857/reports/defect-verification/current-state.md
cap_seconds: 60
tier: default
diff_stat_lines: N/A (survey/report only, no code diff)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:05:00Z

### Reproduce
```python
import os, threading, tempfile, importlib.util, json
spec = importlib.util.spec_from_file_location("spawn", "spawn.py")
spawn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spawn)

tmp = tempfile.mkdtemp()
spawn.ROOT = __import__("pathlib").Path(tmp)
spawn.WORKSPACE_INDEX = spawn.ROOT / "runs" / "workspaces.json"
spawn._repo_identity = lambda cwd: "repoX"

def writer(i):
    spawn._workspace_index_put(857, f"role{i}", f"/work{i}", f"/log{i}")

threads = [threading.Thread(target=writer, args=(i,)) for i in range(20)]
for t in threads: t.start()
for t in threads: t.join()

d = json.loads(spawn.WORKSPACE_INDEX.read_text())
print("expected 20 entries, got:", len(d))
```

### Observed
```
expected 20 entries, got: 1
```
19 of 20 distinct `_workspace_index_put` calls (different roles, same issue) vanish with no error, no warning, no exception — pure silent data loss under concurrent writers.

### Expected
Either `_workspace_index_put`/`_workspace_index_load` should be wrapped in the same `fcntl.flock`-based lock `_roster_locked()` uses for ROSTER, or the collision-detection comment's claim ("같은 키에 다른 work 값이 이미 있으면... 즉시 에러낸다") should acknowledge it only catches collisions visible within a single unlocked read, not concurrent racing writers — which is exactly the observer/fixture-session scenario PR #855 finding 5 is about.
