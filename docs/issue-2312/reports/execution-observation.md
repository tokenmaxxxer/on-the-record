---
issue: 2312
role: execution-observation
author: execution-observation
loop_state: terminal
upstream:
  - path: PR #2340 (branch issue-2312/implementation)
    sha: 848fd537c3738e625cd7706ab4718e3c20497f77
subject: watchdog.py roster_watchdog() dead-entry branch (~watchdog.py:1577-1610)
test: five independently-authored scripts (not derived from the PR's own
  /tmp repro or hunt script) driving the real spawn.roster_watchdog()
  against a worktree checkout of PR #2340's head commit
result: passed
assertedBy: execution-observation (this record)
---

# issue-2312 — execution-observation record

## What was done

Independently re-executed the acceptance scenarios PR #2340 claims for
issue #2312, against a fresh `git worktree` checkout of the PR's head
commit (`848fd537`) at `/tmp/otr-pr2340` — not the implementer's own
`/tmp/repro_2312b.py`. Five scripts, self-contained in `/tmp/otr_obs_scripts/`
(not part of the repo), each importing `spawn`/`watchdog` from that worktree
and calling the real `spawn.roster_watchdog()`, mocking only the collaborators
that would otherwise make real `gh`/`git` calls (`_board_wide_sweep_all`,
`lease_reconcile_sweep`, `standing_red_check`, `_undispositioned_role_prs`,
`reconcile`, `board`, `_pr_open_or_merged_for_branch`, and a fake
`diagnose_health` returning scenario-scoped fixtures) — `ledger_check_and_stamp`
was left real except in scenario 4, where it was forced `True` to keep
simulating "TTL elapsed" every tick (documented inline in that script).

1. **Report exactly once, entry retained** (`expects_pr=True`, `issue` set):
   3 real ticks over one dead entry. `COMPLETED` printed on tick 1 only,
   entry still in `active.json` after all 3 ticks.
2. **Immediate retire** (`expects_pr=False`, `issue=None`): 3 real ticks.
   `COMPLETED` printed on tick 1 only, entry gone from `active.json` by the
   end of tick 1 itself (tighter than the PR's own "removed by tick 2"
   framing).
3. **Respawn with a new pid reported as a new instance**: 2 ticks on pid1,
   then the roster entry's `pid` field is overwritten with a second,
   independently-obtained dead pid (same roster key — simulating a
   respawn reusing the key) and 2 more ticks run. Sequence
   `[1, 0, 1, 0]` across the 4 ticks — each instance reported exactly once.
4. **Warrant-hunt durability case** (sibling entry's `diagnose_health`
   raising every tick): two dead entries in one roster, `issue-7004/qa`
   (healthy fixture) sorts before `issue-7005/impl` (always raises
   `RuntimeError`). All 4 ticks raise (caught outside the tick, matching
   how a real crashing per-entry diagnosis would surface to the caller).
   `issue-7004/qa`'s `COMPLETED` line prints on tick 1 only, and its
   `reported_terminal` flag is present **on disk**
   (`watchdog_state.json`, read fresh from the filesystem each tick, not
   from process memory) from tick 1 onward.
5. **Empty-state byte-identical** (issue's own Acceptance line): ran
   `roster_watchdog()` over an empty roster on both the PR worktree and this
   branch's pre-fix checkout, base64-encoded stdout from both, diffed.

derived: raw per-scenario stdout quoted verbatim under `## Acceptance
evidence` below (`acceptance: python3 -u scenario{1..5}...`) — every
occurrence count and retained/removed state above is read directly off
those pasted transcripts, not summarized from memory.

**Falsifiability check**: before trusting scenarios 1-4 as evidence for
anything, re-ran scenarios 1-4 unmodified against this branch's pre-fix
`watchdog.py` (this checkout, and separately the PR diff reverse-applied
inside the same worktree) — all four failed exactly as the bug report
describes (reprint-every-tick, never-retired, respawn indistinguishable
from a repeat, disk flag never set). This confirms the scripts actually
exercise the defect rather than passing vacuously.

derived: raw pre-fix stdout for all four scenarios quoted verbatim under
`## Acceptance evidence` ("falsifiability re-run" block) below.

Also independently re-ran (not just cited) the two suites the PR's own
test plan lists:
- `python3 -m pytest tests/test_poll_watchdog_log.py -q` in the PR
  worktree.
- The two tests the PR calls "pre-existing, unrelated"
  (`test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal`,
  `test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch`)
  were run standalone with the fix present, then with the fix
  reverse-applied via `git apply -R` on the exact `watchdog.py` diff
  (`git stash` was a no-op here — the PR worktree has the fix *committed*,
  not as an uncommitted diff, so a naive `git stash` would have silently
  re-run the fixed code and produced a false "confirmed" reading, caught
  by checking `git status --short` was empty right after the stash).
- The full regression command from the PR's test plan
  (`tests/test_spawn_observation_recovery.py tests/test_spawn_board_flows.py
  tests/test_standing_red_watch.py tests/test_watch_hardening.py
  tests/test_spawn_pipeline.py -q`).

derived: raw pytest output for all three runs quoted verbatim under
`## Acceptance evidence` below.

## Why

Per the assigned skill (defect-verification independence from upstream
verdicts): the goal was to re-derive whether PR #2340 actually closes issue
#2312, not to restate its own test-plan checkboxes. Concretely that meant:
own worktree (not the implementer's checkout), own scripts (not
`/tmp/repro_2312b.py` or the hunt's own `/tmp/repro_2312b.py` variant —
same filename coincidence, different content, written from the issue's Ask
text and the diff itself, not from reading the PR's prose claims first),
and a falsifiability pass (run the same scripts against the pre-fix code)
so a script that happened to pass regardless of the fix would be caught
rather than silently counted as evidence.

The four scenarios map directly to the task's four explicit asks (report-
once/three-ticks, immediate-retire, respawn-as-new-instance, warrant-hunt
durability) plus a fifth for the issue's own explicit empty-state
Acceptance line, which the task didn't list but the issue's Acceptance
section requires and is cheap to check.

derived: the "would be caught" claim is substantiated by the pre-fix
transcripts quoted verbatim under `## Acceptance evidence` ("falsifiability
re-run" block) below — all four scenarios fail pre-fix, so the scripts do
in fact discriminate fixed from unfixed code rather than passing either
way.

## What did not work

- Initial `common.patched()` mocked `_board_wide_sweep_all`,
  `lease_reconcile_sweep`, `standing_red_check`, `_undispositioned_role_prs`,
  and `reconcile`, but not `board`/`_pr_open_or_merged_for_branch` — the
  first scenario run attempted a real `board(root)` call from inside
  `_build_observed()` (called eagerly as an argument to the mocked
  `reconcile`, so mocking `reconcile` alone didn't prevent it). Fixed by
  mocking `board` and `_pr_open_or_merged_for_branch` too, and keeping test
  entries `work`-less so `_build_observed()`'s git-touching branches
  short-circuit.
- `git stash` inside the PR worktree to test "fix reverted" was a silent
  no-op (nothing uncommitted to stash). Switched to `git diff main --
  watchdog.py | git apply -R`, confirmed via `git diff --stat` showing only
  `watchdog.py` reverted before re-running the two tests, then restored via
  `git checkout -- watchdog.py` afterward.
- Scenario 4's first draft used the real (unmocked) `ledger_check_and_stamp`,
  which naturally deduped `issue-7005/impl`'s crash after tick 1 (its own
  ~15min TTL semantics), producing `crashed = [True, False, False, False]`
  — a true reflection of real polling cadence, but not a test of the
  claimed multi-tick durability. Forced `ledger_check_and_stamp` to always
  return `True` for this scenario only, documented inline in the script,
  to isolate the flag-durability question from the unrelated TTL
  mechanism.

derived: the `git status --short` empty-output check after the no-op
`git stash`, and the `git diff --stat` confirmation of the reverse-applied
patch, are quoted verbatim under `## Acceptance evidence` below (the
"pre-existing, unrelated" block's surrounding commands).

## Upstream basis

- PR #2340, branch `issue-2312/implementation`, head commit `848fd537` —
  `848fd537c3738e625cd7706ab4718e3c20497f77:docs/issue-2312/reports/implementation.md`
  and
  `848fd537c3738e625cd7706ab4718e3c20497f77:docs/issue-2312/reports/implementation/2026-08-25-hunt-dead-active-json-retire.md`
  (commit-pinned: neither path exists on this branch, only on the PR's
  branch/commit) — read for the diff and the claimed acceptance evidence,
  treated as claims to re-derive, not as verdicts to cite.
- Issue #2312 body (Ask + Acceptance section) — the actual basis for what
  "correct" means; scenario design came from this, not from the PR's
  wording of its own test plan.

## Open findings

None. resolution path: not applicable — every scenario and both
pre-existing-failure tests reproduced independently with results matching
the PR's claims, and the falsifiability pass confirms the scripts are not
vacuous, so no finding is open and there is nothing further to route.

derived: see `## Acceptance evidence` below — the full set of raw
transcripts this "none open" conclusion is read off.

## Next steps

None — `loop_state: terminal`.

## Acceptance evidence

acceptance: `python3 -u scenario1_report_once_retained.py` (worktree
`/tmp/otr-pr2340`, PR #2340 head `848fd537`) — result:
```
--- tick 1 (n=1) ---
[poll-report] issue-7001/qa: COMPLETED — obs-scenario1 fake completion
이상 신호 없음
--- tick 2 (n=0) ---
이상 신호 없음
--- tick 3 (n=0) ---
이상 신호 없음

COMPLETED occurrences per tick: [1, 0, 0]
total across 3 ticks: 1
entry retained: True
SCENARIO 1: PASS
```

acceptance: `python3 -u scenario2_immediate_retire.py` — result:
```
--- tick 1 (n=1, present_after=False) ---
[poll-report] issue-7002/qa: COMPLETED — obs-scenario2 fake completion
이상 신호 없음
--- tick 2 (n=0, present_after=False) ---
돌고 있는 역할 세션 없음
이상 신호 없음
--- tick 3 (n=0, present_after=False) ---
돌고 있는 역할 세션 없음
이상 신호 없음

COMPLETED occurrences per tick: [1, 0, 0]
total across 3 ticks: 1
present after each tick: [False, False, False]
SCENARIO 2: PASS
```

acceptance: `python3 -u scenario3_respawn_new_pid.py` — result:
```
--- tick 1 (pid=612133, n=1) ---
[poll-report] issue-7003/qa: COMPLETED — obs-scenario3 fake completion
이상 신호 없음
--- tick 2 (pid=612133, n=0) ---
이상 신호 없음
--- respawn: issue-7003/qa pid 612133 -> 612171 ---
--- tick 3 (pid=612171, n=1) ---
[poll-report] issue-7003/qa: COMPLETED — obs-scenario3 fake completion
이상 신호 없음
--- tick 4 (pid=612171, n=0) ---
이상 신호 없음

COMPLETED occurrences per tick [1,2,3,4]: [1, 0, 1, 0]
SCENARIO 3: PASS
```

acceptance: `python3 -u scenario4_sibling_failure_durability.py` — result:
```
--- tick 1 (crashed=True, n=1, disk_flag=True) ---
[poll-report] issue-7004/qa: COMPLETED — obs-scenario4 fake completion
--- tick 2 (crashed=True, n=0, disk_flag=True) ---
--- tick 3 (crashed=True, n=0, disk_flag=True) ---
--- tick 4 (crashed=True, n=0, disk_flag=True) ---

crashed per tick: [True, True, True, True]
COMPLETED(issue-7004/qa) occurrences per tick: [1, 0, 0, 0]
reported_terminal flag on disk per tick: [True, True, True, True]
SCENARIO 4: PASS
```

acceptance: `python3 -u scenario5_empty_state_byte_identical.py` run
against both the PR worktree and this branch's pre-fix checkout, stdout
base64-diffed — result:
```
== post-fix (PR #2340) ==
돌고 있는 역할 세션 없음
이상 신호 없음
rc=0
== pre-fix (this branch) ==
돌고 있는 역할 세션 없음
이상 신호 없음
rc=0
== diff ==
BYTE-IDENTICAL
```

acceptance: falsifiability re-run of scenarios 1-4 against pre-fix
`watchdog.py` (this branch, and the PR diff reverse-applied inside the
worktree) — result:
```
scenario1: COMPLETED occurrences per tick: [1, 1, 1]   (assert failed, as expected)
scenario2: COMPLETED occurrences per tick: [1, 1, 1]; present after each tick: [True, True, True]
scenario3: COMPLETED occurrences per tick [1,2,3,4]: [1, 1, 1, 1]
scenario4: COMPLETED occurrences per tick: [1, 1, 1, 1]; disk flag per tick: [False, False, False, False]
```
All four fail exactly the way issue #2312 describes ("re-printed every
tick forever"), confirming the scripts detect the defect rather than
passing regardless of the fix.

acceptance: `python3 -m pytest tests/test_poll_watchdog_log.py -q` (PR
worktree) — result:
```
....                                                                     [100%]
4 passed in 0.97s
```

acceptance: independent re-run of the two tests the PR calls "pre-existing,
unrelated", with the fix present — result:
```
E       11
E       22
E       - [11, 22]
E       + [22]
tests/test_spawn_board_flows.py:2802: AssertionError
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
2 failed in 7.18s
```
Same two tests, with the PR's `watchdog.py` diff reverse-applied
(`git diff main -- watchdog.py > pr2340_watchdog.diff && git apply -R
pr2340_watchdog.diff`, confirmed via `git diff --stat` showing only
`watchdog.py` reverted — `git stash` was tried first and printed "저장할
로컬 변경 사항이 없습니다" (nothing to stash), so it would have silently
re-run the fixed code; the reverse-patch approach was used instead, and
`watchdog.py` restored via `git checkout -- watchdog.py` afterward,
`git status --short` empty confirming clean restoration) — result:
```
E       22
E       - [11, 22]
E       + [22]
tests/test_spawn_board_flows.py:2802: AssertionError
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
2 failed in 4.99s
```
Same assertion, same two failures, with and without the fix — confirms
independently that these are pre-existing and unrelated to PR #2340.

acceptance: `python3 -m pytest tests/test_spawn_observation_recovery.py
tests/test_spawn_board_flows.py tests/test_standing_red_watch.py
tests/test_watch_hardening.py tests/test_spawn_pipeline.py -q` (PR
worktree, full regression suite from the PR's own test plan) — result:
```
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
2 failed, 418 passed, 4 xfailed, 1 xpassed in 456.96s (0:07:36)
```
derived: full log at `/tmp/otr_obs_scripts/full_regression.log` (this
session's scratch dir, not part of the repo) — the two named failures are
the same two independently confirmed pre-existing/unrelated in the block
above.

skill-verdict: defect-verification-independence-from-upstream-verdicts —
present: re-derived every scenario from the issue's Ask/Acceptance text and
the diff itself (own worktree, own scripts, own scenario numbers/keys
distinct from the PR's `/tmp/repro_2312b.py`), added a falsifiability pass
(re-run against pre-fix code) that the PR's own hunt record did not
include, and re-derived the "pre-existing failure" claim via reverse-patch
rather than citing the PR's stash-based check.
other mounted skills: not triggered
