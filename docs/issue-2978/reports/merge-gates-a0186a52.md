---
issue: 2978
role: merge-gates-a0186a52
author: merge-gates-a0186a52
skills: merge-gates (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: gates/spawn_on_pr.py, watchdog.py (on branch issue-2978/observability-signal-golden+test-derivation-5c7f5864, PR #3012)
    sha: eb0c85226621d7943aec32e5036c8b695f162f54
---

# issue-2978 — merge-gates-a0186a52 record

## What was done

Build-now bypass (`CORE_BUILD_NOW=1`); delivered directly, no phase-1
proposal round.

This is not a new deliverable against issue #2978 -- the deliverable
(watchdog no longer flags no-PR-yet or record-after-merge as violations)
and its fix round (distinguishing the ambiguous-record-set case from
no-PR-yet) were already built and independently re-verified pass on PR
#3012's own branch,
`issue-2978/observability-signal-golden+test-derivation-5c7f5864` --
canonical: PRs #3029/#3030 (`gh pr view 3029 --json title,state` /
`gh pr view 3030 --json title,state`), both `{"state":"MERGED"}` on
main, independently re-deriving the fix-round's 146/700 board figure.
The only remaining blocker was a git conflict: four record-only PRs for
this issue (#3024, #3026, #3029, #3030) landed on `main` after PR
#3012's branch was cut, so the branch no longer applied cleanly --
canonical: `gh pr view 3012 --json mergeable` before this session's
rebase returned `{"mergeable":"UNKNOWN"}`.

Rebased `issue-2978/observability-signal-golden+test-derivation-5c7f5864`
onto `origin/main` (merge-base moved from `005a3ec6` to `ebd99d66`,
derived: `git merge-base origin/main "origin/issue-2978/observability-signal-golden+test-derivation-5c7f5864"` before the rebase) and resolved
two conflicts, both confined to a single commit (`d9a6845f`, "distinguish
ambiguous deliverable record set from no-PR-yet") -- derived: `git
rebase origin/main` reported exactly these 2 files as conflicted
(`gates/spawn_on_pr.py`, `watchdog.py`), 2 more auto-merged clean
(`spawn.py`, the test file under the branch's own `tests/` directory):

- `gates/spawn_on_pr.py`: an unrelated, already-landed feature (issue
  #2981's `_branch_looks_like_deliverable()` + the `root`-taking
  `subject_deliverable_branch(root, subject, pr_index)` signature) had
  landed on `main` in between, touching the same lines. Resolution kept
  main's landed `_branch_looks_like_deliverable()` function and the
  `root`-taking signature intact, and additively re-inserted this
  branch's own `_deliverable_candidate_count()` helper right before the
  (now root-taking) `subject_deliverable_branch` definition. Git had
  already auto-merged the rest of `missing_verification()`'s body (the
  actual ambiguous-vs-no-PR-yet logic) cleanly outside the conflict
  markers, so no other line needed hand-editing.
- `watchdog.py`: a second unrelated, already-landed feature (issue
  #2979's `_classify_narrowing_prs()` / `_watchdog_note_spawn_coverage_
  delta()`) had landed adjacent to where this branch's own
  `_watchdog_note_ambiguous_deliverable_record()` was appended. Both
  additions are independent, non-overlapping functions -- resolution
  kept both, in sequence.

No code from either side was altered while resolving -- both sides'
functions are byte-identical to their pre-rebase/pre-landing form, only
re-ordered/re-concatenated around the conflict markers. No landed record
was reverted or restated.

Verified after rebase (all commands run on the rebased branch,
post-rebase tip `eb0c8522`, before switching back to this session's own
branch):

- acceptance: `python3 -c "import ast; ast.parse(open('gates/spawn_on_pr.py').read())"` and the same for `watchdog.py` — result: both exited 0, no output (parse OK).
- acceptance: `grep -rn "^<<<<<<<\|^=======\|^>>>>>>>" gates/spawn_on_pr.py watchdog.py spawn.py tests/test_watchdog_normal_state_not_violation_2978.py` — result: no matches (exit 1, empty stdout) -- no leftover conflict markers. (`tests/test_watchdog_normal_state_not_violation_2978.py` is untracked on this session's own branch -- it lives only on PR #3012's branch, not yet merged to main.)
- acceptance: `git diff --stat origin/main..HEAD` (on the rebased branch, against the `ebd99d66` main tip it was rebased onto) — result: only this branch's own 4 commits' files (new/changed): `docs/issue-2978/reports/observability-signal-golden+test-derivation-5c7f5864.md` (untracked on this session's own branch -- lives on PR #3012's branch), a ledger entry, `gates/closure_sweep.py`, `gates/spawn_on_pr.py`, `spawn.py`, `test/test_watchdog_heartbeat_noise.py`, `tests/test_watchdog_normal_state_not_violation_2978.py` (also PR-#3012-branch-only), `watchdog.py` -- derived: the diffstat's own trailer line read "8 files changed, 577 insertions(+), 3 deletions(-)", and none of the changed paths belong to any other subject's landed record.
- Force-pushed the rebased branch: `git push --force-with-lease origin issue-2978/observability-signal-golden+test-derivation-5c7f5864` — result: `d9a6845f...eb0c8522 ... (forced update)`, updating PR #3012 in place.
- canonical: `gh pr view 3012 --json mergeable,mergeStateStatus` output, checked twice -- immediately after the push: `{"mergeStateStatus":"CLEAN","mergeable":"MERGEABLE"}`; again after `main` advanced further to `d3bbcc97` (two unrelated issue-2979/2980 record commits, unrelated to this branch's files): `{"mergeStateStatus":"CLEAN","mergeable":"MERGEABLE"}` -- both clean.
- Re-ran issue #2978's four acceptance checks against the rebased branch (post-rebase tip `eb0c8522`), each in its own invocation:
  - acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` — result: 1 passed in 0.93s
  - acceptance: `python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q` — result: 1 passed in 0.91s
  - acceptance: `python3 -m pytest tests/ -k closure_sweep_record_after_merge -q` — result: 1 passed in 0.89s
  - acceptance: `python3 -m pytest tests/ -k closure_sweep_genuine_violation -q` — result: 1 passed in 0.91s
- Also ran a regression sweep over the broader test files this diff touches: acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py tests/test_watchdog_normal_state_not_violation_2978.py test/test_merge_gate_record_kind.py test/test_subject_deliverable_record_name_free.py test/test_verifies_subject_scaffold.py tests/test_respawn_deliverable_gate.py -q` — result: 4 failed, 44 passed. The 4 failures are all mock-call-count assertions on `_respawn_or_cap`, inside `tests/test_respawn_deliverable_gate.py` (test class `AutoRespawnConsultsDeliverableGateTest`). Confirmed pre-existing and unrelated to this rebase: checked out `origin/main`'s own tree (no rebase-branch changes applied) and ran the same file in isolation -- acceptance: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q` — result: 4 failed, 9 passed, the same 4 test names failing on plain `origin/main`.

## Why

The task was scoped as a git-mechanics fix, not a design decision: keep
both sides' already-verified code byte-identical, resolve the rebase
conflict, and re-run the acceptance checks against the now-current
`main` (see the acceptance results above). There was no alternative
approach to survey -- resolving an existing merge conflict without
altering either side's verified code has exactly one correct shape (a
structural merge of two non-overlapping additions), not a design space
with competing options.

## What did not work

None.

## Upstream basis

- `issue-2978/observability-signal-golden+test-derivation-5c7f5864` (PR
  #3012), pre-rebase tip sha `d9a6845f6f1602d918a1c3a7e95ce0c023db89b5` --
  the branch this record's rebase/conflict-resolution work was performed
  on; post-rebase tip sha `eb0c85226621d7943aec32e5036c8b695f162f54`,
  pushed to `origin` under the same branch name (untracked on this
  session's own branch).
- `origin/main` tip at rebase time, sha
  `ebd99d66b0dc5eb2af78b7ab86e1a1efc99ffe0d` (canonical: `git log
  origin/main -1` at rebase time, the four already-landed record PRs
  #3024/#3026/#3029/#3030 topmost) -- the tip this branch was rebased
  onto.
- `docs/issue-2978/reports/observability-signal-golden+test-derivation-5c7f5864.md`, sha `same-commit` relative to this branch's own prior commits (unchanged content, carried through the rebase; untracked on this session's own branch, lives on PR #3012's branch) -- the original deliverable's own record, documenting the fix this rebase carries forward unmodified.

## Open findings

None -- both merge conflicts resolved additively with no code alteration
on either side, verified by post-rebase syntax parse, marker-absence
grep, `git diff --stat` scope check, and the full acceptance-check
re-run above.

## Next steps

None -- PR #3012 merged during this session: canonical: `gh pr view
3012 --json mergeable,mergeStateStatus,state` returned
`{"mergeStateStatus":"UNKNOWN","mergeable":"UNKNOWN","state":"MERGED"}`
(fields go `UNKNOWN` post-merge, `state` is the authoritative one); `git
log origin/main --oneline -1` after `git fetch origin` showed
`bce83485 issue-2978: watchdog stops flagging no-PR-yet and
record-after-merge as violations (#3012)` at the tip. Re-ran issue
#2978's four acceptance checks a third time directly against this
merged `main` tip (`git worktree add /tmp/main-check-2978 origin/main`):
acceptance: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` —
result: 1 passed in 0.96s; acceptance: `python3 -m pytest tests/ -k
spawn_on_pr_genuinely_missing_branch -q` — result: 1 passed in 0.90s;
acceptance: `python3 -m pytest tests/ -k closure_sweep_record_after_merge
-q` — result: 1 passed in 0.93s; acceptance: `python3 -m pytest tests/
-k closure_sweep_genuine_violation -q` — result: 1 passed in 0.91s.
`loop_state: landed` reflects this session's own work (rebased,
conflict-resolved, pushed, re-verified) and now also PR #3012's actual
merge to `main`.

skill-verdict: work-in-english — applied: invoked; task instruction (from the spawning prompt) was in English, so per the skill's own English-edge-case rule, internal work and the final summary both stay English -- no Korean-report deviation needed.
skill-verdict: merge-gates — not-applicable: this task is resolving a merge conflict that already happened (a code task), which the skill's own trigger explicitly excludes.
