---
status: approved
files:
  - gates/roles_due.py
  - gates/test_roles_due.py
---

## Request

`roles_due.py`'s `record_absent_for` check treats presence of ANY
existing role record as "not due", so a stale record from an earlier,
unrelated review permanently suppresses re-surfacing the role for new
qualifying diffs on the same issue. Scope the check to the triggering
diff instead of bare record existence.

## Constraints

- No new dependency, no schema/frontmatter change to existing records —
  the fix must work against records that already exist with no
  scoping metadata.
- Must not regress the existing "record covers this diff -> not due"
  case (gates/test_roles_due.py's existing cases).
- Diff resolution reuses `gates.py`'s existing `BASE`-relative
  `changed_files()` mechanism `roles_due` already depends on.

## Rationale

Chosen: compare commit ancestry (`git merge-base --is-ancestor`) between
the last commit touching the matched trigger path and the last commit
touching the record path — the record "covers" the diff only if it was
written at or after the triggering commit.

Rejected alternative: add a `covers_sha:`/`covers_commit:` frontmatter
field to records and compare against the diff head. Rejected because it
requires every record-writer across all roles to remember to stamp a new
field (a silent-miss surface), and does nothing for records that already
exist without it — which is exactly the issue's own "stale record" case.

Also rejected: raw filesystem mtime comparison — mtimes don't survive
`git clone`/fresh checkout, which is where this gate runs (CI).

## What will be done

- Add `_last_commit_hash(root, path)` and `_commit_at_or_after(root,
  earlier, later)` helpers to `gates/roles_due.py` using `git log` /
  `git merge-base --is-ancestor`.
- Change `_trigger_matches` to also return the matched path (needed to
  look up its commit).
- In `roles_due()`, when a record file exists, only skip (treat as "not
  due") when the record's last commit is at-or-after the triggering
  file's last commit; otherwise still report as due.
- Uncommitted (working-tree-only) trigger or record content keeps the
  prior conservative behavior (not due) rather than guessing.
- Add a regression test to `gates/test_roles_due.py`: an older record
  followed by a new commit to the matched path must still surface as
  due.

## Out of scope

- Adding scoping metadata to the record format itself.
- Any role spec other than the ones already covered by
  `gates/test_roles_due.py`'s scratch fixtures.

## How you'll know it worked

`python3 gates/test_roles_due.py` passes, including the new case
asserting a stale record does not suppress a genuinely new qualifying
diff, while the existing "record already covers this diff -> not due"
case still passes unchanged.

## Accumulation

This change is not accumulation-shaped: it is a single self-contained
logic fix inside one function (`roles_due()`) plus two small private
helpers in the same file, not an inline `subprocess`/`gh` call added to
a growing list of call sites, and it touches no per-role repeated file
(e.g. `roles/*.json`) with a copy-pasted one-line edit. If this same kind
of "scope a check to the triggering diff" fix recurs elsewhere, the
`_last_commit_hash`/`_commit_at_or_after` helpers added here are already
factored for reuse rather than re-inlined.
