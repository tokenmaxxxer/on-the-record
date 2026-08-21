# Current-state survey: requirements-engineering-rules procedural body

subject: issue-1943
role: implementation

## Write surface

`/tmp/skill-repository` (tokenmaxxxer/skill-repository checkout, `main`
at `589c55e`, clean working tree). Target file:
`skills/requirements-engineering-rules/SKILL.md` (237 lines) plus
`scripts/procedure_authored_skills.txt`.

## Frontmatter shape (pre-change)

```
---
name: requirements-engineering-rules
subject: issue-1174
rule_count_floor: 23
axes: 7
tier: rich
description: Use when you need guidance on Requirements-engineering operational playbook.

---
```

canonical: skills/requirements-engineering-rules/SKILL.md:1-8 (read live
in /tmp/skill-repository). `description:` is still the template default
("Use when you need guidance on X"), not derived from any Trigger
section — this skill has not yet been touched by the procedural-body
wave.

## Body shape (pre-change)

canonical: `grep -n '^## Trigger\|^## Procedure\|^## Output shape'
skills/requirements-engineering-rules/SKILL.md` (run live in
/tmp/skill-repository) — returns no matches: none of the three
procedural-body headings exist yet. The body opens with one framing
paragraph, then goes straight into `## Axis 1 — EARS-pattern selection`
(rules 1-6), followed by Axis 2 (Verification-method selection, rules
7-11b), Axis 3 (Ambiguity detection & resolution, rules 12-15), Axis 4
(Singularity/atomicity, rules 16-17), Axis 5 (Traceability-link
granularity, rules 18-20), Axis 6 (Prioritization scope-cut tie-break,
rules 21-22), Axis 7 (REMOVAL: requirement subtraction and pruning,
rules 23-27), and closes with a "Removal-category self-check" paragraph.
27 numbered rule lines total (including sub-rules 11a/11b), across 7
axes — matches the `axes: 7` frontmatter field; `rule_count_floor: 23`
is a floor, not the live count.

This is a live-edit case, not a no-op: the wave recipe's own step 1
("check the skill's body for existing headings before authoring; if
present, record a no-op") does not apply here per the grep result above.

## Manifest state

canonical: scripts/procedure_authored_skills.txt (196 lines, read live in
/tmp/skill-repository) does not list `requirements-engineering-rules`.
9 families already appended incrementally by prior waves (#1790 pilot,
then per-issue single-skill waves through #1937/#1934 most recently), one
skill name per line, no header/comment lines currently present.

## Checker script

canonical: scripts/check_skill_conformance.py:14-18,26 (read live in
/tmp/skill-repository) — already carries the `--manifest <path>` opt-in
check: `PROCEDURE_HEADINGS = ("## Trigger", "## Procedure", "## Output
shape")`, checked against every skill directory listed in the manifest;
skills absent from the manifest are unaffected. No checker-logic change
is needed for this wave — the issue's own non-goal ("no checker logic
changes") is satisfiable by reuse alone.

## Pattern precedent

canonical: docs/issue-1937/proposals/procedural-body-performance-engineering-operational-playbook.md
and docs/issue-1934/proposals/procedural-body-issue-retrospective.md
(read in this checkout) — both prior single-skill waves used a per-axis
Procedure step (one step per axis/layer, each citing the rule numbers
under it), reusing the existing axis/layer grouping rather than
flattening it. This skill's existing 7-axis grouping maps the same way:
one Procedure step per axis, citing that axis's rule range.

## Skip-condition check

Neither scout skip condition applies on its face (this is not a pure
bugfix, and the wave recipe leaves the Trigger-clause wording an open
design choice) — however, the *scout sweep* itself is skipped: the
frozen recipe from #1790 (adopted verbatim per the issue's own
instruction, "Apply the frozen recipe verbatim") is prior art already
scouted and applied in three prior authoring rounds.
canonical: docs/issue-1790/reports/implementation.md (WAVE RECIPE
section, read in this checkout) plus the two pattern-precedent proposals
cited above — re-scouting the same recipe for a fourth single-skill
application would search a field already searched in this same
repository. This is recipe reuse, not a fresh design decision — recorded
per the scout directive's skip-record requirement.
