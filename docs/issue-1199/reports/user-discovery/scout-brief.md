---
subject: issue-1199
role: user-discovery
kind: scout-brief
---

# Scout brief: Claude Code plugin ecosystem, user-discovery domain

Mode: 4 parallel WebSearch angles in one turn (by-category, by-framework,
by-marketplace-listing, by-repo-keyword), then one deepening round on the
two decision-relevant hits. 2 stages total, well under the 5-stage/3min
budget.

## Category must-bes (from the field)
- A behavioral-evidence-first interview script that structurally defers
  any product pitch until after behavior questions are exhausted (Mom
  Test framing, present in nearly every surveyed skill).
- A switch-story reconstruction (JTBD four-forces: push/pull/anxiety/
  habit) as the primary discovery instrument, not a features/opinion
  survey.
- A hypothesis-fatality ordering step run BEFORE scripting: identify
  which candidate hypothesis, if false, kills the idea, and interview
  that one first rather than working through hypotheses in arbitrary or
  convenience order.

## Performance axes the field competes on
1. How early pitching is structurally blocked (script-level vs.
   discipline-only).
2. Whether switch stories are decomposed into named forces or left as
   one narrative.
3. Whether hypothesis order across a multi-hypothesis study is
   risk-derived or arbitrary.

## Gap line
canonical: this session's Read of `playbook/question-design-past-behavior.md`
and `playbook/switch-timeline-causal-forces.md` in the mounted rulebook
repo (9 rules each, no rule addressing cross-hypothesis ordering). Axis 1
(pitch-blocking) is well covered by `question-design-past-behavior.md`
rules 3, 7, 9; axis 2 (switch-force decomposition) is well covered by
`switch-timeline-causal-forces.md`'s existing push/pull/anxiety/habit
rules. Axis 3 has no covering rule: no existing rule orders WHICH
hypothesis a multi-hypothesis interview script tests first — all 6 axes
assume a single hypothesis already selected. Candidate to adopt:
fatal-assumption-first hypothesis ordering.

## Adopt / skip
- Candidate for adoption: fatal-assumption-first ordering
  (`guia-matthieu/clawfu-skills` `customer-discovery` skill —
  "hypothesis prioritization matrix... to identify fatal assumptions
  before wasting months building"). Targets the gap above. Maps to
  `question-design-past-behavior.md`.
- Left aside: `wondelai/skills` `jobs-to-be-done`
  functional/emotional/social job taxonomy — overlaps
  `switch-timeline-causal-forces.md`'s existing push/pull/anxiety/habit
  decomposition (already above its rule_count_floor); a second,
  differently-shaped taxonomy on the same axis would add bulk without
  closing an open gap.

## Segment fit
One line: both surveyed skills target the same segment as this role
(pre-build customer-discovery interviewing), not a broader PM-toolkit
segment — direct fit, no translation needed.

Stages used: 2 (sweep + 1 deepening round), parallel mode throughout.

Sources:
- https://claudemarketplaces.com/skills/guia-matthieu/clawfu-skills/customer-discovery
- https://github.com/guia-matthieu/clawfu-skills
- https://github.com/wondelai/skills/blob/main/jobs-to-be-done/SKILL.md
- https://github.com/wondelai/skills
- https://mcpmarket.com/tools/skills/the-mom-test-framework
