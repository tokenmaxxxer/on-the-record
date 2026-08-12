Subject: issue-1088

## Current-state survey

`gates/roles_due.py` (function `roles_due`) computed "due" as: trigger
matches AND `docs/<subject>/reports/<record_role>.md` is absent. Bare
file existence suppressed the trigger forever once any record — however
old — existed at that path, per the #1005 hunt cited in the issue
(docs/issue-1005/reports/implementation/2026-08-12-hunt-secure-coding-routing-fix.md,
before-landing stance 0).

Write set actually touched:
- `gates/roles_due.py` — scope `record_absent_for` to the triggering diff.
- `gates/test_roles_due.py` — regression test per the issue's acceptance.

Records in this repo carry no `commit_sha`/diff-range frontmatter field
that's guaranteed present across all role kinds (only `implementation.md`
records carry `code_under_review:`, per the record-shape directive, and
even that is a file list, not a commit sha) — so frontmatter cannot be
relied on as the scoping key. Git history is: every file under version
control already has commit ancestry, and `gates.py` (function
`changed_files`) already resolves the diff against `BASE` — the same
mechanism `roles_due` already uses for matching. Scoping against commit
ancestry reuses that same substrate instead of inventing a second one.

### Alternatives considered

1. **Frontmatter field on the record naming the commit/diff it covers**
   (e.g. `covers_sha:`), compared against the diff's head commit. Rejected:
   requires every future record-writer (many roles, some outside this
   issue's write set) to remember to stamp a new field — a silent-miss
   surface — and doesn't help the many records that already exist without
   it (the issue's own "stale record" case).
2. **mtime comparison** (filesystem modification time) between the record
   file and the matched file. Rejected: mtimes are not preserved across
   `git clone`/`checkout` and are meaningless in CI checkouts, which is
   exactly where `roles_due` runs.
3. **Commit-ancestry comparison** (chosen): compare the last commit that
   touched the *matched* path against the last commit that touched the
   *record* path, using `git merge-base --is-ancestor`. Survives clones
   and doesn't require any record-writer to opt in — every record already
   has commit history the moment it's committed.

## What will be done (see proposal)
