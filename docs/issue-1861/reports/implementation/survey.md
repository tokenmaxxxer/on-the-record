# Current-state survey: finance-unit-economics family, wave 2a

subject: issue-1861
role: implementation

## Scope

Checkout: fresh clone of `tokenmaxxxer/skill-repository` at
`/tmp/skill-repository-1861`, branch `issue-1861-wave2a-finance-unit-economics`,
based on `main` at commit `e4e01a9` (same tip the two prior wave-2a
deliveries — issue-1854 incident-response, issue-1853 ml-engineering —
landed against). canonical: `git log --oneline -3` in
/tmp/skill-repository-1861 showing `e4e01a9 Author procedural bodies for
wave 2a: incident-response family (issue-1854) (#19)` as HEAD.

## The 6 family skills

canonical: `git -C /tmp/skill-repository-1861 ls-files
'skills/finance-unit-economics-*'` — resolves to exactly 6 directories,
matching the issue's "6 skills" count (the issue body's parenthetical
"10 skills — the largest remaining family" does not match this count):

- `finance-unit-economics-cac-payback`
- `finance-unit-economics-evidence-chain`
- `finance-unit-economics-ltv-cac-band`
- `finance-unit-economics-ltv-churn-assumption`
- `finance-unit-economics-proposal-shape`
- `finance-unit-economics-sensitivity-scenario`

## Frontmatter shape

canonical: `grep '^description:' skills/finance-unit-economics-*/SKILL.md`
run in /tmp/skill-repository-1861 — all 6 still carry the un-authored
template description ("Use when you need guidance on <axis label> —
decision rules. Applies to the <axis> axis."), the same template shape
docs/issue-1790/reports/implementation.md's survey section records
finding on its 9 pre-change pilot skills.

## Body shape — all 6 are Shape A (procedure-shaped edit required)

canonical: `grep -c '^## ' skills/finance-unit-economics-*/SKILL.md` run
in /tmp/skill-repository-1861 — every file reports exactly 2 headings,
`## Decision rules` and `## Notes`. None carries `## Trigger`,
`## Procedure`, or `## Output shape` today. All 6 are therefore live
edits under the frozen recipe; the acceptance criterion's no-op/
empty-state clause (a family skill already procedure-shaped) does not
apply to any of the 6, mirroring the #1790 pilot and both prior wave-2a
deliveries (issue-1853, issue-1854).

## Rule numbering convention differs from the pilot family, matches pricing wave

canonical: read of `skills/finance-unit-economics-cac-payback/SKILL.md`
(full file) and `skills/pricing-design-rigor/SKILL.md` (lines 1-60) in
/tmp/skill-repository-1861 — the finance family's `## Decision rules`
section uses unordered `- **ADDITION**:` / `- **REMOVAL**:` bullets
(not the pilot's numbered `1. When ...` lines), the same bullet-tagged
shape the pricing family (issue-1847) already carried and successfully
authored Procedure steps against by citing rule position rather than a
printed number. Rule counts per file: derived: `grep -cE '^- \*\*(ADDITION|REMOVAL)\*\*'
skills/finance-unit-economics-*/SKILL.md` run in
/tmp/skill-repository-1861 — cac-payback 4, evidence-chain 5,
ltv-cac-band 5, ltv-churn-assumption 4, proposal-shape 4,
sensitivity-scenario 4 (26 rule bullets total across the family).

## Manifest state

canonical: `scripts/procedure_authored_skills.txt` (full file, 97 lines)
read in /tmp/skill-repository-1861 — lists the pilot's 9 skills plus the
5 prior wave families (technical-feasibility, release-engineering,
product-discovery, conformance-review, observability, legal-compliance,
ux-engineering, user-discovery, technical-writing, pricing,
ml-engineering, incident-response). No `finance-unit-economics-*` entry
exists yet; all 6 names are additions.

## Checker script

canonical: `scripts/check_skill_conformance.py` (154 lines) read in
/tmp/skill-repository-1861 — unchanged since #1790; `--manifest <path>`
opt-in check requires `## Trigger`, `## Procedure`, `## Output shape`
(any order) in the body of every manifest-listed skill directory. No
checker-logic change is needed or in scope (issue non-goal 3).

## Conclusion feeding the proposal

Recipe reuse is direct: same recipe, same checker, same manifest file,
same two live checks (`--manifest` run, full-tree run) plus the
rule-retention sweep and scoped `git diff --stat`, applied verbatim to 6
Shape-A skills whose only structural difference from the pilot is the
bullet-tagged (not numbered) rule-citation convention already precedented
by the pricing wave.
