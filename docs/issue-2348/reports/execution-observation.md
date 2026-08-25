---
issue: 2348
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: hook_fires.py
    sha: 65d55362cadc3d09348b2dd066ccd46cff072455
  - path: deviation_log.py
    sha: 65d55362cadc3d09348b2dd066ccd46cff072455
  - path: on-the-record/hooks/hook-fires.sh
    sha: 65d55362cadc3d09348b2dd066ccd46cff072455
  - path: on-the-record/hooks/deviation-log-guard.sh
    sha: 65d55362cadc3d09348b2dd066ccd46cff072455
  - path: spawn.py
    sha: 65d55362cadc3d09348b2dd066ccd46cff072455
  - path: tests/test_spawn_consult_panel.py
    sha: 65d55362cadc3d09348b2dd066ccd46cff072455
  - path: docs/issue-2348/reports/implementation.md
    sha: 65d55362cadc3d09348b2dd066ccd46cff072455
subject: PR #2388 (issue-2348/implementation, "shard hook-fires and
  deviation-log per session"), commits
  927079c9c77c26a428bd56ebe2ff3d57aaccb08a/77cdc7b6.../65d55362cadc3d09348b2dd066ccd46cff072455
  (HEAD), branch issue-2348/implementation, checked out into an
  independent git worktree at /tmp/pr2388-src (untracked in this tree,
  removed after this observation)
test: independent re-execution of the acceptance's "executed-live"
  provenance requirement -- "the same two-branch concurrent proof PR
  #2345 ran for consult-log, repeated for hook-fires and a deviation
  log: conflict-free merge, aggregate equivalence, both pasted" -- plus
  the named acceptance gate and the record's three secondary test-plan
  lines, plus a direct read of hook-fires.sh against the operator-frozen
  "no python3 per fire" constraint from issuecomment-5407297407 -- commands
  and outputs below, run from a fresh worktree checkout of the PR branch
  plus fresh scratch git repos this session created, independent of the
  PR's own pasted output
result: passed
assertedBy: execution-observation session for issue-2348, independent of
  PR #2388's authoring (implementation) session
---

# issue-2348 — execution-observation record

## What was done

canonical: `git fetch origin pull/2388/head:pr-2388-check && git worktree
add /tmp/pr2388-src pr-2388-check` -- an independent checkout of the PR's
`hook_fires.py`/`deviation_log.py`/`hook-fires.sh`/`spawn.py` change,
never the PR's pasted transcripts taken as given. Issue #2348's Acceptance
scopes this to one concrete re-execution: repeat #2333's two-branch
concurrent-merge proof for both `.orchestrate-hook-fires.log` and
`deviation-log.md`, plus the named gate.

### Named acceptance gate and secondary test-plan lines — reproduced exactly

canonical: `python3 -m pytest tests/test_spawn_consult_panel.py -q` (PR
worktree) -- result:
```
72 passed, 1 xfailed in 1.31s
```
derived: matches the implementation record's own Executed evidence
(`72 passed, 1 xfailed`) exactly -- includes the new `HookFiresSharding`/
`DeviationLogSharding` classes (both confirmed present at
`65d55362cadc3d09348b2dd066ccd46cff072455:tests/test_spawn_consult_panel.py:1180`/
`:1265`, with the two named empty-state tests at `:1221`/`:1318`).

canonical: `python3 -m pytest on-the-record/hooks/test_hook_fire_counter.py
on-the-record/hooks/test_deviation_log_guard.py
on-the-record/hooks/test_stop_poll_rearm_deadman.py
on-the-record/hooks/test_directive_diet.py
on-the-record/hooks/test_role_deviation_directive.py
on-the-record/hooks/test_skill_verdict_guard.py -q` -- result:
```
1 failed, 41 passed in 2.58s
```
derived: matches exactly. canonical: `git stash` (PR worktree) then
re-run of `test_directive_diet.py::test_always_on_injection_within_size_budget`
alone -- result: identical failure, `2978 <= 2688` assertion fails the
same way with the PR's changes stashed out -- confirms the record's claim
that this failure is pre-existing on the branch and unrelated to
hook-fires/deviation-log. `git stash pop` restored the PR changes.

canonical: `python3 -m pytest gates/test_generated_paths.py
gates/test_boundary.py -q` -- result: `12 passed, 2 xfailed` -- matches
exactly.

canonical: `python3 -m pytest tests/test_consult_trace_root.py
gates/test_consult_siblings.py gates/test_consult_verdict_parsing.py
gates/test_consult_json_parse.py test/test_spawn_cross_family_skill_selection.py
test/test_spawn_skill_judge_haiku_timeout_overlap.py -q` -- result:
`55 passed, 3 xfailed in 2.01s` -- matches exactly (unlike the analogous
#2333 observation, which found a stale count in that PR's record for this
same adjacent-regression line, this PR's figure reproduces as stated).

### Two-branch concurrent merge, hook-fires — reproduced, genuinely concurrent

Built a scratch repo (`mktemp -d`, discarded after the run -- not a path
in this repository) with two real `git worktree` checkouts,
`issue-2348/session-a` and `issue-2348/session-b`, and ran
`hook_fires_record` (sourced directly from the PR worktree's
`65d55362cadc3d09348b2dd066ccd46cff072455:on-the-record/hooks/hook-fires.sh`,
untracked in this tree, the same pure-bash function
`directive.sh`/`stop-gate.sh`/`stop-poll-rearm.sh` call) as two
backgrounded shell subshells so they executed as genuinely simultaneous,
separate OS processes.

canonical:
```
( cd wt-a; source hook-fires.sh; hook_fires_record "..." '{"session_id":"session-a-real"}'; git commit ) &
( cd wt-b; source hook-fires.sh; hook_fires_record "..." '{"session_id":"session-b-real"}'; git commit ) &
wait
```
result: both exit 0, distinct real PIDs (1782034/1782035).
```
shard files A: .orchestrate-hook-fires/b06ba9d6df69129b76b66f04.log
shard files B: .orchestrate-hook-fires/47d456f89ee8d050764e0360.log
```
derived: these shard ids are byte-identical to the ones the PR's own
Executed evidence pastes for the same two session ids -- independent
confirmation that `sha256(session_id)[:24]` is deterministic and that the
bash `sha256sum` path (not python3) produces it.

canonical: `git merge -q --no-edit issue-2348/session-a && git merge
--no-edit issue-2348/session-b` -- result:
```
Merge made by the 'ort' strategy.
 .orchestrate-hook-fires/47d456f89ee8d050764e0360.log | 1 +
 1 file changed, 1 insertion(+)
merge B rc=0
```
No conflict — disjoint shard paths.

canonical: `python3 spawn.py hook-fires -C <scratch>` (against merged
main) -- result: both entries present. Matches the PR's own claim shape
exactly.

### Two-branch concurrent merge, deviation-log — reproduced, byte-faithful multi-line

Same scratch repo, same two worktrees. Session A ran
`CLAUDE_ROLE=implementation CLAUDE_CODE_SESSION_ID=session-a-real
python3 spawn.py deviation-log-path --issue 2348`, wrote a one-line entry
to the printed path; session B (`session-b-real`) wrote a real two-line
entry to its own printed path. Both as backgrounded concurrent
subshells.

canonical: printed shard paths --
```
A: docs/issue-2348/reports/implementation/deviation-log/20260825T093111766433-b06ba9d6df69129b.md
B: docs/issue-2348/reports/implementation/deviation-log/20260825T093111785442-47d456f89ee8d050.md
```
derived: role-scoped under `implementation/`, matching the record's claim
that role now comes from `$CLAUDE_ROLE` rather than the discarded branch
group.

canonical: `git merge -q --no-edit issue-2348/session-a && git merge
--no-edit issue-2348/session-b` -- result: two clean merges, `merge rc=0`
both times, no conflict.

canonical: `python3 spawn.py deviation-log --issue 2348 -C <scratch>`
(with `CLAUDE_ROLE=implementation`, against merged main) -- result:
```
- 2026-08-25T08:00:00Z | inline | session A real deviation entry.
- 2026-08-25T08:05:00Z | filed | session B real deviation,
  multi-line continuation text here.
```
derived: both entries present, session B's two-line entry intact and not
line-spliced with session A's — confirms the record's central claim that
whole-file (not line-level) sharding is what protects multi-line entries.

### Operator-frozen constraint (no python3 per fire) — verified by direct read

canonical: `grep -n "python3\|python " on-the-record/hooks/hook-fires.sh`
(PR worktree, final commit) -- only comment-text matches; the executable
`hook_fires_record()` body calls `sha256sum`, falling back to `shasum -a
256` then `openssl dgst -sha256`, never a python3 subprocess. canonical:
`git show 65d55362` -- confirms the prior commit's python3-heredoc
implementation was replaced by this pure-bash version in the same PR,
addressing issuecomment-5407297407 point (2). canonical: `grep -n
"hook_fires_record\|source.*hook-fires.sh" directive.sh stop-gate.sh
stop-poll-rearm.sh` -- all three hooks call it, confirming it is actually
wired into the always-on fleet-wide path, not merely added and unused.
canonical: `grep -n "sha256\|cut -c1-24" directive.sh` -- the pre-existing
monitor-notice marker uses the identical
`hashlib.sha256(...).hexdigest()[:24]` formula, matching the record's
"same hash formula" claim and consistent with the byte-identical shard
ids observed above.

### Untracked-shard detection gap fix — verified present and passing

canonical: `grep -n "porcelain\|untracked"
65d55362cadc3d09348b2dd066ccd46cff072455:on-the-record/hooks/deviation-log-guard.sh`
(untracked in this tree, PR worktree) -- a `git status --porcelain --
<rel>` fallback exists (line ~180), reporting untracked/staged/unstaged
alike, alongside the pre-existing `git diff`/`git log -p` checks.

canonical: `python3 -m pytest on-the-record/hooks/test_deviation_log_guard.py
-k t_untracked_new_shard_passes -q` (PR worktree, isolated re-run of just
this test, independent of the 41-passed bundle above) -- result:
```
1 passed in 12.26s
```
derived: the specific untracked-shard-detection test exists, is wired
into the guard's own test file, and passes in isolation, confirming both
that the fix is present and that it is exercised (not merely added and
skipped).

## Why

Delegated scope was re-execution of the acceptance's "executed-live"
provenance requirement, not re-derivation of new design claims — same
posture the issue-2333 execution-observation record
([[defect-verification-independence-from-upstream-verdicts]]) took toward
this PR's own predecessor. The two-branch concurrent-merge proof is the
highest-value independent check because it is the one claim a mocked
unit test cannot stand in for; running it from fresh scratch repos with
genuine process concurrency (backgrounded real processes, real distinct
PIDs) rather than trusting the PR's own sequential-checkout transcript is
what makes this observation independent rather than a re-read. The
operator-frozen "no python3 per fire" constraint was checked directly
against the shipped script text (not just the record's prose) because it
is a systemic, hard-to-regression-test property — a future edit could
silently reintroduce a python3 call without failing any existing test.

## Upstream basis

- `docs/issue-2348/reports/implementation.md` (untracked in this tree —
  lives on branch `issue-2348/implementation` at commit
  `65d55362cadc3d09348b2dd066ccd46cff072455`, PR #2388) — the record whose
  Acceptance/Executed-evidence this session re-executed; quoted and
  compared inline above.
- `hook_fires.py`/`deviation_log.py`/`on-the-record/hooks/hook-fires.sh`/
  `spawn.py` at the same commit (untracked in this tree, same branch) —
  the shard-id formulas, aggregators, and `hook-fires`/`deviation-log`/
  `deviation-log-path` CLI verbs this session ran directly.
- `tests/test_spawn_consult_panel.py` at the same commit (untracked in
  this tree, same branch) — the declared gate (`HookFiresSharding`/
  `DeviationLogSharding` classes), re-run in the PR worktree.
- `docs/issue-2333/reports/execution-observation.md` (this tree) — prior
  execution-observation of #2333's `consult-log.md` fix; this
  observation's method (scratch-repo genuine-concurrency reproduction)
  follows its precedent directly.

## Open findings

- Operational note, not a defect in this PR's diff: while this session's
  own Claude Code hooks were live against the `/tmp/pr2388-src` worktree
  (an artifact of testing inside this same on-the-record installation),
  a pre-existing `spawn.py watchdog --auto-respawn` process from this
  session's own environment latched onto that worktree as its cwd and
  spawned a large, growing number of `pytest-xdist` worker processes
  there, which briefly held the directory open and blocked its cleanup
  (`rm -rf`/`git worktree remove` both failed with "directory not empty"
  until every process with that cwd was killed via `/proc/*/cwd`
  inspection). Resolution path: none needed against PR #2388 itself —
  none of the processes involved (`spawn.py watchdog`, the board-flow/
  observation-recovery pytest files they ran) are in this PR's diff, and
  the same class of live-hook side effect would occur in any worktree
  checked out under this installation, not specifically this one. Noted
  here only so a future execution-observation session recognizes the
  symptom (worktree cleanup stuck on "directory not empty") and knows to
  check `/proc/*/cwd` for stray watchdog-spawned test workers rather than
  assuming file corruption.

## Next steps

None — `loop_state` above is this record kind's terminal value,
`handed-off`.
