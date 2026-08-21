# Current-state survey: issue-1882 (knowledge-management wave)

subject: issue-1882

Scope surveyed: the 5 `knowledge-management-*` skills in the
`tokenmaxxxer/skill-repository` checkout at `/tmp/skill-repository`
(commit `d04a34874fdaa39b62a23fd9ff03b01bd4f16efd`, on leftover branch
`issue-1873-procedural-body-refactoring-legacy` — this wave will branch
fresh off `main` before authoring).

## Skill inventory

`ls skill-repository/skills | grep knowledge-management` (canonical: run
live in /tmp/skill-repository) lists exactly 5 directories:

```
knowledge-management-curation-pruning
knowledge-management-pattern-extraction
knowledge-management-structure-findability
knowledge-management-supersession-lifecycle
knowledge-management-taxonomy-tagging
```

The issue's Program-context line states "10 skills — the largest
remaining family"; the live tree has 5.
canonical: docs/issue-1873/reports/implementation/survey.md, read this
session at /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/docs/
issue-1873/reports/implementation/survey.md — that survey noted the same
discrepancy for its own family. The issue's Requirements section
explicitly says "All 5 knowledge-management-* skills", which is what
this wave delivers against, per that precedent.

## Body shape (Shape A/B classification)

canonical: `grep -L '## Trigger' skill-repository/skills/knowledge-management-*/SKILL.md`
run live in /tmp/skill-repository, plus a direct Read of each of the 5
SKILL.md files in full (this session) — all 5 files matched the grep
(i.e. none already carry a `## Trigger` heading).

All 5 are **Shape A** (no `## Trigger`/`## Procedure`/`## Output shape`
section present — live edits required, no no-op/empty-state applies):

- `knowledge-management-curation-pruning` — frontmatter + framing
  paragraph ("Research trail: ...") + `## Rules` (11 numbered rules, 2
  marked `**REMOVAL**`).
- `knowledge-management-pattern-extraction` — same shape, `## Rules` has
  11 numbered rules (2 `**REMOVAL**`).
- `knowledge-management-structure-findability` — same shape, `## Rules`
  has 11 numbered rules (2 `**REMOVAL**`).
- `knowledge-management-supersession-lifecycle` — same shape, `## Rules`
  has 11 numbered rules (2 `**REMOVAL**`).
- `knowledge-management-taxonomy-tagging` — same shape, `## Rules` has 11
  numbered rules (2 `**REMOVAL**`).

Total: 55 rule lines across the 5 files (11 each).

## Rule shape within `## Rules`

All 5 skills use the same flat numbered-list convention as the #1790
pilot and the immediately preceding refactoring-legacy wave (issue-1873):
`1. When ... — ...`, with some entries marked `**REMOVAL**` inline
(not a separate bullet style) and a trailing `source: <url>` on most
rules. Rule numbers are printed and stable, so citation-by-printed-number
(not bullet-position) is the fit, matching the refactoring-legacy wave's
precedent rather than the finance-unit-economics wave's
bullet-position convention.

Cross-links between the 5 skills already use the recipe's `[[axis-name]]`
convention (e.g. `[[pattern-extraction]]`, `[[taxonomy-tagging]]`) inside
rule text — these are pre-existing content, not something this wave
introduces or needs to alter.

## Frontmatter shape

Each skill's frontmatter carries `name`, `description` (currently the
templated "Use when you need guidance on <Title>. Applies to the
<axis> axis."), `axis`, and `rule_count_floor: 10`. No skill's
`description:` yet reflects an authored Trigger section — all 5 need the
`description:` rewrite step.

## Manifest state

canonical: `grep knowledge-management scripts/procedure_authored_skills.txt`
and `tail -5 scripts/procedure_authored_skills.txt`, both run live in
/tmp/skill-repository — the grep produced no output (no
`knowledge-management-*` name listed yet); the tail showed the file's
most recent block (123 lines total as of this checkout) is the 5
refactoring-legacy names (issue-1873, lines 119-123). This wave appends
its 5 names after that block, per the recipe's "extend incrementally"
step.

## Checker state

`python3 scripts/check_skill_conformance.py --manifest
scripts/procedure_authored_skills.txt` and `python3
scripts/check_skill_conformance.py` (no flag) both exist and were used
unmodified by the two most recent waves (refactoring-legacy issue-1873,
risk-management issue-1867); no checker-logic change is needed or
in scope here (issue non-goal).

## Conclusion feeding the proposal

All 5 knowledge-management skills require live authoring (Shape A, no
no-op). The frozen #1790 recipe, reused verbatim by the refactoring-legacy
wave (issue-1873) with printed-rule-number citation, is a direct fit:
same numbered-list rule convention, same absence of any existing
Trigger/Procedure/Output-shape section, same checker/manifest tooling
with no changes needed.
