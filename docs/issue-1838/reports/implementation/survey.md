---
subject: issue-1838
type: survey
---

# Survey: ux-engineering family (wave 2g)

## Scope-field note

canonical: `gh issue view 1838` (read live) — the issue body's `scope:`
line reads `docs/issue-1838/proposals/, docs/issue-1838/reports/`,
matching this issue's own buckets. No correction needed.

## Count discrepancy in the issue body

canonical: `gh issue view 1838` (read live) — the "Program context"
paragraph states "Family: ux-engineering (10 skills — the largest
remaining family per the pilot survey)", but the issue title says "(6
skills)" and Requirement 1 says "All 6 ux-engineering-* skills". derived:
`find /tmp/skill-repository-1838/skills -maxdepth 1 -iname
"ux-engineering-*"` lists exactly 6 directories (below) — the live
checkout matches the title and Requirement 1's count of 6, not the
Program-context paragraph's 10. This wave proceeds against the 6-skill
count the title, Requirements, and live checkout all agree on.

## Checkout and manifest state

canonical: fresh clone at `/tmp/skill-repository-1838` off
`origin/main`, read live via `git log --oneline -3` — HEAD `1edba1f`
("Author procedural bodies for wave 2d: observability family (issue-1830)
(#11) (#11)"), matching the commit named in this role's source-allowlist
mapping (issue #1758, "skill-repository 1edba1f"). Branch
`issue-1838-wave2g-ux-engineering` created off `origin/main` for this
wave. canonical: `git status --short` on the pre-existing
`/tmp/skill-repository` checkout (read live) — that tree is clean and
sits on branch `issue-1830-wave2d-observability`, matching HEAD; no
concurrent in-flight uncommitted work found there this time. This wave
still used its own fresh clone (`/tmp/skill-repository-1838`) rather than
reusing that checkout, per the isolation convention wave-2e/2f each
established in their own records.

canonical: `wc -l scripts/procedure_authored_skills.txt` and `grep -c
"^<family>-" scripts/procedure_authored_skills.txt` per family prefix
(both read live) — the manifest currently lists 46 names: 9 pilot
(`upstream-defect-report-*`/`api-design-*`), 10 wave-2a
`technical-feasibility-*`, 10 wave-2b `release-engineering-*`, 10 wave-2c
`product-discovery-*`, and 7 wave-2d `observability-*`. Neither
`legal-compliance-*` (wave-2e) nor `conformance-review-*` (wave-2f)
appear yet — those two waves' phase-1 proposals exist on disk in this
session's own working tree but their phase-2 delivery has not landed on
`origin/main` as of this checkout. None of the 6 `ux-engineering-*`
skills are present yet.

## Family enumeration

derived: `find skills -maxdepth 1 -iname "ux-engineering-*" | sort` — 6
directories, matching the issue title and Requirement 1's count:

```
skills/ux-engineering-color-visibility
skills/ux-engineering-control-selection
skills/ux-engineering-layout-grouping
skills/ux-engineering-navigation-depth
skills/ux-engineering-research-log
skills/ux-engineering-surface-contrast
```

## Shape A/B split — same pattern as wave-2a/2b/2c, unlike wave-2d

canonical: `sed -n '1,8p' skills/ux-engineering-*/SKILL.md` (read live
from the checkout) — checked each file's own YAML frontmatter directly,
not a bare grep, because `ux-engineering-research-log`'s body prose
contains the literal substring "`rule_count_floor` per axis" (line 12,
describing the other 5 skills' floors), which would false-positive a
plain `grep -l rule_count_floor` match. canonical: `grep -n "^## "
skills/ux-engineering-*/SKILL.md` (read live).

**Shape A** (pilot's structure, `rule_count_floor:` present in YAML
frontmatter, single heading `## Decision rules`):

```
ux-engineering-surface-contrast:    rule_count_floor: 3, "## Decision rules"
ux-engineering-color-visibility:    rule_count_floor: 3, "## Decision rules"
ux-engineering-layout-grouping:     rule_count_floor: 3, "## Decision rules"
ux-engineering-navigation-depth:    rule_count_floor: 3, "## Decision rules"
ux-engineering-control-selection:   rule_count_floor: 3, "## Decision rules"
```

canonical: `sed -n '1,8p' skills/ux-engineering-<name>/SKILL.md` per
file (read live, above) — each of these 5 files' own YAML frontmatter
carries `rule_count_floor: 3`, confirming this shape directly per file
rather than by inference.

**Shape B** (evidence-trail/research-log file, no `rule_count_floor:` in
its own frontmatter, no numbered `## Decision rules` block):

```
ux-engineering-research-log: headings "## Axis: control-selection-by-field-type",
  "## Axis: layout-grouping", "## Axis: background-vs-edit-surface-contrast",
  "## Axis: nav-order-vs-usage-frequency", "## Axis: color-combination-visibility",
  "## Sources fetched but not used as a rule citation",
  "## Removal-rule coverage check" — 131 lines, 0 numbered rule lines.
```

canonical: `sed -n '1,8p' skills/ux-engineering-research-log/SKILL.md`
(read live, above) — its frontmatter has only `name:` and
`description:`, no `rule_count_floor:` or `axis:` field, unlike the 5
Shape-A files.

5 Shape A + 1 Shape B accounts for all 6 family members. This matches
the shape pattern the wave-2e proposal (docs/issue-1834/proposals/
2026-08-21-wave-2e-legal-compliance.md, read live in this session)
recorded for its own family carrying a `-research-log` skill — not
wave-2d's single-shape case.

None of the 6 files carry `## Trigger`/`## Procedure`/`## Output shape`
yet (derived: `grep -c "^## Trigger\|^## Procedure\|^## Output shape"
skills/ux-engineering-*/SKILL.md` — 0 for every file), so none qualifies
for the recipe's no-op/empty-state clause.

## Precedent for the Shape B citation-target resolution

canonical: `skills/release-engineering-postmortem/SKILL.md` (read live)
— an already-authored Shape B skill from wave-2b, present on this
checkout's `origin/main`. canonical:
`docs/issue-1834/proposals/2026-08-21-wave-2e-legal-compliance.md` (read
live in this session) — wave-2e's proposal applied the same convention
to its own `-research-log` skill. Both cite named section headings in
parentheses instead of rule numbers, since Shape B skills have no
numbered rules block to cite. This wave's 1 Shape-B skill
(`research-log`) follows that same already-established convention
(citing its `## Axis: <name>` headings) rather than inventing a new one.

## Checker mechanics

canonical: `git log -1 --format=%H -- scripts/check_skill_conformance.py`
(read live) returns `bb89bdc1ba7458fdf7c4ee494a3c0ea70cd65322` — the
pilot commit — confirming the checker has had zero logic edits across
the pilot and every wave merged to `origin/main` through this checkout's
HEAD `1edba1f`. `--manifest <path>` requires `## Trigger`,
`## Procedure`, `## Output shape` (any order) in a listed skill's
SKILL.md body via a fixed `PROCEDURE_HEADINGS` tuple; skills not listed
are unaffected.

## Rule-retention baseline (pre-change)

derived: per-skill numbered-rule count for the 5 Shape-A skills, `awk
'/^## Decision rules/{flag=1;next} /^## /{flag=0}flag'
skills/ux-engineering-<name>/SKILL.md | grep -c '^[0-9]\+\.'` run per
skill:

```
surface-contrast:    5 rules
color-visibility:    8 rules
layout-grouping:     8 rules
navigation-depth:    6 rules
control-selection:   9 rules
```

derived: sum of the above (5+8+8+6+9) = 36 numbered rule lines total
across the 5 Shape-A skills, to retain post-change. For the 1 Shape-B
skill, the retention target is content-level rather than rule-numbered:
every pre-existing line in `research-log` (derived: `wc -l
skills/ux-engineering-research-log/SKILL.md` = 131 lines) — frontmatter,
framing paragraph, and all existing `## ` sections — same as the pilot's
zero-loss guarantee applied to earlier waves' Shape-B skills.

## Skip-condition check

Neither mandatory scout-directive skip condition applies on its face —
this is not a pure bugfix — but the design decision this survey exists
to resolve (Shape A/B classification, and how to phrase `## Procedure`
citations for the Shape-B subset) is already settled by direct
precedent: the classification above (5 Shape A, 1 Shape B) and the
citation convention (named-section citation for Shape B, already
established in wave-2b's `release-engineering-postmortem` and reused in
wave-2e's `legal-compliance-research-log` proposal) leave no open choice
for this wave to invent. Scouting is not run as a separate external
sweep, for the same reason the earlier waves gave: the applicable
guidance is this repository's own frozen recipe plus the four skills
named in the role's source-allowlist mapping (issue #1758) — there is no
external field to sweep for authoring an internal skill file's
procedural body, and this wave has no unresolved shape-classification or
citation-convention question left to scout against; the classification
and precedent above **are** the direction-setting findings this survey
exists to produce, and the proposal is drafted directly from them.
