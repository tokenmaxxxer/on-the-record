---
status: proposed
files:
  - /tmp/skill-repository/skills/data-modeling-datavault/SKILL.md
  - /tmp/skill-repository/skills/data-modeling-structure/SKILL.md
  - /tmp/skill-repository/skills/data-modeling-kimball/SKILL.md
  - /tmp/skill-repository/skills/data-modeling-inmon/SKILL.md
  - /tmp/skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal — data-modeling family, wave 2a procedural-body authoring

Subject: issue-1906

Scout note: this is a mechanical recipe-application task, not a
product/design deliverable — the applicable "field" is the frozen
recipe itself (#1790) and its 4 already-landed wave 2a applications
(capacity-planning, localization, brand-design, marketing), which the
survey (docs/issue-1906/reports/implementation/survey.md) already read
directly. No external web scouting applies; skip condition: the spec
leaves no design decision open (the recipe is frozen verbatim, and
every wave 2a family so far has applied it identically with zero
family-specific deviation).

## Request

Author procedural bodies (`## Trigger` / `## Procedure` / `## Output
shape`) for the 4 `data-modeling-*` skills in
`tokenmaxxxer/skill-repository`, per the frozen wave recipe from
#1790, and append the 4 names to
`scripts/procedure_authored_skills.txt`. Deliver as a skill-repository
PR plus this issue's phase-2 record, with zero rule-line loss and the
four required checks pasted live.

## Constraints

- Recipe is frozen verbatim (#1790): `## Trigger` / `## Procedure`
  (steps citing rule numbers) / `## Output shape` inserted above the
  existing `## Rules` section; `description:` rewritten from the new
  `## Trigger` text; zero edits to existing rule lines.
- Write set is exactly the 4 `data-modeling-*` SKILL.md files plus the
  manifest — no checker-logic changes, no hooks, no other family.
- Every pre-existing rule line must survive unchanged (rule-retention
  sweep required as evidence).
- Both checker invocations (bare, and with `--manifest
  scripts/procedure_authored_skills.txt`) must exit 0 before and after.

## Rationale

Considered re-deriving the section wording from first principles for
each of the 4 skills (writing fresh Trigger/Procedure/Output-shape
prose without anchoring to the marketing-family precedent's exact
phrasing patterns) — rejected because #1790 froze the recipe precisely
to keep wording style, section placement, and the `(rule N)` citation
convention uniform across all wave 2a families; deriving fresh prose
per family reintroduces the per-family style drift the recipe was
frozen to prevent, and the survey found no data-modeling-specific
reason (frontmatter shape, rule structure) that would justify deviating
from the pattern the 4 already-landed families used.

Considered treating any of the 4 skills as Shape A (already
partially procedure-shaped, handled as a no-op per the issue's empty
state) — rejected because the survey's direct file reads confirmed all
4 currently have only a `## Rules` section with no `## Trigger`/
`## Procedure`/`## Output shape` present; none qualify for the no-op
path.

## What will be done

1. For each of the 4 skills, read the full `## Rules` list, then write
   `## Trigger` (when to apply this skill), `## Procedure` (numbered
   steps, each citing the rule number(s) it operationalizes), and
   `## Output shape` (what a call to this skill should produce),
   inserted directly above the existing `## Rules` section — matching
   the exact section order and citation convention confirmed in the
   marketing-family precedent (commit 1b04844).
2. Rewrite each skill's `description:` frontmatter line from its own
   newly-authored `## Trigger` text (not copied from another skill).
3. Append the 4 skill directory names
   (`data-modeling-datavault`, `data-modeling-structure`,
   `data-modeling-kimball`, `data-modeling-inmon`) to
   `scripts/procedure_authored_skills.txt`.
4. Run and paste, live from the skill-repository checkout: the
   rule-retention sweep (diff of pre- vs. post-change rule lines,
   confirming zero loss), `python3 scripts/check_skill_conformance.py`
   (bare), `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt`, and `git diff --stat`
   scoped to the 4 SKILL.md paths + manifest.
5. Open a skill-repository PR carrying the 4-file + manifest diff, and
   write this issue's phase-2 record
   (`docs/issue-1906/reports/implementation.md`) with the four pasted
   check outputs and the PR link.

## Out of scope

- Any family other than data-modeling.
- Any change to `scripts/check_skill_conformance.py` or its checking
  logic.
- Any change to hooks, CI config, or other operational-surface files.
- Editing any existing rule line's content or numbering.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py` exits 0 post-change.
- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 post-change and lists
  the 4 new names as covered.
- The rule-retention sweep shows every pre-change rule line for all 4
  skills present, unchanged, post-change.
- `git diff --stat` in the skill-repository checkout shows only the 4
  `skills/data-modeling-*/SKILL.md` paths and
  `scripts/procedure_authored_skills.txt`.
- A skill-repository PR exists carrying that diff.
