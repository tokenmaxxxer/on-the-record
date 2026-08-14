# Current-state survey — issue-1085 execution-observation

## Scope

canonical: `gh pr list --head issue-1085/implementation` and `gh pr view 1099 --json
number,state,title,body,commits,reviews,mergeCommit,url`, read this session.
Observed: the `implementation` role's phase-1→phase-2 execution on issue #1085, session
`issue-1085/implementation`, delivered as two merged PRs — #1090 (phase-1: proposal) and #1099
(phase-2: delivery), merge commit `47b601e0130b9862e2a9807e5850972af0ded6cf`.

canonical: `gh pr diff 1099 --patch` (654 lines) and `gh pr diff 1090 --patch`, read this
session, before reading the observed role's own record (fresh-eyes ordering).
Diff hunks read (PR #1099, cumulative vs `main`): `gates/record_lint.py` (new
`git_tracked_path_reference_check` function + `lint_record` wiring), `on-the-record/gates/record_lint.py`
(byte-identical mirror), `gates/test_record_lint.py` (three new tests), `on-the-record/hooks/record-claim-guard.sh`
(hook wiring), `docs/specs/acceptance-commands.md`, `docs/issue-1085/proposals/git-tracked-canonical-path-gate.md`,
`docs/issue-1085/reports/implementation/survey.md`, `docs/issue-1085/reports/implementation.md`,
`docs/issue-1085/reports/implementation/deviation-log.md`.

## What was read this session

canonical: `gh issue view 1085`, read this session — full issue body, acceptance criteria,
`northpole req#3` requirement tag.

canonical: `gh api .../contents/docs/issue-1085/reports/implementation.md?ref=47b601e0`, read
this session — the observed role's own record, read only after the diffs above.

canonical: `docs/specs/approvers.md`, read this session — `JiwonJung94` is a listed approver.

canonical: `gh issue view 1085 --json comments`, read this session — an issue comment whose
entire body is exactly `APPROVE issue-1085/implementation`, posted by `JiwonJung94`.

canonical: acceptance: `python3 -m pytest gates/test_record_lint.py -q` (re-run this session
against the merge commit in a fresh clone at `/tmp/pr1099check`), raw output:
```
22 passed, 1 xfailed
```

canonical: derived: `git log --all --diff-filter=A --name-only -- <path>`, run this session for
both paths below (fenced to avoid a live path-reference):
```
docs/issue-1062/reports/consult-log.md
docs/issue-1062/reports/panel/rest-v1-v2.md
```
Both commands returned empty output — neither path was ever committed.

canonical: derived: `git show origin/main:docs/issue-1062/reports/implementation.md`, run this
session — line 27 of `main`'s current copy still cites both paths above.

## Findings surfaced by this survey (not yet verdict language)

1. canonical: PR #1099 diff (`gates/record_lint.py`, `gates/test_record_lint.py` hunks) plus the
   acceptance run above, this session. The delivered gate check
   (`git_tracked_path_reference_check`) and its three tests are present in the diff; the fenced
   raw output above is from re-running that test file this session.

2. canonical: PR #1099 diff (`gates/record_lint.py` and `on-the-record/hooks/record-claim-guard.sh`
   hunks), read this session. `lint_record`'s call site includes `record_rel=rel`; the hook's
   call site includes no third argument — visible directly in both diff hunks.

3. canonical: PR #1099's `diff --git` header list (`gh pr diff 1099 --patch`) plus the
   `git show origin/main:...` run above, this session. The proposal's item 1 (retracting the
   two false citations) is absent from PR #1099's changed files, and `main`'s current copy
   still cites both paths. The observed role's own record discloses this as a blocked deviation
   (board-gate.sh R4 refusing cross-issue writes), not a silent omission.

## What this record does NOT establish yet

Whether finding 2 constitutes an actual functional bug (whether a session could realistically
hit the hook path with a self-citing, uncommitted record file mid-session) is not settled by
reading the diff alone — the proposal below states this as the step-level check to run.
