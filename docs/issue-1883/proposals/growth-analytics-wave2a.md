---
status: proposed
files:
  - docs/issue-1883/proposals/growth-analytics-wave2a.md
  - docs/issue-1883/reports/implementation.md
---

# Proposal: procedural-body authoring, growth-analytics family (wave 2a)

subject: issue-1883
role: implementation

## Request

Apply the frozen WAVE RECIPE (docs/issue-1790/reports/implementation.md,
"WAVE RECIPE" section) to the 5 `growth-analytics-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger` / `## Procedure` /
`## Output shape` at the top of each body (Procedure steps citing rule
numbers), rewrite each `description:` from its authored Trigger section,
append the 5 names to `scripts/procedure_authored_skills.txt`
incrementally, zero rule-line loss, guidance-only content (no checker or
hook changes). Deliver as a skill-repository PR plus this issue's own
record, repeating the pilot's four checks against this wave's scope.

## Constraints

- Write set is bounded to the 5 `growth-analytics-*` skill directories'
  `SKILL.md` files plus `scripts/procedure_authored_skills.txt` in the
  skill-repository checkout — issue non-goal 3 forbids touching any
  other family, checker logic, or hooks.
- No rule line may be lost or reworded away from its source content —
  the rule-retention sweep (pre-change vs. post-change rule text) must
  show every pre-existing rule line present post-change.
- Both live checks (`--manifest` run, full-tree run) must exit 0 before
  landing.
- Descriptions must retain the checker's trigger-marker substring ("use
  when").
- This is phase-1: this proposal and the survey are the only files this
  session writes now; `docs/issue-1883/reports/implementation.md` (the
  phase-2 record) waits for the Approve per contract v3 s19.

## Rationale

**Chosen: apply the frozen recipe verbatim, treating the missing `##
Decision rules` wrapper as a body-shape variant, not a recipe
deviation.** The survey (docs/issue-1883/reports/implementation/survey.md,
"Body shape" section) found this family has no `## ` heading at all —
rules sit as a flat numbered list directly under the H1. The recipe's
step 2 says to insert the three new headings "between the framing
paragraph and `## Rules`"; here there is no `## Rules` heading to anchor
against, only the first numbered rule. Inserting the block between the
H1's framing paragraph and rule 1 preserves the recipe's intent (new
headings precede the rule content) without requiring a recipe rewrite,
and matches how the risk-management wave (docs/issue-1874's precedent
citation) already handled flat, non-heading-numbered rule bodies.

**Rejected alternative: treat the absence of `## Decision rules` as
Shape B (already procedure-shaped) and file a recipe-scope deviation
before touching these skills.** Rejected because the survey's actual
`## Trigger`/`## Procedure`/`## Output shape` check (the same check the
recipe and checker both use to decide Shape A vs. B) found none of the
three headings in any of the 5 files — the missing `## Decision rules`
wrapper is a structural variant in how rules are printed, not evidence
that the skill is already procedure-shaped. Escalating this as a
deviation would misclassify a routine body-shape variant (already seen
once, in the risk-management wave) as a scope question needing
resolution outside this wave.

**Rejected alternative: renumber rules under a newly-inserted `##
Decision rules` heading to normalize this family to the
partnerships-bd/refactoring-legacy heading style.** Rejected because
issue non-goal 3 scopes this wave to guidance-only Trigger/Procedure/
Output-shape authoring, not restructuring existing rule markup;
inserting a heading the source skill never had would itself be a
content edit outside the frozen recipe's write set, and would risk the
rule-retention sweep flagging a spurious loss/rewrite where none of
substance occurred.

## What will be done

1. Fresh checkout: `cd /tmp/skill-repository && git checkout main && git
   pull --ff-only`.
2. For each of the 5 `growth-analytics-*` skills: read the existing
   rules (flat numbered paragraphs under the H1), author `## Trigger`
   (concrete distinguishing conditions vs. sibling axes in the same
   family), `## Procedure` (ordered steps citing the printed rule
   numbers, e.g. "rule 2"), and `## Output shape` (what applying the
   skill produces), inserted between the H1's framing paragraph and rule
   1. Rewrite `description:` as a sentence derived from the new Trigger
   content, keeping the "use when" trigger-marker substring.
3. Append the 5 skill directory names to
   `scripts/procedure_authored_skills.txt`.
4. Run `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0) and the
   full-tree run with no flag (expect exit 0).
5. Run the rule-retention sweep: diff each file's pre-change rule text
   against post-change, confirming every pre-existing rule line is still
   present.
6. `git diff --stat` scoped to the 5 skill paths plus the manifest file,
   confirming no other path changed.
7. Commit on a skill-repository branch, open a skill-repository PR.
8. Write `docs/issue-1883/reports/implementation.md` (phase-2 record)
   pasting all four check outputs and the scoped `git diff --stat`,
   citing this proposal and the skill-repository PR/commit.

## Out of scope

- Any family other than `growth-analytics-*` (issue non-goal 3).
- Any change to `scripts/check_skill_conformance.py` or any hook (issue
  non-goal 3).
- Restructuring rule markup (e.g. adding a `## Decision rules` heading)
  beyond the three new Trigger/Procedure/Output-shape headings.
- Any frontmatter field other than `description:` (e.g.
  `rule_count_floor`, `axis`) — left unchanged.

## How you'll know it worked

- The four check outputs (manifest-run exit 0, full-tree-run exit 0,
  rule-retention sweep showing zero loss, scoped `git diff --stat`
  showing only the 5 skill paths + manifest) are pasted live in
  `docs/issue-1883/reports/implementation.md`, executed from the
  skill-repository checkout, per Acceptance criteria 1 and 2.
- All 5 `growth-analytics-*` names appear in
  `scripts/procedure_authored_skills.txt` on the skill-repository PR
  branch.
