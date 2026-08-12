---
code_under_review:
  - gates/roles_due.py
  - gates/test_roles_due.py
  - roles/specs/defect-verification.spec.json
  - .gitignore
type: feature
breaking: false
# canonical: python3 gates/test_roles_due.py — result: all cases passed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-1102

## What was done

canonical: docs/issue-1102/proposals/2026-08-12-roles-due-obligation-trigger.md (read this session) — approved via the issue-level comment `APPROVE issue-1102/implementation` (gh issue view 1102 --comments, read this session)

Wired the roles/specs/*.spec.json obligation trigger per the approved
phase-1 proposal:

- gates/roles_due.py: added `_matching_obligation` — a new predicate
  scanning `.landing-obligations/*.json` for a record whose `status` is
  in `trigger["obligation_status"]` and whose `issue` field equals the
  current branch's subject. `_trigger_matches` now takes a `subject`
  parameter and checks this predicate first, returning the same
  `(reason, matched_path)` shape the existing path/content predicates
  return, so `roles_due()`'s existing `record_absent_for`/commit-ancestry
  suppression logic applies unchanged.
- roles/specs/defect-verification.spec.json: `use_when` gained a
  `trigger` block — `{"obligation_status": ["failing"],
  "record_absent_for": "defect-verification"}`.
- .gitignore: added `.landing-obligations/`, mirroring the existing
  `.reexecution/` entry, so obligation records stay untracked worktree
  state (the ADR's stated dependency).
- docs/issue-1102/decisions/2026-08-12-obligation-trigger-predicate.md
  (uncommitted new file at write time; lands with this commit): ADR
  recording the file-format-coupling decision — reading
  .landing-obligations/*.json directly instead of importing the
  obligation-writer module named in PR #1101's proposal step 4, which
  does not exist in this tree.
- gates/test_roles_due.py: three new cases — failing obligation for
  the branch's subject surfaces `defect-verification` as due; a
  `resolved` obligation does not; no `.landing-obligations/` directory
  at all (empty state) does not.

canonical: python3 gates/test_roles_due.py — result: all cases passed (executed live this session, fenced output below)

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

## Why

northpole req#5, per issue #1102 — scoped out of PR #1101's proposal
(step 4 / Out of scope) as a named follow-up. This delivers exactly the
approved phase-1 proposal's write set and design, no more.

## Upstream / basis

Based on: docs/issue-1102/proposals/2026-08-12-roles-due-obligation-trigger.md

## What did not work

None.

## Open findings

canonical: docs/issue-1102/reports/implementation/hunt-roles-due-obligation-trigger.md (read this session)

Phase-1's after-proposal hunt finding (missing `.gitignore` in the
write set) was already folded into the approved proposal before this
phase-2 session began.

The before-landing hunt (stance 0) surfaced one new, unresolved
finding: an uncommitted (never `git add`ed) `docs/<subject>/reports/
<role>.md` stand-in file makes `roles_due()`'s commit-ancestry
"covers" check treat a real `failing` `.landing-obligations/*.json`
obligation as already resolved, because an obligation match's
`matched_path` is always untracked (`_last_commit_hash` always returns
`None` for it), so the `trigger_hash is None: covers = record_hash is
None` branch — correct for the path/content predicates it was written
for — silently defeats the new obligation predicate whenever the
suppression record is also merely uncommitted rather than genuinely
absent. Addressing this needs a design call (an obligation-specific
covers rule) not specified in the approved proposal, so it stays
outside this phase-2's frozen write set — reported here for the next
proposal/role to act on, not built inline.

## Next steps

A follow-up proposal should change the obligation-status covers check
in `gates/roles_due.py` so an uncommitted candidate record no longer
counts as "covers" for an obligation-kind trigger (whose `matched_path`
is inherently always untracked) — see the before-landing finding above
for the repro.

## Resolution path

File as a follow-up issue referencing this record and the hunt file
above; the fix belongs to whichever role next touches
`gates/roles_due.py`'s obligation predicate.

## Rationale for deviations

The build itself followed the approved proposal's planned items
one-for-one, with no swapped alternative and no widened write set.
The before-landing hunt finding noted above under `## Open findings`
surfaced a pre-existing suppression-logic gap (the `trigger_hash is
None: covers = record_hash is None` branch, written for the
path/content predicates) that the new obligation predicate now
exposes; addressing it needs a design call the approved proposal did
not make, so it is filed as a follow-up rather than built here, per
the SCOPE-EXCEEDED rule (finish what the proposal covers, stop,
report — never widen mid-build).

## Doc placement

- [x] ADR: docs/issue-1102/decisions/2026-08-12-obligation-trigger-predicate.md
- [x] This record: docs/issue-1102/reports/implementation.md
