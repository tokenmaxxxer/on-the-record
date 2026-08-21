---
subject: issue-1912
kind: survey
canonical_basis: docs/issue-1790/reports/implementation.md (WAVE RECIPE section, pilot #1790)
---

# Current-state survey: sales family (wave 2a)

## Scope

Checkout: `tokenmaxxxer/skill-repository`. canonical: `git -C
/tmp/skill-repository-1912 log --oneline -1`, 2026-08-21: `1b04844
Author procedural bodies for wave 2a: marketing family (issue-1900)
(#32)` — the marketing-family wave (#1900/#1904) is the latest commit
reachable from `origin/main` at this checkout's clone time. Working
clone: `/tmp/skill-repository-1912`, checked out from `origin/main`.
canonical: `git -C /tmp/skill-repository-1912 rev-parse HEAD`,
2026-08-21: `1b04844169834a225484c3bd425649b0322e4ee3`.

The role-source-allowlist mapping (issue #1758) for this session names
guidance commit `d110b90` — that commit governs which guidance skills
apply to this role (implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice,
implementation-blueprint), not which skill-repository commit to build
against; the wave's own instruction is to build against `origin/main`.

## Family membership

3 `sales-*` skill directories exist under `skills/` — matches the
issue's own Requirement 1 ("3 sales-* skills") and title ("3 skills").
canonical: `find /tmp/skill-repository-1912/skills -maxdepth 1 -name 'sales-*'`, 2026-08-21:

```
skills/sales-objection-handling
skills/sales-pitch-scoping-and-messaging-handoff
skills/sales-qualification-and-discovery
```

The issue body's own text also carries a stray "10 skills" sentence
that contradicts the issue's own Requirement 1 and Acceptance sections
(both say 3, matching the actual directory count above). canonical:
docs/issue-1900/reports/implementation/survey.md, "Family membership"
section — records the identical pattern for the marketing family (issue
body said "10 skills", 5 directories actually existed,
Requirements/Acceptance said 5); the same family-size-estimate leftover
recurs here.

## Shape classification (per frozen recipe step 1)

canonical: `grep -n '^## ' skills/<name>/SKILL.md` run against all 3,
2026-08-21:

| skill | existing `## ` headings | classification |
|---|---|---|
| sales-objection-handling | `## Rules` only | Shape B (needs authoring) |
| sales-pitch-scoping-and-messaging-handoff | `## Rules` only | Shape B (needs authoring) |
| sales-qualification-and-discovery | `## Rules` only | Shape B (needs authoring) |

None carry `## Trigger`/`## Procedure`/`## Output shape` yet — no no-op
case in this family, all 3 require authoring. canonical:
docs/issue-1900/reports/implementation/survey.md, "Shape classification"
section — the marketing wave's 5 skills found the identical outcome
(all Shape B); the #1790 pilot's own 9-skill check (canonical:
docs/issue-1790/reports/implementation.md, WAVE RECIPE step 1) also
found all 9 required authoring.

## Rule-line counts (pre-change baseline for the retention sweep)

canonical: `grep -c '^[0-9]\+\.' skills/<name>/SKILL.md` and `wc -l`,
2026-08-21:

| skill | numbered rules | file lines |
|---|---|---|
| sales-objection-handling | 6 | 61 |
| sales-pitch-scoping-and-messaging-handoff | 6 | 66 |
| sales-qualification-and-discovery | 6 | 60 |

Total: 18 rules across the family, 187 lines. Every skill carries a
`description:` frontmatter line ending on an axis-specific sentence and
an `axis:` + `rule_count_floor:` pair. canonical:
`skills/sales-objection-handling/SKILL.md` lines 1-6, 2026-08-21:

```
---
name: sales-objection-handling
description: Use when you need guidance on Objection handling. Applies to the objection-handling axis.
axis: objection-handling
rule_count_floor: 5
---
```

This shape matches the pilot's pre-change skills (canonical:
docs/issue-1790/reports/implementation/survey.md, "Frontmatter shape"
section) and the marketing-family shape (canonical:
docs/issue-1900/reports/implementation/survey.md, "Rule-line counts"
section) — same authoring surface, same recipe applies without
divergence.

## Manifest state

canonical: `tail -5 scripts/procedure_authored_skills.txt` and `wc -l
scripts/procedure_authored_skills.txt` against `origin/main` at
`1b04844`, 2026-08-21: 163 entries, most recently
`marketing-channel-selection`, `marketing-message-persuasion`,
`marketing-positioning-differentiation`, `marketing-scope-pruning`,
`marketing-segment-targeting` (the #1900 marketing wave). No `sales-*`
entries present yet in this file.

## Checker script

canonical: `scripts/check_skill_conformance.py` lines 14-21, 116-137
(argparse wiring for `--manifest`) — unchanged from the #1790 pilot and
#1900 marketing waves: an optional `--manifest <path>` flag runs the
additive Trigger/Procedure/Output-shape check only against manifest
entries; the full-tree run (no flag) checks basic skill-file
conformance across every skill directory regardless of manifest
membership. No checker-logic change is proposed or needed for this
wave.

## Gap to close

All 3 sales skills need: (a) `## Trigger`/`## Procedure`/
`## Output shape` inserted between the framing paragraph and
`## Rules`, procedure steps citing existing rule numbers; (b)
`description:` frontmatter rewritten from the new Trigger content,
keeping the "use when" trigger-marker substring the checker scans for;
(c) their 3 names appended to `procedure_authored_skills.txt` (after
the existing 163 entries, giving 166). No checker logic change, no hook
change, no path outside these 3 skill dirs + the manifest file.
