---
proposal: docs/issue-587/proposals/implementation-remediation-round3-target-root.md
---

# Hunt record — implementation-remediation-round3-target-root

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: NO FINDING
Seed: docs/issue-587/proposals/implementation-remediation-round3-target-root.md (phase-1-only, no code changes yet)
cap_seconds: 120
tier: default
diff_stat_lines: 2 new doc files (proposal + survey), 0 code lines
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:02:00Z

Checked whether roster_reconcile new root param threaded into _remediation_merge_sweep target_root, issue depends on state nothing maintains. Read spawn.py _remediation_merge_sweep line 2109, roster_reconcile line 2158, and sibling helpers already called with a root arg: _issue_comments line 1122, _merged_pr_for_branch line 1103, _repo_slug line 1062 - all already accept and correctly use a root Path parameter. _remediation_merge_sweep already threads its own root param into decisions_dir, _repo_slug, _issue_comments, _merged_pr_for_branch, and subprocess.run cwd=root consistently. The plan adds a matching root kwarg on roster_reconcile and passes Path a.cwd resolve from main, mirroring how other CLI dispatch already uses -C. No dangling assumption found - the plumbing the proposal depends on already exists and is exercised identically elsewhere in the file. No reproduction of a broken invariant found within the cap.

## before-landing — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — the new `RosterReconcileRemediationMergedCLITargetRoot` test class in test_spawn.py (test_spawn.py only — spawn.py's production diff is not implicated) deterministically breaks two unrelated, previously-passing tests in the same file when the full suite runs, because it spawns a real `python3 spawn.py reconcile --remediation-merged ... -C <fixture>` subprocess with no isolation from the rest of the suite's pid/process-identity assumptions. The write set (spawn.py, test_spawn.py) never adds or checks for the process/pid hygiene this new subprocess-spawning test needs to coexist with `WatcherAutoArm`'s cmdline-based pid-identity tests.
Kind: composition
Seed: git diff spawn.py test_spawn.py docs/issue-587/reports/implementation.md against HEAD (b8eba9d)
cap_seconds: 120
tier: size:default-to-120s
diff_stat_lines: ~240
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:35:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-587-implementation
python3 -m pytest test_spawn.py -q            # with the round-3 diff applied (working tree as-is)
# -> FAILED WatcherAutoArm::test_watchdog_flags_pid_reused_by_unrelated_process
# -> FAILED WatcherAutoArm::test_watcher_looks_real_rejects_live_watcher_of_a_different_role
# -> 2 failed, 356 passed

git stash                                     # revert to HEAD (b8eba9d), diff removed entirely
python3 -m pytest test_spawn.py -q            # -> 357 passed, 0 failed
git stash pop

# isolate to test_spawn.py only (spawn.py reverted, new test class kept):
git stash push -- spawn.py
python3 -m pytest test_spawn.py -q
# -> 3 failed: RosterReconcileRemediationMergedCLITargetRoot::test_cli_dash_c_targets_fixture_repo_not_checkout
#    (fails because spawn.py's fix is reverted, expected)
#    PLUS the same 2 WatcherAutoArm failures — confirming the new test class alone
#    (independent of the spawn.py production change) causes the unrelated breakage
git stash pop
```

### Observed
```
FAILED test_spawn.py::WatcherAutoArm::test_watchdog_flags_pid_reused_by_unrelated_process
FAILED test_spawn.py::WatcherAutoArm::test_watcher_looks_real_rejects_live_watcher_of_a_different_role
...
E       AssertionError: True is not false
    self.assertFalse(spawn._watcher_looks_real(
        os.getpid(), 488, role="implementation"))
2 failed, 356 passed in ~23s
```
Both failures were verified reproducible across repeated runs (ran twice, same result each time) and are order-dependent on running the whole file — running `RosterReconcileRemediationMergedCLITargetRoot` or `WatcherAutoArm` in isolation each passes individually, only the full-suite ordering trips it. Root cause not fully traced (budget-bound), but isolation above rules out the spawn.py production diff and pins it on the new test class's real-subprocess spawn.

### Expected
Adding a test to test_spawn.py should never turn previously-green, unrelated tests red when the full suite is run in its normal order — `python3 -m pytest test_spawn.py -q` should stay at 358 passed (357 existing + 1 new), not regress to 356 passed / 2 failed. This would fail CI today on this branch.
