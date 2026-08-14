# Current-state survey — issue #1005 execution observation

## Scope statement

canonical: `gh pr view 1086 --json number,title,body,mergedAt,mergeCommit,commits,reviews,files`
run this session — output showed merge commit
`fae380c75087e446b8cd8eb1347cc9da2b6161fa`, mergedAt
`2026-08-12T07:18:25Z`.

Observed: the **implementation** role's work on issue #1005 ("secure-coding
routing gap: board_condition never triggers"), branch
`issue-1005/implementation`.

canonical: `gh pr list --state all --search "1005" --json number,title,state,headRefName,mergedAt,url`
run this session — three PRs on that branch, all `state: MERGED`:
- PR #1007 — phase-1 proposal PR.
- PR #1079 — phase-1 delivery of proposal + survey + hunt record,
  mergedAt `2026-08-12T07:09:13Z`.
- PR #1086 — phase-2 delivery, "issue-1005 phase-2: secure-coding
  routing-gap fix", mergedAt `2026-08-12T07:18:25Z`.

This scope was built from reading PR #1086's diff and commit list
directly this session (`gh pr view 1086 --json ...,commits,files`, `gh pr
diff 1086`) before reading its own record narrative — the record file
`docs/issue-1005/reports/implementation.md` appears as an added file
inside that same diff, so its content was first seen as diff content, not
as a separately-fetched self-report.

## What was read this session

canonical: `gh issue view 1005` run this session — issue body, acceptance
criteria, requirement `northpole req#5`, and all 8 issue comments,
including two `APPROVE issue-1005/implementation` comments from
`JiwonJung94`.

canonical: `docs/specs/approvers.md` (file read this session) —
`JiwonJung94` and `jjongkwann` are the two listed approvers.

canonical: `gh pr view 1086 --json ...,commits,reviews,files` run this
session — commit SHAs `65d8b4bd`, `e6ea9bc9`, `a3c3c554`, `eab95d24`;
`reviews: []`; files changed: `docs/issue-1005/reports/implementation.md`
(new), `docs/issue-1005/reports/implementation/2026-08-12-hunt-secure-coding-routing-fix.md`
(modified), `docs/issue-1005/reports/implementation/deviation-log.md`
(new), `gates/test_secure_coding_routing.py` (new),
`roles/specs/secure-coding.spec.json` (modified, +16/-1).

canonical: `gh pr diff 1086` run this session — full diff of the five
files above, read in full (hunks listed below).

canonical: `gh pr view 1079 --json number,title,body,mergedAt,files` run
this session — files: `docs/issue-1005/proposals/secure-coding-routing-fix.md`,
`docs/issue-1005/reports/implementation/2026-08-12-hunt-secure-coding-routing-fix.md`,
`docs/issue-1005/reports/implementation/survey.md`; body states "Part of
#1005."; no code/gate files touched.

canonical: `gh pr view 1007 --json number,title,reviews,mergedAt` run
this session — `reviews: []`.

canonical: this session's own live run — `python3
gates/test_secure_coding_routing.py`, result:
```
PASS: seeded security-relevant diff -> secure-coding is due
PASS: seeded unrelated diff -> secure-coding is not due
```

canonical: this session's own live run — `python3 gates/test_roles_due.py`,
result:
```
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

canonical: `gates/roles_due.py`, `roles_due()` function (file read this
session; `git status` this session showed working tree clean and up to
date with `origin/main`) — confirms `record_absent_for` now does
commit-ancestry comparison via `_commit_at_or_after`, not bare
file-existence.

canonical: `gh pr view 1093 --json number,title,body,mergedAt` run this
session — PR #1093 ("issue-1088: scope roles_due record_absent_for to
triggering diff"), mergedAt `2026-08-12T07:31:21Z`, body states it fixes
the gap "found by the #1005 hunt."

## Diff hunks read (admissible for step-level citation)

canonical: `gh pr diff 1086` run this session — all hunks in PR #1086's
diff:
- `roles/specs/secure-coding.spec.json` +16/-1 (adds `use_when.trigger`:
  `path_patterns`, `content_patterns`, `record_absent_for`).
- `gates/test_secure_coding_routing.py` +107 (new file, two seeded-diff
  cases against the real spec).
- `docs/issue-1005/reports/implementation.md` +75 (new file, the
  observed role's own record).
- `docs/issue-1005/reports/implementation/2026-08-12-hunt-secure-coding-routing-fix.md`
  +31 (before-landing hunt section appended, documenting a
  `record_absent_for` file-existence-only gap).
- `docs/issue-1005/reports/implementation/deviation-log.md` +3 (new,
  logs the hunt finding as `filed`).

## What was NOT read as evidence

canonical: `gates/roles_due.py` (file read this session) — read only to
confirm today's state (the #1088 fix landed after #1086), not as evidence
of what the #1005 implementation role itself did: per role directive,
src/ shows what exists now, not what that role decided. The
`record_absent_for` gap at #1086's merge time is evidenced by #1086's own
before-landing hunt file (diff hunk above), not by reading
`roles_due.py` as it existed at that merge.
