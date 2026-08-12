---
proposal: docs/issue-1080/proposals/2026-08-12-requirement-drift-infra-tag.md
---

# Hunt record — requirement-drift-infra-tag

## before-landing — stance 0: assume the gate/guard just touched is bypassable — find the bypass

Verdict: FINDING — requirement_drift() has no try/except around the new `import requirement_linkage`; if that import fails (missing/broken gates/requirement_linkage.py, gates-dir path issue, etc.) the ModuleNotFoundError propagates unhandled out of requirement_drift(), crashing the whole `_board_wide_sweep` tick and aborting the spawn_coverage check that runs right after it in the same function — even though requirement_drift's own docstring promises "gh 실패는 조용히 건너뛴다" (advisory, non-blocking) and never touches gh for this new check at all.
Kind: composition
Seed: spawn.py requirement_drift() ~2519-2530 (import _requirement_linkage + _INFRA_TAG check), called unguarded from _board_wide_sweep at spawn.py:2584, followed by spawn_coverage checks at spawn.py:2586+
cap_seconds: 60
tier: default (size:small)
diff_stat_lines: 8 (spawn.py) + ~90 (new test file)
started_at: 2026-08-12T16:37:49+09:00
ended_at: 2026-08-12T16:37:49+09:00

### Reproduce
```
python3 -c "
import sys
sys.path.insert(0, '.')
import spawn
from pathlib import Path
import subprocess, json

orig_run = subprocess.run
def fake_run(cmd, **kw):
    if cmd[:2] == ['gh','issue'] or cmd[:2] == ['gh','pr']:
        class R: pass
        r = R(); r.returncode = 0
        r.stdout = json.dumps([{'number':1,'title':'x','body':'no refs here'}])
        return r
    return orig_run(cmd, **kw)
subprocess.run = fake_run

import shutil
gates_dir = Path('gates')
target = gates_dir / 'requirement_linkage.py'
backup = gates_dir / 'requirement_linkage.py.bak'
shutil.move(str(target), str(backup))
try:
    spawn.requirement_drift(Path('.'))
    print('NO CRASH')
except Exception as e:
    print('CRASHED:', type(e).__name__, e)
finally:
    shutil.move(str(backup), str(target))
"
```

### Observed
```
CRASHED: ModuleNotFoundError No module named 'requirement_linkage'
```
The exception is unhandled inside requirement_drift() and propagates to the caller (`_board_wide_sweep`), which would abort that entire watchdog tick — including the spawn_coverage/closure_sweep uncovered-issue check that runs immediately after `requirement_drift(root)` in the same function body — instead of the new infra-tag check merely being skipped.

### Expected
Per requirement_drift's own docstring contract ("이 스윕 자체는 블로킹 게이트가 아니라 이 함수도 그 계약을 넘지 않는다" / advisory, non-blocking, gh failures silently skipped), a failure to import the sibling gate module for the infra-tag exception should degrade this one check (e.g. treat as "tag not found" or catch ImportError and print an advisory notice) rather than raising out of the function and taking down the rest of `_board_wide_sweep` with it.
