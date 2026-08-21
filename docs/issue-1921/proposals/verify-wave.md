---
status: proposed
files:
  - /tmp/skill-repository-1921/skills/verify-finding-record/SKILL.md
  - /tmp/skill-repository-1921/skills/verify-severity-classification/SKILL.md
  - /tmp/skill-repository-1921/scripts/procedure_authored_skills.txt
  - docs/issue-1921/reports/implementation.md
---

## Request

Apply the frozen procedural-body recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 2 `verify-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger`/`## Procedure`/
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt`, run the four
pilot checks, and deliver as a skill-repository PR plus this record.
Guidance-only — no checker logic changes, no hooks, no other family.

## Constraints

- Family-bounded: only the 2 `verify-*` skill dirs + the manifest file
  may be touched in the skill-repository PR (issue Requirement 2 /
  Acceptance criterion 2).
- Zero content loss: every pre-change line of body content in each
  skill's `SKILL.md` must be present, verbatim, post-change (survey,
  "Rule-line counts" section — this family has 0 numbered rule lines,
  so the retention check is a full-body diff, not a rule-count grep).
- Reuse the frozen recipe verbatim — this wave is not a redesign point.
- Guidance role scope for this session maps to skills
  implementation-complexity-coupling-management,
  implementation-design-pattern-selection,
  implementation-performance-data-structure-choice,
  implementation-blueprint only (role-source-allowlist, issue #1758) —
  no rulebook consultation beyond those skills.
- Phase-1 output only: this proposal + the survey, no code changes to
  `docs/issue-1921/reports/implementation.md` land until an approver's
  Approve.

## Rationale

Two shapes of change were available for authoring the 2 bodies, given
the survey found neither skill carries a `## Rules` heading or numbered
rule list (unlike every rulebook-shaped family waved so far — sales,
marketing, data-modeling, data-engineering, devrel):

1. **Reuse the #1790 pilot recipe verbatim, adapted only in what
   Procedure steps cite** (chosen): insert the three headings between
   the framing paragraph and the first existing `##` heading, cite the
   skill's own existing named subsection (e.g. `(see "The outcome
   set")`) in place of a numeric rule id since none exist, derive
   `description:` from Trigger, append to the manifest. This mirrors a
   landed precedent for the identical structural shape:
   `conformance-review-finding-record` — `review`'s counterpart to this
   wave's `verify-finding-record` — has the same no-`## Rules`,
   guidance-only shape and was authored this same way in the
   conformance-review wave (survey, "Structural divergence" section).
   The recipe's own step 2 text ("each citing rule number(s) from `##
   Rules`") presupposes a `## Rules` section; citing the skill's own
   named subsection instead is the literal application of that step
   when no such section exists, not a departure from it.
2. **Retrofit a `## Rules` section with newly-numbered rules extracted
   from existing prose, then cite those numbers** (rejected): would
   satisfy the recipe's literal "rule number" wording but requires
   inventing rule boundaries and numbering where none exist today —
   itself a content change beyond "guidance-only" (the issue's own
   framing) and beyond what the pilot record's WAVE RECIPE describes as
   insertion between the framing paragraph and `## Rules`, not creation
   of a `## Rules` section. Rejected because it would touch the
   skill's existing prose rather than only insert new sections, and
   because a same-shaped precedent (`conformance-review-finding-record`)
   already resolved this exact gap the other way, with no discovered
   defect in that choice.

## What will be done

1. Author `## Trigger` (concrete conditions distinguishing this skill
   from its sibling verify-state-scoped skill — not a title
   restatement), `## Procedure` (ordered steps, each citing the
   existing named subsection it operationalizes, per Rationale option
   1), and `## Output shape` (what the applied skill produces) in each
   of the 2 `SKILL.md` bodies, inserted between the framing paragraph
   and the first existing `##` heading.
2. Rewrite each skill's `description:` frontmatter line as a sentence
   derived from its new `## Trigger` content, preserving the "use
   when"/"Use when" trigger-marker substring the checker scans for.
3. Append the 2 skill directory names to
   `scripts/procedure_authored_skills.txt` (appending after the
   existing 180 entries, not replacing them).
4. Run, live from the skill-repository checkout, and paste into the
   phase-2 record: (a) `check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) a
   full-body retention diff comparing pre- and post-change content for
   both skills (expect zero content loss, since neither carries numbered
   rule lines to sweep), (c) `git diff --stat` scoped to the 2 skill
   paths + the manifest (expect no other paths), (d)
   `check_skill_conformance.py` full-tree run with no flag (expect exit
   0).
5. Open a skill-repository PR carrying the 2 skill-file diffs and the
   manifest diff.

## Out of scope

- Any family other than `verify-*`.
- Checker script (`check_skill_conformance.py`) logic changes.
- Hook changes.
- Retrofitting a `## Rules` section or numbering existing prose (see
  Rationale, rejected option 2) — only insertion of the three new
  sections and the description rewrite touch each file; existing prose
  is carried forward unchanged.

## How you'll know it worked

- All 4 checks from Acceptance criterion 1 pass, pasted live from the
  skill-repository checkout: manifest-checker exit 0, full-body
  retention diff shows zero content loss for both skills, full-tree
  checker exit 0.
- `git diff --stat` (Acceptance criterion 2) shows only the 2
  `skills/verify-*/SKILL.md` paths + `scripts/procedure_authored_skills.txt`.
- `procedure_authored_skills.txt` contains both verify skill names
  appended after the prior 180 entries (182 total).
