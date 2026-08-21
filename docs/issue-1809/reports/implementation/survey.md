---
subject: issue-1809
type: survey
---

# Survey: release-engineering family (wave 2b)

## Scope-field note

The issue body's `scope:` line names issue-1801's proposals/reports
buckets, not issue-1809's. Every other field in the issue (title,
program context, requirements, acceptance) names issue-1809 and this
session's subject is issue-1809 per its own invocation. Treated as a
copy-paste artifact from a template; this survey and the accompanying
proposal are written under this issue's own per-subject bucket, per the
subject convention, not the mismatched one named in that field.

## Checkout and manifest state

canonical: `/tmp/skill-repository` checkout, `origin/main` at commit
`a1701b5` ("Author procedural bodies for wave 2a: technical-feasibility
family (issue-1802) (#8)") — read live via `git log origin/main --oneline
-5`. Branch `issue-1809-wave2b-release-engineering` created off
`origin/main` for this wave.

`scripts/procedure_authored_skills.txt` currently lists 19 names —
canonical: `cat scripts/procedure_authored_skills.txt | wc -l` (read
live) — the 9 pilot skills from the earlier wave plus the 10 wave-2a
`technical-feasibility-*` skills. None of the 10
`release-engineering-*` skills are present yet.

## Family enumeration

derived: `find skills -maxdepth 1 -iname "release-engineering-*"` — 10
directories, matching the issue's stated count:

```
release-engineering-branching-release-strategy
release-engineering-changelog-entry-categorization
release-engineering-deployment-rollout-strategy
release-engineering-error-budget-policy
release-engineering-postmortem
release-engineering-readiness-checklist
release-engineering-release-cadence-and-toil
release-engineering-rollback-and-recovery
release-engineering-rollout-plan
release-engineering-semver-bump-selection
```

## Two distinct pre-existing shapes inside the family

canonical: `grep -n "^## " skills/release-engineering-*/SKILL.md` (read
live from the checkout) — the same Shape A / Shape B split the wave-2a
survey found in `technical-feasibility` recurs here, confirming the
issue's own pilot-survey note that this family was "largest remaining"
by count, not necessarily uniform in shape.

**Shape A — "axis" skills, matches the pilot shape exactly.**
canonical: `grep -lH "^## Rules$" skills/release-engineering-*/SKILL.md`
names exactly 6: `branching-release-strategy`,
`changelog-entry-categorization`, `deployment-rollout-strategy`,
`release-cadence-and-toil`, `rollback-and-recovery`,
`semver-bump-selection`. Each carries `axis:`/`rule_count_floor:`
frontmatter (canonical: `grep -H rule_count_floor
skills/release-engineering-*/SKILL.md`, read live — only these 6 files
match), a single `## Rules` heading, and numbered rules under it.
derived: `awk '/^## Rules/{flag=1;next}/^## /{flag=0}flag'
skills/release-engineering-<name>/SKILL.md | grep -c '^[0-9]\+\.'` run
per skill:

```
branching-release-strategy: 12 rules
changelog-entry-categorization: 12 rules
deployment-rollout-strategy: 13 rules
release-cadence-and-toil: 12 rules
rollback-and-recovery: 12 rules
semver-bump-selection: 12 rules
```

73 rule lines total across the 6 Shape-A skills. canonical: the same
`grep -n "^## "` heading dump above shows no occurrence of `## Trigger`/
`## Procedure`/`## Output shape` across any of the 10 files — none of
the 10 skills has them yet, so none qualifies for the no-op/empty-state
clause.

**Shape B — narrative/state-machine skills, a different, older
convention.** canonical: same `grep -lH "^## Rules$"` command above,
applied as a set-difference against the family enumeration — the
remaining 4: `error-budget-policy`, `postmortem`, `readiness-checklist`,
`rollout-plan`. Each has a `description: >-` block-scalar frontmatter
(no `axis:`/`rule_count_floor:` — canonical: `grep -H rule_count_floor`
above lists only the 6 Shape-A files) and, instead of `## Rules`, a fixed
sequence of narrative/procedural headings specific to each skill:
canonical: per-file `grep -n "^## "` output captured above —
`error-budget-policy` carries `## Fields, per SLI...`, `## Where it is
written`, a per-SLI heading, `## How it is read`; `postmortem` carries
`## Required trigger criteria...`, `## Required sections...`, `## The
mechanical check on every action item...`, `## What this skill does NOT
do...`; `readiness-checklist` carries `## The state file` plus five
`## Working <state> -> <state>` / steady-state / incident-closing
headings; `rollout-plan` carries `## What it asks the user for`, `##
What it writes, and where`, `## Step 1 — 5% traffic`, `## How the
agent-owned rows read it`. None of the 4 has a `## Rules` heading or
numbered rule lines under one; each instead documents a state machine or
fixed artifact shape (fields, steps, state-transition sections) that the
wave-2a survey's "Shape B" reasoning (probe skills describing a
single-purpose artifact/state-machine step, not a decision-axis
rulebook) applies to unchanged.

## What this means for the recipe

Same conclusion as the wave-2a survey, reapplied to this family: the
frozen recipe's step 2 — "`## Procedure` (ordered steps, each citing
rule number(s) from `## Rules`)" — applies unmodified to the 6 Shape-A
skills. For the 4 Shape-B skills, there is no `## Rules` heading and no
numbered rule lines to cite; the wave-2a precedent resolution (cite the
skill's own existing named sections as the Procedure's per-step citation
targets, instead of inventing a `## Rules` block) is the only option
that stays guidance-only and avoids restructuring existing content — the
same two alternatives that earlier wave rejected (inventing a Rules
block; silently narrowing scope to only Shape A) apply here for the
identical reasons.

## Checker mechanics

canonical: `scripts/check_skill_conformance.py` docstring + body, read
live (unchanged since wave 2a — no checker-logic edits between
`a1701b5` and this checkout) — `--manifest <path>` requires `##
Trigger`, `## Procedure`, `## Output shape` (any order) in a listed
skill's SKILL.md body via a fixed `PROCEDURE_HEADINGS` tuple; skills not
listed are unaffected. Applies identically regardless of shape — the
checker only requires the 3 headings, not any particular
Procedure-citation convention.

## Rule-retention baseline (pre-change)

Pre-change totals to retain post-change:
- Shape A: 73 numbered rule lines (12+12+13+12+12+12) under `## Rules`
  across the 6 skills.
- Shape B: no numbered rule lines under a `## Rules` heading exist to
  retain in that sense; retention for these 4 means every existing
  content line (field lists, state-transition sections, step
  descriptions) must survive unchanged — the recipe's zero-loss
  guarantee is content-level, not limited to rule-numbered lines, per
  the same principle the earlier wave applied.

## Skip-condition check

Neither the mandatory scout-directive skip condition applies: this is
not a pure bugfix, and the Shape A/B split is exactly the kind of open
design decision (how to phrase Procedure-step citations for Shape B) the
spec leaves open. Scouting is not run as a separate external sweep
beyond this survey, for the same reason the earlier wave gave: the
applicable guidance is this repository's own frozen recipe plus the four
skills named in the role's source-allowlist mapping (issue #1758) —
there is no external field to sweep for authoring an internal skill
file's procedural body, so the scout protocol's external-sweep stages
are not applicable; this survey is the direction-setting research the
proposal is drafted from, and it reuses the earlier wave's
already-scouted resolution for the identical Shape A/B split rather than
re-deriving it.
