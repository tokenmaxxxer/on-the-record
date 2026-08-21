# Current-state survey: risk-management family, wave 2a

subject: issue-1867
role: implementation

## Scope

Checkout: fresh clone of `tokenmaxxxer/skill-repository` at
`/tmp/skill-repository-1867`, branch `issue-1867-wave2a-risk-management`,
based on `main` at commit `e4e01a9` — the same tip the prior wave-2a
deliveries (issue-1853 ml-engineering, issue-1854 incident-response,
issue-1861 finance-unit-economics) landed against. canonical: `git log
--oneline -3` in /tmp/skill-repository-1867 showing `e4e01a9 Author
procedural bodies for wave 2a: incident-response family (issue-1854)
(#19)` as HEAD.

## The 5 family skills

canonical: `git -C /tmp/skill-repository-1867 ls-files
'skills/risk-management-*'` — resolves to exactly 5 directories,
matching the issue's "5 skills" title count (the issue body's
parenthetical "10 skills — the largest remaining family" is stale
program-context text carried over from the #1790 pilot record and does
not match this family's actual count):

- `risk-management-aggregation-consolidation`
- `risk-management-appetite-tolerance-threshold`
- `risk-management-likelihood-impact-scale`
- `risk-management-monitoring-review-cadence`
- `risk-management-response-strategy-selection`

## Frontmatter shape

canonical: `grep '^description:' skills/risk-management-*/SKILL.md` run
in /tmp/skill-repository-1867 — all 5 still carry the un-authored
template description ("Use when you need guidance on <axis label> —
..."), the same template shape the #1790 pilot's survey recorded finding
on its 9 pre-change skills.

## Body shape — all 5 are Shape A (procedure-shaped edit required)

canonical: `grep -c '^## ' skills/risk-management-*/SKILL.md` run in
/tmp/skill-repository-1867 — every file reports exactly 1 heading,
`## Decision rules` (no `## Notes` section, unlike the finance-unit-
economics family). None carries `## Trigger`, `## Procedure`, or
`## Output shape` today. All 5 are therefore live edits under the
frozen recipe; the acceptance criterion's no-op/empty-state clause (a
family skill already procedure-shaped) does not apply to any of the 5,
mirroring the #1790 pilot and all four prior wave-2a deliveries
(issue-1853, issue-1854, issue-1861, issue-1862).

## Rule numbering convention matches the pilot family directly

canonical: read of `skills/risk-management-aggregation-consolidation/SKILL.md`
(lines 1-80) in /tmp/skill-repository-1867 — the family's `## Decision
rules` section uses numbered `1. When ...` lines (some tagged
"Removal:" inline within the numbered item, not as a separate bullet
marker), the same numbered convention the #1790 pilot's own family used
— not the finance/pricing families' unordered `- **ADDITION**/
**REMOVAL**:` bullet convention. Rule counts per file: derived: `grep
-cE '^[0-9]+\.' skills/risk-management-*/SKILL.md` run in
/tmp/skill-repository-1867 — aggregation-consolidation 5,
appetite-tolerance-threshold 5, likelihood-impact-scale 5,
monitoring-review-cadence 5, response-strategy-selection 6 (26 rule
lines total across the family, matching each file's `rule_count_floor:
10` frontmatter field being an upper planning bound rather than the
live count — unrelated to this wave's scope and left unchanged).

## Manifest state

canonical: `scripts/procedure_authored_skills.txt` (full file, 96
lines) read in /tmp/skill-repository-1867 — lists the pilot's 9 skills
plus the prior wave families (technical-feasibility, release-
engineering, product-discovery, conformance-review, observability,
legal-compliance, ux-engineering, user-discovery, technical-writing,
pricing, ml-engineering, incident-response); finance-unit-economics and
customer-support are not yet present either (their phase-2 delivery has
not landed against this checkout's tip). No `risk-management-*` entry
exists; all 5 names are additions.

## Checker script

canonical: `scripts/check_skill_conformance.py` (154 lines) read in
/tmp/skill-repository-1867 — unchanged since #1790; `--manifest <path>`
opt-in check requires `## Trigger`, `## Procedure`, `## Output shape`
(any order) in the body of every manifest-listed skill directory. No
checker-logic change is needed or in scope (issue non-goal 3).

## Conclusion feeding the proposal

Recipe reuse is direct: same recipe, same checker, same manifest file,
same two live checks (`--manifest` run, full-tree run) plus the
rule-retention sweep and scoped `git diff --stat`, applied verbatim to 5
Shape-A skills whose rule-citation convention (numbered `1.` lines,
including inline "Removal:" tags) already matches the #1790 pilot's own
family — no citation-convention adaptation is needed, unlike the
finance-unit-economics and pricing waves.
