---
issue: 2443
proposal: none — build-now bypass (contract v3 s19a, CORE_BUILD_NOW=1), no proposal round ran this session
---

# Hunt record — sidecar-prune

## before-landing — stance 0: assume the gate/mechanism just touched is bypassable — find the bypass.

Verdict: FINDING — `_prune_orphaned_sidecars()`'s "live roster entry protects it" check (`workspace_dir.resolve() in live`) only ever consults the *calling checkout's own* `ROSTER` file (`ROOT/runs/active.json`, `ROOT = Path(__file__).resolve().parent`), while the sidecar files it scans live in `_workspace_base()` (`~/.tokenmaxxxer/work` by default) — a directory genuinely shared across every concurrently-running checkout on the machine. A workspace whose (issue, role) session is registered alive in a *different* checkout's roster is invisible to this check, so once that workspace's directory is gone (e.g. removed by that owning checkout's own earlier cleanup) and its sidecar files cross the 14-day age threshold, any *other* checkout's spawn-time auto-sweep thread deletes them even though the owning session is still genuinely alive.
Kind: composition
Seed: git diff -- lifecycle.py spawn.py (uncommitted, ~115 lines added: `_prune_orphaned_sidecars()`/`_sidecar_workspace_name()` in lifecycle.py, wired into spawn.py's `_run_auto_sweep()` closure)
cap_seconds: 120
tier: default
diff_stat_lines: ~115
started_at: 2026-08-25T20:55:00Z
ended_at: 2026-08-25T21:14:00Z

### Reproduce
Confirmed the architecture first, live on this machine (25 separate `on-the-record-issue-*` checkouts share `~/.tokenmaxxxer/work`; `ROSTER = STATE_ROOT / "active.json"` with `STATE_ROOT = ROOT / "runs"`, `ROOT = Path(__file__).resolve().parent` — i.e. per-checkout, confirmed by distinct `<checkout>/runs/` dirs, e.g. `/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2432-implementation/runs/` vs this checkout's own, separate `runs/`). Then ran, from this checkout's Python (`cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2443-implementation`):

```python
import sys, os, time, json, tempfile
from pathlib import Path
sys.path.insert(0, ".")
import spawn as _sp
import lifecycle

with tempfile.TemporaryDirectory() as td:
    wb = Path(td) / "work"
    wb.mkdir()
    name = "repo-issue-999-coding"
    old = time.time() - 20*86400   # older than the 14-day default threshold
    for suffix in (".events.jsonl", ".task.txt"):
        f = wb / (name + suffix)
        f.write_text("x")
        os.utime(f, (old, old))
    # No paired `wb/name` directory (simulates: the owning checkout already
    # cleaned its own workspace dir earlier; the sidecars are the only
    # remaining artifact). A DIFFERENT checkout's roster genuinely has this
    # workspace registered alive right now (real, alive pid = os.getpid()).
    other_checkout_roster = {"issue-999/coding": {
        "pid": os.getpid(), "work": str(wb / name),
        "issue": 999, "role": "coding"}}

    fake_roster_this_checkout = Path(td) / "this_checkout_active.json"  # empty/absent
    orig_roster = _sp.ROSTER
    _sp.ROSTER = fake_roster_this_checkout   # this checkout's own private roster
    try:
        print("this checkout's _live_workspaces():", lifecycle._live_workspaces())
        outcome = lifecycle._prune_orphaned_sidecars(wb, max_age_days=14)
        print("prune outcome:", outcome)
        print("files remaining:", sorted(p.name for p in wb.iterdir()))
    finally:
        _sp.ROSTER = orig_roster
```

### Observed
```
this checkout's _live_workspaces(): {}
prune outcome: {'removed': 2, 'kept': 0, 'failed': 0}
files remaining: []
```
Both sidecar files (`repo-issue-999-coding.events.jsonl`, `repo-issue-999-coding.task.txt`) are deleted (`removed: 2`), even though `other_checkout_roster` shows the exact same workspace path registered under a real, currently-alive pid (`os.getpid()`, which `_alive()` would confirm via `os.kill(pid, 0)`) — it is simply an entry in a *different* checkout's roster file, which `_prune_orphaned_sidecars()` never reads because it only calls `_sp._roster_load()` against this process's own `_sp.ROSTER` (`ROOT/runs/active.json`, `ROOT` = this checkout's own path).

### Expected
A sidecar set whose workspace path is claimed by *any* genuinely alive session on the machine — not just one spawned from the same checkout that happens to be running the auto-sweep thread — should be classified "protected" and skipped. Since `_workspace_base()` is explicitly documented (and observed live on this machine) to be a directory shared across concurrently-running sessions/checkouts, while `ROSTER`/`_live_workspaces()` is scoped to a single checkout's own `ROOT/runs/active.json`, condition (b) ("no live-pid roster entry claims that workspace path") is not actually checking "no live-pid roster entry *anywhere* claims it" — it silently degrades to "no entry in *this checkout's own* roster," which is a strictly weaker guarantee than the docstring claims and than `auto_sweep()`'s directory-deletion path (which shares this same scoping gap, but this diff adds a *second*, file-level deletion mechanism riding the identical liveness signal without noting or closing the gap).
