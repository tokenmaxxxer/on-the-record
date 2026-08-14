---
subject: issue-1102
---

# Current-state survey — execution-observation for issue-1102

## Scope

Observing role: implementation. Session/branch observed:
`issue-1102/implementation`.

canonical: `gh issue view 1102` (read this session) — Issue #1102 is
"wire roles/specs trigger for failing landing-obligations so a failing
verification auto-routes a specialist".

canonical: `gh pr view 1109 --json body,commits,reviews,mergeCommit,files`
(read this session) — PRs under observation: phase-1 PR #1107 (merged
`2c428708b61d28b001ef8402f8e0a67588d9fc7f`) and phase-2 delivery PR #1109
(merged `a961deaecbf414287832de59c2a3640055b8ecab`).

What was read this session to arrive at this scope, in order:
`gh issue view 1102` (issue body + comment thread), `gh pr view 1107
--json body,reviews,mergeCommit`, `gh pr view 1109 --json
body,commits,reviews,mergeCommit,files`, then the diff itself —
`git diff 2c428708..a961deaec -- gates/roles_due.py
roles/specs/defect-verification.spec.json` — read before reading the
observed role's own record narrative (`docs/issue-1102/reports/implementation.md`),
per FRESH-EYES ORDERING. Also read: `git show a961deaec:gates/test_roles_due.py`
and `git show a961deaec:docs/issue-1102/reports/implementation/hunt-roles-due-obligation-trigger.md`.

Diff hunks read: the two hunks in `gates/roles_due.py` (new
`_obligations_dir`/`_matching_obligation` functions, and the
`_trigger_matches`/`roles_due` call-site change) and the one hunk in
`roles/specs/defect-verification.spec.json` (the `trigger` block
addition).

## What exists

canonical: `git diff 2c428708..a961deaec -- gates/roles_due.py
roles/specs/defect-verification.spec.json` (read this session) —

- `gates/roles_due.py`: `_matching_obligation` predicate reads
  `.landing-obligations/*.json` directly and feeds
  `record_absent_for`/commit-ancestry suppression unchanged (diff hunk,
  PR #1109).
- `roles/specs/defect-verification.spec.json`: `use_when.trigger` gained
  `{"obligation_status": ["failing"], "record_absent_for":
  "defect-verification"}` (diff hunk, PR #1109).

canonical: `git show a961deaec:gates/test_roles_due.py` (read this
session) — `gates/test_roles_due.py` carries three new cases
(`_t6`/`_t7`/`_t8`) matching the issue's three acceptance checks (failing
obligation → due, resolved → not due, empty state → not due).

canonical: python3 gates/test_roles_due.py (executed live this session,
fenced output below) —
```
$ python3 gates/test_roles_due.py
PASS: no trigger fires -> empty due list
PASS: matching path with no record -> due
PASS: matching path but record already exists -> not due
PASS: stale record predating a new qualifying diff -> still due (issue #1088)
PASS: content pattern match fires
PASS: failing obligation for the branch's subject -> mapped role due
PASS: resolved obligation -> not due
PASS: no .landing-obligations/ directory at all -> not due (empty state)
PASS: format_report renders one line per due role, empty list -> no lines
```
canonical: python3 gates/test_roles_due.py (executed live this session,
fenced output above) — all 9 fenced lines above read `PASS`, including
the 3 acceptance-mapped ones (`_t6`, `_t7`, `_t8`).

canonical: `git show a961deaec:docs/issue-1102/reports/implementation/hunt-roles-due-obligation-trigger.md`
(read this session) — the observed role's own warrant-hunt log discloses
an open composition finding (an uncommitted stand-in `docs/<subject>/reports/<role>.md`
file suppresses a real failing obligation, because `_last_commit_hash` on
the gitignored `.landing-obligations/*.json` path is always `None`),
filed as a follow-up rather than fixed (commit `e360041fdd6a`, "Filed as
a follow-up per SCOPE-EXCEEDED").

canonical: `gh issue view 1102 --json comments` (read this session) —
issue #1102's comment thread carries an exact-string approval:
"APPROVE issue-1102/implementation", posted 2026-08-12T08:08:47Z by
`JiwonJung94`.

canonical: `docs/specs/approvers.md` (read this session) — lists
`JiwonJung94` and `jjongkwann`; `JiwonJung94` is also PR #1109's author
(`gh pr view 1109 --json commits`, read this session), so the approval is
single-account mode.

## Proposal to follow

The phase-1 proposal for this observation session is committed alongside
this survey, under docs/issue-1102/proposals/, in the same phase-1
commit.
