---
subject: issue-1945
role: implementation
kind: survey
loop_state: scope-undeclared
---

# Current-state survey: security-threat-model-threat-modeling-decision-rules

## Scope

skill-repository checkout at `/tmp/skill-repository` (branch `main`,
HEAD `589c55e`, clean working tree — canonical: `git -C /tmp/skill-repository
log --oneline -1` and `git -C /tmp/skill-repository status`, both read live
this session). Target: the single skill named in the issue,
`skills/security-threat-model-threat-modeling-decision-rules/SKILL.md`.

## Skip condition

None applies. This is design work, not a pure bugfix, and the issue leaves
one decision open (how to word `## Trigger` so it distinguishes this skill
from sibling axes, per the frozen recipe's own instruction) — scouting
would normally run, but the frozen WAVE RECIPE (docs/issue-1790/reports/implementation.md,
"WAVE RECIPE" section) is itself the output of a prior scouted pilot
(#1790) that this wave is instructed to reuse verbatim, not re-derive. This
survey therefore treats the recipe as the design-research input in place of
a fresh scout sweep — see the issue's `design-research:` trailer, which
names that same section as basis.

## Frontmatter shape (pre-change)

canonical: `skill-repository/skills/security-threat-model-threat-modeling-decision-rules/SKILL.md`
(read live this session, full contents quoted below).

```
---
name: security-threat-model-threat-modeling-decision-rules
description: Use when you need guidance on Operational playbook: trust-boundary threat modeling decision rules (issue-1174).
rule_count_floor: 12
tier: moderate
axes:
  - trust-boundary-scoping
  - asset-sensitivity-classification
  - stride-enumeration-by-element
  - cvss-risk-rating
  - mitigation-disposition
  - residual-risk-signoff
---
```

The body opens with a framing paragraph ("Numbered condition → choice →
source rules for the `security-threat-model` role...") immediately followed
by `## 1. Trust boundary scoping (axis: trust-boundary-scoping)` — no
`## Trigger`, `## Procedure`, or `## Output shape` heading is anywhere
in the file.

acceptance: grep -n '^## Trigger\|^## Procedure\|^## Output shape' skills/security-threat-model-threat-modeling-decision-rules/SKILL.md — result: no output (zero matches), run live this session in /tmp/skill-repository.

Per WAVE RECIPE step 1, this is therefore a live-edit case, not a no-op.

## Rule inventory (pre-change, for the phase-2 retention sweep baseline)

acceptance: grep -c '^\*\*Rule ' skills/security-threat-model-threat-modeling-decision-rules/SKILL.md — result: 24, run live this session in /tmp/skill-repository.

24 rule-heading lines span 6 axes: trust-boundary-scoping 1.1-1.4;
asset-sensitivity-classification 2.1-2.3; stride-enumeration-by-element
3.1-3.5 plus one `**Rule 5.6` block physically located mid-axis-3 (see
note below); cvss-risk-rating 4.1-4.5; mitigation-disposition 5.1-5.5;
residual-risk-signoff 6.1-6.3. Each rule line is the retention-sweep
baseline for phase 2's step-5 grep diff against the recipe.

Note: the `**Rule 5.6 —` heading sits inside the `## 3. STRIDE
enumeration...` section (after Rule 3.5, before the `## 4.` heading) — an
existing numbering/placement quirk that predates this wave, out of scope
per the issue's non-goals line ("any other family, checker logic changes,
hooks"). Reorganizing rule placement is not requested and will not be
attempted.

## Manifest state

canonical: `skill-repository/scripts/procedure_authored_skills.txt` (read
live this session).

acceptance: grep -n security-threat-model scripts/procedure_authored_skills.txt — result: no output (zero matches), run live this session in /tmp/skill-repository.

`security-threat-model-threat-modeling-decision-rules` is absent from the
manifest. Per the frozen recipe step 4, phase 2 appends this one line to
the existing manifest, extending it rather than replacing it — the
manifest currently lists the 9 pilot skills plus skills landed by
intervening waves (#1932, #1934, #1937 per this branch's recent commit
history).

## Checker script

canonical: `skill-repository/scripts/check_skill_conformance.py` (read
live this session) — accepts an additive, opt-in `--manifest <path>` flag;
any directory name listed in the manifest must have a body containing
`## Trigger`, `## Procedure`, and `## Output shape` (any order). No
checker logic change is needed or in scope for this wave.

## Recipe fit

The frozen 5-step WAVE RECIPE (docs/issue-1790/reports/implementation.md,
"WAVE RECIPE" section) applies to this single-skill family without
modification: insert the three sections between the framing paragraph and
the existing `## 1.` heading; write `## Trigger` from concrete conditions
that set this skill apart from sibling axes (none exist within this
family — it is a single-skill family per the issue's own framing — so the
Trigger instead sets it apart from adjacent security/risk skills already
in this session's skill listing, such as `stride`, `fmea`,
`risk-management-*`, and
`technical-feasibility-threat-model-disposition`); write `## Procedure`
citing rule numbers per axis (6 axes map to 6 procedure steps); write
`## Output shape` naming the artifact this skill's application yields (a
rated, dispositioned STRIDE table plus residual-risk-notes, per axes 3, 4,
5, 6); rewrite `description:` from the new Trigger wording, keeping a
"use when" marker so the checker's trigger-marker recognizer still
matches it; append the skill's directory name to the manifest.
