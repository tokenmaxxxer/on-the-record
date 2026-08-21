---
code_under_review:
  - /tmp/skill-repository/skills/product-discovery-assumption-mapping/SKILL.md
  - /tmp/skill-repository/skills/product-discovery-guardrail-metric-status/SKILL.md
  - /tmp/skill-repository/skills/product-discovery-guardrail-metrics/SKILL.md
  - /tmp/skill-repository/skills/product-discovery-hypothesis-preregistration/SKILL.md
  - /tmp/skill-repository/skills/product-discovery-hypothesis-testing/SKILL.md
  - /tmp/skill-repository/skills/product-discovery-jtbd-problem-framing/SKILL.md
  - /tmp/skill-repository/skills/product-discovery-one-pager/SKILL.md
  - /tmp/skill-repository/skills/product-discovery-opportunity-solution-tree/SKILL.md
  - /tmp/skill-repository/skills/product-discovery-opportunity-solution-tree-branching/SKILL.md
  - /tmp/skill-repository/skills/product-discovery-rice-ice-prioritization/SKILL.md
  - /tmp/skill-repository/scripts/procedure_authored_skills.txt
loop_state: landed
type: implementation
breaking: false
verdict: pass
---

# Implementation record: issue-1812 phase 2 — wave 2c product-discovery

## What was done

canonical: gh issue view 1812 --json comments

The command above (read live) shows the issue comment carries the exact
string `APPROVE issue-1812/implementation` from account `JiwonJung94`,
listed in docs/specs/approvers.md.

Delivered the approved phase-1 proposal
(docs/issue-1812/proposals/2026-08-21-wave-2c-product-discovery.md).
Authored the frozen #1790 wave recipe's `## Trigger` / `## Procedure` /
`## Output shape` sections into all 10 `product-discovery-*` skills in
`tokenmaxxxer/skill-repository` (checkout at `/tmp/skill-repository`,
branch `issue-1812-wave2c-product-discovery` off `origin/main` at
`7279ec9`), rewrote each `description:` from its authored Trigger, and
appended the 10 skill names to `scripts/procedure_authored_skills.txt`
(29 -> 39 entries, incremental). Per the proposal's Shape A/B mapping:
the 5 Shape-A skills (`guardrail-metric-status`,
`hypothesis-preregistration`, `jtbd-problem-framing`,
`opportunity-solution-tree-branching`, `rice-ice-prioritization`) cite
`## Rules` rule numbers verbatim in Procedure; the 5 Shape-B skills
(`assumption-mapping`, `guardrail-metrics`, `hypothesis-testing`,
`one-pager`, `opportunity-solution-tree`) cite their own existing named
sections instead. Committed as `7ee2bce` on the skill-repository
checkout, pushed, and opened as skill-repository PR
https://github.com/tokenmaxxxer/skill-repository/pull/10.

## Why

Basis: the frozen wave recipe (docs/issue-1790/reports/implementation.md
WAVE RECIPE section) and the approved issue-1812 proposal
(docs/issue-1812/proposals/2026-08-21-wave-2c-product-discovery.md),
which resolved the family's Shape A/B split the same way the wave-2a
(#1802) and wave-2b (#1809) proposals resolved it for their own
families — reusing an already-approved resolution rather than
re-litigating a recurring split.

## Upstream basis

docs/issue-1812/proposals/2026-08-21-wave-2c-product-discovery.md;
skill-repository commit `7279ec9` (checkout base) and `7ee2bce` (this
wave's delivery commit).

## The four checks, executed live from the skill-repository checkout

All four commands below were run directly in `/tmp/skill-repository`
this session.

### (a) Manifest checker

canonical: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo exit: $?
exit: 0
```

The command above exited 0.

### (b) Rule-retention sweep

canonical: awk '/^## Rules/{flag=1;next}/^## /{flag=0}flag' skills/product-discovery-<name>/SKILL.md | grep -c '^[0-9]\+\.'

Per-skill post-change output (run for each of the 5 Shape-A skills):

```
guardrail-metric-status: 10 rules
hypothesis-preregistration: 11 rules
jtbd-problem-framing: 10 rules
opportunity-solution-tree-branching: 11 rules
rice-ice-prioritization: 10 rules
```

The counts above match the survey's pre-change baseline exactly
(10+11+10+11+10 = 52) — zero rule lines lost.

canonical: git diff -- skills/

The command above (read live, this session) shows every `-` line in the
5 Shape-B files' diffs falls inside one of the 5 rewritten frontmatter
`description:` blocks — no content-body line (state-machine steps,
field lists, standing directives, common-mistakes lists) was removed
from any of the 10 files.

### (c) `git diff --stat` scoped to the 10 paths + manifest

canonical: git diff --stat

```
 scripts/procedure_authored_skills.txt              | 10 +++++
 .../product-discovery-assumption-mapping/SKILL.md  | 48 ++++++++++++++++++----
 .../product-discovery-guardrail-metric-status/SKILL.md | 42 ++++++++++++++++++-
 .../product-discovery-guardrail-metrics/SKILL.md   | 40 +++++++++++++++---
 .../product-discovery-hypothesis-preregistration/SKILL.md | 39 +++++++++++++++++-
 .../product-discovery-hypothesis-testing/SKILL.md  | 47 ++++++++++++++++++---
 .../product-discovery-jtbd-problem-framing/SKILL.md | 35 +++++++++++++++-
 skills/product-discovery-one-pager/SKILL.md        | 38 ++++++++++++++---
 .../product-discovery-opportunity-solution-tree-branching/SKILL.md | 37 ++++++++++++++++-
 .../product-discovery-opportunity-solution-tree/SKILL.md | 41 +++++++++++++++---
 .../product-discovery-rice-ice-prioritization/SKILL.md | 36 +++++++++++++++-
 11 files changed, 381 insertions(+), 32 deletions(-)
```

Only the 10 `product-discovery-*` SKILL.md paths plus the manifest
appear above — no other path touched.

### (d) Full-tree checker

canonical: python3 scripts/check_skill_conformance.py

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo exit: $?
exit: 0
```

The command above exited 0.

## Empty state

canonical: docs/issue-1812/reports/implementation/survey.md "Two
distinct pre-existing shapes inside the family" section

The survey's own `grep -n "^## "` heading dump (read live during phase
1) shows none of the 10 skills carried `## Trigger`/`## Procedure`/
`## Output shape` pre-change, so no skill qualified for the no-op/
empty-state clause; all 10 were authored fresh.

## Acceptance verification

1. All 10 family skills have the three sections, derived descriptions,
   every pre-existing rule/content line retained; manifest + full-tree
   checker both exit 0.

   canonical: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt

   The manifest and full-tree checkers (checks (a) and (d) above) both
   printed "234 skills checked" and exited 0 when re-run this session.

2. No path outside the 10 family skills + manifest is touched in the
   skill-repository PR.

   canonical: git diff --stat

   The `git diff --stat` output at check (c) above lists only the 10
   family SKILL.md paths plus the manifest file; skill-repository PR
   https://github.com/tokenmaxxxer/skill-repository/pull/10.

## What did not work

None.

## Open findings

None.

## Test-tier note

This wave's work is skill-repository content authoring with no test
suite of its own; the applicable verification is the four checks above,
which is what the issue's acceptance section names. No
`.on-the-record/test-tiers.json` tiering gap applies to this delivery.
