---
subject: issue-1854
type: survey
---

# Survey: incident-response family (wave 2a)

## Role mapping vs. checked-out HEAD

canonical: `gh issue view 1854` (read live) — the prompt states this
role is mapped by role-source-allowlist (issue #1758) to skill-repository
commit `87f3961` for guidance skills. derived: `git log --oneline -3` on
a fresh clone at `/tmp/skill-repository-1854` off `origin/main` shows
HEAD `87f3961` ("Author procedural bodies for wave 2h: technical-writing
family (issue-1844) (#16)") — the mapped commit and this checkout's live
HEAD are the same commit, so there is no ancestry gap to reconcile: the
role-mapping guidance and the actual skill-repository write surface are
already in sync for this wave.

## Count discrepancy in the issue body

canonical: `gh issue view 1854` (read live) — the "Program context"
paragraph states "Family: incident-response (10 skills — the largest
remaining family per the pilot survey)", but the issue title says "(6
skills)" and Requirement 1 says "All 6 incident-response-* skills".
derived: `find /tmp/skill-repository-1854/skills -maxdepth 1 -iname
"incident-response-*"` lists exactly 6 directories (below) — the live
checkout matches the title and Requirement 1's count of 6, not the
Program-context paragraph's 10. canonical:
docs/issue-1844/reports/implementation/survey.md, "Count discrepancy in
the issue body" section (read live) — wave-2h's technical-writing survey
found the identical stale-"10 skills" Program-context wording for its own
family and resolved it the same way: proceed against the 6-skill count
title/Requirements/checkout agree on.

## Checkout and manifest state

canonical: fresh clone at `/tmp/skill-repository-1854` off
`origin/main`, read live via `git log --oneline -3` — HEAD `87f3961`.
Branch `issue-1854-wave2a-incident-response` created off `origin/main`
for this wave, isolated from other prior waves' scratch checkouts under
`/tmp/skill-repository-*`. canonical:
docs/issue-1844/reports/implementation/survey.md, "Checkout and manifest
state" section (read live) — every prior wave's survey established this
same fresh-clone-per-wave isolation convention; this wave follows it.

canonical: `wc -l scripts/procedure_authored_skills.txt` and `grep -c
"^incident-response-" scripts/procedure_authored_skills.txt` (both read
live) — the manifest currently lists 78 names: 9 pilot plus 69 prior-wave
entries (waves 2a-2h through wave-2h technical-writing). 0
`incident-response-*` entries present yet.

canonical: `python3 scripts/check_skill_conformance.py` (full-tree, read
live) — exit 0, "234 skills checked", confirming the checker is currently
green before this wave's changes. canonical: `python3
scripts/check_skill_conformance.py --manifest
scripts/procedure_authored_skills.txt` (read live) — exit 0 on the
pre-change manifest, confirming the manifest-scoped check is also green
before this wave's changes.

## Family enumeration

derived: `find skills -maxdepth 1 -iname "incident-response-*" | sort` —
6 directories, matching the issue title and Requirement 1's count:

```
skills/incident-response-action-item-quality
skills/incident-response-blameless-language-editing
skills/incident-response-rca-method-selection
skills/incident-response-severity-classification-scoping
skills/incident-response-timeline-construction
skills/incident-response-tool-landscape
```

## Shape split — uniform Shape A, no headless or Shape-B member

canonical: `sed -n '1,20p' skills/incident-response-*/SKILL.md` and
`grep -n "^## " skills/incident-response-*/SKILL.md` (both read live) —
all 6 files carry a single heading, `## Rules`, each with a
`rule_count_floor: 4` line in YAML frontmatter (the pilot-equivalent
Shape A structure):

```
incident-response-action-item-quality:              rule_count_floor: 4, "## Rules"
incident-response-blameless-language-editing:        rule_count_floor: 4, "## Rules"
incident-response-rca-method-selection:              rule_count_floor: 4, "## Rules"
incident-response-severity-classification-scoping:   rule_count_floor: 4, "## Rules"
incident-response-timeline-construction:             rule_count_floor: 4, "## Rules"
incident-response-tool-landscape:                    rule_count_floor: 4, "## Rules"
```

Unlike wave-2h's `technical-writing-tool-landscape` (headless, no
heading at all) and unlike wave-2e/2f/2g's Shape-B `-research-log`
members, this family's own `incident-response-tool-landscape` **does**
carry an explicit `## Rules` heading before its numbered entries —
already cited as the counter-example in wave-2h's own survey (canonical:
docs/issue-1844/reports/implementation/survey.md, "Precedent for the
headless numbered-list citation target" section, read live: "canonical:
`skills/incident-response-tool-landscape/SKILL.md` (read live) — ... does
carry an explicit `## Rules` heading"). derived: re-confirmed directly
against this checkout — `grep -n "^## "
skills/incident-response-tool-landscape/SKILL.md` returns `19:## Rules`,
matching. So this wave's split is **6 Shape A, 0 headless, 0 Shape-B** —
no new sub-case beyond the pilot's own structure; this family has no
`-research-log` member (derived: `find skills -maxdepth 1 -iname
"incident-response-research-log"` — no match).

None of the 6 files carry `## Trigger`/`## Procedure`/`## Output shape`
yet (derived: `grep -c "^## Trigger\|^## Procedure\|^## Output shape"
skills/incident-response-*/SKILL.md` — 0 for every file), so none
qualifies for the recipe's no-op/empty-state clause.

## Checker mechanics

canonical: `git log -1 --format=%H -- scripts/check_skill_conformance.py`
(read live) returns `bb89bdc1ba7458fdf7c4ee494a3c0ea70cd65322` — the
pilot commit — confirming the checker has had zero logic edits across
the pilot and every wave merged to `origin/main` through this checkout's
HEAD `87f3961`. `--manifest <path>` requires `## Trigger`, `##
Procedure`, `## Output shape` (any order) in a listed skill's SKILL.md
body via a fixed `PROCEDURE_HEADINGS` tuple; it does not require any
particular pre-existing heading name, so the uniform `## Rules` heading
across all 6 family members poses no classification ambiguity — only the
3 new headings matter for `--manifest` conformance.

## Rule-retention baseline (pre-change)

derived: per-skill numbered-rule count, `awk '/^## Rules/{flag=1;next}
/^## /{flag=0}flag' skills/incident-response-<name>/SKILL.md | grep -c
'^[0-9]\+\.'` run per skill, alongside each file's total line count (`wc
-l`):

```
action-item-quality:              6 rules, 60 total lines
blameless-language-editing:       6 rules, 62 total lines
rca-method-selection:             6 rules, 63 total lines
severity-classification-scoping:  5 rules, 51 total lines
timeline-construction:            5 rules, 53 total lines
tool-landscape:                   5 rules, 63 total lines
```

derived: sum of the above (6+6+6+5+5+5) = 33 numbered rule lines across
the 6 skills; retention target is those 33 lines plus every other
pre-existing line in each file (352 total pre-change lines across the 6
files, same zero-loss guarantee the pilot and every wave since have
applied).

## Skip-condition check

Neither mandatory scout-directive skip condition applies on its face —
this is not a pure bugfix — but the direction decision this survey
exists to resolve (shape classification for this family) is settled by
direct in-repo precedent plus straightforward extension of the frozen
recipe: the classification above (6 Shape A, uniform structure, no
headless or Shape-B member) leaves no open sub-case requiring a new
convention — unlike wave-2h, which had to resolve a headless-citation
question, this family's `## Procedure` citation is the plain
cite-by-rule-number mechanism the pilot and every prior wave already
used for their own `## Rules`/`## Decision rules` skills. Scouting is
not run as a separate external sweep, for the same reason every prior
wave gave: the applicable guidance is this repository's own frozen
recipe plus the four skills named in the role's source-allowlist mapping
(issue #1758) — there is no external field to sweep for authoring an
internal skill file's procedural body, and this wave has no unresolved
shape-classification or citation-convention question left open at all.
