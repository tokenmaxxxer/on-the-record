---
status: proposed
files:
  - docs/issue-1854/reports/implementation.md
  - /tmp/skill-repository-1854/skills/incident-response-action-item-quality/SKILL.md
  - /tmp/skill-repository-1854/skills/incident-response-blameless-language-editing/SKILL.md
  - /tmp/skill-repository-1854/skills/incident-response-rca-method-selection/SKILL.md
  - /tmp/skill-repository-1854/skills/incident-response-severity-classification-scoping/SKILL.md
  - /tmp/skill-repository-1854/skills/incident-response-timeline-construction/SKILL.md
  - /tmp/skill-repository-1854/skills/incident-response-tool-landscape/SKILL.md
  - /tmp/skill-repository-1854/scripts/procedure_authored_skills.txt
---

## Request

Apply the frozen wave recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 6 `incident-response-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger` / `## Procedure` /
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt` with the 6
names, keep every pre-existing content line, and deliver as a
skill-repository PR plus this role's record, scoped to only these 6
skill files + the manifest.

## Constraints

- Zero content loss (issue requirement 1 + record-shape frontmatter's
  `## What did not work` accounting).
- No path outside the 6 family skills + manifest touched (issue
  requirement 2, `git diff --stat` must prove it).
- No checker-logic changes, no hook changes (issue non-goals).
- Guidance-only: the authored sections steer usage, they do not change
  what each skill's rule content resolves.
- The manifest check requires exactly the 3 headings (`## Trigger`/
  `## Procedure`/`## Output shape`, any order) per
  `check_skill_conformance.py` — nothing else is mechanically enforced
  about the pre-existing `## Rules` heading.

## Rationale

The survey (docs/issue-1854/reports/implementation/survey.md) found
this family is **uniform Shape A** across all 6 skills
(`action-item-quality`, `blameless-language-editing`,
`rca-method-selection`, `severity-classification-scoping`,
`timeline-construction`, `tool-landscape`): every file carries a single
`## Rules` heading with numbered entries and a `rule_count_floor:` in
frontmatter, the pilot's own structure. This differs from the last three
waves' 5-A/1-B splits (wave-2e/2f/2g, evidence-trail Shape-B members) and
from wave-2h's 5-A/1-headless split (`technical-writing-tool-landscape`
had no heading at all): this family's own `tool-landscape` member
already carries the explicit `## Rules` heading, matching the other 5
family members, and no `-research-log` (Shape-B) member exists in this
family at all.

Two alternatives were considered and rejected:

1. **Treat `incident-response-tool-landscape` as a special case anyway,
   mirroring wave-2h's headless handling for its own `tool-landscape`
   skill, in case the two `tool-landscape` skills across families should
   be authored identically for consistency.** Rejected: the two skills
   are structurally different in their source files —
   `technical-writing-tool-landscape` has no heading,
   `incident-response-tool-landscape` does (confirmed directly against
   this checkout: `grep -n "^## " skills/incident-response-tool-
   landscape/SKILL.md` returns `19:## Rules`) — and the recipe classifies
   by each skill's own on-disk shape, not by name-matching across
   families. Treating it as a special case here would insert an
   unnecessary heading-anchor decision where none exists.
2. **Insert the 3 new headings after the framing paragraph but before
   the pre-existing content generically, without confirming each file's
   actual first structural marker.** Rejected: the recipe's own
   convention (used by the pilot and every prior wave) anchors the
   insertion point to each skill's existing first heading — here, `##
   Rules` for all 6 — to guarantee the insertion lands in the same
   relative position the checker and prior waves already validate;
   skipping that per-file confirmation risks an insertion inside the
   framing paragraph or after the `## Rules` heading instead of before
   it.

Chosen instead: apply the recipe's headings, description rewrite, and
manifest entry uniformly across all 6, inserting `## Trigger` / `##
Procedure` / `## Output shape` between each skill's framing paragraph and
its existing `## Rules` heading — the same insertion point the pilot and
every prior all-Shape-A wave used. `## Procedure` cites rule numbers by
number from each skill's `## Rules` block.

## What will be done

1. For each of the 6 skills, insert `## Trigger` / `## Procedure` / `##
   Output shape` between the framing paragraph and the `## Rules`
   heading.
   - `## Trigger`: concrete conditions distinguishing the skill from its
     sibling axes in the family (not a title restatement) — derived from
     each skill's current `description:` and framing text.
   - `## Procedure`: ordered steps citing rule numbers from `## Rules`.
   - `## Output shape`: what the skill produces, derived from each
     skill's existing rule content.
2. Rewrite each `description:` as a sentence derived from that skill's
   authored `## Trigger`, keeping the checker's trigger-marker substring
   ("use when").
3. Append all 6 directory names to `procedure_authored_skills.txt`,
   after the existing 78 entries (incremental, not a replacement).
4. Run, from the skill-repository checkout, in this order: (a) `python3
   scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention sweep — diff pre- and post-change content per skill and
   confirm every pre-existing rule/content line from the survey's
   baseline (33 rule lines across the 6 skills, 352 total pre-change
   lines) is still present, (c) `git diff --stat` scoped to the 6 skill
   paths + manifest (expect no other paths), (d) `python3
   scripts/check_skill_conformance.py` with no flag (full-tree, expect
   exit 0).
5. Paste all four check outputs plus the `git diff --stat` into
   `docs/issue-1854/reports/implementation.md` (phase 2, after
   approval), matching the pilot record's structure.

## Out of scope

- Any skill outside the 6 `incident-response-*` family.
- Checker logic changes (`check_skill_conformance.py`) or hook changes.
- Restructuring existing rule content beyond inserting the 3 mandated
  headings.
- Reconciling the issue body's stale "10 skills" Program-context text —
  noted in the survey, not corrected in the issue itself (this role does
  not edit issues).
- The unrelated prior-wave checkouts present at other
  `/tmp/skill-repository-*` paths — this wave works from its own fresh
  clone at `/tmp/skill-repository-1854` and does not touch those other
  checkouts.

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 with all 6 new names included and passing.
- The rule-retention sweep shows zero lost lines against the survey's
  pre-change baseline (33 rule lines across the 6 skills, 352 total
  pre-change lines).
- `check_skill_conformance.py` (full-tree, no flag) exits 0.
- `git diff --stat` lists only the 6 SKILL.md paths + the manifest file.
- All four outputs and the diff --stat are pasted live into
  docs/issue-1854/reports/implementation.md per the issue's acceptance
  checks.
