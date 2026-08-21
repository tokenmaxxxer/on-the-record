---
status: proposed
files:
  - docs/issue-1809/reports/implementation.md
  - /tmp/skill-repository/skills/release-engineering-branching-release-strategy/SKILL.md
  - /tmp/skill-repository/skills/release-engineering-changelog-entry-categorization/SKILL.md
  - /tmp/skill-repository/skills/release-engineering-deployment-rollout-strategy/SKILL.md
  - /tmp/skill-repository/skills/release-engineering-error-budget-policy/SKILL.md
  - /tmp/skill-repository/skills/release-engineering-postmortem/SKILL.md
  - /tmp/skill-repository/skills/release-engineering-readiness-checklist/SKILL.md
  - /tmp/skill-repository/skills/release-engineering-release-cadence-and-toil/SKILL.md
  - /tmp/skill-repository/skills/release-engineering-rollback-and-recovery/SKILL.md
  - /tmp/skill-repository/skills/release-engineering-rollout-plan/SKILL.md
  - /tmp/skill-repository/skills/release-engineering-semver-bump-selection/SKILL.md
  - /tmp/skill-repository/scripts/procedure_authored_skills.txt
---

## Request

Apply the frozen wave recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 10 `release-engineering-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger` / `## Procedure` /
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt` with the 10
names, keep every pre-existing content line, and deliver as a
skill-repository PR plus this role's record, scoped to only these 10
skill files + the manifest.

## Constraints

- Zero rule-line/content loss (issue requirement 1 + record-shape
  frontmatter's `## What did not work` accounting).
- No path outside the 10 family skills + manifest touched (issue
  requirement 2, `git diff --stat` must prove it).
- No checker-logic changes, no hook changes (issue non-goals).
- Guidance-only: the authored sections steer usage, they do not change
  what each skill's Rules/field-list/state-machine content resolves.
- The manifest check requires exactly the 3 headings
  (`## Trigger`/`## Procedure`/`## Output shape`, any order) per
  `check_skill_conformance.py` — nothing else is mechanically enforced
  about Procedure's internal citation style.

## Rationale

The survey (docs/issue-1809/reports/implementation/survey.md) found the
10-skill family is not uniform: 6 skills ("Shape A":
`branching-release-strategy`, `changelog-entry-categorization`,
`deployment-rollout-strategy`, `release-cadence-and-toil`,
`rollback-and-recovery`, `semver-bump-selection`) already match the
pilot's `## Rules`-with-numbered-rules structure the recipe was written
against, but the other 4 ("Shape B": `error-budget-policy`,
`postmortem`, `readiness-checklist`, `rollout-plan`) are an older,
structurally different convention — no `## Rules` heading, no numbered
rule lines, fixed narrative/state-machine headings instead (per-SLI
field lists, required trigger/section criteria, per-state working
sections, per-step rollout stages).

Two alternatives were considered for Shape B and rejected, for the same
reasons the wave-2a proposal gave when it hit the identical split in the
`technical-feasibility` family:

1. **Add a `## Rules` section to each Shape-B skill so the recipe's
   "cite rule number(s) from `## Rules`" applies uniformly across all
   10.** Rejected: this invents new rule-numbered structure the current
   content does not have, well past "guidance-only" — it would
   restructure each skill's actual content rather than add a navigation
   layer on top of it, and risks silently changing what each step
   resolves.
2. **Skip the 4 Shape-B skills this wave and treat them as a follow-up
   wave, delivering only the 6 Shape-A skills against this issue.**
   Rejected: the issue's requirement 1 is explicit — "All 10
   release-engineering-* skills" — and the acceptance check counts all
   10 into the manifest; splitting silently would under-deliver against
   a named, countable requirement without the issue's approval to narrow
   scope.

Chosen instead (matching the wave-2a precedent, since it is the same
Shape A/B split recurring in a second family): apply the recipe's
headings and manifest/description steps identically to all 10, but let
`## Procedure`'s per-step citations point at rule numbers for the 6
Shape-A skills (recipe verbatim) and at each skill's own existing named
sections (e.g. `## Fields, per SLI`, `## Required sections`, `## The
state file`, `## What it asks the user for`) for the 4 Shape-B skills —
the citation target changes to match what each skill actually has, while
the mechanically-checked 3 headings, the description rewrite, and the
manifest entry apply uniformly. This keeps the wave inside the issue's
stated scope (all 10, guidance-only, zero content loss) without
inventing structure Shape B doesn't have, and reuses an already-approved
resolution rather than re-litigating it for a second family.

## What will be done

1. For each of the 10 skills, insert `## Trigger` / `## Procedure` /
   `## Output shape` between the framing paragraph and the skill's
   existing first structural heading (`## Rules` for Shape A; each
   skill's own first narrative heading for Shape B).
   - `## Trigger`: concrete conditions distinguishing the skill from its
     sibling axes in the family (not a title restatement) — derived from
     each skill's current `description:` and framing text.
   - `## Procedure`: ordered steps citing rule numbers (Shape A) or
     existing section names (Shape B) per the Rationale above.
   - `## Output shape`: what the skill produces, derived from each
     skill's existing field-list/state-machine/rule content.
2. Rewrite each `description:` as a sentence derived from that skill's
   authored `## Trigger`, keeping the checker's trigger-marker substring
   ("use when").
3. Append all 10 directory names to `procedure_authored_skills.txt`,
   after the existing 19 entries (incremental, not a replacement).
4. Run, from the skill-repository checkout, in this order: (a)
   `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention sweep — diff pre- and post-change content per skill
   and confirm every pre-existing rule/content line from the survey's
   baseline is still present, (c) `git diff --stat` scoped to the 10
   skill paths + manifest (expect no other paths), (d) `python3
   scripts/check_skill_conformance.py` with no flag (full-tree, expect
   exit 0).
5. Paste all four check outputs plus the `git diff --stat` into
   `docs/issue-1809/reports/implementation.md` (phase 2, after
   approval), matching the pilot record's structure.

## Out of scope

- Any skill outside the 10 `release-engineering-*` family.
- Checker logic changes (`check_skill_conformance.py`) or hook changes.
- Restructuring Shape-B skills' existing content (Rules-block invention,
  section renames/merges) beyond inserting the 3 mandated headings.
- Re-litigating the frozen recipe or the Shape A/B citation resolution
  itself — this wave applies both, as already established by the
  earlier waves.

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 with all 10 new names included and passing.
- The rule-retention sweep shows zero lost lines against the survey's
  pre-change baseline (73 Shape-A rule lines + all Shape-B content
  lines).
- `check_skill_conformance.py` (full-tree, no flag) exits 0.
- `git diff --stat` lists only the 10 SKILL.md paths + the manifest file.
- All four outputs and the diff --stat are pasted live into
  docs/issue-1809/reports/implementation.md per the issue's acceptance
  checks.
