# Current-state survey: capacity-planning family, wave 2a

subject: issue-1884
role: implementation

## Scope

Checkout: fresh clone of `tokenmaxxxer/skill-repository` at
`/tmp/skill-repository-1884`, branch `issue-1884-wave2a-capacity-planning`,
based on `main` at commit `0d300c9`. canonical: `git log --oneline -3` in
/tmp/skill-repository-1884 showing `0d300c9 Author procedural bodies for
wave 2a: refactoring-legacy family (issue-1873) (#26)` as HEAD.

## The 5 family skills

canonical: `git -C /tmp/skill-repository-1884 ls-files
'skills/capacity-planning-*'` — resolves to exactly 5 directories,
matching the issue's "5 skills" title count (the issue body's
parenthetical "10 skills — the largest remaining family" is stale
program-context text carried over from the #1790 pilot record, as in
every prior wave-2a issue, and does not match this family's actual
count):

- `capacity-planning-cost-attribution-at-trigger`
- `capacity-planning-demand-shape-and-forecast-method`
- `capacity-planning-expansion-trigger-threshold-sizing`
- `capacity-planning-headroom-band-and-degradation-risk`
- `capacity-planning-safety-buffer-sizing-by-criticality`

## Frontmatter shape

canonical: `grep '^description:' skills/capacity-planning-*/SKILL.md` run
in /tmp/skill-repository-1884 — all 5 still carry the un-authored
template description ("Use when you need guidance on <axis label> ...
Applies to the <axis> axis."), the same template shape every prior
wave-2a family's survey recorded finding pre-change.

## Body shape — all 5 are Shape A (procedure-shaped edit required)

canonical: `grep -c '^## ' skills/capacity-planning-*/SKILL.md` run in
/tmp/skill-repository-1884 — every file reports exactly 1 heading,
`## Rules`. None carries `## Trigger`, `## Procedure`, or `## Output
shape` today. All 5 are therefore live edits under the frozen recipe;
the acceptance criterion's no-op/empty-state clause (a family skill
already procedure-shaped) does not apply to any of the 5, mirroring the
#1790 pilot and every prior wave-2a delivery (issue-1853, issue-1854,
issue-1861, issue-1862, issue-1866, issue-1867, issue-1874, issue-1875,
issue-1873).

## Rule numbering convention

canonical: read of
`skills/capacity-planning-cost-attribution-at-trigger/SKILL.md` (lines
1-60) in /tmp/skill-repository-1884 — the family's `## Rules` section
uses numbered `1. When ...` lines, with some items tagged `**REMOVAL**:`
inline within the numbered item text, matching the #1790 pilot,
risk-management (issue-1867), market-analysis (issue-1875) and
refactoring-legacy (issue-1873) waves' numbered convention — not the
finance/pricing families' unordered `- **ADDITION**/**REMOVAL**:` bullet
convention. Most rule lines carry a trailing `source: <url>` citation
(some later-added items, e.g. rule 6 and rule 11 in
cost-attribution-at-trigger, omit the trailing `source:` — an existing
per-rule inconsistency in the pre-change files, not something this
wave's edit introduces or is asked to fix).

Rule counts per file: canonical: `grep -cE '^[0-9]+\.'
skills/capacity-planning-*/SKILL.md` run in /tmp/skill-repository-1884 —
cost-attribution-at-trigger 12, demand-shape-and-forecast-method 10,
expansion-trigger-threshold-sizing 12,
headroom-band-and-degradation-risk 12,
safety-buffer-sizing-by-criticality 11 (57 rule lines total across the
family). Every file's `rule_count_floor:` frontmatter field is 8
(canonical: `grep -n rule_count_floor skills/capacity-planning-*/SKILL.md`
run in /tmp/skill-repository-1884) — the live count exceeds the floor in
all 5 files, the same floor-as-lower-bound pattern the market-analysis
wave's survey noted for the risk-management family (unrelated to this
wave's scope and left unchanged).

## Manifest state

canonical: `grep -n capacity-planning
scripts/procedure_authored_skills.txt` in /tmp/skill-repository-1884 —
no match; canonical: `wc -l scripts/procedure_authored_skills.txt` — 133
lines, listing the pilot's 9 skills plus all prior wave families through
partnerships-bd (issue-1874) and refactoring-legacy (issue-1873). No
`capacity-planning-*` entry exists; all 5 names are additions.

## Checker script

canonical: `git -C /tmp/skill-repository-1884 log --oneline -1 --
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
`1.` lines, inline `**REMOVAL**:` tags, mostly-present per-rule
`source:` URLs) already matches the #1790 pilot and the prior wave-2a
families using the numbered convention — no citation-convention
adaptation is needed.
