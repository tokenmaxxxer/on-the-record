---
subject: issue-1802
type: survey
---

# Survey: technical-feasibility family (wave 2a)

## Checkout and manifest state

canonical: `/tmp/skill-repository` checkout, branch `issue-1790-procedural-body-pilot`
(clean, `debb425` HEAD — the #1790 pilot commit), read live via `git log`
+ `git status`.

`scripts/procedure_authored_skills.txt` currently lists 9 names, all from
the #1790 pilot (`upstream-defect-report-*` x3, `api-design-*` x6) —
canonical: `cat scripts/procedure_authored_skills.txt` (read live). None
of the 10 `technical-feasibility-*` skills are present yet.

## Family enumeration

derived: `find skills -maxdepth 1 -iname "technical-feasibility-*"` — 10
directories, matching the issue's count:

```
technical-feasibility-build-vs-buy
technical-feasibility-build-vs-buy-dependency-health
technical-feasibility-license-and-regulatory-risk
technical-feasibility-license-scan
technical-feasibility-reversibility-and-spike-scoping
technical-feasibility-reversibility-tag
technical-feasibility-spike-report
technical-feasibility-stride-table
technical-feasibility-threat-model-disposition
technical-feasibility-verdict-and-timebox-selection
```

## Two distinct pre-existing shapes inside the family

canonical: `grep -n "^## " skills/technical-feasibility-*/SKILL.md` (read
live from the checkout) — the 10 skills split into two shapes that the
#1790 recipe was not tested against together.

**Shape A — "axis" skills, matches the #1790 pilot shape.** derived:
`grep -lH "^## Rules$" skills/technical-feasibility-*/SKILL.md` names
exactly 5: `build-vs-buy-dependency-health`,
`license-and-regulatory-risk`, `reversibility-and-spike-scoping`,
`threat-model-disposition`, `verdict-and-timebox-selection`. Each carries
`axis:`/`rule_count_floor: 10`/`axes:` frontmatter (canonical: `grep -H
rule_count_floor skills/technical-feasibility-*/SKILL.md`, read live), a
single `## Rules` heading, and 11 numbered rules each — derived: `awk
'/^## Rules/{flag=1;next}/^## /{flag=0}flag'
skills/technical-feasibility-<name>/SKILL.md | grep -c '^[0-9]\+\.'` run
per skill returned `11` for all 5, so 55 rule lines total across the 5.
canonical: the same `grep -n "^## "` heading dump above shows no
occurrence of `## Trigger`/`## Procedure`/`## Output shape` across any of
the 10 files — none of the 10 skills has them yet. This shape is what the
#1790 recipe's step 2 ("cite rule number(s) from `## Rules`") assumes.

**Shape B — "probe" skills, a different, older convention.** canonical:
same `grep -lH "^## Rules$"` command above, applied as a set-difference
against the family-enumeration list — the remaining 5: `build-vs-buy`,
`license-scan`, `reversibility-tag`, `spike-report`, `stride-table`. Each
has plain `name:`/`description:` frontmatter (no `axis:`/
`rule_count_floor:` — canonical: `grep -H rule_count_floor` above lists
only the 5 Shape-A files), and instead of `## Rules` carries a fixed
sequence of narrative headings — `## What it asks the user for`,
`## Artifact`, `## Field list`, `## Resolution rule` (or, for
`reversibility-tag`, `## Rule` singular; for `spike-report`, a longer
narrative sequence ending `## Timestamp discipline`) — canonical:
per-file `grep -n "^## "` output captured above. None has a `## Rules`
heading and none has numbered rule lines under one — `spike-report` has 3
numbered items (derived: `grep -n "^[0-9]\+\."
skills/technical-feasibility-spike-report/SKILL.md`), but they live under
`## What it asks the user for, one thing at a time` as an ordered
*question list*, not a rules block. These 5 skills' `description:` lines
each read "Use this skill when running the `<X>` probe inside the
feasibility role's `probing` state..." (canonical: `grep -H
"^description:" skills/technical-feasibility-*/SKILL.md`, read live) —
they describe a single-purpose artifact-producing step inside a state
machine, not a decision-axis rulebook.

## What this means for the recipe

The frozen recipe (docs/issue-1790/reports/implementation.md, WAVE
RECIPE section) step 2 says: "`## Procedure` (ordered steps, each citing
rule number(s) from `## Rules`)". Shape A skills have that structure
verbatim and the recipe applies unmodified. Shape B skills have no `##
Rules` heading and no numbered rule lines to cite — applying the recipe's
step 2 literally is not possible for these 5 without either (a) adding a
`## Rules` section that doesn't exist in the current content (inventing a
rules block changes the skill's shape well past "guidance-only, zero
rule-line loss") or (b) citing the existing named sections (`## Artifact`,
`## Field list`, `## Resolution rule`, etc.) as the Procedure's per-step
citation targets instead of rule numbers, since those sections already
enumerate the same per-step obligations the checker's rule-retention
sweep needs to find unchanged.

## Checker mechanics

canonical: `scripts/check_skill_conformance.py` docstring + body, read
live — `--manifest <path>` is additive: every directory name listed must
have `## Trigger`, `## Procedure`, `## Output shape` (any order) in its
SKILL.md body, checked via a fixed `PROCEDURE_HEADINGS` tuple (line 26).
canonical: same file, docstring lines 14-18 — skills not listed in the
manifest are unaffected. This confirms the recipe's step 5 (manifest run
+ full-tree run) applies identically regardless of shape — the checker
only requires the 3 headings, not any particular rule-numbering
convention inside `## Procedure`.

## Rule-retention baseline (pre-change)

canonical: rule-line counts derived live per skill (see fenced `awk`
command above). Pre-change totals to retain post-change:
- Shape A: 55 numbered rule lines (11 x 5) under `## Rules`.
- Shape B: no numbered rule lines under a `## Rules` heading exist to
  retain in that sense; retention for these 5 means every existing
  content line (question list items, artifact/field-list/resolution-rule
  content) must survive unchanged, since the recipe's zero-loss guarantee
  is content-level, not limited to rule-numbered lines.

## Skip-condition check

Neither #1790's mandatory scout-directive skip condition applies: this is
not a pure bugfix, and the two-shape finding above is exactly the kind of
design decision (how to phrase Procedure-step citations for Shape B) the
spec leaves open. Scouting is not run as a separate external sweep beyond
this survey because the applicable guidance is this repository's own
frozen recipe (#1790) plus the four skills named in the role's
source-allowlist mapping (issue #1758) — there is no external field to
sweep for "how do you author a procedural body for an internal skill
file," so the scout protocol's normal external-sweep stages are not
applicable; this survey itself is the direction-setting research the
proposal is drafted from.
