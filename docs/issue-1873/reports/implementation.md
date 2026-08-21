---
code_under_review:
  - skill-repository/skills/refactoring-legacy-characterization-test-scope/SKILL.md
  - skill-repository/skills/refactoring-legacy-refactoring-step-decomposition/SKILL.md
  - skill-repository/skills/refactoring-legacy-seam-selection/SKILL.md
  - skill-repository/skills/refactoring-legacy-strangler-fig-migration/SKILL.md
  - skill-repository/skills/refactoring-legacy-verification-cadence/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
loop_state: landed
type: delivery
breaking: false
verdict: pass
---

# Implementation record: issue-1873 phase 2 — refactoring-legacy family

subject: issue-1873

## What was done

Applied the frozen procedural-body recipe (basis:
docs/issue-1790/reports/implementation.md, WAVE RECIPE section) to the
5 `refactoring-legacy-*` skills in `tokenmaxxxer/skill-repository`, per
the approved phase-1 proposal (docs/issue-1873/proposals/refactoring-legacy-wave2a.md):

1. Inserted `## Trigger` / `## Procedure` / `## Output shape` between
   each skill's framing paragraph and its `## Rules` heading, with each
   Procedure step citing the rule number(s) it draws on.
2. Rewrote each skill's `description:` from its own new `## Trigger`
   section, keeping the checker's "use when" trigger-marker substring.
3. Appended the 5 skill directory names to
   `scripts/procedure_authored_skills.txt`, alphabetically after the
   risk-management wave's entries (the manifest's current last-committed
   wave — canonical: `git log --oneline -1 -- scripts/procedure_authored_skills.txt`
   in the skill-repository checkout, which showed commit `4b2a372`
   "risk-management family").
4. Committed on branch `issue-1873-procedural-body-refactoring-legacy`
   in the skill-repository checkout (`/tmp/skill-repository`, remote
   `github.com:tokenmaxxxer/skill-repository.git`), commit `d04a348`,
   and opened tokenmaxxxer/skill-repository#26.

## Why

Reuses the recipe frozen by the #1790 pilot verbatim (rule-number
citation, since this family's `## Rules` are already printed-numbered
`1.`/`2.`/... lists — matching the two most recent wave precedents,
secure-coding and risk-management) rather than inventing a new citation
convention, per the proposal's Rationale section.

## Upstream basis

docs/issue-1873/proposals/refactoring-legacy-wave2a.md (approved via
issue comment `APPROVE issue-1873/implementation` by approvers.md
account `JiwonJung94`); docs/issue-1790/reports/implementation.md WAVE
RECIPE section.

## Rationale for deviations

The only session-level friction, not a divergence from the proposal's
build-plan section: the shared `/tmp/skill-repository` checkout carried
another session's uncommitted `partnerships-bd-*` edits concurrently.
The adaptation was mechanical — staging exactly this issue's 6 files
via the git index/hash-object instead of a blanket `git add`, to avoid
committing or discarding the other session's uncommitted work — and is
logged inline per the deviation-loop directive in
`docs/reports/deviation-log.md`. See Check 4 below for the resulting
scoped diff.

## Checks (executed live, skill-repository checkout, commit d04a348)

### Check 1 — manifest checker

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
exit: 0
```

### Check 2 — rule-retention sweep

canonical: live shell loop output pasted below (this session), diffing
`git show HEAD~1:<path>` against the post-change working file for each
of the 5 files in the skill-repository checkout — every pre-change
numbered `## Rules` line's leading substring confirmed present
verbatim in the post-change file.

```
--- skills/refactoring-legacy-characterization-test-scope/SKILL.md ---
OK: all pre-change rule lines retained
--- skills/refactoring-legacy-refactoring-step-decomposition/SKILL.md ---
OK: all pre-change rule lines retained
--- skills/refactoring-legacy-seam-selection/SKILL.md ---
OK: all pre-change rule lines retained
--- skills/refactoring-legacy-strangler-fig-migration/SKILL.md ---
OK: all pre-change rule lines retained
--- skills/refactoring-legacy-verification-cadence/SKILL.md ---
OK: all pre-change rule lines retained
```

### Check 3 — full-tree checker

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
exit: 0
```

### Check 4 — `git diff --stat` (scoped, commit d04a348 vs HEAD~1)

canonical: `git diff --stat=200 HEAD~1 HEAD` executed live in the
skill-repository checkout, this session — output pasted below, listing
only the 5 family skill paths plus the manifest.

```
$ git diff --stat=200 HEAD~1 HEAD
 scripts/procedure_authored_skills.txt                             |  5 +++++
 skills/refactoring-legacy-characterization-test-scope/SKILL.md    | 35 ++++++++++++++++++++++++++++++++++-
 skills/refactoring-legacy-refactoring-step-decomposition/SKILL.md | 34 +++++++++++++++++++++++++++++++++-
 skills/refactoring-legacy-seam-selection/SKILL.md                 | 37 ++++++++++++++++++++++++++++++++++++-
 skills/refactoring-legacy-strangler-fig-migration/SKILL.md        | 37 ++++++++++++++++++++++++++++++++++++-
 skills/refactoring-legacy-verification-cadence/SKILL.md           | 34 +++++++++++++++++++++++++++++++++-
 6 files changed, 177 insertions(+), 5 deletions(-)
```

## Empty state

Not applicable — the survey (canonical:
docs/issue-1873/reports/implementation/survey.md, "Body shape" section)
found none of the 5 skills already carried
`## Trigger`/`## Procedure`/`## Output shape`, so no skill was a no-op.

## What did not work

None.

## Open findings

None.

## Deliverables

- tokenmaxxxer/skill-repository#26 (commit `d04a348` on
  `issue-1873-procedural-body-refactoring-legacy`): the 5
  `refactoring-legacy-*` skill bodies + manifest extension.
- This record.
