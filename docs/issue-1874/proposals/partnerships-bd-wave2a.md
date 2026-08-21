---
status: proposed
files:
  - skill-repository/skills/partnerships-bd-deal-structure-selection/SKILL.md
  - skill-repository/skills/partnerships-bd-exclusivity-and-scope-terms/SKILL.md
  - skill-repository/skills/partnerships-bd-governance-cadence-and-kpi/SKILL.md
  - skill-repository/skills/partnerships-bd-negotiation-positioning/SKILL.md
  - skill-repository/skills/partnerships-bd-term-sheet-comprehensibility-and-convention/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural-body wave 2a — partnerships-bd family

subject: issue-1874

## Request

Apply the procedural-body recipe frozen in
`docs/issue-1790/reports/implementation.md` (the #1790 pilot) to the 5
`partnerships-bd-*` skills in `tokenmaxxxer/skill-repository`: insert
`## Trigger` / `## Procedure` / `## Output shape` sections, each
Procedure step citing the rule number(s) it draws on; rewrite each
skill's `description:` from its own new Trigger section; append the 5
skill names to `scripts/procedure_authored_skills.txt`; verify with the
manifest checker, a rule-retention sweep, a full-tree checker run, and a
scoped `git diff --stat`. No checker-logic change, no other family, no
hooks (issue non-goals).

## Constraints

- Zero rule-line loss: every pre-change `### N. <title>` heading and its
  following `- **Condition** ... **Choice** ... **Why** ... **Source**
  ... **Counter-example test** ...` bullet line in each skill's
  `## Decision rules` section must survive verbatim in the post-change
  file.
- Write set is exactly the 5 SKILL.md files plus
  `scripts/procedure_authored_skills.txt` — no other skill, no checker
  script edit, no hook.
- Guidance-only: Procedure steps describe when/how to apply a rule; they
  do not restate or paraphrase the rule's Condition/Choice/Why content,
  matching the pilot's navigational-layer framing.
- Both checker runs (`--manifest` and full-tree) must exit 0.

## Rationale

**Chosen approach**: reuse the frozen recipe verbatim, citing rules by
their printed `### N.` heading number (e.g. "rule 2") rather than
inventing a bullet-position count, since the survey found (canonical:
docs/issue-1874/reports/implementation/survey.md, "Rule numbering
convention — heading-level, not inline-numbered" section) that this
family prints each rule as its own numbered level-3 heading, distinct in
markup from both the secure-coding/risk-management families' inline
`1. When ...` paragraph numbering and the finance-unit-economics/pricing
families' unordered `- **ADDITION**/**REMOVAL**:` bullets — but the
printed number is citable in the same way regardless of which markup
token carries it.

**Rejected alternative — treat the heading-level numbering as requiring
the finance-unit-economics wave's bullet-position citation convention
(counting bullet order instead of citing the printed number)**: rejected
because the survey confirms a real, printed rule number already exists
in the source text (`### 1.`, `### 2.`, `### 3.`) — canonical:
docs/issue-1874/reports/implementation/survey.md, "Rule numbering
convention" section's `grep -c '^### [0-9]'` output (3 per file, 15
total). Inventing a position count when a printed number is already
present would be strictly worse: it discards an existing, unambiguous
citation surface for a derived one, with no benefit to this family's
actual rule shape.

**Rejected alternative — treat any of the 5 as already procedure-shaped
(Shape B) and skip authoring it as a no-op**: rejected because the
survey found, not assumed, that all 5 files carry exactly one heading
(`## Decision rules`) with no `## Trigger`/`## Procedure`/`## Output
shape` present — canonical: docs/issue-1874/reports/implementation/survey.md,
"Body shape" section's live `grep -n '^## '` output. Treating any skill
as a no-op without that live check would violate the acceptance
criterion's own empty-state requirement, which needs a check result, not
an inference from family membership.

## What will be done

1. For each of the 5 skills, read the existing `## Decision rules`
   section (3 numbered rule headings each) and framing paragraph, then
   insert `## Trigger` / `## Procedure` / `## Output shape` between the
   framing paragraph and `## Decision rules`, with each Procedure step
   citing the rule number(s) (`### N.`) it draws on.
2. Rewrite each skill's frontmatter `description:` as a sentence derived
   from that skill's own new `## Trigger` section (matching the pilot's
   "description derived from Trigger" step), keeping a checker
   trigger-marker substring ("use when").
3. Append the 5 skill directory names to
   `scripts/procedure_authored_skills.txt` (alphabetical, appended after
   the risk-management wave's 5 entries — the file's current tail per
   the survey's "Manifest state" section).
4. Run `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (must exit 0).
5. Run the rule-retention sweep: for each of the 5 files, diff pre-change
   vs. post-change `### N.` headings and their Condition/Choice/Why/
   Source/Counter-example-test bullet lines, confirming every pre-change
   line is present post-change verbatim.
6. Run `python3 scripts/check_skill_conformance.py` (full-tree, no
   manifest arg) and confirm it still exits 0.
7. Run `git diff --stat` scoped to the working tree and confirm it lists
   only the 5 SKILL.md paths plus `scripts/procedure_authored_skills.txt`.
8. Commit on a wave branch in the skill-repository checkout, open a PR
   there, and paste all four check outputs plus the `git diff --stat`
   into the phase-2 implementation record in this repo
   (`docs/issue-1874/reports/implementation.md`), matching the issue's
   Acceptance checks verbatim.

## Out of scope

- Any family other than the 5 `partnerships-bd-*` skills.
- Any change to `scripts/check_skill_conformance.py`'s logic (the
  `--manifest` flag already exists from the #1790 pilot; no further
  checker change is needed).
- Any hook change.
- Reconciling each skill's `rule_count_floor: 3` frontmatter field
  against the frozen recipe — the survey found floor already equals live
  rule count for this family, and no frontmatter numeric field is part
  of the recipe's write set.
- Reconciling the issue's Program-context "10 skills" figure against the
  live 5-skill tree beyond noting the discrepancy in the survey — the
  Requirements section's explicit "All 5 partnerships-bd-* skills"
  wording is what this wave delivers against.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 post-change.
- `python3 scripts/check_skill_conformance.py` (full-tree) exits 0
  post-change.
- The rule-retention sweep shows every pre-change `## Decision rules`
  heading and bullet line retained verbatim across all 5 files.
- `git diff --stat` in the skill-repository checkout lists only the 5
  `partnerships-bd-*/SKILL.md` paths plus
  `scripts/procedure_authored_skills.txt`.
