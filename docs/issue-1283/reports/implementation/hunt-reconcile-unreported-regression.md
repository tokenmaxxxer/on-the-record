---
proposal: docs/issue-1283/proposals/reconcile-unreported-regression.md
---

# Hunt record — reconcile-unreported-regression

## after-proposal — stance 1: removing the existence-skip lets _roster_reconcile_unreported crash the whole reconcile pass on a missing workspace

Verdict: FINDING — `_issue_comments(Path(work), issue_n)` calls `_repo_slug(root)` and `subprocess.run(..., cwd=root, ...)` with `root=Path(work)`; when `work` no longer exists on disk (the exact case the removed early-skip existed to handle), `subprocess.run` raises an uncaught `FileNotFoundError` because `cwd` points at a nonexistent directory — the exception propagates out of `_roster_reconcile_unreported`, aborting the whole sweep instead of just skipping/flagging that one entry.
Kind: silent-failure
Seed: spawn.py `_roster_reconcile_unreported()` — early-skip-on-missing-workspace branch removed (see diff comment citing issue #1283 at spawn.py:2911-2915), tests added in tests/test_spawn.py class RosterReconcileUnreported
cap_seconds: unspecified (not given by dispatcher)
tier: default
diff_stat_lines: n/a (reviewed via source inspection, not a diff artifact)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:20:00Z

### Reproduce
```
python3 -c "
import spawn, json
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as td:
    idx_path = Path(td) / 'workspace_index.json'
    spawn.WORKSPACE_INDEX = idx_path
    idx = {'issue-9001/implementation': {'work': str(Path(td) / 'gone-workspace'), 'log': None}}
    idx_path.write_text(json.dumps(idx))
    spawn.session_end_verdict = lambda work, log_path, now=None, **kw: 'normal'
    spawn._roster_reconcile_unreported()
"
```

### Observed
```
Traceback (most recent call last):
  ...
  File ".../subprocess.py", line 1863, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
FileNotFoundError: [Errno 2] No such file or directory: PosixPath('/tmp/.../gone-workspace')
```
The function crashes uncaught instead of returning a count; any other issues later in the sorted workspace-index iteration (and the caller `roster_reconcile`/its CLI invocation) never get processed for this run.

### Expected
`_issue_comments` (or `_roster_reconcile_unreported` around its call) should tolerate a `work` path that no longer exists — either by catching the `OSError`/`FileNotFoundError` from `subprocess.run` and returning `([], False)` like the other failure branches, or by having `_roster_reconcile_unreported` fall back to a directory that is guaranteed to exist (e.g. the checkout root) for the `cwd`/slug lookup instead of the workspace path itself — so a single stale/cleaned workspace entry degrades to "treat as unreported" rather than aborting the entire reconcile sweep.
