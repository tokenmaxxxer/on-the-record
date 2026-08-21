# Survey: issue-retrospective-timeline-comprehensibility-and-subtraction-rules procedural body

Subject: issue #1934, procedural-body wave 2a, single-skill family
`issue-retrospective-timeline-comprehensibility-and-subtraction-rules` in
tokenmaxxxer/skill-repository. Recipe basis: docs/issue-1790/reports/implementation.md
WAVE RECIPE section (pilot #1790).

## Checkout state

canonical: /tmp/skill-repository, `git status`/`git log -1` output (this
turn) — clean tree, `main` at `33dd0cb` ("Merge pull request #39 from
tokenmaxxxer/issue-1921-wave2a-verify-authoring"), tracking `origin/main`.

## Target skill's current shape

canonical: /tmp/skill-repository/skills/issue-retrospective-timeline-comprehensibility-and-subtraction-rules/SKILL.md,
read in full (140 lines), this turn.

Frontmatter today:
```
---
name: issue-retrospective-timeline-comprehensibility-and-subtraction-rules
description: Use when you need guidance on Retrospective-record convention, subtraction, and comprehensibility rules. Applies to the convention, subtraction, comprehensibility axis.
axis: convention, subtraction, comprehensibility
rule_count_floor: 8
axes: convention,subtraction,comprehensibility
---
```

canonical: `grep -n "^## " skills/issue-retrospective-timeline-comprehensibility-and-subtraction-rules/SKILL.md`
(this turn) — output lists only `## Rules`; no `## Trigger`, `## Procedure`,
or `## Output shape` heading anywhere in the body. Per WAVE RECIPE step 1,
this skill needs authoring (not a no-op).

Body after the frontmatter: one framing paragraph (research trail +
domain-classification sentence), then `## Rules` with numbered rules
(rules 8, 9, 10, 11 marked `**REMOVAL**`). canonical:
`grep -c "^[0-9]\+\." skills/issue-retrospective-timeline-comprehensibility-and-subtraction-rules/SKILL.md`
(this turn) — output `15`.

## Manifest state

canonical: `grep -n issue-retrospective-timeline scripts/procedure_authored_skills.txt`
(this turn) — exit 1, no match: the skill name is absent from
`scripts/procedure_authored_skills.txt`.

## Checker baseline (executed live, this checkout, this turn)

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo exit=$?
exit=0
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo exit=$?
exit=0
```

acceptance: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt — result: exit 0, "234 skills checked"
acceptance: python3 scripts/check_skill_conformance.py — result: exit 0, "234 skills checked"

Reason the baseline reads clean pre-change: the manifest check only
inspects skills already listed in the manifest file, and the full-tree
check only inspects frontmatter `name:`/`description:` shape, not the
procedure headings — consistent with `scripts/check_skill_conformance.py`'s
own docstring (`--manifest` is additive/opt-in, unlisted skills
unaffected). canonical: /tmp/skill-repository/scripts/check_skill_conformance.py,
module docstring, read this turn.

## Precedent read: already-authored skills in the same wave family

canonical: `grep -l "^## Trigger" skills/*/SKILL.md` (this turn) — lists
prior procedure-authored skills (e.g. `architecture-interface-contract-shape`,
`api-design-error-design`). Read
/tmp/skill-repository/skills/architecture-interface-contract-shape/SKILL.md
lines 1-45 in full, this turn, as the concrete pattern to mirror: `## Trigger`
is 4-6 lines naming the concrete deciding conditions (not a restatement of
the skill title); `## Procedure` is an ordered list whose each step cites
rule numbers in parentheses, e.g. "route long-running ... through
asynchronous messaging instead (rule 2)"; `description:` in frontmatter is
rewritten to a sentence derived from the Trigger content, keeping a
checker trigger-marker substring ("Use when"). No `## Output shape`
example was in the read range, but the WAVE RECIPE and checker both
require it as a third heading alongside Trigger/Procedure — it names what
the applied skill produces (here: retrospective-record section
content/decisions, following the family's own record-shape convention
already documented in rule 13's five fixed sections).

## Unknowns / gaps this survey found

- No family sibling of `issue-retrospective-timeline-comprehensibility-and-subtraction-rules`
  exists in skill-repository (single-skill family per the issue text) —
  so there is no in-family Trigger example to copy verbatim; the
  cross-family precedent above is the closest available model.
- The frozen recipe's step 2 says Trigger must be "not a restatement of
  the title" but for a single-skill family there is no sibling axis to
  distinguish from — the Trigger for this skill will instead distinguish
  it from adjacent record-writing moments (drafting mid-incident vs.
  writing a records-only retrospective) rather than from a sibling skill,
  which is a valid reading of the recipe (the recipe's "sibling axes"
  language assumes multi-skill families but does not forbid single-skill
  application).
