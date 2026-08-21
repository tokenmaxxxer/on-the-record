---
subject: issue-1830
type: survey
---

# Survey: observability family (wave 2d)

## Scope-field note

canonical: `gh issue view 1830` (read live) — the issue body's `scope:`
line reads `docs/issue-1801/proposals/, docs/issue-1801/reports/`, not
issue-1830's own buckets — the same copy-paste artifact the wave-2b
(#1809) and wave-2c (#1812) surveys each found in their own issue
bodies. Every other field (title, requirements, acceptance) names
issue-1830, and this session's subject is issue-1830 per its own
invocation. This survey and the accompanying proposal are written under
this issue's own per-subject bucket, not the mismatched one named in
that field.

## Count discrepancy in the issue body

canonical: `gh issue view 1830` (read live) — the "Program context"
paragraph states "Family: observability (10 skills — the largest
remaining family per the pilot survey)", but the issue title says "(7
skills)" and Requirement 1 says "All 7 observability-* skills". derived:
`find /tmp/skill-repository/skills -maxdepth 1 -iname "observability-*"`
lists exactly 7 directories (below) — the live checkout matches the
title and Requirement 1's count of 7, not the Program-context
paragraph's 10. This wave proceeds against the 7-skill count the title,
Requirements, and live checkout all agree on; the Program-context "10"
looks like stale text carried over from an earlier planning round, the
same class of copy-paste artifact as the scope-field note above.

## Checkout and manifest state

canonical: `/tmp/skill-repository` checkout, `origin/main` at commit
`d0bde0e` ("Author procedural bodies for wave 2c: product-discovery
family (issue-1812) (#10)") — read live via `git log origin/main
--oneline -3`. Branch `issue-1830-wave2d-observability` created off
`origin/main` for this wave.

`scripts/procedure_authored_skills.txt` currently lists 39 names —
canonical: `wc -l scripts/procedure_authored_skills.txt` (read live) —
the 9 pilot skills, 10 wave-2a `technical-feasibility-*`, 10 wave-2b
`release-engineering-*`, and 10 wave-2c `product-discovery-*` skills.
None of the 7 `observability-*` skills are present yet.

## Family enumeration

derived: `find skills -maxdepth 1 -iname "observability-*" | sort` — 7
directories, matching the issue title and Requirement 1's count:

```
skills/observability-cardinality-budget
skills/observability-explorability
skills/observability-methodology-selection
skills/observability-phase-trace
skills/observability-signal-golden
skills/observability-signal-red
skills/observability-signal-use
```

## Single shape across the whole family — no Shape A/B split this wave

canonical: `grep -n "^## " skills/observability-*/SKILL.md` (read live
from the checkout) — unlike wave-2a, wave-2b, and wave-2c, all 7 files
show the identical single heading `## Rules` (no other `## ` heading
present pre-change). canonical: `grep -H rule_count_floor
skills/observability-*/SKILL.md` — all 7 carry `rule_count_floor: 3`
frontmatter, confirming all 7 are Shape A (the pilot's `## Rules`-with-
numbered-rules structure the recipe was written against). There is no
Shape B subset in this family — the classification the issue's prompt
asked this survey to perform ("classify Shape A/B per the #1802/#1809/
#1812 precedent") resolves to: 7 of 7 Shape A, 0 Shape B.

derived: per-skill numbered-rule count, `awk '/^## Rules/{flag=1;next}
/^## /{flag=0}flag' skills/observability-<name>/SKILL.md | grep -c
'^[0-9]\+\.'` run per skill:

```
cardinality-budget:      4 rules
explorability:           3 rules
methodology-selection:   3 rules
phase-trace:             3 rules
signal-golden:           4 rules
signal-red:              4 rules
signal-use:              4 rules
```

25 rule lines total across the 7 skills. canonical: the same
`grep -n "^## "` heading dump above shows no occurrence of `## Trigger`/
`## Procedure`/`## Output shape` across any of the 7 files — none of the
7 skills has them yet, so none qualifies for the no-op/empty-state
clause.

## What this means for the recipe

Because every skill in this family is Shape A, the frozen recipe's step
2 — "`## Procedure` (ordered steps, each citing rule number(s) from
`## Rules`)" — applies unmodified and uniformly to all 7, with no
citation-target branching needed. This is a simpler case than wave-2a/
2b/2c: no alternative-resolution decision to reuse or re-litigate for a
Shape-B subset, because there isn't one.

## Checker mechanics

canonical: `git log -1 --format=%H -- scripts/check_skill_conformance.py`
(read live) returns `bb89bdc1ba7458fdf7c4ee494a3c0ea70cd65322` — the
pilot commit — confirming the checker has had zero logic edits across
the pilot and all three prior waves (2a/2b/2c), through this checkout at
`d0bde0e`. `--manifest <path>` requires `## Trigger`, `## Procedure`,
`## Output shape` (any order) in a listed skill's SKILL.md body via a
fixed `PROCEDURE_HEADINGS` tuple; skills not listed are unaffected.

## Rule-retention baseline (pre-change)

Pre-change totals to retain post-change: 25 numbered rule lines
(4+3+3+3+4+4+4) under `## Rules` across the 7 skills, plus every other
pre-existing content line in each file (frontmatter, framing paragraph,
research-trail line, source: URLs inside rule bodies) — the recipe's
zero-loss guarantee is content-level, not limited to rule-numbered
lines, per the same principle the earlier waves applied.

## Skip-condition check

Neither mandatory scout-directive skip condition applies on its face —
this is not a pure bugfix — but the design decision the earlier three
waves' surveys existed to resolve (how to phrase `## Procedure` citations
for a Shape-B subset) does not arise in this family: all 7 skills are
Shape A, so the recipe applies verbatim with no open citation-target
choice left. Scouting is not run as a separate external sweep, for the
same reason the three earlier waves gave: the applicable guidance is
this repository's own frozen recipe plus the four skills named in the
role's source-allowlist mapping (issue #1758) — there is no external
field to sweep for authoring an internal skill file's procedural body,
and this wave has no unresolved shape-classification question left to
scout against; the classification above **is** the direction-setting
finding this survey exists to produce, and the proposal is drafted
directly from it.
