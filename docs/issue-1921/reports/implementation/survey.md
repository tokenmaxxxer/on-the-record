---
subject: issue-1921
kind: survey
canonical_basis: docs/issue-1790/reports/implementation.md (WAVE RECIPE section, pilot #1790)
---

# Current-state survey: verify family (wave 2a)

## Scope

Checkout: `tokenmaxxxer/skill-repository`. canonical: `git -C
/tmp/skill-repository-1921 log --oneline -1`, 2026-08-21: `44d58f9 Merge
pull request #36 from tokenmaxxxer/issue-1912-wave2a-sales` — the
sales-family wave (#1912) is the latest commit reachable from
`origin/main` at this checkout's clone time. Working clone:
`/tmp/skill-repository-1921`, checked out fresh from `origin/main` (a
prior `/tmp/skill-repository` checkout on a different branch carried an
unrelated uncommitted change and was left untouched rather than reused).
canonical: `git -C /tmp/skill-repository-1921 rev-parse HEAD`,
2026-08-21: `44d58f94c3cbe40a9d056cc3f2062e3fd60a5c37`.

The role-source-allowlist mapping (issue #1758) for this session names
guidance skills implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice,
implementation-blueprint — not a rulebook, and not a directive on which
skill-repository commit to build against; the wave's own instruction is
to build against `origin/main`.

## Family membership

The issue's own title/body say "verify role family (2 skills)" and
Requirement 1 says "All 2 verify-* skills" — 2, not the body's separate
stray "verify (10 skills — the largest remaining family per the pilot
survey)" sentence. canonical: `find /tmp/skill-repository-1921/skills
-maxdepth 1 -name 'verify-*'`, 2026-08-21:

```
skills/verify-severity-classification
skills/verify-finding-record
```

2 directories exist, matching Requirement 1 and the Acceptance section
("All 2 family skills"), not the stray "10 skills" sentence. canonical:
docs/issue-1912/reports/implementation/survey.md, "Family membership"
section — records the identical pattern for the sales family (issue body
said "10 skills" once, 3 directories actually existed, Requirements/
Acceptance said 3); docs/issue-1900/reports/implementation/survey.md
records the same leftover for marketing (5 vs. a stray "10"). The same
family-size-estimate leftover recurs a third time here.

## Shape classification (per frozen recipe step 1)

canonical: `grep -n '^## ' skills/<name>/SKILL.md` run against both,
2026-08-21:

| skill | existing `## ` headings | classification |
|---|---|---|
| verify-finding-record | `## What it asks the user for`, `## The outcome set`, `## The artifact and its field list`, `## Refusal the skill itself enforces`, `## What this skill never does` | Shape B (needs authoring) |
| verify-severity-classification | `## What it asks the user for`, `## The shape of the classification`, `## Two distinct spec fields, not one`, `## The artifact`, `## What this skill never does` | Shape B (needs authoring) |

Neither carries `## Trigger`/`## Procedure`/`## Output shape` yet — no
no-op case in this family, both require authoring. canonical:
docs/issue-1912/reports/implementation/survey.md, "Shape classification"
section — the sales wave's 3 skills found the identical outcome (all
Shape B); the #1790 pilot's own 9-skill check (canonical:
docs/issue-1790/reports/implementation.md, WAVE RECIPE step 1) also
found all 9 required authoring.

## Structural divergence from the rulebook-shaped families

Unlike every prior wave family surveyed so far (sales, marketing,
data-modeling, data-engineering, devrel, etc.), neither verify skill
carries a `## Rules` heading, a numbered rule list, or `axis:`/
`rule_count_floor:` frontmatter. canonical: `grep -c '^[0-9]\+\.'
skills/verify-finding-record/SKILL.md skills/verify-severity-classification/SKILL.md`,
2026-08-21: both `0`. canonical: `sed -n '1,4p'
skills/verify-finding-record/SKILL.md skills/verify-severity-classification/SKILL.md`,
2026-08-21 — both frontmatter blocks carry only `name:` and
`description:`, no `axis:`/`rule_count_floor:` pair.

A same-shaped sibling already exists in this repository.
`conformance-review-finding-record` — the `review` role's counterpart to
this wave's `verify-finding-record` — has the identical guidance-only
shape: no `## Rules`, no numbered list, only `name:`/`description:`
frontmatter. canonical: `skills/conformance-review-finding-record/SKILL.md`
lines 20-32, 2026-08-21 — its `## Procedure` section cites `(see "<heading
name>")` in place of a rule number for each step; the step-4 line reads
verbatim: "Refuse to write Present, Surface, Absent, or Incorrect with no
evidence pointer or no spec_ref (see 'Refusal the skill itself
enforces')." canonical: `git -C /tmp/skill-repository-1921 log --oneline
--all -- skills/conformance-review-finding-record/SKILL.md`, 2026-08-21
(tail line): `51c99f6 Author procedural bodies for wave 2f:
conformance-review family (issue-1835) (#12)`. This is the recipe's own
step 2 language applied literally: "each citing rule number(s) from
`## Rules`" presupposes a `## Rules` section exists; where a skill has no
such section (this family, like conformance-review's guidance-only
skills), the landed precedent above cites the skill's own named
subsection instead of a numeric rule id.

## Rule-line counts (pre-change baseline for the retention sweep)

There are no numbered rule lines to retain. canonical: `grep -c
'^[0-9]\+\.' skills/<name>/SKILL.md`, 2026-08-21: `verify-finding-record`
0, `verify-severity-classification` 0. canonical: `wc -l
skills/verify-finding-record/SKILL.md
skills/verify-severity-classification/SKILL.md`, 2026-08-21: 140 lines
and 82 lines respectively (222 total, pre-change). The proposal's
retention sweep for this wave will diff full pre-change body content
against post-change body content per skill, checked live at build time
and pasted into the phase-2 record.

## Manifest state

canonical: `tail -3 scripts/procedure_authored_skills.txt` and `wc -l
scripts/procedure_authored_skills.txt` against `origin/main` at
`44d58f9`, 2026-08-21: 180 entries, most recently `sales-objection-handling`,
`sales-pitch-scoping-and-messaging-handoff`,
`sales-qualification-and-discovery` (the #1912 sales wave). canonical:
`grep -c 'verify-' scripts/procedure_authored_skills.txt`, 2026-08-21: 0
— no `verify-*` entries present yet in this file.

## Checker script

canonical: `scripts/check_skill_conformance.py` (present, unchanged from
prior waves) — an optional `--manifest <path>` flag runs the additive
Trigger/Procedure/Output-shape check only against manifest entries; the
full-tree run (no flag) checks basic skill-file conformance across every
skill directory regardless of manifest membership. No checker-logic
change is proposed or needed for this wave.

## Gap to close

Both verify skills need: (a) `## Trigger`/`## Procedure`/`## Output
shape` inserted between the framing paragraph and the first existing
`##` heading (`## What it asks the user for` in both), procedure steps
citing the existing named subsection each step operationalizes (no
numeric rule ids exist in this family — see "Structural divergence"
above); (b) `description:` frontmatter rewritten from the new Trigger
content, keeping the "Use when"/"use when" trigger-marker substring the
checker scans for; (c) their 2 names appended to
`procedure_authored_skills.txt` (after the existing 180 entries, giving
182). No checker logic change, no hook change, no path outside these 2
skill dirs + the manifest file.
