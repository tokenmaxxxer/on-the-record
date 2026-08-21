---
code_under_review:
  - skills/marketing-channel-selection/SKILL.md
  - skills/marketing-message-persuasion/SKILL.md
  - skills/marketing-positioning-differentiation/SKILL.md
  - skills/marketing-scope-pruning/SKILL.md
  - skills/marketing-segment-targeting/SKILL.md
  - scripts/procedure_authored_skills.txt
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Implementation record: issue-1900 — marketing family wave 2a

## What was done

Applied the frozen #1790 procedural-body recipe verbatim to the 5
`marketing-*` skills in `tokenmaxxxer/skill-repository`:
`marketing-channel-selection`, `marketing-message-persuasion`,
`marketing-positioning-differentiation`, `marketing-scope-pruning`,
`marketing-segment-targeting`.
canonical: docs/issue-1900/reports/implementation/survey.md (family
membership list, "Family membership" section).

For each: inserted `## Trigger` / `## Procedure` / `## Output shape`
between the framing paragraph and `## Rules`, with Procedure steps
citing the pre-existing rule number(s) they operationalize; rewrote
`description:` from the new Trigger content, preserving the "use when"
trigger-marker substring the checker scans for; no rule text or
`source:` line was rewritten or renumbered. Appended the 5 skill names
to `scripts/procedure_authored_skills.txt` (after the existing
entries, none removed).
canonical: `acceptance: git -C /tmp/skill-repository-1900 diff --stat -- skills/marketing-* scripts/procedure_authored_skills.txt — result: 6 files changed, 170 insertions(+), 5 deletions(-)`, run live this turn.

Delivered as skill-repository PR
https://github.com/tokenmaxxxer/skill-repository/pull/32 (branch
`issue-1900-wave2a-marketing` off `origin/main` at `c93b81b`, this
role's own commit `c3051d0`).
canonical: `acceptance: gh pr create --repo tokenmaxxxer/skill-repository ... — result: https://github.com/tokenmaxxxer/skill-repository/pull/32`, run live this turn.

## Why

canonical: docs/issue-1900/proposals/marketing-family-wave2a.md
("Rationale" section, rejected alternative 2).
Reusing the #1790 pilot recipe verbatim keeps every wave since #1790
consistent; the survey found no structural divergence in the marketing
family's shape that would justify a variant recipe.

## Upstream / basis

- docs/issue-1900/proposals/marketing-family-wave2a.md
- docs/issue-1900/reports/implementation/survey.md
- docs/issue-1790/reports/implementation.md (WAVE RECIPE section)

## Four checks — executed live, skill-repository checkout `/tmp/skill-repository-1900`

canonical: commands run directly in `/tmp/skill-repository-1900` on
branch `issue-1900-wave2a-marketing`, this session, this turn.

### (a) Manifest checker

canonical: `acceptance: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt — result: exit 0`, run live this turn.

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo $?
0
```

### (b) Rule-retention sweep (all 30 pre-change rule lines present post-change)

canonical: `acceptance: for-loop grep sweep comparing /tmp/marketing-pre/*.txt against post-change skills/marketing-*/SKILL.md — result: missing=0 for all 5 files`, run live this turn.

```
== check 2: rule-retention sweep ==
-- marketing-channel-selection --
pre=6 post=12 missing=0
-- marketing-message-persuasion --
pre=6 post=12 missing=0
-- marketing-positioning-differentiation --
pre=6 post=12 missing=0
-- marketing-scope-pruning --
pre=6 post=12 missing=0
-- marketing-segment-targeting --
pre=6 post=12 missing=0
```

`post` count exceeds `pre` because the new `## Procedure` section's own
numbered steps also match the `^[0-9]+\.` grep pattern used for the
sweep — not rule loss or duplication of `## Rules` content.

### (c) `git diff --stat` scoped to the 5 skill paths + manifest

canonical: `acceptance: git diff --stat -- skills/marketing-* scripts/procedure_authored_skills.txt — result: 6 files changed, 170 insertions(+), 5 deletions(-)`, run live this turn.

```
 scripts/procedure_authored_skills.txt              |  5 +++
 skills/marketing-channel-selection/SKILL.md        | 33 +++++++++++++++++++-
 skills/marketing-message-persuasion/SKILL.md       | 33 +++++++++++++++++++-
 .../marketing-positioning-differentiation/SKILL.md | 36 +++++++++++++++++++++-
 skills/marketing-scope-pruning/SKILL.md            | 33 +++++++++++++++++++-
 skills/marketing-segment-targeting/SKILL.md        | 35 ++++++++++++++++++++-
 6 files changed, 170 insertions(+), 5 deletions(-)
```

canonical: `acceptance: git diff --stat (unscoped, no path filter) — result: byte-identical output to the scoped run above`, run live this turn.

### (d) Full-tree checker (no flag)

canonical: `acceptance: python3 scripts/check_skill_conformance.py — result: exit 0`, run live this turn.

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo $?
0
```

## What did not work

None.

## Open findings

None.

## loop_state

landed — skill-repository PR #32 opened
(https://github.com/tokenmaxxxer/skill-repository/pull/32) carrying
the 5 skill-file diffs + manifest diff; this record is the phase-2
delivery for issue-1900.
