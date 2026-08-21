---
subject: issue-1907
role: implementation
kind: survey
---

# Current-state survey: data-engineering family (wave 2a)

## Scope

Checkout: `/tmp/skill-repository`, branch `main` at commit `1b04844`
(`Author procedural bodies for wave 2a: marketing family (issue-1900)
(#32)`). This survey covers the 3 `data-engineering-*` skills named in
issue #1907:

- `skills/data-engineering-data-quality/SKILL.md`
- `skills/data-engineering-failure-handling/SKILL.md`
- `skills/data-engineering-pipeline-design/SKILL.md`

canonical: `find skills -maxdepth 1 -iname 'data-engineering-*'` (run in
`/tmp/skill-repository`) — returns exactly these 3 directories, matching
the issue's "3 data-engineering-* skills" count.

## Frontmatter shape (Shape A/B classification, per #1790 precedent)

canonical: `grep -n '^## ' skills/data-engineering-*/SKILL.md` (run in
`/tmp/skill-repository`) — none of the 3 files contain `## Trigger`,
`## Procedure`, or `## Output shape` headings; each file's only headings
are the H1 title and the framing paragraph, followed directly by the
numbered rules list (unheaded, starts right after the framing paragraph
in these 3 files — same layout as the #1790 pilot's `api-design-*`
skills, which used a bare numbered list with no explicit `## Rules`
heading either).

All 3 skills are **Shape A** (need live authoring) — none is already
procedure-shaped, so the acceptance criterion's no-op/empty-state clause
does not apply to any of the 3, matching the #1790 pilot's own
determination for all 9 of its skills.

## Per-skill rule inventory

| Skill | axis | rule_count_floor | actual rule lines (addition/REMOVAL) |
|---|---|---|---|
| `data-engineering-data-quality` | data-quality | 10 | 13 (11 addition, 2 REMOVAL) |
| `data-engineering-failure-handling` | failure-handling | 10 | 13 (11 addition, 2 REMOVAL) |
| `data-engineering-pipeline-design` | pipeline-design | 10 | 15 (13 addition, 2 REMOVAL) |

derived: `grep -c '\*\*addition\*\*\|\*\*REMOVAL\*\*' skills/data-engineering-*/SKILL.md` (run in `/tmp/skill-repository`):

```
skills/data-engineering-data-quality/SKILL.md:13
skills/data-engineering-failure-handling/SKILL.md:13
skills/data-engineering-pipeline-design/SKILL.md:15
```

Each file's `description:` follows the same pre-authoring template as the
#1790 pilot's skills: `Use when you need guidance on <Title> — decision
rules. Applies to the <axis> axis.` — all 3 need rewriting per the
recipe's step 3.

## Manifest state

canonical: `wc -l scripts/procedure_authored_skills.txt` (run in
`/tmp/skill-repository`) and `grep -c data-engineering
scripts/procedure_authored_skills.txt` (same location) — the manifest
already lists names from the pilot and every wave 2a family landed
through commit `1b04844` (technical-feasibility, release-engineering,
product-discovery, conformance-review, observability, legal-compliance,
ux-engineering, user-discovery, technical-writing, pricing,
ml-engineering, incident-response, finance-unit-economics,
customer-support, secure-coding, risk-management, market-analysis,
partnerships-bd, refactoring-legacy, growth-analytics,
knowledge-management, capacity-planning, localization, brand-design,
marketing), and 0 `data-engineering` matches pre-change.

## Unrelated in-flight changes (not this issue's scope)

canonical: `git status` (run in `/tmp/skill-repository`) — shows 4
modified files outside this issue's write set:
`skills/defect-verification-{evidence-artifact-completeness,
independence-from-upstream-verdicts,reproduction-evidence-quality,
severity-band-assignment}/SKILL.md`. These belong to a different
in-flight wave (per #1905, defect-verification family) and are left
untouched; the phase-2 diff for this issue must not include them.

## Checker script

`scripts/check_skill_conformance.py` already carries the `--manifest`
opt-in flag from the #1790 pilot (unchanged since); no checker-logic
change is needed or in scope per this issue's non-goals.

## Conclusion

Recipe applies verbatim, same as every prior wave 2a family (per the
"Per-skill rule inventory" and "Manifest state" sections above): author
the Trigger/Procedure/Output-shape sections into each Shape-A skill,
rewrite each `description:`, append each name to
`procedure_authored_skills.txt`, then run the manifest checker, the
rule-retention sweep, `git diff --stat`, and the full-tree checker.
