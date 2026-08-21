---
subject: issue-1835
type: survey
---

# Survey: conformance-review family (wave 2f)

## Scope-field note

canonical: `gh issue view 1835` (read live) — the issue body's `scope:`
line reads `docs/issue-1835/proposals/, docs/issue-1835/reports/`,
matching this issue's own buckets (unlike wave-2c/2d, which each found a
stale mismatched issue number in this field). No correction needed.

## Count discrepancy in the issue body

canonical: `gh issue view 1835` (read live) — the "Program context"
paragraph states "Family: conformance-review (10 skills — the largest
remaining family per the pilot survey)", but the issue title says "(7
skills)" and Requirement 1 says "All 7 conformance-review-* skills".
derived: `find /tmp/skill-repository-1835/skills -maxdepth 1 -iname
"conformance-review-*"` lists exactly 7 directories (below) — the live
checkout matches the title and Requirement 1's count of 7, not the
Program-context paragraph's 10. canonical: `gh issue view 1830` and `gh
issue view 1812` (read live in the prior waves' own sessions, referenced
here for pattern only) found the same class of stale copy-paste artifact
in their own issue bodies' Program-context text. This wave proceeds
against the 7-skill count the title, Requirements, and live checkout all
agree on.

## Checkout and manifest state

canonical: fresh clone at `/tmp/skill-repository-1835` off
`origin/main`, read live via `git log --oneline -3` — HEAD `d0bde0e`
("Author procedural bodies for wave 2c: product-discovery family
(issue-1812) (#10)"), matching the commit named in this role's
source-allowlist mapping. Branch `issue-1835-wave2f-conformance-review`
created off `origin/main` for this wave. canonical: `git status` on
`/tmp/skill-repository` (read live) — a separate pre-existing checkout
carries uncommitted wave-2d observability changes on branch
`issue-1830-wave2d-observability`, belonging to a concurrent role
session; this wave used its own fresh clone instead of touching that
tree, to avoid interfering with that in-flight work.

canonical: `wc -l scripts/procedure_authored_skills.txt` (read live) —
`scripts/procedure_authored_skills.txt` currently lists 39 names: the 9
pilot skills, 10 wave-2a `technical-feasibility-*`, 10 wave-2b
`release-engineering-*`, and 10 wave-2c `product-discovery-*` skills.
None of the 7 `conformance-review-*` skills are present yet (wave-2d
observability is still in flight on the other checkout, uncommitted, so
not yet on `origin/main`).

## Family enumeration

derived: `find skills -maxdepth 1 -iname "conformance-review-*" | sort`
— 7 directories, matching the issue title and Requirement 1's count:

```
skills/conformance-review-finding-record
skills/conformance-review-requirement-extraction
skills/conformance-review-sampling-derivation
skills/conformance-review-severity-classification
skills/conformance-review-traceability-and-evidence
skills/conformance-review-verdict-assignment
skills/conformance-review-verification-method-selection
```

## Shape A/B split — same pattern as wave-2a/2b/2c, unlike wave-2d

canonical: `grep -n "^## " skills/conformance-review-*/SKILL.md` (read
live from the checkout). canonical: `grep -H rule_count_floor
skills/conformance-review-*/SKILL.md` (read live).

**Shape A** (pilot's `## Rules`-with-numbered-rules structure,
`rule_count_floor:` frontmatter present):

```
conformance-review-requirement-extraction:        rule_count_floor: 3, single heading "## Rules"
conformance-review-sampling-derivation:            rule_count_floor: 3, single heading "## Rules"
conformance-review-traceability-and-evidence:      rule_count_floor: 3, single heading "## Rules"
conformance-review-verdict-assignment:             rule_count_floor: 3, single heading "## Rules"
conformance-review-verification-method-selection:  rule_count_floor: 3, single heading "## Rules"
```

derived: `grep -lc rule_count_floor skills/conformance-review-*/SKILL.md
| wc -l` — 5 files match this shape.

**Shape B** (narrative role-state-machine skill, no `rule_count_floor:`,
no numbered `## Rules`):

```
conformance-review-finding-record:      headings "## What it asks the user for",
  "## The verdict set", "## The artifact and its field list",
  "## EARL alignment (issue-521 spec)", "## Refusal the skill itself
  enforces", "## What this skill never does", "## Per-requirement
  checklist" — 164 lines, 0 numbered rule lines.
conformance-review-severity-classification: headings "## What it asks
  the user for", "## The shape of the classification", "## The
  artifact", "## What this skill never does" — 80 lines, 0 numbered rule
  lines.
```

derived: the same `grep -lc rule_count_floor` command's inverse (the
other 2 of the 7 family files) — the remaining 2 files match this shape.
5 Shape A + 2 Shape B accounts for all 7 family members.

None of the 7 files carry `## Trigger`/`## Procedure`/`## Output shape`
yet, so none qualifies for the recipe's no-op/empty-state clause.

## Precedent for the Shape B citation-target resolution

canonical: `skills/release-engineering-postmortem/SKILL.md` (read live)
— an already-authored Shape B skill from wave-2b. Its `## Procedure`
steps cite named section headings in parentheses (e.g. "(see 'Required
trigger criteria')", "(see 'What this skill does NOT do')") instead of
rule numbers, since Shape B skills have no numbered `## Rules` block to
cite. This wave's 2 Shape-B skills (`finding-record`,
`severity-classification`) follow that same already-established
convention rather than inventing a new one.

## Checker mechanics

canonical: `git log -1 --format=%H -- scripts/check_skill_conformance.py`
(read live) returns `bb89bdc1ba7458fdf7c4ee494a3c0ea70cd65322` — the
pilot commit — confirming the checker has had zero logic edits across
the pilot and all four prior waves (2a/2b/2c/2d-in-flight), through this
checkout at `d0bde0e`. `--manifest <path>` requires `## Trigger`,
`## Procedure`, `## Output shape` (any order) in a listed skill's
SKILL.md body via a fixed `PROCEDURE_HEADINGS` tuple; skills not listed
are unaffected.

## Rule-retention baseline (pre-change)

derived: per-skill numbered-rule count for the 5 Shape-A skills, `awk
'/^## Rules/{flag=1;next} /^## /{flag=0}flag'
skills/conformance-review-<name>/SKILL.md | grep -c '^[0-9]\+\.'` run
per skill:

```
requirement-extraction:        6 rules
sampling-derivation:           5 rules
traceability-and-evidence:     5 rules
verdict-assignment:            6 rules
verification-method-selection: 5 rules
```

derived: sum of the above (6+5+5+6+5) = 27 numbered rule lines total
across the 5 Shape-A skills, to retain post-change. For the 2 Shape-B
skills, the retention target is content-level rather than
rule-numbered: every pre-existing line in `finding-record` (derived: `wc
-l skills/conformance-review-finding-record/SKILL.md` = 164 lines) and
`severity-classification` (derived: `wc -l
skills/conformance-review-severity-classification/SKILL.md` = 80 lines)
— frontmatter, framing paragraph, and all existing `## ` sections — same
as the pilot's zero-loss guarantee applied to earlier waves' Shape-B
skills.

## Skip-condition check

Neither mandatory scout-directive skip condition applies on its face —
this is not a pure bugfix — but the design decision this survey exists
to resolve (Shape A/B classification, and how to phrase `## Procedure`
citations for the Shape-B subset) is already settled by direct
precedent: the classification above (5 Shape A, 2 Shape B) and the
citation convention (named-section citation for Shape B, already
established in wave-2b's `release-engineering-postmortem`) leave no open
choice for this wave to invent. Scouting is not run as a separate
external sweep, for the same reason the four earlier waves gave: the
applicable guidance is this repository's own frozen recipe plus the four
skills named in the role's source-allowlist mapping (issue #1758) — there
is no external field to sweep for authoring an internal skill file's
procedural body, and this wave has no unresolved shape-classification or
citation-convention question left to scout against; the classification
and precedent above **are** the direction-setting findings this survey
exists to produce, and the proposal is drafted directly from them.
