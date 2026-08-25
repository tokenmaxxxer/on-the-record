---
proposal: docs/issue-2293/reports/implementation.md
---

# Hunt record — issue-2293-implementation

## before-landing — stance 1: boundary between new adhoc isolation code and existing pid-keyed workspace reuse machinery

Verdict: FINDING — `issue_workspace()`'s reuse-by-existing-directory branch is not skipped for adhoc (`issue is None`) spawns, contradicting its own docstring; under PID reuse (routine on Linux once the PID space wraps) a fresh, unrelated adhoc spawn silently reuses a stale prior adhoc task's workspace — branch, uncommitted/committed leftover files and all — instead of cloning fresh.
Kind: design-error
Seed: git show HEAD (commit 0f744098), spawn.py issue_workspace()/`_spawn_one` adhoc isolation block
cap_seconds: n/a (not provided by dispatcher)
tier: default
diff_stat_lines: 566 insertions / 0 deletions (7 files)
started_at: 2026-08-25T15:20:00+09:00
ended_at: 2026-08-25T15:45:00+09:00

### Reproduce
```
cd /tmp && rm -rf ots_test && mkdir ots_test && cd ots_test
git init -q --bare origin.git
git clone -q origin.git caller_repo && cd caller_repo
git commit --allow-empty -q -m init && git push -q origin HEAD:main -u

MUSTER_WORK_DIR=/tmp/ots_test/work python3 - <<'PY'
import sys, os, subprocess
sys.path.insert(0, "<repo>")
import spawn
cwd, role = "/tmp/ots_test/caller_repo", "implementation"
os.getpid = lambda: 4242          # simulate the OS reusing a PID
w1 = spawn.issue_workspace(cwd, None, role)     # adhoc spawn #1
subprocess.run(["git","-C",w1,"checkout","-q","-b","stale-task-branch-from-first-spawn"])
open(os.path.join(w1,"STALE_MARKER_FROM_TASK_1.txt"),"w").write("leftover\n")
subprocess.run(["git","-C",w1,"add","STALE_MARKER_FROM_TASK_1.txt"])
subprocess.run(["git","-C",w1,"commit","-q","-m","task1 work"])
w2 = spawn.issue_workspace(cwd, None, role)     # adhoc spawn #2, unrelated task, same pid
print("same dir reused?", w1 == w2)
print("stale file visible in spawn #2's workspace?",
      os.path.exists(os.path.join(w2, "STALE_MARKER_FROM_TASK_1.txt")))
print("branch spawn #2 silently inherited:",
      subprocess.run(["git","-C",w2,"branch","--show-current"],capture_output=True,text=True).stdout.strip())
PY
```

### Observed
```
same dir reused? True
stale file visible in spawn #2's workspace? True
branch spawn #2 silently inherited: stale-task-branch-from-first-spawn
```
`issue_workspace()`'s docstring (spawn.py ~line 1692) states the adhoc path "always takes the fresh-clone path below rather than the reuse branches," but the code computes `work` from `{repo}-adhoc-{role}-{pid}` and then falls into the *same* `if (work / ".git").exists():` reuse branch used for issue-scoped resume — there is no `issue is not None` guard around it. A second adhoc spawn that lands on a reused PID (routine on a busy Linux host as PIDs wrap, independent of concurrency) silently inherits an unrelated prior task's branch and files with no error, no warning, and no divergent log line — exactly the "isolation" this issue exists to add fails silently.

### Expected
Adhoc spawns should never hit the reuse-by-directory branch (per the docstring's own claim) — e.g. by refusing/halting or forcing a fresh clone (removing/renaming the stale dir first) when `issue is None`, rather than transparently reusing whatever happens to sit at the pid-keyed path.
