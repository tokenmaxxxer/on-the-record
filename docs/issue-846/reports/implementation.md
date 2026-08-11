---
code_under_review:
  - on-the-record/hooks/retry-loop-bound.sh
  - on-the-record/hooks/test_retry_loop_bound.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #846

## What was done

Implemented the approved proposal's "What will be done" verbatim.

In `on-the-record/hooks/retry-loop-bound.sh`'s `pre`-mode `count >= K`
branch (previously lines 216-223), the `hookSpecificOutput` dict is now
built with `hookEventName` and `additionalContext` unconditionally, and
`permissionDecision`/`permissionDecisionReason` are added to it only when
`tool_name != "Bash"`. No other branch changed: the `count >= 2*K` abort
(`exit 2`) is byte-for-byte unchanged for every `tool_name`, and the
`count < K` silent path is unchanged. Also updated the file's header
comment (lines 16-27) to document the Bash scope-out, since it directly
describes the `pre`-mode behavior the code now implements differently.

The red-then-green sequence below (code-fenced, `derived:`-tagged) was
run before touching the hook and again after. Added two regression tests
to `on-the-record/hooks/test_retry_loop_bound.py`:
- `t_bash_kth_denial_no_longer_carries_permission_decision` — this
  issue's/PR #843's 3-step repro shape with `tool_name = "Bash"`: after 5
  `post` denials of an identical `Bash` command, the 6th `pre` lookup's
  JSON output has no `permissionDecision`/`permissionDecisionReason` key,
  while `additionalContext` still names the deny count.
- `t_write_kth_denial_still_carries_permission_decision` — same shape
  with the file's existing `tool_name = "Write"` default, asserting
  `permissionDecision == "allow"` is still present (the scope-out is
  `Bash`-only, not global; #507's shipped behavior is unchanged for every
  other `tool_name`).

To pass `tool_name`/an input key other than `TOOL`/`"file_path"` into the
already-existing `_post`/`_pre` helpers without adding a fifth inline
`subprocess.run` call site (the accumulation constraint the proposal's
`## Accumulation` section names), both helpers gained two new optional
keyword parameters, `tool_name=TOOL` and `input_key="file_path"` — every
existing call site's positional/keyword usage is unchanged and every
existing test's asserted outcome is unchanged.

Added `docs/issue-846/decisions/2026-08-11-bash-scope-fatigue-allow.md`
recording both judgment calls the issue handed off (keep `allow` for
non-`Bash`; scope it out for `Bash` categorically, inside
`retry-loop-bound.sh` itself, no shared/duplicated shape-check) and the
rejected alternatives, per the doctrine ladder for a changed-behavior
decision.

### Red, before the fix

derived: `python3 -m pytest on-the-record/hooks/test_retry_loop_bound.py -q -k "bash or write_kth"`, run against the pre-fix hook (before editing `retry-loop-bound.sh`)
```
F.                                                                       [100%]
=================================== FAILURES ===================================
___________ t_bash_kth_denial_no_longer_carries_permission_decision ____________
E           AssertionError: assert 'permissionDecision' not in {'additionalContext': 'retry-loop-bound: this exact Bash on \'cd $(touch /tmp/pwned_poc_846)&&python3 spawn.py impleme...pected: requires branch issue-474/implementation. Retrying identically will abort this action class after 10 denials.'}
on-the-record/hooks/test_retry_loop_bound.py:171: AssertionError
=========================== short test summary info ============================
FAILED on-the-record/hooks/test_retry_loop_bound.py::t_bash_kth_denial_no_longer_carries_permission_decision
1 failed, 1 passed, 8 deselected in 0.46s
```
(`t_write_kth_denial_still_carries_permission_decision` was the 1 passed
— it asserts #507's existing `Write` behavior, unaffected pre-fix.)

### Green, after the fix

derived: `python3 -m pytest on-the-record/hooks/test_retry_loop_bound.py -q`
```
..........                                                               [100%]
10 passed in 3.90s
```
(8 pre-existing tests + 2 new; all pass, no existing test's asserted
outcome changed.)

### Hand reproduction of the issue's/hunt's 3-step scenario, post-fix

derived: manual re-run of the survey's adapted PR #843 3-step repro
(`spawn-allow-gate.sh` withholds allow for the `cd`-prefix-hidden
command-substitution shape; 5 `post` denials from a stand-in unrelated
gate; 6th-attempt `pre` lookup) against the fixed
`on-the-record/hooks/retry-loop-bound.sh`
```
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "retry-loop-bound: this exact Bash on 'cd $(touch /tmp/pwned_poc_846)&&python3 spawn.py implementation \"task\" --issue 834' has been denied 5 times this session with no change between attempts. Last deny reason: plan-order-guard.sh: refused — issue-834 plan order not reached yet. Retrying identically will abort this action class after 10 denials."}}
pre exit: 0
```
No `permissionDecision` key present — the fatigue hook no longer supplies
an independent allow signal for this `Bash` shape. `spawn-allow-gate.sh`
and `merge-allow-gate.sh` were not touched (frozen per the issue).

### Full-suite comparison, branch vs. `origin/main`

`origin/main` advanced past this branch's phase-1-commit base
(`ac9732a`, the survey's recorded baseline) by the time phase 2 started —
see `## What did not work` below. Ran the acceptance check's exact
command on both, using a `git worktree` checkout of `origin/main`
(`2207183`) so the branch's own working tree (mid-edit) was not
disturbed.

derived: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`, run on the branch (working tree, fix applied, pre-commit)
```
FAILED tests/test_gates.py::t_rulebook_version_is_recorded - AssertionError: assert '커밋안됨' not in '4783509+커밋안됨 (issue-846/implementation) — 설치본 없음'
1 failed, 1223 passed, 2 skipped, 1 xfailed in 178.17s (0:02:58)
```
canonical: this session's own execution of the two pytest commands above (pasted verbatim)
This single failure is a dirty-working-tree artifact of
`spawn.rulebook_version()` reporting "커밋안됨" (uncommitted) because
this session's edits were not yet committed when the run happened — not
a behavioral regression from the fix itself; committing resolves it (see
the post-commit re-run below).

derived: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`, run in a `git worktree` checkout of `origin/main` (`2207183`)
```
FAILED tests/test_spec_index.py::t_baseline_repo_passes - AssertionError: ['docs/handbooks/setup.md: 내용이 바뀌었는데 docs/specs/reconciled-index.md 의 기록된 해시와 다르다 (기록=df9c71068366…, 실제=240ea33619b4…) — 의도된 변경이면 `python3 gates/spec_index.py --update` 로 재생성하고 관련 있다면 "Resolved ambiguities" 도 갱신하라']
1 failed, 1254 passed, 2 skipped, 1 xfailed in 181.87s (0:03:01)
```
This is a pre-existing `docs/specs/reconciled-index.md`/`docs/handbooks/setup.md`
hash-drift failure already present on `origin/main`, independent of this
issue's change — this issue's write set never touches either file. The
two failure sets share no test name; neither failure is caused by this
issue's fix. (`origin/main`'s higher pass count reflects the additional
landed commits — issue #857, #858 — this branch has not rebased onto;
this issue's write set does not overlap either of those issues' files.)

## Why

Implements the phase-1 proposal
`docs/issue-846/proposals/2026-08-11-narrow-retry-fatigue-allow-to-non-bash.md`,
approved via `APPROVE issue-846/implementation` on the issue thread by
`jjongkwann` (approvers.md-listed, single-account mode).

## Upstream

docs/issue-846/proposals/2026-08-11-narrow-retry-fatigue-allow-to-non-bash.md

## What did not work

Expected the survey's recorded baseline ("Branch and `origin/main` are
the same commit today", both `ac9732a`) to still hold at phase-2 start.

canonical: `git fetch origin main && git rev-parse origin/main` and
`git log --oneline origin/main -5`, this session's direct run
Actual: `origin/main` had advanced to `2207183` (this issue's own
phase-1 PR #864, squash-merged) plus three further, unrelated landed
commits (issue #857 x2, issue #858) by the time phase 2 began. Worked
around it by running the `origin/main` side of the acceptance check's
suite comparison in a `git worktree` checkout of `origin/main` rather
than assuming the branch's already-recorded baseline output still
applied — see `## What was done`, "Full-suite comparison" above.

## Open findings

None.

canonical: `docs/issue-846/reports/implementation/2026-08-11-hunt-narrow-retry-fatigue-allow-to-non-bash.md`,
"## before-landing — stance 1" section, this session's dispatch of
`warrant:warrant-hunter` (model sonnet, 120s cap, default tier)
Verdict: NO FINDING. The hunter grepped every hook registered on the
Bash-matching `PreToolUse` matcher groups for `permissionDecision`
emission and for any reference to `retry-loop-bound.sh`; only
`merge-allow-gate.sh`/`spawn-allow-gate.sh` besides `retry-loop-bound.sh`
itself ever emit `permissionDecision`, and neither reads or branches on
`retry-loop-bound.sh`'s state or output. It ran the actual three-way
composition (the test file's `BASH_CMD` fixture) through all three hooks
side by side post-fix: `retry-loop-bound.sh` emits `additionalContext`
only, `spawn-allow-gate.sh`/`merge-allow-gate.sh` both independently emit
no output for that shape — consistent, not cancelling.

The earlier after-proposal hunt (stance 0, phase 1)'s finding was already
resolved in the proposal itself, not carried forward as open here.
canonical: `docs/issue-846/reports/implementation/survey.md`, "Warrant
hunt" section, this session's direct read (see also `## Rationale`, "Why
`Bash`-only and not every `tool_name`" in
`docs/issue-846/proposals/2026-08-11-narrow-retry-fatigue-allow-to-non-bash.md`)

## Next steps

None — `loop_state: landed` below is terminal for this record's `kind`
(implementation.spec.json: `coding, committing -> landed`).

## Resolution path

N/A — no open finding to resolve.
