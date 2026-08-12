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

None open. Phase-1's after-proposal hunt finding (missing `.gitignore`
in the write set) was already folded into the approved proposal
(canonical: docs/issue-1102/reports/implementation/hunt-roles-due-obligation-trigger.md,
read this session) before this phase-2 session began.

## Doc placement

- [x] ADR: docs/issue-1102/decisions/2026-08-12-obligation-trigger-predicate.md
- [x] This record: docs/issue-1102/reports/implementation.md
