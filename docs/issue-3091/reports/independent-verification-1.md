---
issue: 3091
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # independent verification of PR #3111's own deliverable against issue #3091
code_under_review: 6df0350a9d4a7ae04a640446e218f8615a421c5c
loop_state: landed
type: defect-verification-record
breaking: false
verdict: All 3 acceptance checks Present, both must-not clauses held. Every
  diagnosis claim spot-checked against actual source corroborates the
  PR's stated cause. No assertion was loosened in any of the 6 fix
  commits. Zero findings.
upstream:
  - path: PR #3111 (github.com/tokenmaxxxxer/on-the-record/pull/3111),
      fetched as local ref pr-3111-review, head commit 6df0350a -- the
      deliverable under review
    sha: 6df0350a9d4a7ae04a640446e218f8615a421c5c
---

# issue-3091 — independent-verification-1 record

## What was done

Independent, builder-blind verification of PR #3111 against issue #3091's
three `check:` acceptance commands and its two `must-not` clauses,
re-derived from a fresh worktree rather than trusting the PR's own
pasted output or its own record's citations. All three commands below
were run against `python3 gates/probe_full_suite_is_one_command.py` and
`test/`/`tests/` as they exist on PR #3111's own head commit -- these
paths are untracked (do not exist) on this verification session's own
`issue-3091/independent-verification-1` branch, which carries none of
PR #3111's commits; they were reached only via the separate
`pr-3111-review` worktree checkout below.

canonical: `gh pr view 3111 --json body,commits,files` (read in full
this session) and a fresh `git worktree add /tmp/pr-3111-wt
pr-3111-review` checkout of head commit `6df0350a`.

acceptance: `bash -c "python3 -m pytest test/ -q"` — result:
```
563 passed, 3 xfailed in 32.33s
```
Matches the PR's claimed count exactly.

acceptance: `bash -c "python3 -m pytest tests/ -q"` — result:
```
5 failed, 182 passed, 2 warnings in 10.45s
```
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest
(x4), FAILED
tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present.
PR #3111's own record claims these 5 are pre-existing on its `main`
base, out of scope, and already fixed by PR #3089 on a branch not yet
merged at diagnosis time.

derived: `git merge-base pr-3111-review origin/main` → `573e7382`;
`git merge-base --is-ancestor 7ee16612 573e7382` (7ee16612 is PR #3089's
merge commit, confirmed via `gh pr view 3089 --json mergeCommit`)
exits non-zero -- PR #3111 branched before PR #3089 merged, so the base
genuinely predates that fix.

acceptance: `bash -c "python3 -m pytest tests/ -q"` (second worktree, on
current `origin/main`, which does include `7ee16612`) — result:
```
216 passed, 2 warnings in 9.45s
```
Zero failures once PR #3089's fix is present, confirming the 5 failures
are that gap and not a regression from PR #3111's own diff.

derived: `gh pr view 3111 --json files` lists only files under
`docs/issue-3091/reports/`, one new file under `gates/`, and five files
under `test/` (singular) -- zero files under `tests/` (plural) -- so PR
#3111's diff cannot itself be the cause of any `tests/` failure.
`gh pr view 3111 --json mergeable` reports `"MERGEABLE"`.

acceptance: `bash -c "python3 gates/probe_full_suite_is_one_command.py"`
(this new gate file itself is untracked on this session's own branch;
run only inside the `pr-3111-review` worktree, where PR #3111 adds it)
— result:
```
FAIL: 2 shell test file(s) exist that `python3 -m pytest` can never collect: ['tests/check-write-set-conflicts.test.sh', 'tests/claim-scan-preflight.test.sh'] -- running every test in the repo therefore requires a SECOND, separate command (`bash tests/run-orchestrate-tests.sh`, per docs/handbooks/on-the-record.md), so no single command currently suffices.
```
derived: ran the script with output redirected to a file and checked
`$?` immediately after (not through a piped `tail`, which would report
the pipe's own exit code instead): `real exit: 1`. Matches the issue's
explicit requirement that this new gate must fail against the current
tree.

## Why

Chose direct source-level re-derivation over trusting the PR's own
citations, per this issue's own point: the deliverable under review is
itself a diagnosis-quality claim (12 "stale, not live-defect"
classifications), so accepting its citations at face value would repeat
the failure mode the parent issue exists to catch. Ran all three
acceptance commands from a scratch worktree rather than reusing the
PR's pasted output, and read the actual current call sites, function
signatures, and hook regex literals named in the diagnosis table rather
than trusting the commit messages describing them.

## Must-not clauses

canonical: `git diff origin/main pr-3111-review -- test/*.py` (full diff
of all six fix commits read in this session, not summarized from the
PR's own record).

- "do not fix any failure by deleting or skipping the test": every
  hunk in that diff either (a) updates a pinned literal/regex to match
  intentionally-changed production behaviour, (b) repoints a mock at
  the function real code now calls (unchanged call semantics), or (c)
  replaces a position-fragile `recorded[-1]` index with a search for
  the one entry carrying the field under test, still requiring exactly
  one match. No `assertEqual`/`assertIn`/`assertTrue` was removed. One
  test was renamed and its expected value flipped from `[]` to a
  populated match (test name changed from asserting family-exclusion
  to asserting the opposite); see the `_ROLE_SKILLS` finding below for
  why that direction is correct rather than a loosening.
- "do not mark one an environment artifact without showing the
  environment difference": the diagnosis table classifies all 15 as
  "stale test," never "environment artifact" -- no instance of that
  classification exists in the diff or record to check.

## Diagnosis claims re-derived against current source

canonical: direct reads of `spawn.py`, `consult.py`, and `pipeline.py`,
plus the three `on-the-record/hooks/*.sh` files, in the `pr-3111-review`
worktree this session (not re-citing the PR's own record's line
numbers without checking them; these files are untracked on this
session's own branch and were reached only via that worktree).

- `checkout_issue_branch` dead-mock claim: `grep -n
  "checkout_issue_branch\|_checkout_named_branch" spawn.py` shows
  `_spawn_one`'s real call path is `checkout_issue_branch_for_skill(...)`
  → `_checkout_named_branch(cwd, f"issue-{issue}/{skill}")`; the bare
  `checkout_issue_branch` is imported but not called from `_spawn_one`.
  Matches the PR's claim.
- `_consult_cmd_and_env` signature claim (issue #2537): `grep -n "def
  _consult_cmd_and_env" -A5 consult.py` shows
  `(skill, cwd, model=None, exclude_core_plugins=..., task_text=...,
  issue=...)` -- no `spec` parameter. Matches.
- `_ROLE_SKILLS[role]` exclusion-removal claim (issue #2507): read
  `pipeline.py` around the cross-family candidate function directly --
  its own in-repo comment states the `_ROLE_SKILLS[role]` exclusion was
  removed because a fixed role->skill table no longer defines "family."
  Independently confirms the PR record's citation of the same removal.
- `_create_workspace_with_signal_guard` call-site claim (issue #2731/
  #2742): read `_spawn_one`'s body directly -- the function calls
  `_create_workspace_with_signal_guard(` from two places, an earlier
  adhoc-task branch and a later one following `origin_cwd = cwd`. The
  fixed test's `body.index(needle, capture_at)` searches forward from
  the capture point, which is exactly what skips the earlier,
  unrelated call. Matches.
- Widened branch/citation regex claim (issue #2576): `grep -n
  'issue-(\d+)/(\[' on-the-record/hooks/approval-gate.sh
  on-the-record/hooks/pr-preflight.sh on-the-record/hooks/contract-guard.sh`
  shows all three hooks already use `[^/]+`, not `[\w-]+`. Matches the
  fixed test's new pinned literal.

derived: `for sha in 96699800 2cc3cf4f e1f390ab b4d05522 2cc6d108
a4d85dbb 0879f12a 6ae45558 e7cd06c2 082bfd7b; do git cat-file -t $sha;
done` -- all ten return `commit`, confirming every hash the diagnosis
table cites exists in this repo's history and none is fabricated.

## What did not work

None.

## Upstream basis

- Issue #3091: canonical: `gh issue view 3091` (read in full this
  session).
- PR #3111, head commit `6df0350a`: canonical: `gh pr view 3111`,
  `gh pr diff 3111`, and a local `git worktree` checkout of
  `pr-3111-review`.
- PR #3111's own record (path present only on the `pr-3111-review`
  worktree/branch, untracked on this session's own branch): canonical:
  read in full this session, cross-checked against source rather than
  cited as ground truth.
- `origin/main` at `7ee16612` (current, includes merged PR #3089):
  canonical: separate `git worktree` checkout, used to confirm the
  `tests/` gap is branch-timing rather than a regression.

## Open findings

None.

## Next steps

None -- `loop_state: landed`.

skill-verdict: work-in-english:work-in-english — applied: invoked; whole
session's internal reasoning, tool commands, code/record English kept in
English per the skill (final message to the user is in Korean).
other mounted skills: not triggered
