---
subject: issue-1900
kind: survey
canonical_basis: docs/issue-1790/reports/implementation.md (WAVE RECIPE section, pilot #1790)
---

# Current-state survey: marketing family (wave 2a)

## Scope

Checkout: `tokenmaxxxer/skill-repository`, origin/main at `c93b81b`
(matches the role's mapped guidance commit per the invocation). Working
clone: `/tmp/skill-repository-1900`, branch
`issue-1900-wave2a-marketing`, checked out from `origin/main`.

## Family membership

5 `marketing-*` skill directories exist under `skills/` — matches
Requirement 1's count of 5, not the issue body's stray "10 skills"
sentence (a leftover from an earlier family-size estimate; the
Requirements section and the acceptance section both say 5).
canonical: `find /tmp/skill-repository-1900/skills -maxdepth 1 -name 'marketing-*'`, 2026-08-21:

```
skills/marketing-channel-selection
skills/marketing-message-persuasion
skills/marketing-positioning-differentiation
skills/marketing-scope-pruning
skills/marketing-segment-targeting
```

## Shape classification (per frozen recipe step 1)

canonical: `grep -n '^## ' skills/<name>/SKILL.md` run against all 5,
2026-08-21:

| skill | existing `## ` headings | classification |
|---|---|---|
| marketing-channel-selection | `## Rules` only | Shape B (needs authoring) |
| marketing-message-persuasion | `## Rules` only | Shape B (needs authoring) |
| marketing-positioning-differentiation | `## Rules` only | Shape B (needs authoring) |
| marketing-scope-pruning | `## Rules` only | Shape B (needs authoring) |
| marketing-segment-targeting | `## Rules` only | Shape B (needs authoring) |

None carry `## Trigger`/`## Procedure`/`## Output shape` yet — no no-op
case in this family, all 5 require authoring. This matches the pilot's
own finding (recipe step 1 canonical citation: all 9 pilot skills also
required authoring).

## Rule-line counts (pre-change baseline for the retention sweep)

canonical: `grep -c '^[0-9]\+\.' skills/<name>/SKILL.md`, 2026-08-21:

| skill | numbered rules | file lines |
|---|---|---|
| marketing-channel-selection | 6 | 56 |
| marketing-message-persuasion | 6 | 68 |
| marketing-positioning-differentiation | 6 | 58 |
| marketing-scope-pruning | 6 | 63 |
| marketing-segment-targeting | 6 | 57 |

Total: 30 rules across the family, 302 lines. Every skill carries a
`description:` frontmatter line ending on an axis-specific sentence and
an `axis:` + `rule_count_floor:` pair; each rule line ends with a
`source:` URL. This shape matches the pilot's pre-change skills
(canonical: docs/issue-1790/reports/implementation/survey.md,
"Frontmatter shape" section) — same authoring surface, same recipe
applies without divergence.

## Manifest state

canonical: `tail -30 scripts/procedure_authored_skills.txt` against
`origin/main`, 2026-08-21: `scripts/procedure_authored_skills.txt`
currently lists 29 skill names from prior waves (refactoring-legacy,
growth-analytics, knowledge-management, capacity-planning,
localization — the last 5 families landed on main; `brand-design` from
#1896/#1898 is still an unmerged PR branch, not yet on origin/main, so
it is absent from this manifest read).

## Checker script

canonical: `scripts/check_skill_conformance.py` lines 14-21, 116-137
(argparse wiring for `--manifest`): the script accepts an optional
`--manifest <path>` flag — an additive, opt-in check that every
manifest name has a `SKILL.md` body meeting the Trigger/Procedure/
Output-shape contract. Full-tree run (no flag) checks basic skill-file
conformance across every skill directory regardless of manifest
membership.

## Gap to close

All 5 marketing skills need: (a) `## Trigger`/`## Procedure`/
`## Output shape` inserted between the framing paragraph and
`## Rules`, procedure steps citing existing rule numbers; (b)
`description:` frontmatter rewritten from the new Trigger content,
keeping the "use when" trigger-marker substring the checker scans for;
(c) their 5 names appended to `procedure_authored_skills.txt`. No
checker logic change, no hook change, no path outside these 5 skill
dirs + the manifest file.
