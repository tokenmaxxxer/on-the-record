---
issue: 2333
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: consult.py
    sha: 458abd2a10d9a69d6adca464314e67961b389408
  - path: spawn.py
    sha: 458abd2a10d9a69d6adca464314e67961b389408
  - path: tests/test_spawn_consult_panel.py
    sha: 458abd2a10d9a69d6adca464314e67961b389408
  - path: docs/issue-2333/reports/implementation.md
    sha: ea75927c0c8d631c90da5629c456c0d1154ce050
subject: PR #2345 (issue-2333/implementation, "shard consult-log per session to
  eliminate the append-only merge-conflict class"), commits
  458abd2a10d9a69d6adca464314e67961b389408/ea75927c0c8d631c90da5629c456c0d1154ce050,
  branch issue-2333/implementation, checked out into an independent git
  worktree at /tmp/pr2345-src (untracked in this tree)
test: independent re-execution of the two-branch concurrent-consult merge
  (Acceptance provenance requirement -- "two real concurrent sessions on one
  issue both consulting; show the merge that previously conflicted now clean")
  and the aggregated single-file-view equivalence claim, plus the named
  acceptance gate and the record's secondary regression-check test-plan line
  -- commands and outputs below, run from a fresh worktree checkout of the PR
  branch plus fresh scratch git repos/worktrees this session created,
  independent of the PR's own pasted output
result: passed
assertedBy: execution-observation session for issue-2333, independent of PR
  #2345's authoring (implementation) session
---

# issue-2333 — execution-observation record

## What was done

canonical: `git worktree add /tmp/pr2345-src pr-2345-check` (after
`git fetch origin pull/2345/head:pr-2345-check`) -- an independent checkout
of the PR's `consult.py`/`spawn.py` change, never the PR's pasted
transcripts taken as given. Spawning prompt scoped this observation to two
specific re-executions: the two-branch concurrent-consult merge (must be
conflict-free) and the aggregated-view equivalence.

### Two-branch concurrent-consult merge — reproduced, genuinely concurrent

Unlike the PR's own provenance section (sequential branch checkouts in one
shared working directory), this session used two real `git worktree`
checkouts of one scratch repo -- `/tmp/otr-verify/scratch-a` on
`issue-2333/session-a`, `/tmp/otr-verify/scratch-b` on
`issue-2333/session-b` -- and ran both `spawn.py consult` invocations as
backgrounded shell jobs so they executed as genuinely simultaneous, separate
OS processes (real distinct PIDs, not a monkeypatched shard id). `claude`
was stubbed on `PATH` with a shell script returning a canned verdict JSON
(same technique the PR's own test class uses, applied to a real subprocess
instead of a mocked one).

canonical: two concurrent processes --
```
PATH=.../fakebin:$PATH python3 spawn.py consult implementation \
  "session A concurrent-consult question" --issue 2333 -C .../scratch-a &
PATH=.../fakebin:$PATH python3 spawn.py consult implementation \
  "session B concurrent-consult question" --issue 2333 -C .../scratch-b &
wait
```
result: both exit 0.
```
$ find docs -type f   (scratch-a)
docs/issue-2333/reports/consult-log/20260825T044751703059-678540.md
$ find docs -type f   (scratch-b)
docs/issue-2333/reports/consult-log/20260825T044751713755-678541.md
```
Distinct shard filenames (distinct `<session-ts-pid>`), each committed on
its own branch by the real `_commit_consult_trace()` path.

canonical: `git checkout main && git merge -q --no-edit
issue-2333/session-a && git merge --no-edit issue-2333/session-b` -- result:
```
Merge made by the 'ort' strategy.
 docs/issue-2333/reports/consult-log/20260825T044751713755-678541.md | 1 +
 1 file changed, 1 insertion(+)
 create mode 100644 docs/issue-2333/reports/consult-log/20260825T044751713755-678541.md
merge B exit: 0
```
derived: both merges exit 0, no conflict markers, no manual resolution, per
the codefence immediately above -- the two sessions wrote disjoint paths, so
there was nothing for git to reconcile. Confirms the PR's central claim
independently.

### Aggregated view equivalence — reproduced, byte-identical

canonical: `python3 spawn.py consult-log --issue 2333 -C .../scratch` (the
new reader/aggregator, run against the merged `main`) -- result:
```
- 2026-08-25T04:47:51.703115+00:00 | role=implementation | verb=consult | issue=2333 | question='session A concurrent-consult question' | outcome='ok: answer-from-pid-681246'
- 2026-08-25T04:47:51.713808+00:00 | role=implementation | verb=consult | issue=2333 | question='session B concurrent-consult question' | outcome='ok: answer-from-pid-681253'
```
Both entries present, in chronological (filename-sorted) order.

canonical: `diff manual-concat-ordered.txt aggregate.txt` (plain shell
concatenation of the two shard files in filename order, compared against
the `consult-log` CLI output above) -- result:
```
(no output -- files identical)
```
derived: byte-identical, per the diff above -- the aggregator invents no
new format; it reproduces the pre-#2333 single-file line format exactly,
matching the record's claim.

### Named acceptance gate — reproduced exactly

canonical: `python3 -m pytest tests/test_spawn_consult_panel.py -q`
(PR worktree) -- result:
```
.........................................................x......         [100%]
63 passed, 1 xfailed in 17.08s
```
derived: same count (63 passed / 1 xfailed) as the implementation record's
own Test plan, per the codefence above.

### Secondary regression-check line — does not reproduce as stated

canonical: `python3 -m pytest tests/test_consult_trace_root.py
gates/test_consult_siblings.py gates/test_consult_verdict_parsing.py
gates/test_consult_json_parse.py test/test_spawn_cross_family_skill_selection.py
test/test_spawn_skill_judge_haiku_timeout_overlap.py -q` (PR worktree,
exact command from the implementation record's Executed evidence) -- result:
```
...................x....xx................................               [100%]
55 passed, 3 xfailed in 19.89s
```
canonical: re-run of the identical command with `-p xdist -n0` to rule out
an xdist worker-count reporting artifact -- result:
```
.............x.x..x.......................................               [100%]
55 passed, 3 xfailed in 9.71s
```
derived: both runs above agree at `55 passed, 3 xfailed` (58 collected,
also confirmed via `--collect-only`). The implementation record (untracked
in this tree -- lives on `issue-2333/implementation`, PR #2345, at commit
`ea75927c0c8d631c90da5629c456c0d1154ce050`)'s Executed evidence section
claims `118 passed, 4 xfailed` for this exact same command. `git diff
main...pr-2345-check --stat` does not list any of these six files as
touched by this PR's diff, so this is not a regression the PR introduced;
it looks like a copy/paste or stale-number error in that record's evidence
section rather than a real functional gap -- see Open findings.

## Why

Delegated scope was re-execution of the acceptance's "executed-live"
provenance requirement, not re-derivation of new design claims: the
issue's Acceptance explicitly requires two real concurrent sessions
consulting and a clean merge, so the highest-value independent check is
reproducing that scenario from a clean worktree/scratch repos with genuine
process concurrency (two backgrounded real processes, two real git
worktrees) rather than trusting the PR's own sequential-checkout
transcript or its mocked unit test alone -- the same posture prior
execution-observation records in this repo (issue-2227, issue-2298,
issue-2314) have taken toward PR-pasted live-run evidence, per
[[defect-verification-independence-from-upstream-verdicts]]. derived: from
the Two-branch concurrent-consult merge and Aggregated view equivalence
canonical results above -- both hold under independent re-execution.
Re-running the implementation record's own cited test-plan command (rather
than only the named gate) surfaced the count discrepancy above as an
unplanned but genuine finding.

## Upstream basis

- `docs/issue-2333/reports/implementation.md` (untracked in this tree --
  lives on branch `issue-2333/implementation` at commit
  `ea75927c0c8d631c90da5629c456c0d1154ce050`, PR #2345; see the
  `gh pr view 2345` citation under What was done) -- the record whose
  Acceptance/Executed-evidence this session re-executed; quoted and
  compared inline above.
- `consult.py`/`spawn.py` at commit `458abd2a10d9a69d6adca464314e67961b389408`
  (untracked in this tree, same branch) -- `_consult_trace_path()`,
  `_consult_trace_dir()`, `_consult_session_shard_id()`,
  `_consult_log_aggregate()`, and the `spawn.py consult-log` subcommand this
  session ran directly.
- `tests/test_spawn_consult_panel.py` at the same commit (untracked in this
  tree, same branch) -- the declared gate (`ConsultLogSharding` class),
  re-run in the PR worktree, not this branch (which does not carry the
  PR's changes).

## Open findings

derived: from the Secondary regression-check line canonical results above.
- The implementation record (untracked in this tree -- branch
  `issue-2333/implementation`, PR #2345, commit
  `ea75927c0c8d631c90da5629c456c0d1154ce050`)'s Executed evidence claims
  `118 passed, 4 xfailed` for a six-file pytest command; independent
  re-execution of the identical command against the identical commit gives
  `55 passed, 3 xfailed` (58 collected total), reproduced twice (default
  xdist and forced `-n0`). None of the six files are touched by this PR's
  diff, and the primary named acceptance gate (`tests/test_spawn_consult_panel.py`,
  63 passed/1 xfailed) and the two acceptance-critical live-provenance
  claims (conflict-free merge, byte-identical aggregate) all reproduce
  exactly, per the canonical results above. Resolution path: no action
  needed against the shard-per-session design or this PR's merge-worthiness
  -- the acceptance-critical claims hold under independent re-execution --
  but flag to the PR author (or whoever next touches this evidence section)
  that the `118 passed, 4 xfailed` figure appears to be a stale or
  miscounted number and should be corrected or re-verified before being
  cited again.

## Next steps

None -- `loop_state` above is this record kind's terminal value,
`handed-off`.
