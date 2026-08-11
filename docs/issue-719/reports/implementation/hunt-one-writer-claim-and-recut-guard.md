---
proposal: docs/issue-719/proposals/one-writer-claim-and-recut-guard.md
---

# Hunt record — one-writer-claim-and-recut-guard

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — widening the claim-held window to cover `ensure_pushed()` introduces an unhandled-exception leak: if `ensure_pushed()` raises (e.g. `gh` missing/unreachable, or any other uncaught exception from its `subprocess.run(["gh", ...])` calls, which are not wrapped in `_run_net`/try), `_release_spawn_claim()` on the very next line is never reached, and the claim leaks until stale-timeout. In the old code the release ran immediately after `proc.wait()`/`roster_remove()`, *before* `ensure_pushed()` was even called, so the same exception could never leak the claim — this is a genuine regression introduced by the widening, not a pre-existing gap.
Kind: silent-failure
Seed: spawn.py `_spawn_one()` — `push_result = ensure_pushed(cwd, issue, role)` followed immediately by `_release_spawn_claim(cwd, os.getpid())` (spawn.py:4760-4761), replacing the old release-right-after-`proc.wait()` placement.
cap_seconds: 120
tier: default
diff_stat_lines: ~197 (spawn.py + test_spawn.py)
started_at: 2026-08-11T12:32:04+09:00
ended_at: 2026-08-11T12:34:30+09:00

### Reproduce
```
cd /tmp/.../scratchpad/repro/work   # a git repo with branch issue-999/tester, origin remote set up, already pushed
python3 - <<'PYEOF'
import sys, os
sys.path.insert(0, "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-719-implementation")
import spawn

work = os.getcwd()
rej = spawn._acquire_spawn_claim(work, 999, "tester")
claim_path = spawn._spawn_claim_path(work)
print("claim exists after acquire:", claim_path.exists())

import subprocess
real_run = subprocess.run
def fake_run(cmd, *a, **kw):
    if cmd and cmd[0] == "gh":
        raise FileNotFoundError("gh: command not found (simulated)")
    return real_run(cmd, *a, **kw)
subprocess.run = fake_run

try:
    push_result = spawn.ensure_pushed(work, 999, "tester")
    spawn._release_spawn_claim(work, os.getpid())
except Exception as e:
    print("ensure_pushed raised:", repr(e))
    print("claim exists AFTER exception:", claim_path.exists())
PYEOF
```

### Observed
```
claim exists after acquire: True
ensure_pushed raised: FileNotFoundError('gh: command not found (simulated)')
claim exists AFTER exception: True
```
The `.spawn-claim` file is never cleaned up because `_release_spawn_claim()` sits after `ensure_pushed()` in `_spawn_one()`, and any exception inside `ensure_pushed()` (its `gh pr list` / `gh pr create` calls are plain `subprocess.run`, not exception-safe) skips straight past the release call. Every subsequent spawn attempt for the same `(issue, role)` is refused with "이미 세션이 이 스폰 클레임을 쥐고 있다" until the claim goes stale — a materially longer outage than before, since the claim is now held through the network-touching push/PR window instead of being released right after the local subprocess exits.

### Expected
`_release_spawn_claim()` should run in a `finally` (or equivalent) that covers `ensure_pushed()`, so a raised exception from the push/PR-create step cannot leave the (issue, role) claim held past the point where the old code already released it.
