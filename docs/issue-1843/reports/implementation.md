---
subject: issue-1843
role: implementation
kind: record
code_under_review:
  - skill-repository/skills/user-discovery-evidence-strength-tagging/SKILL.md
  - skill-repository/skills/user-discovery-follow-up-ladder-depth/SKILL.md
  - skill-repository/skills/user-discovery-question-design-past-behavior/SKILL.md
  - skill-repository/skills/user-discovery-saturation-stopping-rule/SKILL.md
  - skill-repository/skills/user-discovery-switch-timeline-causal-forces/SKILL.md
  - skill-repository/skills/user-discovery-verdict-prevalence-reporting/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# Phase 2 record: wave 2h user-discovery family

## What was done

Applied the frozen procedural-body recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 6 `user-discovery-*` axis skills in
`tokenmaxxxer/skill-repository`, per the approved proposal
(docs/issue-1843/proposals/wave-2h-user-discovery.md):

- Inserted `## Trigger` / `## Procedure` / `## Output shape` between the
  framing paragraph and `## Rules` in each of the 6 skills:
  `user-discovery-evidence-strength-tagging`,
  `user-discovery-follow-up-ladder-depth`,
  `user-discovery-question-design-past-behavior`,
  `user-discovery-saturation-stopping-rule`,
  `user-discovery-switch-timeline-causal-forces`,
  `user-discovery-verdict-prevalence-reporting`.
- Rewrote each `description:` as a sentence derived from that skill's
  new `## Trigger` content.
- Appended the 6 skill directory names to
  `scripts/procedure_authored_skills.txt`.
- Ran all four checks live in the checkout, then committed on branch
  `issue-1843-wave2h-user-discovery` (skill-repository commit `4903310`)
  and opened tokenmaxxxer/skill-repository#15.

Note on manifest baseline: the checked-out `main` had advanced past the
survey's 44-line snapshot (waves 2e/2f/2g had landed in the checkout by
phase-2 time, per `git fetch` output), so the manifest held more entries
pre-change than the survey recorded; this wave's own contribution is
exactly the 6 appended lines shown in check 3 below, matching the
proposal's scope.

## Why

canonical: docs/issue-1843/reports/implementation/survey.md, "Per-skill
frontmatter/body shape (Shape A/B classification)" section

Per the approved proposal: the survey found all 6 skills Shape A
(no existing Trigger/Procedure/Output-shape section), structurally
identical to every family already carried through this recipe since the
#1790 pilot — applying the frozen recipe verbatim, rather than inventing
a family-specific variant, keeps one shape bar across all waves.

## Upstream / basis

- Proposal: docs/issue-1843/proposals/wave-2h-user-discovery.md
- Survey: docs/issue-1843/reports/implementation/survey.md
- Recipe: docs/issue-1790/reports/implementation.md (WAVE RECIPE section)
- Approval: issue #1843 comment, exact string `APPROVE issue-1843/implementation`
- Delivery PR: tokenmaxxxer/skill-repository#15
  (https://github.com/tokenmaxxxer/skill-repository/pull/15), branch
  `issue-1843-wave2h-user-discovery`, commit `4903310`

## Four checks, executed live in the skill-repository checkout (/tmp/skill-repository)

### Check 1: manifest-scoped checker

acceptance: `python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt` — result:

```
234 skills checked
exit: 0
```

### Check 2: rule-retention sweep

acceptance: per-skill diff of `^[0-9]+\.` rule lines, HEAD (pre-change) vs. working tree (post-change), each pre-change line checked present verbatim post-change — result:

```
=== user-discovery-evidence-strength-tagging ===
pre-change rule lines: 9, missing post-change: 0
=== user-discovery-follow-up-ladder-depth ===
pre-change rule lines: 9, missing post-change: 0
=== user-discovery-question-design-past-behavior ===
pre-change rule lines: 10, missing post-change: 0
=== user-discovery-saturation-stopping-rule ===
pre-change rule lines: 9, missing post-change: 0
=== user-discovery-switch-timeline-causal-forces ===
pre-change rule lines: 9, missing post-change: 0
=== user-discovery-verdict-prevalence-reporting ===
pre-change rule lines: 9, missing post-change: 0
```

Total: 55 pre-change rule lines (9+9+10+9+9+9), all 55 present post-change (matches the survey's per-file rule counts).

### Check 3: `git diff --stat`, scoped to the write set

acceptance: `git diff --stat` (pre-commit, in /tmp/skill-repository) — result:

```
 scripts/procedure_authored_skills.txt              |  6 +++
 .../user-discovery-evidence-strength-tagging/SKILL.md | 42 ++++++++++++++++++++-
 .../user-discovery-follow-up-ladder-depth/SKILL.md | 40 +++++++++++++++++++-
 .../user-discovery-question-design-past-behavior/SKILL.md | 42 ++++++++++++++++++++-
 .../user-discovery-saturation-stopping-rule/SKILL.md | 38 ++++++++++++++++++-
 .../user-discovery-switch-timeline-causal-forces/SKILL.md | 42 ++++++++++++++++++++-
 .../user-discovery-verdict-prevalence-reporting/SKILL.md | 44 +++++++++++++++++++++-
 7 files changed, 248 insertions(+), 6 deletions(-)
```

Only the 6 named `SKILL.md` files plus `scripts/procedure_authored_skills.txt` — no other path touched, matching Acceptance criterion 2.

### Check 4: full-tree checker

acceptance: `python3 scripts/check_skill_conformance.py` (no flag, in /tmp/skill-repository) — result:

```
234 skills checked
exit: 0
```

## What did not work

None.

## Open findings

None.
