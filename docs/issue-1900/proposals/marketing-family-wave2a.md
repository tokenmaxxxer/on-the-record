---
status: proposed
files:
  - /tmp/skill-repository-1900/skills/marketing-channel-selection/SKILL.md
  - /tmp/skill-repository-1900/skills/marketing-message-persuasion/SKILL.md
  - /tmp/skill-repository-1900/skills/marketing-positioning-differentiation/SKILL.md
  - /tmp/skill-repository-1900/skills/marketing-scope-pruning/SKILL.md
  - /tmp/skill-repository-1900/skills/marketing-segment-targeting/SKILL.md
  - /tmp/skill-repository-1900/scripts/procedure_authored_skills.txt
  - docs/issue-1900/reports/implementation.md
---

## Request

Apply the frozen procedural-body recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 5 `marketing-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger`/`## Procedure`/
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt`, run the four
pilot checks, and deliver as a skill-repository PR plus this record.
Guidance-only — no checker logic changes, no hooks, no other family.

## Constraints

- Family-bounded: only the 5 `marketing-*` skill dirs + the manifest
  file may be touched in the skill-repository PR (issue Requirement 2 /
  Acceptance criterion 2).
- Zero rule-line loss: every pre-change numbered rule line (30 total,
  per survey) must be present, verbatim, post-change.
- Reuse the frozen recipe verbatim — this wave is not a redesign point.
- Guidance role scope for this session maps to skills
  implementation-complexity-coupling-management,
  implementation-design-pattern-selection,
  implementation-performance-data-structure-choice,
  implementation-blueprint only (role-source-allowlist, issue #1758) —
  no rulebook consultation beyond those skills.
- Phase-1 output only: this proposal + the survey, no code changes to
  `docs/issue-1900/reports/implementation.md` land until an approver's
  Approve.

## Rationale

Two shapes of change were available for authoring the 5 bodies:

1. **Reuse the #1790 pilot recipe verbatim** (chosen): insert the three
   headings between framing paragraph and `## Rules`, cite existing
   rule numbers in Procedure steps, derive `description:` from Trigger,
   append to the manifest. This is what every wave since #1790
   (refactoring-legacy, growth-analytics, knowledge-management,
   capacity-planning, localization, brand-design) has done, and the
   pilot record explicitly names "largest remaining families first,
   one wave per family" as the intended reuse path.
2. **Design a marketing-specific variant of the recipe** (rejected):
   e.g. a Trigger section keyed to funnel stage or campaign type
   instead of the axis distinction the recipe specifies. Rejected
   because the survey found the marketing family's shape (6 rules per
   skill, `description:`/`axis:`/`rule_count_floor:` frontmatter,
   `source:`-suffixed rule lines) matches the pilot's pre-change shape
   with no structural divergence — inventing a variant recipe here
   would break consistency across the wave with no gap in the frozen
   recipe to justify it, and the issue explicitly says "apply the
   frozen recipe verbatim."

## What will be done

1. Author `## Trigger` (concrete conditions distinguishing this skill
   from its sibling marketing axes — not a title restatement),
   `## Procedure` (ordered steps, each citing the existing rule
   number(s) it operationalizes), and `## Output shape` (what the
   applied skill produces) in each of the 5 `SKILL.md` bodies, inserted
   between the framing paragraph and `## Rules`.
2. Rewrite each skill's `description:` frontmatter line as a sentence
   derived from its new `## Trigger` content, preserving the "use when"
   trigger-marker substring the checker scans for.
3. Append the 5 skill directory names to
   `scripts/procedure_authored_skills.txt` (appending after the
   existing 29 entries, not replacing them).
4. Run, live from the skill-repository checkout, and paste into the
   phase-2 record: (a) `check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention grep sweep comparing pre- and post-change rule lines
   for all 5 skills (expect zero loss), (c) `git diff --stat` scoped to
   the 5 skill paths + the manifest (expect no other paths), (d)
   `check_skill_conformance.py` full-tree run with no flag (expect exit
   0).
5. Open a skill-repository PR carrying the 5 skill-file diffs and the
   manifest diff.

## Out of scope

- Any family other than `marketing-*`.
- Checker script (`check_skill_conformance.py`) logic changes.
- Hook changes.
- Rewriting or renumbering existing rule content — only insertion of
  the three new sections and the description rewrite touch each file;
  rule text and `source:` lines are carried forward unchanged.

## How you'll know it worked

- All 4 checks from Acceptance criterion 1 pass, pasted live from the
  skill-repository checkout: manifest-checker exit 0, rule-retention
  sweep shows all 30 pre-change rule lines present post-change,
  full-tree checker exit 0.
- `git diff --stat` (Acceptance criterion 2) shows only the 5
  `skills/marketing-*/SKILL.md` paths + `scripts/procedure_authored_skills.txt`.
- `procedure_authored_skills.txt` contains all 5 marketing skill names
  appended after the prior 29 entries (34 total).
