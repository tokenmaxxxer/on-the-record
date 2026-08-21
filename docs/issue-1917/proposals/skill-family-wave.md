---
status: proposed
files:
  - /tmp/skill-repository-1917/skills/architecture-coupling-classification/SKILL.md
  - /tmp/skill-repository-1917/skills/architecture-decomposition-strategy/SKILL.md
  - /tmp/skill-repository-1917/skills/architecture-dependency-direction/SKILL.md
  - /tmp/skill-repository-1917/skills/architecture-interface-contract-shape/SKILL.md
  - /tmp/skill-repository-1917/skills/architecture-module-boundary-definition/SKILL.md
  - /tmp/skill-repository-1917/scripts/procedure_authored_skills.txt
  - docs/issue-1917/reports/implementation.md
---

## Request

Apply the frozen procedural-body recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 5 `architecture-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger`/`## Procedure`/
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt`, run the four
pilot checks, and deliver as a skill-repository PR plus this record.
Guidance-only — no checker logic changes, no hooks, no other family.

## Constraints

- Family-bounded: only the 5 `architecture-*` skill dirs + the manifest
  file may be touched in the skill-repository PR (issue Requirement 2 /
  Acceptance criterion 2).
- Zero rule-line loss: every pre-change rule heading (74 `### N.`/`### Nb.`
  headings total, per survey) must be present, verbatim, post-change.
- Reuse the frozen recipe verbatim — this wave is not a redesign point,
  even though this family's rule-body shape (`### N. <condition>`
  subheadings, only 1 of 5 skills carrying a `## Rules` heading) differs
  from every prior family surveyed; the survey found the divergence
  affects only the exact insertion point, not the recipe's substance.
- Guidance role scope for this session maps to skills
  implementation-complexity-coupling-management,
  implementation-design-pattern-selection,
  implementation-performance-data-structure-choice,
  implementation-blueprint only (role-source-allowlist, issue #1758) —
  no rulebook consultation beyond those skills.
- Phase-1 output only: this proposal + the survey, no code changes to
  `docs/issue-1917/reports/implementation.md` land until an approver's
  Approve.

## Rationale

Two shapes of change were available for authoring the 5 bodies:

1. **Reuse the #1790 pilot recipe verbatim, adapting only the literal
   insertion point per file** (chosen): insert the three headings
   between the framing paragraph(s) and the first existing rule/
   conflicts heading (that boundary is `## Rules` for
   architecture-coupling-classification, and the first `### N.` rule
   heading for the other four, since they carry no `## Rules` heading —
   see survey's Shape-classification section), cite existing rule
   numbers (including `Nb.` sub-rules) in Procedure steps, derive
   `description:` from Trigger, append to the manifest. This is what
   every wave since #1790 has done, and the pilot record explicitly
   names "largest remaining families first, one wave per family" as the
   intended reuse path — the survey found no gap the recipe fails to
   cover, only a difference in where the fixed insertion point falls
   file-to-file.
2. **Design an architecture-specific variant of the recipe that
   standardizes a `## Rules` heading across all 5 skills as part of this
   wave** (rejected): since 4 of the 5 skills currently run rules
   directly under the framing paragraph with no `## Rules` heading at
   all, a stricter reading could add that heading everywhere for
   consistency with the one skill that has it
   (architecture-coupling-classification) before inserting Trigger/
   Procedure/Output-shape. Rejected because the issue's Non-goals
   explicitly scope this wave to "guidance-only" content addition and
   forbid "checker logic changes" — adding a heading not required by
   the checker and not part of the frozen recipe's own required-section
   list would expand the touched surface of every file beyond what the
   recipe calls for, for a cosmetic consistency gain the issue does not
   ask for and the checker does not enforce structurally on
   non-manifest skills.

## What will be done

1. Author `## Trigger` (concrete conditions distinguishing this skill
   from its sibling architecture-decision skills — not a title
   restatement), `## Procedure` (ordered steps, each citing the
   existing rule number(s), including `Nb.` sub-rules, it
   operationalizes), and `## Output shape` (what the applied skill
   produces) in each of the 5 `SKILL.md` bodies, inserted between the
   framing paragraph(s) and the first existing rule/conflicts heading
   per the per-file insertion point recorded in the survey.
2. Rewrite each skill's `description:` frontmatter line as a sentence
   derived from its new `## Trigger` content, preserving the "use when"
   trigger-marker substring the checker scans for.
3. Append the 5 skill directory names to
   `scripts/procedure_authored_skills.txt` (appending after the
   existing 174 entries, not replacing them).
4. Run, live from the skill-repository checkout, and paste into the
   phase-2 record: (a) `check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention sweep comparing pre- and post-change rule heading
   lines (`### N.`/`### Nb.`) for all 5 skills (expect zero loss), (c)
   `git diff --stat` scoped to the 5 skill paths + the manifest (expect
   no other paths), (d) `check_skill_conformance.py` full-tree run with
   no flag (expect exit 0).
5. Open a skill-repository PR carrying the 5 skill-file diffs and the
   manifest diff.

## Out of scope

- Any family other than `architecture-*`.
- Checker script (`check_skill_conformance.py`) logic changes.
- Hook changes.
- Adding a `## Rules` heading to the 4 skills that currently lack one,
  or otherwise restructuring existing rule content — only insertion of
  the three new sections and the description rewrite touch each file;
  rule text, headings, and content are carried forward unchanged.

## How you'll know it worked

- All 4 checks from Acceptance criterion 1 pass, pasted live from the
  skill-repository checkout: manifest-checker exit 0, rule-retention
  sweep shows all 74 pre-change rule heading lines present post-change,
  full-tree checker exit 0.
- `git diff --stat` (Acceptance criterion 2) shows only the 5
  `skills/architecture-*/SKILL.md` paths + `scripts/procedure_authored_skills.txt`.
- `procedure_authored_skills.txt` contains all 5 architecture skill
  names appended after the prior 174 entries (179 total).
