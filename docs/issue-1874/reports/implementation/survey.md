# Current-state survey: partnerships-bd family, wave 2a

subject: issue-1874
role: implementation

## Scope

Checkout: `/tmp/skill-repository`, `git checkout main && git pull
--ff-only`, landing at `main` commit `4b2a372` ("Author procedural
bodies for wave 2a: risk-management family (issue-1867) (#23)") — the
tip named in this session's own role-mapping banner. canonical: `git
log -1 --oneline` in /tmp/skill-repository — `4b2a372 Author procedural
bodies for wave 2a: risk-management family (issue-1867) (#23)`.

## The 5 family skills

canonical: `ls skills | grep partnerships-bd` run in
/tmp/skill-repository — resolves to exactly 5 directories, matching the
issue's title count ("5 skills"); the issue body's Program-context
parenthetical "10 skills — the largest remaining family" is stale text
and does not match this live listing. The Requirements section's
explicit "All 5 partnerships-bd-* skills" wording governs:

- `partnerships-bd-deal-structure-selection`
- `partnerships-bd-exclusivity-and-scope-terms`
- `partnerships-bd-governance-cadence-and-kpi`
- `partnerships-bd-negotiation-positioning`
- `partnerships-bd-term-sheet-comprehensibility-and-convention`

## Frontmatter shape

canonical: `grep '^description:' skills/partnerships-bd-*/SKILL.md` run
in /tmp/skill-repository — all 5 still carry the un-authored template
description ("Use when you need guidance on <axis label> rules. Applies
to the <axis> axis.").

## Body shape — all 5 are Shape A (procedure-shaped edit required)

canonical: `grep -n '^## ' skills/partnerships-bd-*/SKILL.md` run in
/tmp/skill-repository — every file reports exactly one heading,
`## Decision rules`. None carries `## Trigger`, `## Procedure`, or
`## Output shape`. All 5 are therefore live edits under the frozen
recipe (Shape A); the acceptance criterion's no-op/empty-state clause
(a family skill already procedure-shaped) does not apply to any of the
5.

## Rule numbering convention — heading-level, not inline-numbered

canonical: read of `skills/partnerships-bd-deal-structure-selection/SKILL.md`
(lines 1-30) in /tmp/skill-repository — this family's `## Decision
rules` section numbers each rule as its own level-3 heading
(`### 1. Pick governance structure by ...`, `### 2. Default to the
lightest vehicle ...`, `### 3. Remove a revenue-share structure ...`),
each followed by `- **Condition** ... **Choice** ... **Why** ...
**Source** ... **Counter-example test** ...` on a single bullet line.
canonical: `grep -n '^### ' skills/risk-management-aggregation-consolidation/SKILL.md`
run in /tmp/skill-repository — that family's own rules print as flat
`1. When ... — ...` numbered paragraphs under `## Decision rules`, not
level-3 headings, confirming the markup token differs between the two
families while the printed rule number itself remains citable in both
("rule 2" is a valid citation either way).

canonical: `grep -c '^### [0-9]' skills/partnerships-bd-*/SKILL.md` run
in /tmp/skill-repository — every one of the 5 files reports exactly 3
(15 rule headings total across the family), matching each file's
frontmatter `rule_count_floor: 3` — canonical: `grep 'rule_count_floor'
skills/partnerships-bd-*/SKILL.md` run in /tmp/skill-repository, all 5
report `rule_count_floor: 3`, i.e. floor equals live count in this
family. This floor-vs-live-count relationship is unrelated to this
wave's scope (no frontmatter numeric field is part of the frozen
recipe's write set) and is left unchanged.

## Manifest state

canonical: `wc -l scripts/procedure_authored_skills.txt` run in
/tmp/skill-repository — 118 lines total. canonical: `tail -20
scripts/procedure_authored_skills.txt` run in /tmp/skill-repository —
the most recent 5 entries are the risk-management family
(`risk-management-aggregation-consolidation` …
`risk-management-response-strategy-selection`). No `partnerships-bd-*`
entry exists in the file; all 5 names are additions.

## Checker script

canonical: `ls scripts/check_skill_conformance.py` and `git log --
scripts/check_skill_conformance.py` (latest touching commit predates
`4b2a372`), both run in /tmp/skill-repository — the checker script is
present and no commit since the surveyed tip has touched it. Per prior
reads of this same script (docs/issue-1867/reports/implementation/survey.md,
"Checker script" section), `--manifest <path>` opt-in check requires
`## Trigger`, `## Procedure`, `## Output shape` (any order) in the body
of every manifest-listed skill directory. No checker-logic change is
needed or in scope (issue non-goal 3).

## Conclusion feeding the proposal

Recipe reuse is direct: same recipe, same checker, same manifest file,
same two live checks (`--manifest` run, full-tree run) plus the
rule-retention sweep and scoped `git diff --stat`, applied verbatim to 5
Shape-A skills. The one adaptation this family needs relative to the
secure-coding/risk-management precedent (per the "Rule numbering
convention" section above) is citation surface, not citation method:
Procedure steps cite `### N. <title>` heading numbers (e.g. "rule 2")
rather than inline-numbered-paragraph numbers — the printed number is
still authoritative and citable either way, so no bullet-position
translation (the finance-unit-economics/pricing waves' adaptation) is
needed here.
