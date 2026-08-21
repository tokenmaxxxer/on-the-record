---
status: proposed
files:
  - docs/issue-1844/reports/implementation.md
  - /tmp/skill-repository-1844/skills/technical-writing-doc-type-selection/SKILL.md
  - /tmp/skill-repository-1844/skills/technical-writing-minimalism-scoping/SKILL.md
  - /tmp/skill-repository-1844/skills/technical-writing-persuasion-trust/SKILL.md
  - /tmp/skill-repository-1844/skills/technical-writing-structure-comprehension/SKILL.md
  - /tmp/skill-repository-1844/skills/technical-writing-style-guide-compliance/SKILL.md
  - /tmp/skill-repository-1844/skills/technical-writing-tool-landscape/SKILL.md
  - /tmp/skill-repository-1844/scripts/procedure_authored_skills.txt
---

## Request

Apply the frozen wave recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 6 `technical-writing-*` skills in
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
  about a particular pre-existing heading name or the presence of any
  heading at all above the rules content.

## Rationale

The survey (docs/issue-1844/reports/implementation/survey.md) found
this family splits **5 Shape A + 1 Shape A-headless**, not the 5-A/1-B
split wave-2e/2f/2g each found for their own families: 5 of 6 skills
(`doc-type-selection`, `minimalism-scoping`, `persuasion-trust`,
`structure-comprehension`, `style-guide-compliance`) are the pilot's
structure under the heading `## Rules` (this family's heading name,
distinct from wave-2e/2f/2g's `## Decision rules`). The 6th,
`tool-landscape`, carries the same numbered-rules content shape and its
own `rule_count_floor: 3` in frontmatter, but with **no heading at all**
above its 3 numbered entries — unlike the two other already-existing
tool-landscape skills (`api-design-tool-landscape`,
`incident-response-tool-landscape`), both of which do carry an explicit
`## Rules` heading. This family has no `-research-log` member, so the
Shape-B evidence-trail pattern the last three waves resolved does not
apply here at all.

Two alternatives were considered and rejected:

1. **Insert a synthetic `## Rules` heading above `tool-landscape`'s 3
   numbered entries before authoring the 3 recipe headings, so every
   skill in the family ends up structurally identical.** Rejected: this
   restructures pre-existing content beyond the recipe's own scope
   (insert 3 named headings; do not otherwise touch existing content) —
   the same content-invention alternative wave-2a's survey already
   rejected for its own Shape-B skills, applied here to a heading
   instead of a rules block. The skill's 3 entries are already citable
   by number without a heading; adding one produces no functional gain
   and is not "guidance-only."
2. **Treat `tool-landscape` as Shape B (cite by entry description
   instead of by number, mirroring the `-research-log` citation
   convention) since it lacks a heading like the other Shape-A
   skills.** Rejected: Shape B's citation convention exists because
   `-research-log` skills have no numbered rules to cite at all — only
   named `## Axis:` sections. `tool-landscape` does have numbered rules
   (1-3); citing them by number is strictly more precise than citing by
   description, and the recipe's own instruction ("cite rule
   number(s)") applies directly once headless is understood as an
   absence of a *heading*, not an absence of *numbering*.

Chosen instead: apply the recipe's headings, description rewrite, and
manifest entry uniformly across all 6, inserting `## Trigger` / `##
Procedure` / `## Output shape` between the framing paragraph and the
first pre-existing structural marker for each skill — the `## Rules`
heading for the 5 Shape-A skills, and directly before the first numbered
entry (`1.`) for the headless `tool-landscape` skill, since it has no
heading to anchor after. `## Procedure` cites rule numbers 1-3 by number
in both cases; no synthetic heading is invented and no shape is
misclassified.

## What will be done

1. For each of the 6 skills, insert `## Trigger` / `## Procedure` / `##
   Output shape` between the framing paragraph and the skill's existing
   first structural marker (`## Rules` heading for the 5 Shape-A skills;
   the first numbered entry `1.` for `tool-landscape`, which has no
   heading).
   - `## Trigger`: concrete conditions distinguishing the skill from its
     sibling axes in the family (not a title restatement) — derived from
     each skill's current `description:` and framing text.
   - `## Procedure`: ordered steps citing rule numbers from `## Rules`
     (the 5 Shape-A skills) or from the 3 headless numbered entries
     (`tool-landscape`) per the Rationale above.
   - `## Output shape`: what the skill produces, derived from each
     skill's existing rule content.
2. Rewrite each `description:` as a sentence derived from that skill's
   authored `## Trigger`, keeping the checker's trigger-marker substring
   ("use when").
3. Append all 6 directory names to `procedure_authored_skills.txt`,
   after the existing 66 entries (incremental, not a replacement).
4. Run, from the skill-repository checkout, in this order: (a) `python3
   scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention sweep — diff pre- and post-change content per skill and
   confirm every pre-existing rule/content line from the survey's
   baseline (54 rule lines across the 5 `## Rules` skills, plus
   `tool-landscape`'s 53 pre-existing lines including its 3 numbered
   entries) is still present, (c) `git diff --stat` scoped to the 6
   skill paths + manifest (expect no other paths), (d) `python3
   scripts/check_skill_conformance.py` with no flag (full-tree, expect
   exit 0).
5. Paste all four check outputs plus the `git diff --stat` into
   `docs/issue-1844/reports/implementation.md` (phase 2, after
   approval), matching the pilot record's structure.

## Out of scope

- Any skill outside the 6 `technical-writing-*` family.
- Checker logic changes (`check_skill_conformance.py`) or hook changes.
- Restructuring existing rule/axis content beyond inserting the 3
  mandated headings — no synthetic `## Rules` heading invented for
  `tool-landscape`.
- Reconciling the issue body's stale "10 skills" Program-context text —
  noted in the survey, not corrected in the issue itself (this role does
  not edit issues).
- The unrelated prior-wave checkouts present at `/tmp/skill-repository`
  and other `/tmp/skill-repository-*` paths — this wave works from its
  own fresh clone at `/tmp/skill-repository-1844` and does not touch
  those other checkouts.

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 with all 6 new names included and passing.
- The rule-retention sweep shows zero lost lines against the survey's
  pre-change baseline (54 rule lines across the 5 `## Rules` skills,
  plus `tool-landscape`'s 53 pre-existing lines).
- `check_skill_conformance.py` (full-tree, no flag) exits 0.
- `git diff --stat` lists only the 6 SKILL.md paths + the manifest file.
- All four outputs and the diff --stat are pasted live into
  docs/issue-1844/reports/implementation.md per the issue's acceptance
  checks.
