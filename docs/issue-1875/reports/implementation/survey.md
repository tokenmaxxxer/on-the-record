# Current-state survey: market-analysis family, wave 2a

subject: issue-1875
role: implementation

## Scope

Checkout: fresh clone of `tokenmaxxxer/skill-repository` at
`/tmp/skill-repository-1875`, branch
`issue-1875-wave2a-market-analysis`, based on `main` at commit
`4b2a372` — the same tip cited in this session's invocation prompt
("skill-repository 4b2a372"). canonical: `git log --oneline -3` in
/tmp/skill-repository-1875 showing `4b2a372 Author procedural bodies
for wave 2a: risk-management family (issue-1867) (#23)` as HEAD.

## The 5 family skills

canonical: `git -C /tmp/skill-repository-1875 ls-files
'skills/market-analysis-*'` — resolves to exactly 5 directories,
matching the issue's "5 skills" title count (the issue body's
parenthetical "10 skills — the largest remaining family" is stale
program-context text carried over from the #1790 pilot record, as in
every prior wave-2a issue, and does not match this family's actual
count):

- `market-analysis-competitor-mapping`
- `market-analysis-evidence-rigor`
- `market-analysis-five-forces`
- `market-analysis-jtbd-fit`
- `market-analysis-mece-proposal`

## Frontmatter shape

canonical: `grep '^description:' skills/market-analysis-*/SKILL.md` run
in /tmp/skill-repository-1875 — all 5 still carry the un-authored
template description ("Use when you need guidance on <axis label>
... Applies to the <axis> axis."), the same template shape the #1790
pilot's survey recorded finding on its 9 pre-change skills.

## Body shape — all 5 are Shape A (procedure-shaped edit required)

canonical: `grep -c '^## ' skills/market-analysis-*/SKILL.md` run in
/tmp/skill-repository-1875 — every file reports exactly 1 heading,
`## Rules` (not `## Decision rules`, the risk-management family's
heading text — a per-family naming difference, not a structural one).
None carries `## Trigger`, `## Procedure`, or `## Output shape` today.
All 5 are therefore live edits under the frozen recipe; the acceptance
criterion's no-op/empty-state clause (a family skill already
procedure-shaped) does not apply to any of the 5, mirroring the #1790
pilot and every prior wave-2a delivery (issue-1853, issue-1854,
issue-1861, issue-1862, issue-1866, issue-1867).

## Rule numbering convention

canonical: read of
`skills/market-analysis-competitor-mapping/SKILL.md` (lines 1-80) in
/tmp/skill-repository-1875 — the family's `## Rules` section uses
numbered `1. When ...` lines, with some items tagged `**REMOVAL**:`
inline within the numbered item text (not a separate bullet marker) —
the same numbered convention the #1790 pilot family and the
risk-management wave (issue-1867) both used, not the finance/pricing
families' unordered `- **ADDITION**/**REMOVAL**:` bullet convention.
Every rule line also carries a trailing `source: <url>` citation,
consistent across all 5 files. Rule counts per file: canonical: `grep
-cE '^[0-9]+\.' skills/market-analysis-*/SKILL.md` run in
/tmp/skill-repository-1875 — competitor-mapping 10, evidence-rigor 10,
five-forces 10, jtbd-fit 10, mece-proposal 10 (50 rule lines total
across the family, exactly matching each file's `rule_count_floor: 10`
frontmatter field — unlike the risk-management family where the floor
was an upper planning bound above the live count, this family's live
count already equals its floor; unrelated to this wave's scope and
left unchanged).

## Manifest state

canonical: `grep -n market-analysis
scripts/procedure_authored_skills.txt` in /tmp/skill-repository-1875 —
no match; canonical: `wc -l scripts/procedure_authored_skills.txt` —
118 lines, listing the pilot's 9 skills plus all prior wave families
through customer-support (issue-1862), secure-coding (issue-1866), and
risk-management (issue-1867). No `market-analysis-*` entry exists; all
5 names are additions.

## Checker script

canonical: `git -C /tmp/skill-repository-1875 log --oneline -1 --
scripts/check_skill_conformance.py` — last touched at `bb89bdc` (the
#1790 pilot commit), unchanged since. `--manifest <path>` opt-in check
requires `## Trigger`, `## Procedure`, `## Output shape` (any order) in
the body of every manifest-listed skill directory. No checker-logic
change is needed or in scope (issue non-goal 3).

## Conclusion feeding the proposal

Recipe reuse is direct: same recipe, same checker, same manifest file,
same four live checks (manifest-scoped checker run, rule-retention
sweep, scoped `git diff --stat`, full-tree checker run), applied
verbatim to 5 Shape-A skills whose rule-citation convention (numbered
`1.` lines, inline `**REMOVAL**:` tags, per-rule `source:` URLs)
already matches the #1790 pilot and risk-management wave's convention
— no citation-convention adaptation is needed, unlike the
finance-unit-economics and pricing waves.
