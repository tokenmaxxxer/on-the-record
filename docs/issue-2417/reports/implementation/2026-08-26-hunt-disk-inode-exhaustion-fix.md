---
proposal: (build-now bypass — no phase-1 proposal file; dispatch context is the diff itself)
---

# Hunt record — disk/inode exhaustion fix (issue #2417, build-now delivery)

## before-landing — stance 0: assume the gate/check just added is bypassable — find the bypass

Verdict: FINDING — `_spawn_capacity_check()` is only called on the fresh-clone branch of `issue_workspace()`; both reuse branches (src==work, and existing-.git-with-matching-origin) skip it entirely and go straight to `_fetch_or_halt`, which can still ENOSPC and produce the exact buried/truncated `sys.exit` message the fix was meant to eliminate.
Kind: composition
Seed: spawn.py `_spawn_capacity_check`/`_workspace_clone_incomplete` additions + call sites around `def issue_workspace` (~line 2135-2274); `_fetch_or_halt` in pipeline.py (~line 831)
cap_seconds: 180
tier: size:diff>200 lines
diff_stat_lines: (not provided by dispatcher; spawn.py + watchdog.py diff, >200 lines per dispatch note)
started_at: 2026-08-26T00:00:00Z (approx, wall-clock within cap)
ended_at: 2026-08-26T00:03:00Z (approx, within 180s cap)

### Reproduce
```
grep -n "_spawn_capacity_check(" spawn.py
# -> only two matches: the def (line 609) and ONE call site (line 2232),
#    which sits after `if (work / ".git").exists(): ...` has already
#    returned via the two reuse branches (lines 2183 and 2227).

# Concrete run: build a local origin+src repo, do a normal fresh clone
# via issue_workspace() to populate the reuse-path workspace, then set an
# impossibly high MUSTER_MIN_FREE_BYTES and call issue_workspace() again
# for (a) a NEW issue number (fresh-clone branch) and (b) the SAME issue
# number (reuse branch, existing .git + matching origin).
mkdir -p /tmp/capcheck_test && cd /tmp/capcheck_test
git init -q --bare origin.git
git clone -q origin.git src
cd src && git config user.email a@b.c && git config user.name a
echo hi > f.txt && git add f.txt && git commit -q -m init
git push -q origin HEAD:main
cd /tmp/capcheck_test && mkdir -p workbase

# run1.py: import spawn; spawn.issue_workspace("/tmp/capcheck_test/src", 1, "test")
MUSTER_WORK_DIR=/tmp/capcheck_test/workbase python3 run1.py   # normal fresh clone, succeeds

# run2.py: with MUSTER_MIN_FREE_BYTES=10**18 set, calls
#   spawn.issue_workspace("/tmp/capcheck_test/src", 2, "test2")   # NEW issue -> fresh-clone branch
#   spawn.issue_workspace("/tmp/capcheck_test/src", 1, "test")    # SAME issue -> reuse branch (workspace from run1.py)
MUSTER_WORK_DIR=/tmp/capcheck_test/workbase MUSTER_MIN_FREE_BYTES=1000000000000000000 python3 run2.py
```

### Observed
```
FRESH clone correctly refused: 스폰을 거부한다: /tmp/capcheck_test/workbase 에 여유 공간이 부족하다 (83750MB 가용, 임계값 953674316406MB) — clone 을 시도하기 전에 미리 막는다. 정책: 워크스페이스 상한 실측치(~119MB)의 3배를 동시-스폰 헤드룸으로 둔다. 알고 진행하려면 MUSTER_SKIP_SPACE_CHECK=1.
REUSE path workspace: /tmp/capcheck_test/workbase/origin-issue-1-test -- capacity check was NOT applied here
```
Under the identical "disk is far below threshold" condition, the fresh-clone branch is correctly refused with a clear pre-flight message naming free space and threshold, while the reuse branch (issue #1, existing `.git`, matching origin) proceeds straight into `_fetch_or_halt` with zero capacity guard.

### Expected
`_spawn_capacity_check()` should guard every branch that clones/fetches non-trivial data into `work` (the fresh-clone branch at line 2232 is not the only one that writes to disk) — otherwise a respawn onto an already-existing, previously-cloned workspace on a now-nearly-full disk still hits `_fetch_or_halt`'s truncated `git fetch` stderr `sys.exit`, i.e. exactly the "buried git clone/fetch error" failure mode issue #2417 set out to eliminate, just relocated to the reuse path instead of removed.

### Resolution
Fixed before landing. `_spawn_capacity_check(work)` moved from immediately before the `git clone` call to immediately after `work` is computed, before any of the three branches (`src == work.resolve()` self-reuse, existing-`.git` workspace reuse, fresh clone) — so all three now hit the same pre-flight probe before their first disk-writing call (`_fetch_or_halt` or `git clone`). Regression test added:
`tests/test_spawn_pipeline.py::SpawnCapacityCheck::test_reuse_branch_is_also_refused_not_just_fresh_clone` — builds a reuse-eligible workspace, mocks `shutil.disk_usage` to report near-zero free space, and asserts the reuse branch now raises the same "여유 공간이 부족하다" `SystemExit` with `_fetch_or_halt` never called. Passes, alongside the original fresh-clone and skip-env-var tests (3 passed).
