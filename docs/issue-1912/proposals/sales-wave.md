---
status: proposed
files:
  - /tmp/skill-repository-1912/skills/sales-objection-handling/SKILL.md
  - /tmp/skill-repository-1912/skills/sales-pitch-scoping-and-messaging-handoff/SKILL.md
  - /tmp/skill-repository-1912/skills/sales-qualification-and-discovery/SKILL.md
  - /tmp/skill-repository-1912/scripts/procedure_authored_skills.txt
  - docs/issue-1912/reports/implementation.md
---

## Request

Apply the frozen procedural-body recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 3 `sales-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger`/`## Procedure`/
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt`, run the four
pilot checks, and deliver as a skill-repository PR plus this record.
Guidance-only — no checker logic changes, no hooks, no other family.

## Constraints

- Family-bounded: only the 3 `sales-*` skill dirs + the manifest file
  may be touched in the skill-repository PR (issue Requirement 2 /
  Acceptance criterion 2).
- Zero rule-line loss: every pre-change numbered rule line (18 total,
  per survey) must be present, verbatim, post-change.
- Reuse the frozen recipe verbatim — this wave is not a redesign point.
- Guidance role scope for this session maps to skills
  implementation-complexity-coupling-management,
  implementation-design-pattern-selection,
  implementation-performance-data-structure-choice,
  implementation-blueprint only (role-source-allowlist, issue #1758) —
  no rulebook consultation beyond those skills.
- Phase-1 output only: this proposal + the survey, no code changes to
  `docs/issue-1912/reports/implementation.md` land until an approver's
  Approve.

## Rationale

Two shapes of change were available for authoring the 3 bodies:

1. **Reuse the #1790 pilot recipe verbatim** (chosen): insert the three
   headings between framing paragraph and `## Rules`, cite existing
   rule numbers in Procedure steps, derive `description:` from Trigger,
   append to the manifest. This is what every wave since #1790
   (refactoring-legacy, growth-analytics, knowledge-management,
   capacity-planning, localization, brand-design, marketing,
   data-engineering, data-modeling, defect-verification) has done, and
   the pilot record explicitly names "largest remaining families first,
   one wave per family" as the intended reuse path — the survey found
   the sales family's shape (6 rules per skill,
   `description:`/`axis:`/`rule_count_floor:` frontmatter) has no
   structural divergence from the pilot or from the already-landed
   marketing wave.
2. **Design a sales-specific variant of the recipe** (rejected): e.g. a
   Trigger section keyed to deal stage or buyer-role instead of the
   axis distinction the recipe specifies, given each sales skill maps
   to a distinct stage of a sales conversation (qualification,
   pitch/handoff, objection handling) rather than a topical facet the
   way e.g. brand-design's axes did. Rejected because the survey found
   no structural gap the frozen recipe fails to cover — each sales
   skill already carries an `axis:` field and a self-contained
   `## Rules` list the same shape as every prior wave, and the issue
   explicitly says "apply the frozen recipe verbatim." A stage-keyed
   variant would diverge from every landed wave's Trigger convention
   for no documented gap.

## What will be done

1. Author `## Trigger` (concrete conditions distinguishing this skill
   from its sibling sales-conversation-stage skills — not a title
   restatement), `## Procedure` (ordered steps, each citing the
   existing rule number(s) it operationalizes), and `## Output shape`
   (what the applied skill produces) in each of the 3 `SKILL.md`
   bodies, inserted between the framing paragraph and `## Rules`.
2. Rewrite each skill's `description:` frontmatter line as a sentence
   derived from its new `## Trigger` content, preserving the "use when"
   trigger-marker substring the checker scans for.
3. Append the 3 skill directory names to
   `scripts/procedure_authored_skills.txt` (appending after the
   existing 163 entries, not replacing them).
4. Run, live from the skill-repository checkout, and paste into the
   phase-2 record: (a) `check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention grep sweep comparing pre- and post-change rule lines
   for all 3 skills (expect zero loss), (c) `git diff --stat` scoped to
   the 3 skill paths + the manifest (expect no other paths), (d)
   `check_skill_conformance.py` full-tree run with no flag (expect exit
   0).
5. Open a skill-repository PR carrying the 3 skill-file diffs and the
   manifest diff.

## Out of scope

- Any family other than `sales-*`.
- Checker script (`check_skill_conformance.py`) logic changes.
- Hook changes.
- Rewriting or renumbering existing rule content — only insertion of
  the three new sections and the description rewrite touch each file;
  rule text and content are carried forward unchanged.

## How you'll know it worked

- All 4 checks from Acceptance criterion 1 pass, pasted live from the
  skill-repository checkout: manifest-checker exit 0, rule-retention
  sweep shows all 18 pre-change rule lines present post-change,
  full-tree checker exit 0.
- `git diff --stat` (Acceptance criterion 2) shows only the 3
  `skills/sales-*/SKILL.md` paths + `scripts/procedure_authored_skills.txt`.
- `procedure_authored_skills.txt` contains all 3 sales skill names
  appended after the prior 163 entries (166 total).
