---
proposal: build-now/issue-2413
---

# Hunt record — issue-2413-prune-fix

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — `_pid_is_alive()` treats a non-`int` `pid` field (e.g. a string, from a corrupted/hand-repaired spawn-attempts ledger) as unconditionally dead with no OS probe, so a genuinely-alive spawn attempt whose `pid` was serialized as a string gets pruned by `_prune_spawn_attempts()` once its `ts` ages past `SPAWN_ATTEMPTS_RETENTION_SEC` — violating the stated invariant that a live, in-flight attempt must never be pruned at any age.
Kind: silent-failure
Seed: spawn.py:1000-1065 (`_pid_is_alive`, `_prune_spawn_attempts`), roster.py:465-505 (`spawn_attempt_sweep` dedup)
cap_seconds: 120
tier: size:21-200
diff_stat_lines: 187
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:05:00Z

### Reproduce
```python
import sys, json, tempfile, time, os
from pathlib import Path
sys.path.insert(0, ".")
import spawn

td = tempfile.TemporaryDirectory()
path = Path(td.name) / "spawn-attempts.jsonl"
spawn.SPAWN_ATTEMPTS_PATH = path

mypid = os.getpid()  # genuinely alive right now
now = time.time()
old_ts = now - spawn.SPAWN_ATTEMPTS_RETENTION_SEC - 3600  # aged past retention

with path.open("w") as fh:
    fh.write(json.dumps({"event": "spawn_attempt", "attempt_id": "live1",
                          "issue": 99, "role": "implementation",
                          "pid": str(mypid), "ts": old_ts}) + "\n")

print("_pid_is_alive(str pid):", spawn._pid_is_alive(str(mypid)))
print("_pid_is_alive(int pid):", spawn._pid_is_alive(mypid))
dropped = spawn._prune_spawn_attempts(now=now)
remaining = {json.loads(l)["attempt_id"] for l in path.read_text().splitlines()} if path.exists() else set()
print("dropped:", dropped)
print("remaining ids:", remaining)
```

### Observed
```
_pid_is_alive(str pid): False
_pid_is_alive(int pid): True
dropped: 1
remaining ids: set()
```
The genuinely-alive attempt `live1` is pruned (`dropped == 1`, record gone) solely because its `pid` field is a string rather than an `int` — the exact same real, running pid returns `True` when checked directly as an `int`.

### Expected
Per `_pid_is_alive`'s own documented policy ("판정이 불확실할 때 실행 중인 spawn 을 실수로 지우는 쪽보다... 낫다" — when uncertain, prefer not to delete) and per the feature's stated invariant, a record whose `pid` genuinely maps to a live process must be kept regardless of age. The `isinstance(pid, int)` guard short-circuits before ever calling `os.kill`, so a non-`int`-but-numeric `pid` (plausible after any hand-repair or re-serialization of a corrupted ledger — this repo's own recent history, commit cea0f583, is literally titled "root-cause implementation.json corruption") is treated as certainly dead rather than "uncertain", inverting the function's own conservative-on-uncertainty design and pruning a live in-flight attempt.
