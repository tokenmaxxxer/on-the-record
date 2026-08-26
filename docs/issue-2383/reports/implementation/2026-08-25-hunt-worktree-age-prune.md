---
proposal: docs/issue-2383/proposals/worktree-age-prune.md
---

# Hunt record — worktree-age-prune

## before-landing — stance 1: lifecycle.py `_prune_worktrees` age-sweep may force-remove a worktree that is actively in use

Verdict: FINDING — `_prune_worktrees` (lifecycle.py) keys "is this worktree stale" off the top-level worktree directory's own mtime, which git only bumps when entries are added/removed directly under that directory at `worktree add` time; writes to files that already exist inside nested subdirectories (exactly what a long-running check_runner/reexecution_gate process does — append to an existing log/results file) never touch it. A worktree whose top-level dir was created >24h ago but whose contents are being actively written to seconds before `roster_clean()` runs gets `git worktree remove --force`d anyway, silently, with no notion of "is a process still using this."
Kind: silent-failure
Seed: git diff main...issue-2383/implementation -- lifecycle.py (added `_prune_worktrees`/`_worktree_max_age_hours`, wired into `roster_clean()`)
cap_seconds: (not specified by dispatcher)
tier: default
diff_stat_lines: lifecycle.py +81/-3 (see `git diff main...issue-2383/implementation -- lifecycle.py spawn.py tests/test_spawn_gate_wiring.py gates/test_clean_reconcile_safety.py`)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:20:00Z

### Reproduce

Save as `/tmp/repro_worktree_prune.py` and run with `python3 /tmp/repro_worktree_prune.py` from the repo root (needs `lifecycle.py` importable, i.e. run from `/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2383-implementation`):

```python
import sys, os, subprocess
sys.path.insert(0, os.getcwd())
import lifecycle
from pathlib import Path

base = Path("/tmp/wt_repro2")
subprocess.run(["rm", "-rf", str(base)]); base.mkdir()
main_repo = base / "main_repo"
subprocess.run(["git", "init", "-q", str(main_repo)])
subprocess.run(["git", "-C", str(main_repo), "commit", "-q", "--allow-empty", "-m", "init"])

wt = base / "wt_active"
subprocess.run(["git", "-C", str(main_repo), "worktree", "add", "-q", str(wt), "-b", "wtbranch"])

# Simulate a check process: it made a results dir once at checkout time,
# then only ever appends to a file that already exists inside it -- this
# is what a check_runner/reexecution_gate worktree actually looks like
# while a check is still running.
(wt / "results").mkdir()
(wt / "results" / "log.txt").write_text("start\n")
creation_mtime = wt.stat().st_mtime

with open(wt / "results" / "log.txt", "a") as f:
    f.write("still actively writing, right now, immediately before prune runs\n")

print("top-level worktree dir mtime (unchanged by the write above):", wt.stat().st_mtime)
print("dir mtime == creation mtime:", wt.stat().st_mtime == creation_mtime)

fake_now = creation_mtime + 30 * 3600  # 30h after the dir's mtime
lifecycle._prune_worktrees(main_repo, max_age_hours=24, now=fake_now)

print("worktree dir still exists on disk after prune?", wt.exists())
```

### Observed

```
top-level worktree dir mtime (unchanged by the write above): 1787657978.5699308
dir mtime == creation mtime: True
worktree age-prune: /tmp/wt_repro2/wt_active (30.0h > 24h) -- 지운다
worktree dir still exists on disk after prune? False
```

`_prune_worktrees` force-removed the worktree (deleting its files via `git worktree remove --force`) even though its nested log file had just been appended to a moment before the call -- the top-level dir mtime never reflected that activity, so the age check saw a 30h-old directory and could not distinguish it from one that has genuinely been idle for 30h.

### Expected

The age check should not be able to force-remove a worktree whose contents were touched seconds earlier. Either the mtime probe should walk/aggregate mtimes recursively (or check some activity marker actually updated by the running process) instead of trusting the single top-level directory mtime, or the force-remove should not run at all without a positive signal that no process still holds the worktree (a lock file, a PID check, etc.). As written, any check process whose worktree's own top-level directory predates `MUSTER_WORKTREE_MAX_AGE_HOURS` (e.g., created once at the start of a long check run, or one that was paused/queued and later resumed) can have its working tree deleted out from under it mid-run, and `roster_clean()` -> `spawn.py clean` runs this sweep on every routine clean with no confirmation or dry-run guard.
