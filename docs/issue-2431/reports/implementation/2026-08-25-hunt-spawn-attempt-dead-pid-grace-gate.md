---
proposal: docs/issue-2431/proposals/spawn-attempt-dead-pid-grace-gate.md
---

# Hunt record — spawn-attempt-dead-pid-grace-gate

## before-landing — stance 1: dead-pid grace-gate could still let a genuinely-halted record vanish with zero reports, via composition with the per-tick `reported_subjects` dedup

Verdict: FINDING — when two spawn-attempt records for the same (issue, role) subject are both dead-pid and both already past `SPAWN_ATTEMPT_GRACE_SEC` at the same sweep tick, `spawn_attempt_sweep()`'s per-tick `reported_subjects` dedup (issue #2413) suppresses the report for the second one, but `_prune_spawn_attempts()`'s new age-gate (this diff) has no knowledge of that suppression and deletes both records anyway in the same call — the second, genuinely dead process attempt disappears having never once been reported, in the same tick, by the very sweep this CHANGES round exists to make report-before-prune.
Kind: composition
canonical: spawn.py:1118-1131 (dead-pid branch, new `SPAWN_ATTEMPT_GRACE_SEC` age gate — `keep_ids.add(aid)` gated only on pid liveness + `ts` age, no awareness of per-subject report suppression) and roster.py:478-500,510 (`reported_subjects` in-tick dedup inside `spawn_attempt_sweep()` — `if subject in reported_subjects: continue` skips the report/ledger-stamp for the second attempt_id of a subject, then `_sp._prune_spawn_attempts(now=now)` at roster.py:510 runs anyway in the same call)
Seed: spawn.py `_prune_spawn_attempts()` dead-pid branch (new `SPAWN_ATTEMPT_GRACE_SEC` age gate) + roster.py `spawn_attempt_sweep()`'s `reported_subjects` in-tick dedup; tests/test_watch_hardening.py `SpawnAttemptPruneLiveness` / `SpawnAttemptSweepReportsBeforePrune`
cap_seconds: (not specified by dispatcher)
tier: default
diff_stat_lines: spawn.py +41/-3, tests/test_watch_hardening.py +117/-24 (uncommitted working-tree diff)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:40:00Z

### Reproduce

acceptance: run the following inline script from the repo root with `python3` — result:

```python
import sys, os, json, tempfile, contextlib, io
sys.path.insert(0, ".")
import spawn
import roster
import unittest.mock as mock
from pathlib import Path

td = tempfile.TemporaryDirectory()
path = os.path.join(td.name, "spawn-attempts.jsonl")

def dead_pid():
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
    return pid

p1, p2 = dead_pid(), dead_pid()
now = 1_000_000.0
old_ts = now - roster.SPAWN_ATTEMPT_GRACE_SEC - 1  # already past grace for both

records = [
    {"event": "spawn_attempt", "attempt_id": "attemptA", "issue": 41,
     "role": "implementation", "pid": p1, "ts": old_ts},
    {"event": "spawn_attempt", "attempt_id": "attemptB", "issue": 41,
     "role": "implementation", "pid": p2, "ts": old_ts},
]
with open(path, "w") as fh:
    for r in records:
        fh.write(json.dumps(r) + "\n")

with mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", Path(path)), \
     mock.patch.object(spawn, "ledger_write", lambda e: None), \
     mock.patch.object(spawn, "ledger_check_and_stamp", lambda *a, **k: True):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        count = roster.spawn_attempt_sweep(d_all={}, now=now)
    remaining = set()
    if os.path.exists(path):
        with open(path) as fh:
            remaining = {json.loads(l)["attempt_id"] for l in fh}
    print("count reported:", count)
    print("stdout:", repr(buf.getvalue()))
    print("remaining attempt_ids after sweep:", remaining)
```

### Observed

canonical: output of the `acceptance:` script above, run against this working tree's `spawn.py`/`roster.py`

```
count reported: 1
stdout: '[spawn-attempt] issue-41/implementation: spawn halted pre-workspace: no outcome recorded 301s after spawn attempt (pid ...) — process likely died before it could report why\n'
remaining attempt_ids after sweep: set()
```

`attemptB` — a distinct spawn-attempt record for a distinct, confirmed-dead pid — is deleted in the same call with no report ever printed or ledger-stamped for it, and the file no longer contains it, so there is no future tick in which it could be reported either. Only `attemptA` (whichever attempt_id sorts first) produced output.

### Expected

canonical: spawn.py:1118-1131 (dead-pid branch) and roster.py:478-500,510 (`reported_subjects` dedup + same-call `_prune_spawn_attempts()` call), same citation as above

Either every dead-pid, past-grace record for the subject gets at least one report before being pruned (e.g. the prune step should not delete an attempt_id this same tick's report loop skipped purely because of the per-subject dedup, only ones it evaluated and found not-reportable for a substantive reason such as a roster entry appearing), or the per-subject dedup should not be allowed to leave a record's very last reportable tick silently unreported. As written, the new `SPAWN_ATTEMPT_GRACE_SEC` age gate guarantees "report before prune" only for the single attempt_id per subject that happens to win the in-tick dedup race; any sibling attempt_id crossing the grace threshold in the same tick is pruned with zero reports, reproducing the exact "no outcome recorded, disappeared silently" failure class #2291/#2393/#2413/#2431 were meant to eliminate — just gated on a subject-dedup collision instead of on the age-blind pruning this diff set out to fix.
