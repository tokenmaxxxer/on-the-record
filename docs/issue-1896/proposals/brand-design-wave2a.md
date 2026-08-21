---
status: proposed
files:
  - skill-repository/skills/brand-design-brand-consistency-governance/SKILL.md
  - skill-repository/skills/brand-design-brand-identity-strategy/SKILL.md
  - skill-repository/skills/brand-design-color-visibility/SKILL.md
  - skill-repository/skills/brand-design-logo-clear-space-size/SKILL.md
  - skill-repository/skills/brand-design-typography-pairing/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural-body wave 2a — brand-design family

subject: issue-1896

## Request

Apply the procedural-body recipe frozen in
`docs/issue-1790/reports/implementation.md` (the #1790 pilot) to the 5
`brand-design-*` skills in `tokenmaxxxer/skill-repository`: insert
`## Trigger` / `## Procedure` / `## Output shape` sections, each
Procedure step citing the rule(s) it draws on; rewrite each skill's
`description:` from its own new Trigger section; append the 5 skill
names to `scripts/procedure_authored_skills.txt`; verify with the
manifest checker, a rule-retention sweep, a full-tree checker run, and
a scoped `git diff --stat`. No checker-logic change, no other family,
no hooks (issue non-goals).

## Constraints

- Zero rule-line loss: every pre-change `### N. <title>` rule block in
  each skill's `## Decision rules` section (heading line, `**Condition**`,
  `**Choice**`, `**Why**`, `**Source**`, and `**Counter-example test**`
  sub-bullets) must survive verbatim in the post-change file.
- Write set is exactly the 5 SKILL.md files plus
  `scripts/procedure_authored_skills.txt` — no other skill, no checker
  script edit, no hook.
- Guidance-only: Procedure steps describe when/how to apply a rule;
  they do not restate or paraphrase the rule's content, matching the
  pilot's navigational-layer framing.
- Both checker runs (`--manifest` and full-tree) must exit 0.

## Rationale

**Chosen approach**: reuse the frozen recipe verbatim, citing rules by
their `### N.` heading number (rule 1, rule 2, rule 3) within
`## Decision rules`, matching the citation convention already proven
for the `legal-compliance-*`, `finance-unit-economics-*`,
`partnerships-bd-*`, and `pricing-*` families (all already listed in
`scripts/procedure_authored_skills.txt`, per the survey). All 5 are
Shape A (single un-authored `## Decision rules` heading, no existing
Trigger/Procedure/Output shape) — the same classification the
localization (#1892), market-analysis (#1875), refactoring-legacy
(#1873), and capacity-planning (#1884) waves recorded for their own
families.

**Rejected alternative — cite rules by paragraph position instead of
the printed `### N.` heading number** (as the localization wave did,
since its `## Rules` items are unheaded inline-numbered paragraphs,
not `### N.` sub-headings): rejected because the brand-design family's
rules already carry an explicit, unambiguous `### N.` heading — using
paragraph position instead would introduce a second, redundant
numbering scheme with no benefit, and would diverge from the citation
form the already-authored `legal-compliance-*`/`finance-unit-economics-*`
families (same `### N.` + Decision-rules shape) already established as
the working convention for this exact structural shape.

**Rejected alternative — normalize the `## Decision rules` heading to
`## Rules`** (to match the pilot's own heading name) while inserting
the three new sections: rejected because the issue's non-goals scope
this wave to inserting Trigger/Procedure/Output-shape and deriving
`description:` only — renaming an existing heading is a content edit
outside the frozen recipe's five steps and outside the zero-rule-loss
guarantee's intent (the guarantee covers rule *lines*, not heading
text); the already-authored `legal-compliance-*` family also left its
own `## Decision rules` heading unchanged (confirmed in the survey),
so leaving it as-is is also the precedent-consistent choice.

## What will be done

1. For each of the 5 skills, read the existing `### N.` rule blocks
   under `## Decision rules`, then insert `## Trigger` / `## Procedure`
   / `## Output shape` between the framing paragraph and
   `## Decision rules`, with each Procedure step citing the rule
   number(s) it draws on (e.g. "(rule 1)").
2. Rewrite each skill's frontmatter `description:` as a sentence
   derived from that skill's own new `## Trigger` section (matching the
   pilot's "description derived from Trigger" step), keeping the "use
   when" trigger-marker substring.
3. Append the 5 skill directory names to
   `scripts/procedure_authored_skills.txt` (alphabetical, consistent
   with the existing file's per-wave grouping).
4. Run `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (must exit 0).
5. Run the rule-retention sweep: for each of the 5 files, diff
   pre-change vs. post-change `## Decision rules` rule blocks and
   confirm every pre-change `### N.` block (heading plus all five
   sub-bullets) is present post-change.
6. Run `python3 scripts/check_skill_conformance.py` (full-tree, no
   manifest arg) and confirm it still exits 0.
7. Run `git diff --stat` scoped to the working tree and confirm it
   lists only the 5 SKILL.md paths plus
   `scripts/procedure_authored_skills.txt`.
8. Commit, push branch `issue-1896-wave2a-brand-design`, open a PR
   against `tokenmaxxxer/skill-repository` main.
9. Paste all four check outputs plus the `git diff --stat` output into
   `docs/issue-1896/reports/implementation.md` (this repo), citing the
   skill-repository PR.

## Out of scope

- Any skill outside the 5 `brand-design-*` skills.
- Any edit to `scripts/check_skill_conformance.py` (checker logic).
- Any hook, gate, or CI config change.
- Renaming the `## Decision rules` heading, renumbering or rewording
  existing rule blocks, and any change to each file's
  `rule_count_floor:` frontmatter field.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 and reports the 5 new
  skills conformant.
- `python3 scripts/check_skill_conformance.py` (full-tree) exits 0.
- The rule-retention sweep shows every pre-change `## Decision rules`
  rule block present post-change for all 5 files (15/15 rules retained
  per the survey's count).
- `git diff --stat` lists exactly the 5 SKILL.md paths plus
  `scripts/procedure_authored_skills.txt`, nothing else.
