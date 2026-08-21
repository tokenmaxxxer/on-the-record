---
status: proposed
files:
  - docs/issue-1830/reports/implementation.md
  - /tmp/skill-repository/skills/observability-cardinality-budget/SKILL.md
  - /tmp/skill-repository/skills/observability-explorability/SKILL.md
  - /tmp/skill-repository/skills/observability-methodology-selection/SKILL.md
  - /tmp/skill-repository/skills/observability-phase-trace/SKILL.md
  - /tmp/skill-repository/skills/observability-signal-golden/SKILL.md
  - /tmp/skill-repository/skills/observability-signal-red/SKILL.md
  - /tmp/skill-repository/skills/observability-signal-use/SKILL.md
  - /tmp/skill-repository/scripts/procedure_authored_skills.txt
---

## Request

Apply the frozen wave recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 7 `observability-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger` / `## Procedure` /
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt` with the 7
names, keep every pre-existing content line, and deliver as a
skill-repository PR plus this role's record, scoped to only these 7
skill files + the manifest.

## Constraints

- Zero rule-line/content loss (issue requirement 1 + record-shape
  frontmatter's `## What did not work` accounting).
- No path outside the 7 family skills + manifest touched (issue
  requirement 2, `git diff --stat` must prove it).
- No checker-logic changes, no hook changes (issue non-goals).
- Guidance-only: the authored sections steer usage, they do not change
  what each skill's Rules content resolves.
- The manifest check requires exactly the 3 headings
  (`## Trigger`/`## Procedure`/`## Output shape`, any order) per
  `check_skill_conformance.py` — nothing else is mechanically enforced
  about Procedure's internal citation style.

## Rationale

The survey (docs/issue-1830/reports/implementation/survey.md) found this
family, unlike the three prior waves, has no Shape A/B split: all 7
`observability-*` skills already carry `rule_count_floor:` frontmatter, a
single `## Rules` heading, and numbered rules under it — the pilot's
exact structure. The issue's prompt asked this survey to classify Shape
A/B "per the #1802/#1809/#1812 precedent"; the classification result
itself is 7-of-7 Shape A, 0 Shape B.

Two alternatives were considered and rejected:

1. **Reuse the earlier waves' Shape-B citation-resolution language
   (citing each skill's own named sections instead of rule numbers) as a
   standing convention, applied uniformly regardless of whether a given
   skill actually needs it.** Rejected: there is no Shape-B skill in this
   family to apply that resolution to; writing Procedure steps that cite
   named sections instead of rule numbers, when every skill in the family
   has numbered rules to cite, would deviate from the recipe's own
   default ("citing rule number(s) from `## Rules`") without cause, and
   would misrepresent structure the survey found does not exist here.
2. **Treat the Program-context paragraph's stated count of "10 skills"
   as authoritative and look for 3 more `observability-*` skills beyond
   the 7 the checkout has.** Rejected: the survey found the live checkout
   has exactly 7 `observability-*` directories, matching both the issue
   title ("7 skills") and Requirement 1 ("All 7 observability-* skills");
   the Program-context "10" is the same class of stale-text artifact the
   wave-2c survey found in this issue's own `scope:` field, and inventing
   work items to reach a number found nowhere in the checkout, the title,
   or the acceptance-relevant Requirement text would be scope invention,
   not scope-following.

Chosen instead: apply the frozen recipe verbatim to all 7 skills, citing
rule numbers from each skill's own `## Rules` section in every
`## Procedure` step — the recipe's default case, with no Shape-B
citation-target substitution needed because no Shape-B skill exists in
this family.

## What will be done

1. For each of the 7 skills, insert `## Trigger` / `## Procedure` /
   `## Output shape` between the framing paragraph (including the
   "Research trail:" line where present) and the existing `## Rules`
   heading.
   - `## Trigger`: concrete conditions distinguishing the skill from its
     sibling axes in the family (not a title restatement) — derived from
     each skill's current `description:` and framing text.
   - `## Procedure`: ordered steps citing rule numbers from that skill's
     own `## Rules`.
   - `## Output shape`: what the skill produces, derived from each
     skill's existing rule content.
2. Rewrite each `description:` as a sentence derived from that skill's
   authored `## Trigger`, keeping the checker's trigger-marker substring
   ("use when").
3. Append all 7 directory names to `procedure_authored_skills.txt`, after
   the existing 39 entries (incremental, not a replacement).
4. Run, from the skill-repository checkout, in this order: (a) `python3
   scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention sweep — diff pre- and post-change content per skill and
   confirm every pre-existing rule/content line from the survey's
   baseline (25 rule lines total) is still present, (c) `git diff --stat`
   scoped to the 7 skill paths + manifest (expect no other paths), (d)
   `python3 scripts/check_skill_conformance.py` with no flag (full-tree,
   expect exit 0).
5. Paste all four check outputs plus the `git diff --stat` into
   `docs/issue-1830/reports/implementation.md` (phase 2, after approval),
   matching the pilot record's structure.

## Out of scope

- Any skill outside the 7 `observability-*` family.
- Checker logic changes (`check_skill_conformance.py`) or hook changes.
- Reconciling the issue body's stale "10 skills" Program-context text —
  noted in the survey, not corrected in the issue itself (this role does
  not edit issues).
- Restructuring existing `## Rules` content beyond inserting the 3
  mandated headings.

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 with all 7 new names included and passing.
- The rule-retention sweep shows zero lost lines against the survey's
  pre-change baseline (25 rule lines across the 7 skills).
- `check_skill_conformance.py` (full-tree, no flag) exits 0.
- `git diff --stat` lists only the 7 SKILL.md paths + the manifest file.
- All four outputs and the diff --stat are pasted live into
  docs/issue-1830/reports/implementation.md per the issue's acceptance
  checks.
