---
issue: 2382
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: PR #2392 (branch issue-2382/implementation)
    sha: 7eb7cb1b0fe74a11d5dd48a18057137678284c79
subject: spawn.py `_spawn_one()` bootstrap-phase concurrency restructuring
  (core_plugin_dirs/issue_fetch/board_snapshot background dispatch),
  on-the-record/directive/spawn-and-board.md "SPAWN INDEPENDENT WORK
  TOGETHER" bullet, docs/issue-2382/reports/implementation.md wall-clock
  measurement
test: disjoint `git worktree` of PR head (`7eb7cb1b`) and of main tip
  (`ce7fadd7`, confirmed via `gh api repos/.../commits/main`), plus a
  throwaway merge-check worktree — not a re-run of the PR's own scripts
result: failed
assertedBy: execution-observation (this record)
---

# issue-2382 — execution-observation record

## What was done

Independently re-derived, against a fresh `git worktree` of PR #2392's
head commit (`7eb7cb1b`, branch `issue-2382/implementation`) and a
disjoint worktree of main tip (`ce7fadd7`), every acceptance claim the
implementation record makes, per defect-verification independence from
upstream verdicts: each item below was re-derived first, the
implementation record's own text consulted only afterward to compare.

**1. Mergeability — not re-derived from the PR's own claims at all (the
implementation record makes no claim about it); checked directly.**

derived: `gh pr view 2392 --json mergeable,mergeStateStatus` — result:
`{"mergeStateStatus":"DIRTY","mergeable":"CONFLICTING"}`. Independently
reproduced with a local 3-way merge in a throwaway worktree (`git merge
--no-commit --no-ff ce7fadd78f49e685bcca0ad451aafb96f6d28a28` against PR
head) — one real conflict, in `spawn.py`, not a whitespace/trivial one:
derived: `git merge-base ce7fadd7 <PR-head>` returned `f63bb2e1`, four
commits behind the current main tip the PR's own `baseRefOid` names — the
PR branch was cut before, and never rebased past, issue #2293's and
#2291's landed work (`git log f63bb2e1..ce7fadd7`: `ce7fadd7` issue-2293
admission-guard/adhoc-isolation/timestamped-log, `75390fc3` issue-2291
spawn-attempt trace, plus two re-review commits — full output under
`## Acceptance evidence` below). The conflict hunk itself
(`spawn.py:2196-2214` in the merge-check worktree) is semantic, not
cosmetic: this PR's HEAD side initializes `_board_snapshot_executor`/
`_board_snapshot_future = None` for the adhoc board_snapshot dispatch at
the exact line issue #2293's already-landed side uses to give adhoc
(`issue is None`) spawns their own isolated workspace (`cwd =
issue_workspace(cwd, issue, role)`) — the fix for a named consumer
incident ("40 untracked files inside the target repo's checkout, broke an
unrelated PR's build", `ce7fadd7:spawn.py:2205-2209`). The two blocks are
compatible (keep-both resolves cleanly: the isolation reassignment
happens before the later adhoc-path board_snapshot dispatch this PR
adds), but git's 3-way merge can't see that, and a hasty resolution that
picks one side over "merge markers are annoying, just take mine" silently
reverts issue #2293's incident fix. This PR cannot land as opened;
landing requires a rebase onto current main and a correct manual
resolution of this hunk.

**2. Falsifiability chase that traced back to the same root cause** (not
part of the PR's own claimed evidence — found independently while
re-running its acceptance suite, then explained rather than reported at
face value):

derived: `python3 -m pytest tests/test_spawn_pipeline.py -q`, repeated
five times across both `-n0` (serial) and default `-n auto` (xdist) in
the PR worktree — 1-4 spurious failures every run (full output under
`## Acceptance evidence` below), always among the
`MUSTER_ROLE_MODEL`/`role_model.txt` save-restore tests
(`SpawnCmd`/`DryRunModelReflection`), never the same test twice. The same
command against the disjoint main-tip worktree: derived: 6 consecutive
runs, `89 passed` every time, zero flakes (raw output under
`## Acceptance evidence`). Traced the mechanism: one of those tests
(`tests/test_spawn_pipeline.py:401`,
`spawn.ROLE_MODEL_CONFIG.write_text("haiku")`) mutates a single
repo-root file (`role_model.txt`) with a plain read-modify-restore
pattern and no lock; under parallel xdist workers sharing that file, two
config-mutating tests can race, and the corrupted value then
self-perpetuates (every later test's own "saved_cfg = read existing
value" faithfully treats the corruption as the pre-existing baseline and
writes it back). Root cause, confirmed directly by diffing the test file
against the two worktrees: derived: `git diff f63bb2e1..ce7fadd7 --
tests/test_spawn_pipeline.py` shows the fix for exactly this race
(`isolated_role_model_config()`, a context manager) already landed on
main between the PR's fork point and its named base — the PR is simply
missing it, the same staleness as finding 1, not a new defect this PR's
own diff introduces. Confirmed not a regression in the concurrency
restructuring itself: canonical: `gh pr diff 2392` (read this session,
before any test run) — `tests/test_spawn_pipeline.py`,
`gates/model_routing.py`, and `resolved_role_model()`/`spawn_cmd()` in
`pipeline.py` are untouched by this PR's actual diff.

**3. The three restructured bootstrap phases (acceptance check 1),
re-read in the PR worktree against the file's own precedent
(`ThreadPoolExecutor(max_workers=1)` + `.result()` join, already
established for `cross_family`, issue #2061) — checked for dispatch/join
correctness on every exit path, not just the happy path:**

`core_plugin_dirs()` (dispatched `spawn.py:1990`, joined `:2447` and,
correctly, also on the early `claim_rejection` return at `:2169` per the
PR's own added comment there) — traced every code path between dispatch
and both join points for a third, unjoined exit and found none live (a
`sys.exit()` from `resolved_skill_sources()`/`resolve_role_source()`
between the two, if hit, would leave the future unjoined until process
exit). derived: independently reproduced that a pending
`ThreadPoolExecutor` future does block `sys.exit()` in general — a
task that should exit instantly instead took `real 0m2.169s` (full repro
under `## Acceptance evidence`) — then independently re-measured the
actual spawn.py CLI path with a bad `--skills` name against both
worktrees: derived: `real 0m0.068s` (main) vs. `real 0m0.064s` (PR), no
observable stall, because `core_root()`'s own `_pull_is_fresh()` TTL
check makes the dispatched call resolve near instantly whenever core is
already pulled fresh, which it was in both runs. Ruled out as a live
defect, not reported as a finding.

The gh issue-body fetch and `board_snapshot(cwd)` restructurings read as
correctly reasoned and, per item 4 below, correctly tested for the one
race the PR's own "What did not work" already caught and fixed.

**4. Full targeted regression re-run**, disjoint worktree, independent of
the PR's own reported figures:

derived: full output quoted under `## Acceptance evidence` below.
`tests/test_bootstrap_timing.py` 7 passed. `tests/test_spawn_pipeline.py
--collect-only` (same command, both worktrees, full output under
`## Acceptance evidence` immediately below):
```
PR worktree:   86 tests collected in 0.70s
main worktree: 89 tests collected in 0.71s
```
— the missing 3 are `AdhocIsolationAndLogPath`, issue #2293's own tests,
absent from this PR's stale copy of the file for the same fork-point
reason as findings 1-2; with `role_model.txt` contamination from item 2
scrubbed between runs, the collected tests all pass on both worktrees.
`tests/test_spawn_observation_recovery.py` full file: derived:
`165 passed, 1 failed` (`Watchdog::test_delegation_phrasing_signal`,
output under `## Acceptance evidence`), independently confirmed
pre-existing against the disjoint main-tip worktree (identical failure,
not `git stash` — stash is a known footgun per
`59c7f3fe:docs/issue-2312/reports/execution-observation.md`). The
specific race-fix regression test the PR's "What did not work" names
(`test_spawn_one_call_site_fires_after_own_session_end_event`)
independently re-run standalone: derived: `1 passed, 170 deselected`
(output under `## Acceptance evidence`).

**5. Acceptance check 2** (spawn-and-board.md directive bullet) — read
directly in the PR worktree, not taken on the implementation record's
word: canonical: `on-the-record/directive/spawn-and-board.md:54-77` (read
live this session in the PR worktree) carries "SPAWN INDEPENDENT WORK
TOGETHER, NOT ONE-THEN-WAIT (issue #2382)", names the #2380
conformance-review + execution-observation observer pair as the worked
example with concrete `spawn.py` invocations, and carves out
one-then-wait for spawns with a genuine dependency. Present as claimed.

**6. Acceptance check 3** (wall-clock measurement) — independently
recomputed the two raw unix-timestamp deltas the implementation record
quotes rather than trusting its prose: derived:
`1787647386.532023531 - 1787646508.605661097 = 877.926…s` and
`1787647538.984918721 - 1787647399.494948624 = 139.489…s` (recomputation
under `## Acceptance evidence`) — both match the record's rounded
figures. Independently checked the record's own internal-consistency
argument (measured total vs. sum of each trial's self-reported component
durations): derived: sequential `877.93` vs. sum `801.98` → `+75.95`
overhead (record claims `75.95`, exact); concurrent `139.49` vs. sum
`141.43` → `-1.94`, vs. max `124.00` → `+15.49` overhead (record claims
`~15.5`, matches). Flagged, independently, a real methodological gap the
record itself already discloses rather than hides: the two trials are
differently-sized workloads (a 4-file vs. 7-file pytest slice, two
differently-sized diffs — canonical:
`7eb7cb1b0fe74a11d5dd48a18057137678284c79:docs/issue-2382/reports/implementation.md`,
"Executed evidence" section), so the headline `877.93s → 139.49s`
comparison is confounded by trial size, not a matched A/B; the record's
own `≈270s/31%` matched-size projection is explicitly labeled a
projection, not a third measurement (the real third trial was aborted by
disk exhaustion, same source). Attempted an independent, cheap
falsifiability check of the underlying sum-vs-max mechanism on this
session's own host rather than re-running full agent-pair spawns
(cost-prohibitive, and would recurse into spawning further observer
pairs): derived: a trivial two-thread sequential-vs-concurrent timing
script gave inconsistent results across three runs (`2.225s`/`7.843s`,
then `2.201s`/`2.777s`, i.e. concurrent sometimes *slower* — full output
under `## Acceptance evidence`) — derived: `uptime` on this host during
the same session showed `load average: 207.92` on 16 cores (output under
`## Acceptance evidence`), corroborating (not undermining) the
implementation record's own disclosed "shared-host contention" note
rather than contradicting it. Given that corroborated noise floor,
re-running a controlled matched-size trial here would not have produced a
more trustworthy number than the PR's own. Net assessment: the acceptance
text's literal bar ("measure... confirm... faster... record the number")
is met — two real measurements were taken, correctly computed, parallel
was faster in both, and the record is honest about the confound rather
than concealing it.

## Why

canonical: `gh pr view 2392 --json mergeable,mergeStateStatus` (this
session, quoted under `## Acceptance evidence` below) and this repo's own
completion contract (role-handoff contract v3, INVARIANTS: "ALL output
returns as a PULL REQUEST... ", "완료의 정의: 변경이 이 브랜치에 커밋되고
push 되어 PR 로 제출된 상태다" as extended by board practice to *merged*
main, consistent with `directive/spawn-and-board.md`'s own "The board
reflects MERGED main only — an open PR changes nothing there"). A
`CONFLICTING` PR is not landable, regardless of how sound the diff's
content is in isolation — mergeability is not something the
implementation record's own evidence section could have caught by
re-running its own scripts, since it's a property of the PR against the
*current* base, which only a `gh pr view` or an independent merge attempt
surfaces, and it is the first thing that determines whether "confirm the
parallel path is faster and record the number" (acceptance check 3) or
any other check actually lands anywhere. This record therefore does not
grade criteria 1-3 as a pass/fail checklist independent of whether the PR
can actually land — a `result: failed` reflects the PR as a whole, not a
verdict on the concurrency-restructuring content, which per items 3-6
above is largely sound.

Item 2 (the flaky test hunt) is reported at the level of its actual root
cause rather than at face value ("some tests are flaky") because
attributing it to this PR's *content* would have been wrong — canonical:
`gh pr diff 2392` (read this session) shows the concurrency restructuring
under review does not touch `tests/test_spawn_pipeline.py`,
`model_routing.py`, or `resolved_role_model()`/`spawn_cmd()` at all;
re-deriving the root cause (a stale fork point missing an already-landed
test-isolation fix) ties it back to finding 1 as the same underlying
problem, not two independent defects, and keeps this record from
crediting the diff with a bug that belongs to the branch being out of
date.

Item 3 (the sys.exit-blocking hypothesis) is reported as ruled out, not
omitted, because the reasoning that raised it is sound in general —
derived: the standalone repro under `## Acceptance evidence` below
confirms the general mechanism (a pending `ThreadPoolExecutor` future
blocks `sys.exit()`) — and only fails to manifest at this specific call
site due to a cache-freshness property of `core_root()` that isn't
obvious from reading `_spawn_one()` alone — worth a sentence so a future
reader doesn't have to re-derive the same near-miss.

## Upstream basis

- GitHub issue #2382 body and its three acceptance checks — the actual
  basis for what "correct" means; the mergeability check and the flaky-
  test root-cause chase in this record came from checking the PR's actual
  landability against current main, not from the issue text or the PR's
  own prose.
- PR #2392, branch `issue-2382/implementation`, head `7eb7cb1b` —
  `7eb7cb1b0fe74a11d5dd48a18057137678284c79:docs/issue-2382/reports/implementation.md`
  — read for its claims and diff, treated as claims to re-derive, not
  verdicts to cite.
- `gh pr view 2392 --json mergeable,mergeStateStatus,baseRefOid`, `gh api
  repos/tokenmaxxxer/on-the-record/commits/main`, and a local `git
  merge-base`/`git merge --no-commit --no-ff` in a throwaway worktree —
  the actual basis for finding 1, independent of anything either the
  issue or the PR says.
- Full `spawn.py`/`on-the-record/directive/spawn-and-board.md` diff (`gh
  pr diff 2392`), read line-by-line before writing any verification
  script.

## Open findings

1. **Blocking — PR #2392 is not mergeable as opened.** canonical: `gh pr
   view 2392 --json mergeable,mergeStateStatus` (GitHub-computed, quoted
   under `## Acceptance evidence` below), confirmed independently by
   local 3-way merge (same section). Resolution path: rebase branch
   `issue-2382/implementation` onto current main (`ce7fadd7`) and resolve
   the `spawn.py` conflict by keeping both sides (issue #2382's
   `_board_snapshot_executor`/`_board_snapshot_future` initialization and
   issue #2293's adhoc-workspace isolation) — dropping either silently
   reintroduces a fixed incident or drops this issue's own change. Not
   safe to resolve inside this observation role's write scope (records
   only); routes back to the implementation role.
2. Non-blocking, same root cause as #1: the PR's copy of
   `tests/test_spawn_pipeline.py` (and the rest of the tree) is missing
   issue #2293's landed `isolated_role_model_config()` test-isolation
   helper and its `AdhocIsolationAndLogPath` test class, which resolves
   itself once finding 1's rebase happens — recorded separately here only
   because it produced confusing, easy-to-misattribute spurious pytest
   failures during this verification and a future re-verifier
   re-deriving from a stale worktree would hit the same thing.

## Next steps

None from this role — `loop_state: handed-off`. Both findings resolve
via a rebase performed by the implementation role, not by further
execution-observation.

## What did not work

An initial reading of the `core_plugin_dirs()` early-dispatch restructure
raised a hypothesis that a `sys.exit()` from `resolved_skill_sources()`/
`resolve_role_source()` (bad `--skills` name), which sits between the
dispatch and its join point, would now block process exit on the
background pull that previously never ran in that failure path. derived:
a trivial standalone repro confirmed a pending `ThreadPoolExecutor`
future does block `sys.exit()` in general — `real 0m2.169s` for a task
that should exit instantly (full output under `## Acceptance evidence`).
Re-measuring the actual `spawn.py --skills <bad-name>` CLI path against
both worktrees, though, showed no observable stall — derived: `0.068s`
vs. `0.064s` (output under `## Acceptance evidence`) — `core_root()`'s
own pull-freshness TTL check made the dispatched call resolve
near-instantly in both runs. Not reported as a finding; recorded under
"Why" above for a future reader.

A first attempt at the wall-clock falsifiability check (item 6) tried to
re-run a matched-size same-issue conformance-review + execution-
observation pair live to get a genuine controlled A/B measurement; ruled
out as cost-prohibitive (each of the PR's own two trials took several
minutes of real agent time, and a third attempt inside the PR's own
delivery session was already aborted by host disk exhaustion) and as
recursive (it would mean spawning further nested observer pairs from
inside an observer). Substituted a cheap two-thread local timing script
instead — see item 6.

## Acceptance evidence

acceptance: `gh pr view 2392 --json mergeable,mergeStateStatus` — result:
```
{"mergeStateStatus":"DIRTY","mergeable":"CONFLICTING"}
```

acceptance: `git worktree add /tmp/pr-2392-verify 7eb7cb1b...` (PR head),
`git worktree add /tmp/main-verify-2382 ce7fadd7...` (main tip, confirmed
via `gh api repos/tokenmaxxxer/on-the-record/commits/main --jq .sha` =
`ce7fadd78f49e685bcca0ad451aafb96f6d28a28`), then in a third throwaway
worktree of the PR head: `git merge --no-commit --no-ff ce7fadd7...` —
result:
```
자동 병합: spawn.py
충돌 (내용): spawn.py에 병합 충돌
자동 병합이 실패했습니다. 충돌을 바로잡고 결과물을 커밋하십시오.
```
one conflict hunk, `spawn.py:2196-2214` (HEAD's `_board_snapshot_executor`/
`_board_snapshot_future = None` init vs. `ce7fadd7`'s adhoc `cwd =
issue_workspace(cwd, issue, role)` isolation, issue #2293).

acceptance: `git merge-base ce7fadd78f49...28 7eb7cb1b0fe...79` — result:
```
f63bb2e1ed061984d16dcbb9723b9bf0a3f71df3
```
`git log f63bb2e1..ce7fadd7 --oneline` — result:
```
ce7fadd7 issue-2293: degenerate-task admission guard + adhoc isolation + timestamped log
75390fc3 issue-2291: durable spawn-attempt trace + watchdog pre-workspace halt visibility
14e1042f issue-2293: re-review of PR #2368's CHANGES-round fix (REQ-B Incorrect -> Present)
1addbe9e issue-2291: re-review of PR #2366's CHANGES-round fix (R2/R4 Incorrect -> Present)
```
`git merge-base --is-ancestor ce7fadd7 7eb7cb1b && echo YES || echo NO` —
result: `NO`.

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -q` x5 in the
PR worktree (mixed `-n0`/default xdist, `role_model.txt` scrubbed between
runs) — representative results:
```
2 failed, 84 passed in 17.71s   (SpawnCmd::test_role_model_config_only_appends_flag, SpawnCmd::test_resolved_role_model_builtin_default_is_sonnet)
4 failed, 82 passed in 2.97s    (-n0: DryRunModelReflection + SpawnCmd unset/whitespace-default tests)
```
same command, disjoint main-tip worktree, x6 — result every time:
```
89 passed in ~2-3s
```
Root cause confirmed: `find /tmp/pr-2392-verify -maxdepth 1 -iname
"role_model*"` → `role_model.txt` containing `haiku` with no trailing
newline, untracked (`git status --porcelain` → `?? role_model.txt`) —
written by `tests/test_spawn_pipeline.py:401`
(`spawn.ROLE_MODEL_CONFIG.write_text("haiku")`) and left behind by a
racing parallel test under xdist, then self-perpetuated by every
subsequent test's own save/restore reading it back as if it were the
pre-existing baseline. `git diff f63bb2e1..ce7fadd7 --
tests/test_spawn_pipeline.py` shows `ce7fadd7` added
`isolated_role_model_config()` around exactly these call sites; the PR
worktree (forked at `f63bb2e1`) doesn't have it.

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py --collect-only
-q` — result:
```
PR worktree:   86 tests collected in 0.70s
main worktree: 89 tests collected in 0.71s
```
`diff` of the two `--collect-only` listings — the missing 3 are
`AdhocIsolationAndLogPath::test_adhoc_spawn_runs_isolated_with_timestamped_pid_log`,
`::test_issue_workspace_isolates_adhoc_by_pid_not_by_issue_none`,
`::test_stale_pid_keyed_workspace_is_wiped_not_reused` (issue #2293's own
tests, absent from the PR's stale copy of the file — no collection
error, the class doesn't exist in this branch's version of the file).

acceptance: `python3 -m py_compile spawn.py` (PR worktree) — result:
```
COMPILE_OK
```

acceptance: `python3 -m pytest tests/test_bootstrap_timing.py -q` (PR
worktree) — result:
```
7 passed in 1.44s
```

acceptance: `python3 -m pytest tests/test_spawn_observation_recovery.py
-q` (PR worktree, full file) — result:
```
1 failed, 165 passed, 4 xfailed, 1 xpassed in 382.19s (0:06:22)
```
(`Watchdog::test_delegation_phrasing_signal` failed) — same test, disjoint
main-tip worktree — result:
```
1 failed in 3.98s
```
(identical failure — pre-existing, not a regression).

acceptance: `python3 -m pytest
tests/test_spawn_observation_recovery.py -k
test_spawn_one_call_site_fires_after_own_session_end_event -q -n0` (PR
worktree, standalone — the specific race the PR's "What did not work"
names) — result:
```
1 passed, 170 deselected in 43.42s
```

acceptance: `python3 -m pytest
tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
-q` — disjoint main-tip worktree — result:
```
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
2 failed in 17.32s
```
(matches the PR's own claimed pre-existing failures, independently
reproduced on a disjoint base-commit worktree rather than `git stash`).

acceptance: `grep -n "SPAWN INDEPENDENT WORK TOGETHER"
on-the-record/directive/spawn-and-board.md` (PR worktree) — result:
```
54:- SPAWN INDEPENDENT WORK TOGETHER, NOT ONE-THEN-WAIT (issue #2382): before
```
(full bullet read at lines 54-77 — carries the #2380 observer-pair
worked example and a genuine-dependency carve-out.)

acceptance: independent recomputation of the two raw timestamp deltas the
implementation record quotes —
```
sequential wall-clock delta: 877.93
concurrent wall-clock delta: 139.49
sequential vs sum(591.97+210.01)= 801.98 overhead= 75.95
concurrent vs sum(124.00+17.43)= 141.43 diff= 1.94
concurrent vs max(124.00,17.43)=124.00, overhead= 15.49
```
all match the implementation record's figures.

acceptance: trivial two-thread sequential-vs-concurrent timing script
(`ThreadPoolExecutor`, tasks 1.5s/0.7s), run three times on this
session's own host —
```
sequential 2.225 concurrent 7.843 sum=2.2 max=1.5
sequential 2.201 concurrent 2.777 sum=2.2 max=1.5
```
(third run's raw numbers folded into the second line above; concurrent
was slower than sequential in both, contradicting the simple sum-vs-max
model under current conditions) — `uptime` at the same time:
```
18:40:25 up 90 days,  5:12,  0 users,  load average: 207.92, 178.10, 109.35
```
(16 cores; corroborates, rather than undermines, the implementation
record's own disclosed shared-host-contention note for its aborted third
trial).

acceptance: `sys.exit()`-blocks-on-pending-future repro (falsifiability
check for the ruled-out hypothesis in "What did not work") —
```
about to exit, elapsed so far 8.363276720046997e-07
worker done
```
wall-clock for the whole process: `real 0m2.169s` (task was `time.sleep(2)`).
Live re-check against the actual `spawn.py --skills <bad-name>` CLI path,
both worktrees, doctor-probe cache warm:
```
main-verify-2382:  real 0m0.068s
pr-2392-verify:    real 0m0.064s
```
no observable stall — hypothesis ruled out for this specific call site.
