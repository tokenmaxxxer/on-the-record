kind: current-state-survey
subject: issue-1160
role: execution-observation

## Scope

Observing role: implementation (issue-1160). Session: PR #1164
(canonical: gh pr view 1164 --json commits,files, read this session),
merged commit 6baf542805576cd898b9e668fdf5f15a4d90a67e, sole content
commit cd97d6bc1c0609ee0d93eb3efedbff72f65faa1e. Its own record:
docs/issue-1160/reports/implementation.md (read this session at
cd97d6b via git show). Issue under observation: #1160, step 3 (live
pilot, executed-live acceptance), citing northpole req#1.

## What was read this session

- `gh issue view 1160` (full issue body, requirements, acceptance,
  execution plan) — canonical: gh issue view 1160.
- `gh pr view 1164 --json number,title,body,mergeCommit,commits,files` —
  canonical: gh pr view 1164.
- `git show cd97d6b:docs/issue-1160/reports/implementation.md`
  (implementation's own phase-2 record) — canonical: git show cd97d6b.
- `git show cd97d6b:roles/specs/brand-design.spec.json` (the landed
  spec diff's full content, including `use_when.need_detector`,
  `outcome_mission`, `mission_deliverables`, `verified_by`) —
  canonical: git show cd97d6b:roles/specs/brand-design.spec.json.
- grep across `gates/`, `spawn.py`, `on-the-record/hooks/` for
  `need_detector`/`mission_deliverables`/`outcome_mission`/`use_when`/
  `verified_by` — canonical: the grep commands and outputs below.

## Current state

canonical: git show cd97d6b:docs/issue-1160/reports/implementation.md
("Rationale for deviations" section). Implementation's own record
states plainly: "no live pilot run (fixture repo, role waking,
deliverable landing) was performed in this session — only the spec
declarations themselves were built and are unexecuted until a role
session actually runs against them." Step 3 (this role's task) is
exactly that unexercised leg.

```
$ grep -rn "need_detector" gates/ spawn.py on-the-record/hooks/ 2>/dev/null
(no output)
$ grep -rn "mission_deliverables\|verified_by" gates/quality_bar.py 2>/dev/null
(no output)
$ grep -n "IN_SCOPE_ROLES" -A5 gates/spec_schema_five_activities_test.py
IN_SCOPE_ROLES = [
    "content-design",
    ...  (brand-design, market-analysis absent)
```

canonical: gates/roles_due.py module docstring, read this session (lines
1-17). `roles_due.py` evaluates only `use_when.trigger`, a distinct
field from `use_when.need_detector` — the three pilot specs carry
`need_detector`, not `trigger`, so `roles-due` does not read them
either.

## Derived

derived: grep -rln "need_detector\|mission_deliverables" --include=*.py --include=*.sh .
— result: zero hits outside docs/issue-1160/** (this issue's own
paperwork; canonical: the derived command above, run this session).

## Conclusion carried into the proposal

The landed artifact (PR #1164, canonical: gh pr view 1164) is
declarative JSON text only — three fields on three spec files. No code
path in this repository reads `need_detector`, wakes a role from it, or
checks `mission_deliverables`/`verified_by` against a landed
deliverable. The three-leg live pilot step 3 asks for is being tested
against machinery that does not exist as machinery yet.
