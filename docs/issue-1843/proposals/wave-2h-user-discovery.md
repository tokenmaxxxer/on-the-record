---
status: proposed
files:
  - skill-repository/skills/user-discovery-evidence-strength-tagging/SKILL.md
  - skill-repository/skills/user-discovery-follow-up-ladder-depth/SKILL.md
  - skill-repository/skills/user-discovery-question-design-past-behavior/SKILL.md
  - skill-repository/skills/user-discovery-saturation-stopping-rule/SKILL.md
  - skill-repository/skills/user-discovery-switch-timeline-causal-forces/SKILL.md
  - skill-repository/skills/user-discovery-verdict-prevalence-reporting/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
  - docs/issue-1843/reports/implementation.md
---

# Wave 2h: procedural-body authoring for the user-discovery family

## Request

Apply the procedural-body authoring recipe frozen in
docs/issue-1790/reports/implementation.md ("WAVE RECIPE" section) to the
6 `user-discovery-*` axis skills in `tokenmaxxxer/skill-repository`:
insert `## Trigger` / `## Procedure` / `## Output shape` into each body,
rewrite each `description:` from its authored Trigger section, extend
`scripts/procedure_authored_skills.txt` incrementally, keep every
pre-change rule line, and confirm nothing outside those 6 skills +
manifest is touched. Deliver as a skill-repository PR plus this record.

## Constraints

- Guidance-only content: no checker-logic changes, no hooks, no other
  skill family (issue's own non-goals list).
- Zero rule-line loss: every pre-change numbered rule line (55 total per
  the survey) must still be present, verbatim, post-change.
- Write set bounded to the 6 named skill files plus
  `scripts/procedure_authored_skills.txt` in the skill-repository
  checkout, plus this record in the current repository — nothing else.
- Four checks must be executed live and pasted in the phase-2 record:
  manifest-scoped `check_skill_conformance.py --manifest ...` (exit 0),
  the rule-retention sweep, `git diff --stat` scoped to those paths, and
  a full-tree `check_skill_conformance.py` run with no flag (exit 0).

## Rationale

The survey (docs/issue-1843/reports/implementation/survey.md) found all
6 skills Shape A (no existing Trigger/Procedure/Output-shape section),
structurally identical to the pilot's `upstream-defect-report-*` and
`api-design-*` files and to every family touched in waves 2a-2d. Two
alternatives were considered and rejected:

- **Design a family-specific procedural-body variant** (e.g. an
  interview-methodology-flavored template distinct from the frozen
  recipe) — rejected because the survey found no structural divergence
  from the pilot's files that would justify a different shape; inventing
  a variant here would fork the recipe for no observed reason and break
  the "recipe reuse" premise every wave since #1790 has relied on
  (frozen recipe = one bar all waves are checked against).
- **Include the `user-discovery` overview skill (no suffix) in the write
  set**, treating the family as 7 skills rather than 6 — rejected
  because the issue's own Acceptance criterion names exactly 6 family
  skills (the axis skills), and every prior wave's manifest additions
  only ever added a family's dash-suffixed axis skills, never that
  family's own overview/harness skill; broadening the write set here
  would violate the issue's own scoped-write-set acceptance check
  ("No path outside the 6 family skills + manifest is touched").

The chosen approach — apply the frozen recipe verbatim to exactly the 6
named skills, extend the manifest incrementally — is the only option
consistent with both the survey's shape findings and the issue's stated
scope.

## What will be done

1. For each of the 6 skills, insert `## Trigger` (concrete distinguishing
   conditions for that axis within the user-discovery family),
   `## Procedure` (ordered steps, each citing rule number(s) from that
   file's `## Rules`), and `## Output shape` between the framing
   paragraph and `## Rules`.
2. Rewrite each skill's `description:` as a sentence derived from its own
   new `## Trigger` content, keeping a "use when" trigger-marker
   substring.
3. Append the 6 skill directory names to
   `scripts/procedure_authored_skills.txt`.
4. Run `check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt`, the full-tree run with no
   flag, and the rule-retention grep sweep, all live in the checkout,
   before committing.
5. Commit on a fresh branch off the checkout's default branch, open a
   skill-repository PR, and write
   `docs/issue-1843/reports/implementation.md` here with the four
   pasted check outputs and a scoped `git diff --stat`.

## Out of scope

Any other skill family; changes to `check_skill_conformance.py`'s logic;
hooks; the `user-discovery` overview skill (no suffix).

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 with all 50 manifest entries (44 existing + 6 new) passing.
- The full-tree `check_skill_conformance.py` run (no flag) exits 0.
- The rule-retention sweep shows all 55 pre-change rule lines present
  post-change, per skill.
- `git diff --stat` in the skill-repository checkout lists only the 6
  `SKILL.md` files and `scripts/procedure_authored_skills.txt`.
