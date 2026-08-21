---
Subject: issue-1906
---

# Survey — data-modeling family, wave 2a procedural-body authoring

## Scope

skill-repository checkout: `/tmp/skill-repository`, main branch at
`1b04844` (matches issue #1906's cited pilot-recipe commit basis; this
is also the exact commit the wave 2a marketing family (#1900) landed
at, the most recent prior wave family).

canonical: `git log --oneline -3` and `git status`, executed live this session, /tmp/skill-repository

```
$ git log --oneline -3
1b04844 Author procedural bodies for wave 2a: marketing family (issue-1900) (#32)
e62e9bd Author procedural bodies for wave 2a: brand-design family (issue-1896) (#31)
c93b81b Author procedural bodies for wave 2a: localization family (issue-1892) (#30)
```

Target write set (4 skills, per issue #1906 requirement 1):

- `skills/data-modeling-datavault/SKILL.md`
- `skills/data-modeling-structure/SKILL.md`
- `skills/data-modeling-kimball/SKILL.md`
- `skills/data-modeling-inmon/SKILL.md`
- `scripts/procedure_authored_skills.txt` (manifest, append-only)

## Current shape of the 4 skills

canonical: skills/data-modeling-{datavault,structure,kimball,inmon}/SKILL.md read in full this session, /tmp/skill-repository main@1b04844

All 4 are Shape B (rules-only body, no `## Trigger`/`## Procedure`/
`## Output shape` sections yet):

```
$ grep -E '^## ' skills/data-modeling-{datavault,structure,kimball,inmon}/SKILL.md
skills/data-modeling-datavault/SKILL.md:## Rules
skills/data-modeling-structure/SKILL.md:## Rules
skills/data-modeling-kimball/SKILL.md:## Rules
skills/data-modeling-inmon/SKILL.md:## Rules
```

Rule counts (top-level numbered items under `## Rules`), each above its
`rule_count_floor: 10` frontmatter:

derived:
```
$ for f in datavault structure kimball inmon; do echo -n "$f: "; sed -n '/^## Rules/,$p' skills/data-modeling-$f/SKILL.md | grep -cE '^[0-9]+\.'; done
datavault: 11
structure: 12
kimball: 11
inmon: 11
```

Current `description:` frontmatter on all 4 follows the pre-recipe
generic template (`Use when you need guidance on <Title>. Applies to
the <axis> axis.`) — the exact template the recipe's description-rewrite
step replaces, same as every prior wave 2a family (localization,
capacity-planning, brand-design, marketing) rewrote from.

## Manifest state

canonical: `wc -l scripts/procedure_authored_skills.txt` and `grep -c data-modeling scripts/procedure_authored_skills.txt`, executed live this session, /tmp/skill-repository main@1b04844

`scripts/procedure_authored_skills.txt` currently has 163 lines (all
prior procedure-authored families across waves, including the 20 most
recent wave 2a entries: capacity-planning x5, localization x5,
brand-design x5, marketing x5). None of the 4 data-modeling names are
present yet:

```
$ wc -l scripts/procedure_authored_skills.txt
163 scripts/procedure_authored_skills.txt
$ grep -c data-modeling scripts/procedure_authored_skills.txt
0
```

## Checker baseline (pre-change)

canonical: `python3 scripts/check_skill_conformance.py` and `python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`, executed live this session, /tmp/skill-repository main@1b04844

Both required checks were run live this session, on current main before
any edit, and both exited 0 — recorded here as the pre-change baseline
the phase-2 record's post-change runs will be diffed against:

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo $?
0
```

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo $?
0
```

## Precedent: wave 2a marketing family (#1900, commit 1b04844)

canonical: `git show 1b04844 -- skills/marketing-channel-selection/SKILL.md` and `git show 1b04844 --stat`, executed live this session, /tmp/skill-repository

Read as the most recent applied instance of the frozen recipe. Confirms
the exact recipe shape: `description:` rewritten from a new `## Trigger`
paragraph; `## Trigger` / `## Procedure` (numbered steps, each citing
`(rule N)`) / `## Output shape` inserted directly above the pre-existing
`## Rules` section, with zero rule-line edits:

```
$ git show 1b04844 --stat
 scripts/procedure_authored_skills.txt              |  5 +++
 skills/marketing-channel-selection/SKILL.md        | 33 +++++++++++++++++++-
 skills/marketing-message-persuasion/SKILL.md       | 33 +++++++++++++++++++-
 .../marketing-positioning-differentiation/SKILL.md | 36 +++++++++++++++++++++-
 skills/marketing-scope-pruning/SKILL.md            | 33 +++++++++++++++++++-
 skills/marketing-segment-targeting/SKILL.md        | 35 ++++++++++++++++++++-
 6 files changed, 170 insertions(+), 5 deletions(-)
```

The 5 marketing skill names were appended to
`scripts/procedure_authored_skills.txt` in that same commit, per the
diffstat above (manifest +5 lines, no deletions).

## Classification

canonical: same file reads cited in "Current shape of the 4 skills"
section above, this session

All 4 data-modeling skills classify **Shape B** (rules-only, no
existing procedural sections) — same classification as every prior wave
2a family surveyed above. No Shape A precedent (a skill already
partially procedure-shaped) exists in this family; this matches the
issue's `empty state: a family skill already procedure-shaped is
recorded as no-op with evidence` acceptance clause, which does not
apply here since none of the 4 pre-qualify.

## Open questions for the proposal

canonical: file reads and precedent diff cited above (this session)

None. The file reads and the marketing-family precedent diff cited
above found no data-modeling-specific structural difference
(frontmatter shape, rule numbering style, section layout) relative to
the 4 already-completed wave 2a families, so the frozen recipe (#1790)
applies without adaptation.
