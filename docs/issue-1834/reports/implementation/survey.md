---
subject: issue-1834
type: survey
---

# Survey: legal-compliance family (wave 2e)

## Checkout state

canonical: `git clone git@github.com:tokenmaxxxer/skill-repository.git
/tmp/skill-repository-1834` then `git log --oneline -3` (read live) —
`origin/main` at commit `d0bde0e` ("Author procedural bodies for wave
2c: product-discovery family (issue-1812) (#10)"), the same tip the
wave-2d (#1830) survey read. Branch
`issue-1834-wave2e-legal-compliance` created off `origin/main` for this
wave, in a fresh checkout separate from the `/tmp/skill-repository`
working copy another session currently has uncommitted wave-2d changes
in — this wave does not touch or discard that unrelated in-progress
work.

`scripts/procedure_authored_skills.txt` currently lists 39 names —
canonical: `wc -l scripts/procedure_authored_skills.txt` (read live) —
the 9 pilot skills, 10 wave-2a `technical-feasibility-*`, 10 wave-2b
`release-engineering-*`, and 10 wave-2c `product-discovery-*` skills.
None of the 7 `legal-compliance-*` skills are present yet.

## Family enumeration

derived: `find skills -maxdepth 1 -iname "legal-compliance-*" | sort` —
7 directories, matching the issue title and Requirement 1's count:

```
skills/legal-compliance-consent-ux
skills/legal-compliance-cross-border-transfer
skills/legal-compliance-lawful-basis-selection
skills/legal-compliance-license-compatibility
skills/legal-compliance-research-log
skills/legal-compliance-retention-minimization
skills/legal-compliance-vendor-dpa
```

## Two shapes across the family

canonical: `grep -n "^## " skills/legal-compliance-*/SKILL.md` (read
live from the checkout).

**Shape A — 6 "axis" skills, the pilot's `## Rules`-equivalent
convention under a different heading name.** `consent-ux`,
`cross-border-transfer`, `lawful-basis-selection`,
`license-compatibility`, `retention-minimization`, `vendor-dpa` each
carry `axis:`/`rule_count_floor: 2` frontmatter (canonical: `grep -H
rule_count_floor skills/legal-compliance-*/SKILL.md`) and a single
`## Decision rules` heading with numbered rules under it — structurally
identical to the pilot's `## Rules` shape, just named `## Decision
rules` instead of `## Rules`. The recipe's step 2 ("citing rule
number(s) from `## Rules`") applies unmodified in substance; the only
adjustment is citing `## Decision rules` by its actual heading name
instead of assuming the literal string `## Rules` is present.

derived: per-skill numbered-rule count, `awk '/^## Decision
rules/{flag=1;next}/^## /{flag=0}flag' skills/legal-compliance-<name>/SKILL.md
| grep -c '^[0-9]\+\.'` run per skill:

```
consent-ux:               5 rules
cross-border-transfer:    4 rules
lawful-basis-selection:   4 rules
license-compatibility:    5 rules
retention-minimization:   5 rules
vendor-dpa:               5 rules
```

28 rule lines total across the 6 axis skills.

**Shape B — 1 "research-log" skill, an evidence-trail convention with
no numbered rules at all.** `legal-compliance-research-log` carries
plain `name:`/`description:` frontmatter only (no `axis:`/
`rule_count_floor:` field — canonical: `grep -H rule_count_floor
skills/legal-compliance-research-log/SKILL.md` returns no frontmatter
match, only a prose occurrence of the string inside the body).
canonical: `grep -n "^## " skills/legal-compliance-research-log/SKILL.md`
shows 6 `## Axis: <name> -> \`playbook/<file>.md\`` headings (one per
sibling axis skill), followed by `## Sources fetched but not used as a
rule citation` and `## Removal-rule coverage check (amendment 4)` — no
`## Rules` or `## Decision rules` heading, no numbered rule lines under
any of its headings (the numbered "rules 1-4" references inside each
axis block are prose citations back to the sibling skill's own
numbered rules, not numbered items in this file itself). This is the
same class of structural mismatch the wave-2a survey (#1802,
canonical: docs/issue-1802/reports/implementation/survey.md, read
live) found for its 5 "probe" skills: a body organized around named
sections instead of a `## Rules`/numbered-rules block, so the recipe's
literal "cite rule number(s) from `## Rules`" instruction has no
numbered-rule target to cite in this file.

canonical: `grep -c "" skills/legal-compliance-research-log/SKILL.md`
— 133 lines total, all of which (frontmatter, the tier/floor
explanation paragraph, all 6 axis blocks with their source URLs, the
"Sources fetched but not used" section, and the "Removal-rule coverage
check" section) are the zero-loss retention surface for this file,
per the same content-level (not rule-numbered-line-only) principle the
wave-2a and wave-2d surveys applied to their own non-Shape-A skills.

## What this means for the recipe

derived: set-difference of the family enumeration (7 directories) above
against the Shape-A list (the 6 `axis:`/`rule_count_floor:` skills
named in the previous section):

```
Shape A (6): consent-ux, cross-border-transfer, lawful-basis-selection,
             license-compatibility, retention-minimization, vendor-dpa
Shape B (1): research-log
```

Classification requested by the issue's prompt ("classify Shape A/B per
the wave precedents") resolves to this 6-Shape-A / 1-Shape-B split: the
6 axis skills need no citation-target change beyond citing `## Decision
rules` by name; `research-log` cites its own `## Axis: <name>` section
headings as the Procedure's per-step targets, mirroring the #1802
precedent's Shape-B resolution of citing existing named sections
instead of inventing a rules block.

## Checker mechanics

canonical: `git log -1 --format=%H -- scripts/check_skill_conformance.py`
(read live) returns `bb89bdc1ba7458fdf7c4ee494a3c0ea70cd65322` — the
pilot commit — confirming the checker has had zero logic edits across
the pilot and all four prior waves (2a/2b/2c/2d), through this checkout
at `d0bde0e`. `--manifest <path>` requires `## Trigger`, `## Procedure`,
`## Output shape` (any order) in a listed skill's SKILL.md body via a
fixed `PROCEDURE_HEADINGS` tuple; skills not listed are unaffected.
canonical: the `grep -n "^## "` heading dump above shows no occurrence
of `## Trigger`/`## Procedure`/`## Output shape` across any of the 7
files — none of the 7 skills has them yet, so none qualifies for the
no-op/empty-state clause.

## Rule-retention baseline (pre-change)

Pre-change totals to retain post-change: 28 numbered rule lines
(5+4+4+5+5+5) under `## Decision rules` across the 6 axis skills, plus
every pre-existing content line in the 7th (`research-log`, 133 lines),
plus every other pre-existing content line in each of the 6 axis files
(frontmatter, framing paragraph, `source:`/`counter-example:` text
inside each numbered rule) — the recipe's zero-loss guarantee is
content-level, not limited to rule-numbered lines, per the same
principle wave-2a and wave-2d applied.

## Skip-condition check

Neither mandatory scout-directive skip condition applies on its face —
this is not a pure bugfix — but the design decision this survey exists
to resolve (how to phrase `## Procedure` citations for the one Shape-B
skill) already has a direct precedent in the #1802 (wave-2a) survey and
proposal, canonical: docs/issue-1802/reports/implementation/survey.md
and docs/issue-1802/proposals/2026-08-21-wave-2a-technical-feasibility.md
(both read live): cite the skill's own existing named sections instead
of inventing a `## Rules` block. Scouting is not run as a separate
external sweep, for the same reason the four earlier waves gave: the
applicable guidance is this repository's own frozen recipe plus the
four skills named in the role's source-allowlist mapping (issue #1758)
— there is no external field to sweep for authoring an internal skill
file's procedural body, and the one open classification question this
wave has (Shape A vs Shape B, and Shape B's citation-target choice) is
resolved directly against the #1802 precedent rather than requiring a
fresh external sweep. The classification above **is** the
direction-setting finding this survey exists to produce, and the
proposal is drafted directly from it.
