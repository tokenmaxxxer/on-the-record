---
issue: 2293
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: PR #2368 (branch issue-2293/implementation, redelivery)
    sha: 042e47f744e91609f2994099fe7e9844b1f04efb
subject: pipeline.py `_admission_check_degenerate_task` / `ADMISSION_CHECKS`
  row, spawn.py `issue_workspace()` adhoc-isolation + stale-pid wipe +
  unified `_session_log_path()`, watchdog.py `diagnose_health()`
  `_diagnosis()` ADHOC-tag injection
test: tests/test_admission_checklist.py, tests/test_spawn_pipeline.py,
  tests/test_spawn_gate_wiring.py (re-run in a fresh `git worktree` of the
  PR's head commit) plus two standalone falsifiability repros (pre-fix vs
  post-fix) against `spawn.issue_workspace()`, not derived from the PR's
  own scripts
result: passed
assertedBy: execution-observation (this record)
---

# issue-2293 — execution-observation record

## What was done

Independently re-executed, against a fresh `git worktree` of PR #2368's
head commit (`042e47f7`, branch `issue-2293/implementation`), every
acceptance claim the implementation record makes for issue #2293's three
asks (admission refusal, adhoc isolation + timestamped log, watchdog
adhoc-visibility) plus the before-landing warrant-hunt fix, per
defect-verification independence from upstream verdicts: each figure below
was re-derived first, the implementation record's own text consulted only
afterward to compare.

**1. Full acceptance suites, re-run standalone in the PR worktree.**

derived: full raw output for all three suites quoted verbatim under
`## Acceptance evidence` below (`acceptance: python3 -m pytest ...`) —
`test_admission_checklist.py` 31 passed, `test_spawn_pipeline.py` 89
passed, `test_spawn_gate_wiring.py` 70 passed / 1 failed
(`Ledger::test_toolchain_cache_env_redirected_into_workspace` by name).

**2. Pre-existing-failure claim, independently checked** (not just cited):
ran the same single failing test in a separate `git worktree` of `main`
(`46da1c8a`, the exact base commit) rather than a `git stash` inside the
PR worktree — issue-2312's execution-observation record
(`59c7f3fe:docs/issue-2312/reports/execution-observation.md`, "What did
not work") flags `git stash` as a footgun here: a no-op stash silently
re-runs the fixed code and produces a false-positive "confirmed" reading.
A disjoint worktree of the cited base sidesteps that.

derived: the base-commit run is quoted verbatim under `## Acceptance
evidence` below (`test_toolchain_cache_env_redirected_into_workspace`
fails identically on `46da1c8a`, before this PR's diff exists).

**3. Live CLI repro of the exact consumer incident, re-run**: `python3
spawn.py implementation 538`, `... -538`, and `... "#538"` in the PR
worktree.

derived: raw stdout for all three quoted verbatim under `## Acceptance
evidence` below — all three refuse `RC=1` with the same `did you mean:
spawn.py implementation "<task>" --issue 538` text.

**4. Override path, re-run**: direct
`_admission_check_degenerate_task(..., force_adhoc_task=True)` call.

derived: quoted verbatim under `## Acceptance evidence` below — returns
`True` (admits).

**5. Watchdog ADHOC-tag claim**: not re-derived via a standalone script — a
first attempt hit `watchdog._sp is None` under a bare `import watchdog`,
which is the module's own cross-file wiring contract
(`watchdog.py`'s own module docstring: `_sp` is injected by `spawn.py`
right after it imports `watchdog`), not a defect in the PR under review.
Instead this claim rests on the three purpose-built tests that already
call the module's real wired entry point
(`test_adhoc_entry_tags_detail_with_task`,
`test_adhoc_entry_without_task_field_uses_placeholder`,
`test_issue_scoped_entry_has_no_adhoc_tag` in
`tests/test_spawn_gate_wiring.py:826-853`), which passed as part of item
1's full-suite run.

derived: item 1's `test_spawn_gate_wiring.py` run (`## Acceptance
evidence` below) includes these three tests in its 70-passed count; their
source (`042e47f744e91609f2994099fe7e9844b1f04efb:tests/test_spawn_gate_wiring.py:826-853`)
asserts the exact `ADHOC task="538"` / `ADHOC (no task recorded)` /
no-tag-when-issue-scoped strings.

**6. Falsifiability re-derivation of the before-landing warrant-hunt fix**
(not merely re-running the PR's own regression test — reproduced the
underlying `issue_workspace()` behavior directly, once against the
pre-fix commit and once against the post-fix PR head, using two disjoint
local bare-origin fixtures so neither run could contaminate the other):
mocked `os.getpid()` to collide across two `issue_workspace(cwd, None,
"implementation")` calls, wrote a branch + committed file into the first
adhoc workspace, called `issue_workspace()` again for a second
"unrelated" adhoc spawn on the same (mocked) pid.

derived: both runs quoted verbatim under `## Acceptance evidence` below —
against `0f744098` (this PR's first delivery commit, before the
warrant-hunt fix commit `9c581828`), the second spawn silently inherits
the first spawn's branch and file; against PR head `042e47f7`, the second
spawn gets a clean `master` with no inherited file, matching the hunt
record's own repro
(`042e47f744e91609f2994099fe7e9844b1f04efb:docs/issue-2293/reports/implementation/2026-08-25-hunt-2293-implementation.md`,
commit-pinned: this path does not exist on this branch, only on the PR's
branch/commit).

## Why

Re-executed rather than re-read, per this repo's established
execution-observation practice
(`59c7f3fe:docs/issue-2312/reports/execution-observation.md`,
`bd5e58dd:docs/issue-2331/reports/execution-observation.md`): a PR's own
"acceptance evidence" section is a claim, not proof, until reproduced
independently in a disjoint worktree/fixture. The falsifiability step for
the warrant-hunt fix specifically (item 6) matters because the fix commit
(`9c581828`) touches the single riskiest line in this PR — a
`shutil.rmtree()` gated on `issue is None` — and a passing regression
test alone doesn't distinguish "the guard fires correctly" from "the test
fixture happens not to trigger the guarded branch"; re-deriving both the
broken and fixed behavior from the same script against two commits does.

Item 5 (watchdog) was the one claim not re-derived via a fresh standalone
script, for the reason stated there — a hand-written direct call would
have bypassed the module's own wiring contract, so it would not have been
a fair substitute for the module's real entry point.

## Upstream basis

- GitHub issue #2293 body (admission-refusal ask, Acceptance section) and
  the consumer's scope-addition comment (isolation + timestamped log ask)
  — the actual basis for what "correct" means; scenario/repro design in
  this record came from that text and from the diff itself, not from
  reading the PR's own prose claims first.
- PR #2368, branch `issue-2293/implementation`, head commit `042e47f7` —
  `042e47f744e91609f2994099fe7e9844b1f04efb:docs/issue-2293/reports/implementation.md`,
  `042e47f744e91609f2994099fe7e9844b1f04efb:docs/issue-2293/reports/implementation/2026-08-25-hunt-2293-implementation.md`,
  and
  `042e47f744e91609f2994099fe7e9844b1f04efb:docs/issue-2293/reports/implementation/deviation-log.md`
  (commit-pinned: none of these three paths exist on this branch, only on
  the PR's branch/commit) — read for the diff and the claimed acceptance
  evidence, treated as claims to re-derive, not as verdicts to cite.
- Full `pipeline.py`/`spawn.py`/`watchdog.py` diff (`git diff
  46da1c8a..042e47f7`), read line-by-line before writing any verification
  script.

## Open findings

None. resolution path: not applicable — every acceptance claim and the
warrant-hunt fix reproduced independently, matching the implementation
record's figures exactly (item-by-item in `## What was done` above), so
no finding is open and there is nothing further to route.

derived: see `## Acceptance evidence` below — the full set of raw
transcripts this "none open" conclusion is read off.

## What did not work

A first attempt at item 5 (watchdog ADHOC-tag claim) called
`watchdog.diagnose_health()` directly against a synthetic entry after a
bare `import watchdog`, and hit `AttributeError: 'NoneType' object has no
attribute '_alive'` — `watchdog._sp` is only populated when `spawn.py`
imports `watchdog` and self-registers (`watchdog.py`'s own module
docstring), not on a standalone import. Rather than patch around this
harness gap, switched to relying on the module's own real entry-point
tests (item 5's final approach above).

## Next steps

None — `loop_state: handed-off`.

## Acceptance evidence

acceptance: `python3 -m pytest tests/test_admission_checklist.py -n0 -q`
(worktree `/tmp/pr-2368-verify`, PR #2368 head `042e47f7`) — result:
```
...............................
31 passed in 0.39s
```

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -n0 -q` —
result:
```
........................................................................
.................
89 passed in 14.45s
```

acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py -n0 -q` —
result:
```
...
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
1 failed, 70 passed in 57.70s
```

acceptance: `git worktree add /tmp/main-verify 46da1c8a && cd
/tmp/main-verify && python3 -m pytest
tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
-n0 -q` — result:
```
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
1 failed in 21.08s
```
(same failure, same base commit the implementation record cites, before
this PR's diff exists — confirms pre-existing, not introduced)

acceptance: `python3 spawn.py implementation 538; echo "RC=$?"` — result:
```
[admission] degenerate-task: task '538' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 538? Pass --force-adhoc-task to admit this literal task anyway.
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```

acceptance: `python3 spawn.py implementation -538; echo "RC=$?"` —
result:
```
[admission] degenerate-task: task '-538' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 538? Pass --force-adhoc-task to admit this literal task anyway.
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```

acceptance: `python3 spawn.py implementation "#538"; echo "RC=$?"` —
result:
```
[admission] degenerate-task: task '#538' looks like an issue number; did you mean: spawn.py implementation "<task>" --issue 538? Pass --force-adhoc-task to admit this literal task anyway.
[implementation] admission refused: missing precondition 'degenerate-task' (issue #2100) — no session created, no workspace left behind. This refusal is deterministic and non-retryable: publish the missing precondition, then dispatch again.
RC=1
```

acceptance: `python3 -c "import spawn;
print('override admits:', spawn._admission_check_degenerate_task({'issue': None, 'task': '538', 'role': 'implementation', 'force_adhoc_task': True}))"`
— result:
```
override admits: True
```

acceptance: falsifiability script (pre-fix, worktree
`/tmp/prefix-verify` of commit `0f744098`, fixture
`/tmp/ots_test/caller_repo`):
```
import sys, os, subprocess
sys.path.insert(0, "/tmp/prefix-verify")
import spawn
cwd, role = "/tmp/ots_test/caller_repo", "implementation"
os.getpid = lambda: 4242
w1 = spawn.issue_workspace(cwd, None, role)
subprocess.run(["git","-C",w1,"checkout","-q","-b","stale-task-branch-from-first-spawn"])
open(os.path.join(w1,"STALE_MARKER_FROM_TASK_1.txt"),"w").write("leftover\n")
subprocess.run(["git","-C",w1,"add","STALE_MARKER_FROM_TASK_1.txt"])
subprocess.run(["git","-C",w1,"commit","-q","-m","task1 work"])
w2 = spawn.issue_workspace(cwd, None, role)
print("PRE-FIX (0f744098) same dir reused?", w1 == w2)
print("PRE-FIX stale file visible in spawn #2 workspace?",
      os.path.exists(os.path.join(w2, "STALE_MARKER_FROM_TASK_1.txt")))
print("PRE-FIX branch spawn #2 inherited:",
      subprocess.run(["git","-C",w2,"branch","--show-current"],capture_output=True,text=True).stdout.strip())
```
— result:
```
PRE-FIX (0f744098) same dir reused? True
PRE-FIX stale file visible in spawn #2 workspace? True
PRE-FIX branch spawn #2 inherited: stale-task-branch-from-first-spawn
```

acceptance: identical script, post-fix (worktree `/tmp/pr-2368-verify` of
PR head `042e47f7`, disjoint fixture `/tmp/ots_test2/caller_repo`) —
result:
```
POST-FIX (PR HEAD) same dir reused? True
POST-FIX stale file visible in spawn #2 workspace? False
POST-FIX branch spawn #2 has: master
```
