# Current-state survey — execution-observation for issue #1490

## Scope

Observed: role `implementation`, issue #1490, branch `issue-1490/implementation`,
PR #1494.
canonical: `gh pr view 1494 --json number,title,state,mergedAt,commits,baseRefName,headRefName,body`
(this turn) — state MERGED, mergedAt 2026-08-14T13:45:09Z, baseRefName main,
headRefName issue-1490/implementation, single commit 379afcc2.

Read this session, fresh-eyes order: `gh pr diff 1494` (full diff, read this
turn) before treating either file inside it as narrative — the diff and the
two files' content are the same read here, since the PR adds exactly those
two new files with no separate framing commit. Also read this session:
`gh issue view 1490 --json comments` (all 6 comments), `git show
origin/main:docs/specs/approvers.md`, `git show origin/main:pytest.ini`,
`git show origin/main:requirements-dev.txt` (path absent), `git ls-tree
origin/main docs/issue-1490/ -r`, `gh pr view 1494 --json comments,reviews`
(both empty).

Diff hunks read (PR #1494, commit 379afcc2): the entire diff — two new files,
no modification hunks — `docs/issue-1490/proposals/parallel-test-suite.md`
(+153 lines) and `docs/issue-1490/reports/implementation/survey.md` (+98
lines). canonical: `gh pr diff 1494` (this turn) — no other file appears in
this PR's diff.

code_under_review:
- docs/issue-1490/proposals/parallel-test-suite.md
- docs/issue-1490/reports/implementation/survey.md

## What the observed PR actually contains

PR #1494's single commit adds only two documents: the implementation role's
own current-state survey and its phase-1 proposal for issue #1490 (parallel
pytest run, `slow`-tier marker, per-test isolation fixes, <300s target).
canonical: `gh pr diff 1494` (this turn) — no code, config, or
dependency-manifest file is in this diff.

## What main carries today

canonical: `git ls-tree origin/main docs/issue-1490/ -r` (this turn) — only
the two phase-1 files above exist under `docs/issue-1490/` on main; a
phase-2 delivery record at reports/implementation.md (a path the proposal's
own frontmatter `files:` list commits to producing, per PR #1494's diff) is
not among them.

canonical: `git show origin/main:pytest.ini` (this turn) — full file is still
just `python_functions = test_* t_*` / `norecursedirs = runs`; no `addopts`,
no `markers`. canonical: `git show origin/main:requirements-dev.txt` (this
turn) — path does not exist. None of the proposal's "What will be done"
steps 1-8 (dependency manifest, pytest.ini changes, isolation fixes, `slow`
marker, delivery record) are present on main.

## Approval-flow evidence

canonical: `gh issue view 1490 --json comments` (this turn) — comment
https://github.com/tokenmaxxxer/on-the-record/issues/1490#issuecomment-5294013565
(2026-08-14T13:44:53Z, author JiwonJung94) is the exact string `APPROVE
issue-1490/implementation`. canonical: `git show
origin/main:docs/specs/approvers.md` (this turn) — lists JiwonJung94 and
jjongkwann. canonical: `gh pr view 1494 --json commits` (this turn) — PR
#1494's sole commit is co-authored by JiwonJung94 and Claude — author and
approver are the same human account (single-account mode).

canonical: `gh issue view 1490 --json comments` (this turn) — comment
https://github.com/tokenmaxxxer/on-the-record/issues/1490#issuecomment-5294057947
(2026-08-14T13:49:21Z) is a `stranded-relay` message: "pull request create
failed: GraphQL: No commits between main and issue-1490/implementation …
The implementation-role session's work stopped here … Needs human
intervention." This posted 4 minutes after PR #1494's mergedAt
(2026-08-14T13:45:09Z, cited above) and 4 minutes after the APPROVE comment
(13:44:53Z, cited above). canonical: `gh issue view 1490 --json comments`
(this turn) — the session-end comment that follows
(issuecomment-5294058499, 13:49:24Z) points back at PR #1494's own URL, not a
different PR. canonical: `gh pr list --search "issue-1490" --state all`
(this turn) — returns only PR #1494; no second PR exists for this issue.

## Gaps for the proposal to resolve

- Whether the phase-2 build for issue #1490 (pytest-xdist install, isolation
  fixes, `slow` marker, delivery record, timing measurements) ever executed
  anywhere, given main's current state (cited above) shows none of it and
  the only PR for this issue carries only the phase-1 proposal.
- canonical: `gh issue view 1490 --json comments` and `gh pr list --search "issue-1490" --state all` (both this turn) — whether the stranded-relay failure ("No commits between main and issue-1490/implementation") means the phase-2 session did no work at all, or did work never committed before the branch merged as phase-1-only, cannot be told apart: no phase-2 commit, local record, or second PR exists to read this session.
- Which verdict levels the phase-2 record can support, and against what
  evidence each will be checked: an outcome-level verdict against main's
  current file state (pytest.ini, requirements-dev.txt, docs/issue-1490/
  tree — all read this session, cited above) compared to issue #1490's four
  Requirements and three Acceptance items; a trajectory-level verdict against
  the phase-1 evidence already read this session (scouted-when-required via
  the survey's own canonical-tagged commands, surveyed-before-proposing via
  the single-commit ordering, approved-by-human via the APPROVE comment cited
  above); a step-level finding, if any, bounded to mode=asserted since its
  only source is the stranded-relay comment's own text (cited above), not
  independently re-derivable without re-executing the phase-2 session, which
  this role is prohibited from doing.
