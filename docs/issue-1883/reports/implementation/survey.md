# Current-state survey: growth-analytics family, wave 2a

subject: issue-1883
role: implementation

## Scope

Checkout: `/tmp/skill-repository`, `git checkout main && git pull
--ff-only`, landing at `main` commit `0d300c9` ("Author procedural
bodies for wave 2a: refactoring-legacy family (issue-1873) (#26)").
canonical: `git log -1 --oneline` in /tmp/skill-repository — `0d300c9
Author procedural bodies for wave 2a: refactoring-legacy family
(issue-1873) (#26)`.

## The 5 family skills

canonical: `ls skills | grep growth-analytics` run in
/tmp/skill-repository — resolves to exactly 5 directories, matching the
issue's title count ("5 skills"); the issue body's Program-context
parenthetical "10 skills — the largest remaining family" is stale text
carried over from the #1790 pilot survey's family-size table and does
not match this live listing. The Requirements section's explicit "All 5
growth-analytics-* skills" wording governs:

- `growth-analytics-experiment-trust`
- `growth-analytics-funnel-stage-attribution`
- `growth-analytics-metric-selection`
- `growth-analytics-reporting-reduction`
- `growth-analytics-segmentation`

## Frontmatter shape

canonical: `grep '^description:' skills/growth-analytics-*/SKILL.md` run
in /tmp/skill-repository — all 5 still carry the un-authored template
description ("Use when you need guidance on <axis label> rules. Applies
to the <axis> axis.").

## Body shape — all 5 are Shape A (procedure-shaped edit required)

canonical: `grep -n '^## ' skills/growth-analytics-*/SKILL.md` run in
/tmp/skill-repository — returns **no matches for any of the 5 files**:
unlike the partnerships-bd/risk-management/refactoring-legacy
precedents, this family carries no `## Decision rules` (or any other
`## `) heading at all — the rules sit as a flat numbered list directly
under the `# <Title>` H1, with no intervening H2. None of the 5 carries
`## Trigger`, `## Procedure`, or `## Output shape` either. All 5 are
therefore live edits under the frozen recipe (Shape A); the acceptance
criterion's no-op/empty-state clause (a family skill already
procedure-shaped) does not apply to any of the 5.

## Rule numbering convention — flat top-level numbered paragraphs

canonical: read of
`skills/growth-analytics-experiment-trust/SKILL.md` (lines 1-30) in
/tmp/skill-repository — rules print as `1. **When** ... **run** ...`
flat numbered paragraphs directly under the H1 title (no `## Decision
rules` wrapper), each closed with a `Source:` line. canonical: `grep -c
'^[0-9]\+\. \*\*' skills/growth-analytics-*/SKILL.md` run in
/tmp/skill-repository — counts of 3, 2, 2, 2, 2 respectively (11 rules
total across the family), matching each file's frontmatter
`rule_count_floor` (`3, 2, 2, 2, 2` per `grep -n
'^rule_count_floor' skills/growth-analytics-*/SKILL.md`) — floor equals
live count in every file of this family.

canonical: docs/issue-1874/reports/implementation/survey.md, "Rule
numbering convention" section — that survey found "that family's own
rules print as flat `1. When ... — ...` numbered paragraphs ... not
level-3 headings" for risk-management. This growth-analytics family
matches that same flat-printed-number style rather than the
partnerships-bd/refactoring-legacy `### N. <title>` heading style —
Procedure steps in this wave cite the printed rule number directly
(e.g. "rule 2"), no heading-anchor translation needed. The floor-equals-
live-count relationship noted above is, per the same partnerships-bd
survey's own note, unrelated to this wave's scope (no frontmatter
numeric field is part of the frozen recipe's write set) and is left
unchanged here too.

## Manifest state

canonical: `wc -l scripts/procedure_authored_skills.txt` run in
/tmp/skill-repository — 133 lines total. canonical: `tail -5
scripts/procedure_authored_skills.txt` run in /tmp/skill-repository —
the most recent 5 entries are the refactoring-legacy family
(`refactoring-legacy-characterization-test-scope` …
`refactoring-legacy-verification-cadence`). No `growth-analytics-*`
entry exists in the file; all 5 names are additions.

## Checker script

canonical: `ls scripts/check_skill_conformance.py` run in
/tmp/skill-repository — present. Per prior reads of this same script
across every precedent wave survey back to #1790, `--manifest <path>`
opt-in check requires `## Trigger`, `## Procedure`, `## Output shape`
(any order) in the body of every manifest-listed skill directory; the
full-tree run (no flag) checks structural conformance across the whole
repo. No checker-logic change is needed or in scope (issue non-goal 3).

## Conclusion feeding the proposal

Recipe reuse is direct: same recipe, same checker, same manifest file,
same two live checks (`--manifest` run, full-tree run) plus the
rule-retention sweep and scoped `git diff --stat`, applied verbatim to 5
Shape-A skills. The one adaptation this family needs relative to the
partnerships-bd/refactoring-legacy precedent is the absence of a `##
Decision rules` wrapper: the new `## Trigger` / `## Procedure` / `##
Output shape` block inserts between the H1 title paragraph and the
first flat numbered rule (rule 1), not after a `## Decision rules`
heading that does not exist here. Procedure steps cite the printed
rule number (e.g. "rule 2") — same citation surface as the
risk-management precedent, no bullet-position or heading-anchor
translation needed.
