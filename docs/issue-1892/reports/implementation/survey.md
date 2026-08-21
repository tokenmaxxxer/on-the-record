# Current-state survey: localization family, wave 2a

subject: issue-1892
role: implementation

## Scope

Checkout: fresh clone of `tokenmaxxxer/skill-repository` at
`/tmp/skill-repository-1892`, branch `issue-1892-wave2a-localization`,
based on `main` at commit `1d6ecd5`. canonical: `git -C
/tmp/skill-repository-1892 log --oneline -3` showing `1d6ecd5 Author
procedural bodies for wave 2a: knowledge-management family
(issue-1882)` as HEAD.

## The 5 family skills

canonical: `git -C /tmp/skill-repository-1892 ls-files
'skills/localization-*'` — resolves to exactly 5 directories, matching
the issue's "5 skills" title count (the issue body's parenthetical "10
skills — the largest remaining family" is stale program-context text
carried over from the #1790 pilot record, as in every prior wave-2a
issue, and does not match this family's actual count):

- `localization-locale-convention-formatting`
- `localization-pluralization-and-grammar`
- `localization-rtl-and-script-support`
- `localization-string-externalization`
- `localization-text-expansion-and-layout`

## Frontmatter shape

canonical: `grep '^description:' skills/localization-*/SKILL.md` run in
/tmp/skill-repository-1892 — all 5 still carry the un-authored template
description ("Use when you need guidance on Decision axis: ... Applies
to the ... axis."), the same template shape every prior wave-2a family's
survey recorded finding pre-change.

## Body shape — all 5 are Shape A (procedure-shaped edit required)

canonical: `grep -c '^## ' skills/localization-*/SKILL.md` run in
/tmp/skill-repository-1892 — every file reports exactly 1 heading, `##
Rules`. None carries `## Trigger`, `## Procedure`, or `## Output shape`
today. All 5 are therefore live edits under the frozen recipe; the
acceptance criterion's no-op/empty-state clause (a family skill already
procedure-shaped) does not apply to any of the 5, mirroring the #1790
pilot and every prior wave-2a delivery (issue-1853, issue-1854,
issue-1861, issue-1862, issue-1866, issue-1867, issue-1874, issue-1875,
issue-1873, issue-1884, issue-1883, issue-1882).

## Rule numbering convention

canonical: read of
`skills/localization-locale-convention-formatting/SKILL.md` (lines
1-90) in /tmp/skill-repository-1892 — the family's `## Rules` section
uses numbered `1. **when** ... **choose** ...` lines, with some items
tagged `REMOVAL —` inline within the numbered item text, matching the
#1790 pilot, risk-management (issue-1867), market-analysis (issue-1875),
refactoring-legacy (issue-1873), and capacity-planning (issue-1884)
waves' numbered convention — not the finance/pricing families'
unordered `- **ADDITION**/**REMOVAL**:` bullet convention.

derived:
```
grep -cE '^[0-9]+\. \*\*' skills/localization-*/SKILL.md
```
run in /tmp/skill-repository-1892 — rule counts per file:
locale-convention-formatting 7, pluralization-and-grammar 6,
rtl-and-script-support 5, string-externalization 9,
text-expansion-and-layout 5 (32 rule lines total across the family).
Every file's `rule_count_floor:` frontmatter field is 10 (canonical:
`grep -n rule_count_floor skills/localization-*/SKILL.md` run in
/tmp/skill-repository-1892) — the live count is below the floor in all
5 files, the inverse of the capacity-planning wave's (#1884) "count
exceeds floor" note but the same floor-as-non-binding-target pattern
noted there and in the market-analysis wave's survey (#1875); unrelated
to this wave's scope (a structural edit, not a rule-content edit) and
left unchanged.

derived:
```
for f in skills/localization-*/SKILL.md; do echo "$f: $(grep -c 'source:' "$f")"; done
```
run in /tmp/skill-repository-1892 — per-file `source:` line counts:
locale-convention-formatting 6, string-externalization 7,
pluralization-and-grammar 6, rtl-and-script-support 5,
text-expansion-and-layout 5. Comparing against the rule counts above,
two files carry fewer `source:` lines than rule lines
(locale-convention-formatting: 6 vs. 7 rules; string-externalization: 7
vs. 9 rules) — an existing per-rule inconsistency in the pre-change
files (the same class of gap the capacity-planning wave's survey
recorded for its own family), not something this wave's edit introduces
or is asked to fix.

## Manifest state

canonical: `grep -n localization scripts/procedure_authored_skills.txt`
in /tmp/skill-repository-1892 — no match (grep exit 1); canonical: `wc
-l scripts/procedure_authored_skills.txt` — 138 lines, listing the
pilot's 9 skills plus all prior wave families through
knowledge-management (issue-1882). No `localization-*` entry exists;
all 5 names are additions.

## Checker script

canonical: `git -C /tmp/skill-repository-1892 log --oneline -1 --
scripts/check_skill_conformance.py` — last touched at `bb89bdc` (the
#1790 pilot commit), unchanged since. `--manifest <path>` opt-in check
requires `## Trigger`, `## Procedure`, `## Output shape` (any order) in
the body of every manifest-listed skill directory. No checker-logic
change is needed or in scope (issue non-goal 3).

## Pre-change checker baseline

canonical: `python3 scripts/check_skill_conformance.py --manifest
scripts/procedure_authored_skills.txt` run in /tmp/skill-repository-1892
— exit 0, "234 skills checked" (the 5 localization skills are not yet
manifest-listed, so this run does not check them). canonical: `python3
scripts/check_skill_conformance.py` (full-tree, no manifest arg) run in
/tmp/skill-repository-1892 — exit 0, "234 skills checked".

## Conclusion feeding the proposal

Recipe reuse is direct: same recipe, same checker, same manifest file,
same four live checks (manifest-scoped checker run, rule-retention
sweep, full-tree checker run, scoped `git diff --stat`) as every prior
wave-2a family. All 5 skills are Shape A. Rule citation is by existing
line number (no new numbering scheme needed), matching the
risk-management, market-analysis, refactoring-legacy, and
capacity-planning precedent.
