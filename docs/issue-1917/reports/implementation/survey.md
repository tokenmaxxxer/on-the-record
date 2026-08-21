---
subject: issue-1917
kind: survey
canonical_basis: docs/issue-1790/reports/implementation.md (WAVE RECIPE section, pilot #1790)
---

# Current-state survey: architecture family (wave 2a)

## Scope

Checkout: `tokenmaxxxer/skill-repository`. canonical: `git -C
/tmp/skill-repository-1917 log --oneline -1`, 2026-08-21: `74d9125
Author procedural bodies for wave 2a: data-modeling family (issue-1906)`
— the data-modeling-family wave (#1906/#1913) is the latest commit
reachable from `origin/main` at this checkout's clone time. Working
clone: `/tmp/skill-repository-1917`, checked out from `origin/main`.
canonical: `git -C /tmp/skill-repository-1917 rev-parse HEAD`,
2026-08-21: `74d9125ec4958d81c660f4cf214369628f6b1833`.

The role-source-allowlist mapping (issue #1758) for this session names
guidance commit `46ca8c2` — that commit governs which guidance skills
apply to this role (implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice,
implementation-blueprint), not which skill-repository commit to build
against; the wave's own instruction is to build against `origin/main`.

## Family membership

5 `architecture-*` skill directories exist under `skills/` — matches
the issue's own Requirement 1 ("All 5 architecture-* skills") and title
("5 skills"). The issue body also carries a stray "architecture (10
skills — the largest remaining family)" sentence in its Program-context
prose that contradicts the issue's own title, Requirement 1, and
Acceptance sections (all three say 5, matching the actual directory
count below) — the same family-size-estimate leftover the #1900 and
#1912 surveys already recorded for their families. canonical: `find
/tmp/skill-repository-1917/skills -maxdepth 1 -name 'architecture-*'`,
2026-08-21:

```
skills/architecture-coupling-classification
skills/architecture-decomposition-strategy
skills/architecture-dependency-direction
skills/architecture-interface-contract-shape
skills/architecture-module-boundary-definition
```

## Shape classification (per frozen recipe step 1)

canonical: `grep -n '^## \|^### ' skills/<name>/SKILL.md` run against
all 5, 2026-08-21:

| skill | existing headings | classification |
|---|---|---|
| architecture-coupling-classification | `## Cross-source conflicts and resolution`, `## Rules` (rules as `### N.` under it) | Shape B (needs authoring) |
| architecture-decomposition-strategy | rules as `### N.` directly, then `## Conflicts and resolution` | Shape B (needs authoring) |
| architecture-dependency-direction | `## Conflicts and how resolved`, then rules as `### N.` | Shape B (needs authoring) |
| architecture-interface-contract-shape | rules as `### N.` directly, then `## Conflicts between sources and resolution` | Shape B (needs authoring) |
| architecture-module-boundary-definition | rules as `### N.` directly (no `## Conflicts` heading; conflict is folded into the framing prose) | Shape B (needs authoring) |

None carry `## Trigger`/`## Procedure`/`## Output shape` yet — no no-op
case in this family, all 5 require authoring. canonical:
docs/issue-1906/reports/implementation/survey.md, "Shape classification"
section — the data-modeling wave's 4 skills found the identical outcome
(all Shape B).

**Structural divergence from prior waves (noted for the proposal's
Rationale/Constraints, not a recipe change):** unlike the sales/
marketing/data-modeling families surveyed so far, this family's rules
are authored as `### N. <condition>` subheadings (with `condition`/
`choice`/`why`/`source` bullet fields under each), not as flat numbered
`1. **Title.**` list lines, and only one of the five skills
(`architecture-coupling-classification`) carries a `## Rules` heading
at all — the other four run rules directly under the framing
paragraph(s), with the `## Conflicts...` heading appearing either
before or after the rule block, or (module-boundary-definition) not as
its own heading at all. The frozen recipe's stated insertion point
("between the framing paragraph and `## Rules`") is defined for the
common case; for the four skills with no `## Rules` heading, the
equivalent insertion point is between the framing paragraph(s) and the
first rule (`### 1. ...`) or `## Conflicts...` heading, whichever comes
first in the file.

## Rule-line counts (pre-change baseline for the retention sweep)

canonical: `grep -c '^### [0-9]' skills/<name>/SKILL.md` and `wc -l`,
2026-08-21:

| skill | numbered rules (`### N.` headings) | file lines |
|---|---|---|
| architecture-coupling-classification | 15 | 214 |
| architecture-decomposition-strategy | 13 | 97 |
| architecture-dependency-direction | 14 | 184 |
| architecture-interface-contract-shape | 17 | 127 |
| architecture-module-boundary-definition | 15 | 109 |

Total: 74 rules across the family, 731 lines. (Note:
`architecture-interface-contract-shape` and
`architecture-decomposition-strategy` each carry two ancillary "Nb."
sub-rule headings, e.g. `### 2b.`/`### 9b.`/`### 11b.`, in addition to
their main-numbered rules — these count toward the retention sweep as
their own distinct lines but not toward the `### [0-9]` grep count
above, which only matches headings starting with a bare digit
immediately after `### `; the retention sweep for the phase-2 record
must diff the full rule-heading line set, not just the numeric count,
to catch these.) Every skill carries a `description:` frontmatter line
ending on an axis-specific sentence and an `axis:` +
`rule_count_floor:` pair. canonical:
`skills/architecture-coupling-classification/SKILL.md` lines 1-6,
2026-08-21:

```
---
name: architecture-coupling-classification
description: Use when you need guidance on Coupling Classification — Operational Decision Rules. Applies to the coupling-classification axis.
axis: coupling-classification
rule_count_floor: 12
---
```

This frontmatter shape matches the pilot's pre-change skills (canonical:
docs/issue-1790/reports/implementation/survey.md, "Frontmatter shape"
section) and every landed wave since — same authoring surface for the
description rewrite step, no divergence there even though the rule-body
shape (### headings vs. flat numbered lines) differs from prior
families.

## Manifest state

canonical: `tail -8 scripts/procedure_authored_skills.txt` and `wc -l
scripts/procedure_authored_skills.txt` against `origin/main` at
`74d9125`, 2026-08-21: 174 entries, most recently `data-modeling-datavault`,
`data-modeling-structure`, `data-modeling-kimball`, `data-modeling-inmon`
(the #1906 data-modeling wave). canonical: `grep -c
'^architecture-' scripts/procedure_authored_skills.txt`, 2026-08-21: `0`
— no `architecture-*` entries present yet in this file.

## Checker script

canonical: `scripts/check_skill_conformance.py` — unchanged from the
#1790 pilot and every landed wave since: an optional `--manifest
<path>` flag runs the additive Trigger/Procedure/Output-shape check
only against manifest entries; the full-tree run (no flag) checks basic
skill-file conformance across every skill directory regardless of
manifest membership. No checker-logic change is proposed or needed for
this wave.

## Gap to close

All 5 architecture skills need: (a) `## Trigger`/`## Procedure`/
`## Output shape` inserted between the framing paragraph(s) and the
first existing rule/conflicts heading (see Shape-classification
divergence note above — exact insertion point varies per file since
only one of the five carries a `## Rules` heading), procedure steps
citing existing rule numbers (including the `Nb.` sub-rules); (b)
`description:` frontmatter rewritten from the new Trigger content,
keeping the "use when" trigger-marker substring the checker scans for;
(c) their 5 names appended to `procedure_authored_skills.txt` (after
the existing 174 entries, giving 179). No checker logic change, no hook
change, no path outside these 5 skill dirs + the manifest file.
