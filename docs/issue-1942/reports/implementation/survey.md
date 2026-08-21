---
subject: issue-1942
role: implementation
kind: survey
loop_state: coding
---

# Current-state survey: pr-communications-message-planning-and-evaluation-rules procedural body

## Scope

Skill-repository checkout: `/tmp/skill-repository`, `main` at commit
`589c55e5835735e017743cf399b3288c6726e1d`.

Target: `skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md`
(single-skill family, per issue #1942).

## Frontmatter shape

canonical: skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md
(read in /tmp/skill-repository at commit 589c55e5835735e017743cf399b3288c6726e1d)

```
---
name: pr-communications-message-planning-and-evaluation-rules
description: Use when you need guidance on pr-communications operational playbook.
role: pr-communications
axes:
  - objective-channel-fit
  - message-hierarchy
  - approval-sequencing
  - risk-qa-prep
  - evaluation-criteria
  - persuasion-technique
rule_count_floor: 12
tier: moderate
---
```

`description:` is still the unfilled template ("Use when you need
guidance on X"), matching the pre-recipe default seen in other
not-yet-authored skills rather than a Trigger-derived sentence.

## Body shape

The body is a flat numbered `## Rules` list (rules 1-13, three marked
`**REMOVAL**`: rules 3, 10, 13), each rule stating a When/choose
condition with an inline `Source:` citation, followed by a
`## Counter-example` section and an `## Open gap` section.
derived: `grep -cE "^[0-9]+\." skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md`
(run in /tmp/skill-repository at commit 589c55e5835735e017743cf399b3288c6726e1d),
result: `13`.

No `## Trigger`, `## Procedure`, or `## Output shape` heading exists
anywhere in the body. derived: `grep -E "^## (Trigger|Procedure|Output shape)" skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md`
(run in /tmp/skill-repository at commit 589c55e5835735e017743cf399b3288c6726e1d),
result: no matches (empty output, exit 1). This skill is therefore a
live-edit case under the frozen recipe's step 1
(docs/issue-1790/reports/implementation.md, WAVE RECIPE section), not a
no-op.

The frontmatter's own `axes:` list (6 entries: objective-channel-fit,
message-hierarchy, approval-sequencing, risk-qa-prep,
evaluation-criteria, persuasion-technique) maps onto the 13 rules as:
rule 1 -> objective-channel-fit; rules 2-3 -> message-hierarchy; rules
4-6 -> persuasion-technique; rules 7-9 -> risk-qa-prep; rule 10 ->
risk-qa-prep (REMOVAL); rules 11-12 -> evaluation-criteria; rule 13 ->
message-hierarchy (REMOVAL). canonical:
skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md
(Rules section, read in /tmp/skill-repository at commit
589c55e5835735e017743cf399b3288c6726e1d).

## Manifest state

canonical: scripts/procedure_authored_skills.txt (read in
/tmp/skill-repository, 195 lines total; derived: `grep -c
pr-communications scripts/procedure_authored_skills.txt`, result: `0`)

`pr-communications-message-planning-and-evaluation-rules` is not yet
listed. The file's most recent entries (tail of the same read) are
`content-design-operational-playbook`,
`accessibility-aria-and-contrast-rules`,
`interaction-design-form-control-and-layout`,
`issue-retrospective-timeline-comprehensibility-and-subtraction-rules`,
`performance-engineering-operational-playbook` (issues #1928, #1927,
#1932, #1934, #1937), all authored under the same frozen recipe in
prior waves.

## Pattern precedent

canonical: skills/upstream-defect-report-comprehensibility/SKILL.md
(read in /tmp/skill-repository at commit
589c55e5835735e017743cf399b3288c6726e1d) — one of the #1790 pilot's flat
`## Rules`-list skills (not a layered/axis skill like
performance-engineering-operational-playbook), authored with `## Trigger`
naming concrete conditions with inline rule citations, `## Procedure` as
ordered numbered steps each citing rule number(s), `## Output shape`
describing what applying the skill produces. This skill's own shape (flat
numbered `## Rules`, no layer/axis subheadings in the body, but an `axes:`
list in frontmatter) is closer to the #1790 pilot's flat-list skills than
to `performance-engineering-operational-playbook`'s layered body, so the
per-rule-citing Procedure-step pattern from the pilot applies directly
rather than the axis-grouped one-step-per-axis pattern.

## Checker behavior

canonical: scripts/check_skill_conformance.py (read in
/tmp/skill-repository at commit 589c55e5835735e017743cf399b3288c6726e1d)
— `PROCEDURE_HEADINGS = ("## Trigger", "## Procedure", "## Output
shape")`; `--manifest <path>` is additive/opt-in, checking only skills
listed in the given manifest file. Executed live, pre-change:

```
$ cd /tmp/skill-repository && python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo "exit: $?"
exit: 0
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo "exit: $?"
exit: 0
```
canonical: python3 scripts/check_skill_conformance.py [--manifest
scripts/procedure_authored_skills.txt] (both run in /tmp/skill-repository
at commit 589c55e5835735e017743cf399b3288c6726e1d, pre-change baseline —
`pr-communications-message-planning-and-evaluation-rules` is unlisted so
neither run currently checks its Trigger/Procedure/Output-shape
presence).

## Rule-retention baseline (pre-change)

derived: `grep -nE "^[0-9]+\." skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md`
executed live in /tmp/skill-repository at commit
589c55e5835735e017743cf399b3288c6726e1d:

```
29:1. When the audience for a message is not yet named, choose the
38:2. When more than one audience segment exists for the same activity
46:3. **REMOVAL**: when a communications plan lists more than one core
55:4. When a key message has no proof point attached, either attach a
63:5. When choosing which of ethos, pathos, or logos to lead with, match it
73:6. When a message states a change as a gain-or-loss trade-off (e.g. a
83:7. When a communications activity touches a live incident or negative
91:8. When a Q&A entry has a drafted answer, route it through an explicit
100:9. When more than one spokesperson may face the same question, use one
108:10. **REMOVAL**: when a risk/Q&A document accumulates answers for
117:11. When defining success criteria for a communications activity,
126:12. When an outcome claim ("this changed perception/behavior") has no
136:13. **REMOVAL**: when a supporting message restates the core message in
```

derived: the count above (13 rule lines) is the pre-change baseline that
phase-2's rule-retention sweep must reproduce in full against the
post-change file before that phase's checks are considered passing.

## Skip-condition check

Neither scout-directive skip condition applies literally (this is not a
pure bugfix and the recipe leaves the exact Trigger/Procedure wording
open), but per contract v3 s19 this is phase 1 (proposal only; no
CORE_BUILD_NOW=1 in the environment) — the actual authoring, the four
live checks, and the `git diff --stat` are phase-2 deliverables that
wait for the approval gate. This survey and its companion proposal are
the full phase-1 output.
