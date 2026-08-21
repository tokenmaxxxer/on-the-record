---
status: proposed
files:
  - docs/issue-1838/reports/implementation.md
  - /tmp/skill-repository-1838/skills/ux-engineering-color-visibility/SKILL.md
  - /tmp/skill-repository-1838/skills/ux-engineering-control-selection/SKILL.md
  - /tmp/skill-repository-1838/skills/ux-engineering-layout-grouping/SKILL.md
  - /tmp/skill-repository-1838/skills/ux-engineering-navigation-depth/SKILL.md
  - /tmp/skill-repository-1838/skills/ux-engineering-research-log/SKILL.md
  - /tmp/skill-repository-1838/skills/ux-engineering-surface-contrast/SKILL.md
  - /tmp/skill-repository-1838/scripts/procedure_authored_skills.txt
---

## Request

Apply the frozen wave recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 6 `ux-engineering-*` skills in
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
  what each skill's rule/axis content resolves.
- The manifest check requires exactly the 3 headings (`## Trigger`/
  `## Procedure`/`## Output shape`, any order) per
  `check_skill_conformance.py` — nothing else is mechanically enforced
  about Procedure's internal citation style.

## Rationale

The survey (docs/issue-1838/reports/implementation/survey.md) found this
family has both shapes the wave precedents defined: 5 of 6 skills
(`surface-contrast`, `color-visibility`, `layout-grouping`,
`navigation-depth`, `control-selection`) are Shape A — the pilot's
structure, just under the heading name `## Decision rules` instead of
`## Rules` — and 1 of 6 (`research-log`) is Shape B: an evidence-trail
file with `## Axis: <name>` section headings and no numbered rule lines
to cite. This is the same split wave-2e (legal-compliance, 6 Shape A + 1
Shape B `-research-log`) already found for a family carrying its own
research-log skill, not wave-2d's single-shape case.

Two alternatives were considered and rejected:

1. **Add a `## Decision rules`/numbered-rules section to `research-log`
   so the recipe's "cite rule number(s)" instruction applies uniformly
   across all 6.** Rejected: `research-log` is a citation/evidence trail
   for the other 5 skills' rules, not a rules file itself; inventing a
   numbered-rules block would restructure content that does not
   naturally have one, going past "guidance-only" into content
   invention — exactly the alternative wave-2a's survey rejected for its
   own Shape-B skills, and wave-2e rejected for its own
   `legal-compliance-research-log`, for the same reason.
2. **Skip `research-log` this wave and deliver only the 5 Shape-A
   skills against #1838, treating the 6th as a follow-up.** Rejected:
   the issue's requirement 1 is explicit — "All 6 ux-engineering-*
   skills" — and the acceptance check counts all 6 into the manifest;
   under-delivering against a named, countable requirement without the
   issue's approval to narrow scope is not this role's call to make.

Chosen instead: apply the recipe's headings, description rewrite, and
manifest entry uniformly across all 6, varying only the `## Procedure`
citation target per shape — rule numbers from `## Decision rules` for
the 5 Shape-A skills, the skill's own `## Axis: <name>` section headings
for `research-log` — mirroring the wave-2e precedent's Shape-A/Shape-B
citation-target split rather than inventing a new convention or
narrowing this wave's scope.

## What will be done

1. For each of the 6 skills, insert `## Trigger` / `## Procedure` /
   `## Output shape` between the framing paragraph and the skill's
   existing first structural heading (`## Decision rules` for the 5
   Shape-A skills; the first `## Axis: <name>` heading for
   `research-log`).
   - `## Trigger`: concrete conditions distinguishing the skill from its
     sibling axes in the family (not a title restatement) — derived from
     each skill's current `description:` and framing text.
   - `## Procedure`: ordered steps citing rule numbers from `##
     Decision rules` (Shape A) or citing the relevant `## Axis: <name>`
     section(s) (Shape B, `research-log`) per the Rationale above.
   - `## Output shape`: what the skill produces, derived from each
     skill's existing rule content (Shape A) or its axis-block/
     removal-coverage content (Shape B).
2. Rewrite each `description:` as a sentence derived from that skill's
   authored `## Trigger`, keeping the checker's trigger-marker substring
   ("use when").
3. Append all 6 directory names to `procedure_authored_skills.txt`,
   after the existing 46 entries (incremental, not a replacement).
4. Run, from the skill-repository checkout, in this order: (a) `python3
   scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention sweep — diff pre- and post-change content per skill and
   confirm every pre-existing rule/content line from the survey's
   baseline (36 rule lines across the 5 Shape-A skills, plus
   `research-log`'s 131 pre-existing lines) is still present, (c) `git
   diff --stat` scoped to the 6 skill paths + manifest (expect no other
   paths), (d) `python3 scripts/check_skill_conformance.py` with no flag
   (full-tree, expect exit 0).
5. Paste all four check outputs plus the `git diff --stat` into
   `docs/issue-1838/reports/implementation.md` (phase 2, after approval),
   matching the pilot record's structure.

## Out of scope

- Any skill outside the 6 `ux-engineering-*` family.
- Checker logic changes (`check_skill_conformance.py`) or hook changes.
- Restructuring existing rule/axis content beyond inserting the 3
  mandated headings — no `## Decision rules` block invented for
  `research-log`.
- Reconciling the issue body's stale "10 skills" Program-context text —
  noted in the survey, not corrected in the issue itself (this role does
  not edit issues).
- The unrelated wave-2d (`observability-*`) checkout state present at
  `/tmp/skill-repository` — this wave works from its own fresh clone at
  `/tmp/skill-repository-1838` and does not touch that other checkout.

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 with all 6 new names included and passing.
- The rule-retention sweep shows zero lost lines against the survey's
  pre-change baseline (36 rule lines across the 5 Shape-A skills, plus
  `research-log`'s 131 pre-existing lines).
- `check_skill_conformance.py` (full-tree, no flag) exits 0.
- `git diff --stat` lists only the 6 SKILL.md paths + the manifest file.
- All four outputs and the diff --stat are pasted live into
  docs/issue-1838/reports/implementation.md per the issue's acceptance
  checks.
