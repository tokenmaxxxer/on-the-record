---
subject: issue-1790
role: implementation
kind: survey
---

# Current-state survey: skill procedural-body authoring (pilot wave)

## Scope surveyed

`/tmp/skill-repository` checkout, commit `65d58b43a60b9b70024d2054a7c68a951ff4b33d`
(issue text cites `ad577a4`; that sha is not HEAD in this checkout — treated
as an earlier reference point, not a mismatch requiring action, since
`git log --oneline -- scripts/check_skill_conformance.py skills/upstream-defect-report-* skills/api-design-*`
shows no commits touching those paths since that point).
canonical: git log --oneline -- scripts/check_skill_conformance.py skills/upstream-defect-report-* skills/api-design-* (run in /tmp/skill-repository)

9 pilot skills:
- `skills/upstream-defect-report-comprehensibility/SKILL.md` (67 lines, 6 rules)
- `skills/upstream-defect-report-convention/SKILL.md` (7 rules, per body read)
- `skills/upstream-defect-report-subtraction/SKILL.md` (81 lines, 7 rules)
- `skills/api-design-error-design/SKILL.md` (38 lines, 13 rules)
- `skills/api-design-http-semantics/SKILL.md` (36 lines, 12 rules)
- `skills/api-design-payload-design/SKILL.md` (36 lines, 12 rules)
- `skills/api-design-resource-modeling/SKILL.md` (38 lines, 13 rules)
- `skills/api-design-tool-landscape/SKILL.md` (58 lines, 4 rules)
- `skills/api-design-versioning-evolution/SKILL.md` (42 lines, 15 rules)
canonical: wc -l + grep -c rule-pattern per file (run in /tmp/skill-repository)

## Frontmatter shape (all 9)

```
---
name: <dirname>
description: Use when you need guidance on <Title>. Applies to the <axis> axis.
axis: <axis>
rule_count_floor: <n>
role: <role>   # only present on upstream-defect-report-* skills
---
```

`description:` reads as a template restating the axis title with a bare
"Use when you need guidance on X" wrapper — no concrete trigger condition
distinguishing when an agent should invoke this specific skill over another.

## Body shape (all 9)

Identical structure: `# <Title>` heading, one paragraph of framing prose,
then `## Rules` with a numbered list. Each rule line follows the pattern
`**When** <condition> — **choice**: <action>; <consequence/rationale>.
source: <citation>`. This reads as playbook/reference material: there is
no ordered "steps the agent executes" section and no stated output-shape
section separate from the per-rule "When" clauses.
canonical: cat skills/upstream-defect-report-convention/SKILL.md, skills/api-design-tool-landscape/SKILL.md (read in /tmp/skill-repository)

`api-design-tool-landscape` differs slightly: its rules read as
tool-adoption recommendations ("the design move behind the
`api-schema-validator` Claude Code skill") rather than authoring
decision rules — same numbered-list shape, same absence of a procedure
section.

None of the 9 pilot skills contain a trigger/procedure/output section in
their current bodies — no no-op candidates surfaced in this pilot set.

## Checker (`scripts/check_skill_conformance.py`)

Checks only frontmatter: `name:` matches dirname, `description:` contains
one of a fixed list of trigger markers (`use when`, `use this`, `trigger`,
etc.). It does not parse the body at all. No existing manifest file exists
in the repo.
canonical: find /tmp/skill-repository -iname '*manifest*' (empty result)

Adding a procedure-section check requires: (a) a manifest data source —
issue text says "a manifest of procedure-authored skills"; since no
existing manifest convention exists to reuse, this is a new file (proposed:
`scripts/procedure_authored_skills.txt`, one skill-dirname per line);
(b) a body-parsing check gated on manifest membership; (c) the new rule
must apply to no skill outside the manifest, so non-manifest skills'
checker behavior stays identical to the unmodified checker's.

## Baseline live run (full tree, unmodified checker)

```
$ python3 /tmp/skill-repository/scripts/check_skill_conformance.py
234 skills checked
```
canonical: python3 scripts/check_skill_conformance.py (run in /tmp/skill-repository, this turn)

Exit code observed: 0. This is the pre-change baseline the phase-2 record
will diff against.

## Corpus scale for the wave recipe

```
$ ls /tmp/skill-repository/skills | wc -l
234
```
canonical: ls skills | wc -l (run in /tmp/skill-repository, this turn)

225 skills remain after this 9-skill pilot. Skills group into role
families by directory-name prefix (e.g. `technical-feasibility` 10,
`release-engineering` 10, `product-discovery` 10, `user-discovery` 7,
`legal-compliance` 7, `conformance-review` 7, `ux-engineering` 6,
`technical-writing` 6, `ml-engineering` 6, `incident-response` 6,
`finance-unit-economics` 6, `customer-support` 6, `secure-coding` 5,
`risk-management` 5, `refactoring-legacy` 5, `partnerships-bd` 5,
`market-analysis` 5, `knowledge-management` 5, `growth-analytics` 5, and
~25 more families of 2-4 each). Family size varies 2-10; this shapes the
wave partition proposed in the proposal document.
canonical: ls skills | awk -F- '{print $1"-"$2}' | sort | uniq -c | sort -rn (run in /tmp/skill-repository, this turn)

## No existing procedure-authored skills to model from

Grep across the whole repo for section headings named "Trigger",
"Procedure", or "Output shape" (case-insensitive) in any `SKILL.md` finds
none — the 9 pilot skills' target shape has no precedent in this repo; the
pattern is being originated by this issue.
canonical: grep -ril -E '^## +(Trigger|Procedure|Output shape)' /tmp/skill-repository/skills (empty result)
