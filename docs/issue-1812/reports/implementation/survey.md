---
subject: issue-1812
type: survey
---

# Survey: product-discovery family (wave 2c)

## Scope-field note

canonical: `gh issue view 1812` (read live) — the issue body's `scope:`
line reads `docs/issue-1801/proposals/, docs/issue-1801/reports/`, not
issue-1812's own buckets, the same copy-paste artifact the wave-2b
(#1809) survey found in its own issue body. Every other field (title,
program context, requirements, acceptance) names issue-1812, and this
session's subject is issue-1812 per its own invocation. This survey and
the accompanying proposal are written under this issue's own
per-subject bucket, not the mismatched one named in that field.

## Checkout and manifest state

canonical: `/tmp/skill-repository` checkout, `origin/main` at commit
`7279ec9` ("Author procedural bodies for wave 2b: release-engineering
family (issue-1809) (#9)") — read live via `git log origin/main
--oneline -3`. Branch `issue-1812-wave2c-product-discovery` created off
`origin/main` for this wave.

`scripts/procedure_authored_skills.txt` currently lists 29 names —
canonical: `wc -l scripts/procedure_authored_skills.txt` (read live) —
the 9 pilot skills, 10 wave-2a `technical-feasibility-*` skills, and 10
wave-2b `release-engineering-*` skills. None of the 10
`product-discovery-*` skills are present yet.

## Family enumeration

derived: `find skills -maxdepth 1 -iname "product-discovery-*"` — 10
directories, matching the issue's stated count:

```
product-discovery-assumption-mapping
product-discovery-guardrail-metric-status
product-discovery-guardrail-metrics
product-discovery-hypothesis-preregistration
product-discovery-hypothesis-testing
product-discovery-jtbd-problem-framing
product-discovery-one-pager
product-discovery-opportunity-solution-tree
product-discovery-opportunity-solution-tree-branching
product-discovery-rice-ice-prioritization
```

## Two distinct pre-existing shapes inside the family

canonical: `grep -n "^## " skills/product-discovery-*/SKILL.md` (read
live from the checkout) — the same Shape A / Shape B split the wave-2a
and wave-2b surveys found recurs a third time here.

**Shape A — "axis" skills, matches the pilot shape exactly.**
canonical: `grep -H rule_count_floor skills/product-discovery-*/SKILL.md`
names exactly 5: `guardrail-metric-status`, `hypothesis-preregistration`,
`jtbd-problem-framing`, `opportunity-solution-tree-branching`,
`rice-ice-prioritization`. Each carries `rule_count_floor:` frontmatter,
a single `## Rules` heading, and numbered rules under it. derived:
`awk '/^## Rules/{flag=1;next}/^## /{flag=0}flag'
skills/product-discovery-<name>/SKILL.md | grep -c '^[0-9]\+\.'` run per
skill:

```
guardrail-metric-status: 10 rules
hypothesis-preregistration: 11 rules
jtbd-problem-framing: 10 rules
opportunity-solution-tree-branching: 11 rules
rice-ice-prioritization: 10 rules
```

52 rule lines total across the 5 Shape-A skills. canonical: the same
`grep -n "^## "` heading dump above shows no occurrence of `## Trigger`/
`## Procedure`/`## Output shape` across any of the 10 files — none of
the 10 skills has them yet, so none qualifies for the no-op/empty-state
clause.

**Shape B — narrative/state-machine skills, a different, older
convention.** canonical: same `grep -H rule_count_floor` command above,
applied as a set-difference against the family enumeration — the
remaining 5: `assumption-mapping`, `guardrail-metrics`,
`hypothesis-testing`, `one-pager`, `opportunity-solution-tree`. Each has
a `description: >` block-scalar frontmatter (no `rule_count_floor:` —
canonical: the same grep above lists only the 5 Shape-A files) and,
instead of `## Rules`, a fixed sequence of narrative/procedural headings
specific to each skill: canonical: per-file `grep -n "^## "` output
captured above — `assumption-mapping` carries `` ## `evidence_log` ``,
`## Standing directive: the Mom Test`, `## How to run the conversation`,
`## Common mistakes this skill exists to prevent`; `guardrail-metrics`
carries `## Precondition this skill enforces`, `## How to run the
conversation`, `## Common mistakes this skill exists to prevent`;
`hypothesis-testing` carries `## The carrying file`, `## Moving through
the states`, `## Common mistakes this skill exists to prevent`;
`one-pager` carries `## How to run the conversation`, `## Common
mistakes this skill exists to prevent`; `opportunity-solution-tree`
carries `## How to run the conversation`, `## Common mistakes this skill
exists to prevent`. None of the 5 has a `## Rules` heading or numbered
rule lines under one; each instead documents a state-machine step,
artifact write, or standing directive (evidence log, precondition,
carrying-file semantics, common-mistakes list) that the earlier waves'
"Shape B" reasoning (skills describing a single-purpose artifact/state
step, not a decision-axis rulebook) applies to unchanged.

## What this means for the recipe

Same conclusion as the wave-2a and wave-2b surveys, reapplied to this
family a third time: the frozen recipe's step 2 — "`## Procedure`
(ordered steps, each citing rule number(s) from `## Rules`)" — applies
unmodified to the 5 Shape-A skills. For the 5 Shape-B skills, there is
no `## Rules` heading and no numbered rule lines to cite; the earlier
waves' precedent resolution (cite the skill's own existing named
sections as the Procedure's per-step citation targets, instead of
inventing a `## Rules` block) is the only option that stays
guidance-only and avoids restructuring existing content — the same two
alternatives the earlier waves rejected (inventing a Rules block;
silently narrowing scope to only Shape A) apply here for the identical
reasons.

## Checker mechanics

canonical: `scripts/check_skill_conformance.py` docstring + body, read
live (unchanged since wave 2b — no checker-logic edits between
`7279ec9` and this checkout) — `--manifest <path>` requires `##
Trigger`, `## Procedure`, `## Output shape` (any order) in a listed
skill's SKILL.md body via a fixed `PROCEDURE_HEADINGS` tuple; skills not
listed are unaffected. Applies identically regardless of shape — the
checker only requires the 3 headings, not any particular
Procedure-citation convention.

## Rule-retention baseline (pre-change)

Pre-change totals to retain post-change:
- Shape A: 52 numbered rule lines (10+11+10+11+10) under `## Rules`
  across the 5 skills.
- Shape B: no numbered rule lines under a `## Rules` heading exist to
  retain in that sense; retention for these 5 means every existing
  content line (standing directives, field/evidence-log semantics,
  state-carrying-file descriptions, common-mistakes lists) must survive
  unchanged — the recipe's zero-loss guarantee is content-level, not
  limited to rule-numbered lines, per the same principle the earlier
  waves applied.

## Skip-condition check

Neither the mandatory scout-directive skip condition applies: this is
not a pure bugfix, and the Shape A/B split is exactly the kind of open
design decision (how to phrase Procedure-step citations for Shape B)
the spec leaves open. Scouting is not run as a separate external sweep
beyond this survey, for the same reason the two earlier waves gave: the
applicable guidance is this repository's own frozen recipe plus the four
skills named in the role's source-allowlist mapping (issue #1758) —
there is no external field to sweep for authoring an internal skill
file's procedural body, so the scout protocol's external-sweep stages
are not applicable; this survey is the direction-setting research the
proposal is drafted from, and it reuses the earlier waves'
already-scouted resolution for the identical Shape A/B split rather than
re-deriving it a third time.
