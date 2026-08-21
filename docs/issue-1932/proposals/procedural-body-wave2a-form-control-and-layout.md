---
status: proposed
files:
  - skill-repository/skills/interaction-design-form-control-and-layout/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural body for interaction-design-form-control-and-layout

## Request

Issue #1932 asks for the frozen procedural-body recipe (#1790 pilot,
docs/issue-1790/reports/implementation.md WAVE RECIPE section) to be
applied to one additional skill,
`interaction-design-form-control-and-layout`, in the
tokenmaxxxer/skill-repository checkout: author `## Trigger` /
`## Procedure` / `## Output shape` sections, rewrite `description:` from
the authored Trigger, extend `scripts/procedure_authored_skills.txt`
with the skill's directory name, and repeat the pilot's four acceptance
checks (manifest checker, rule-retention sweep, scoped `git diff --stat`,
full-tree checker) against the live checkout. No checker-logic changes,
no other family, no hooks.

## Constraints

- Apply the #1790 recipe verbatim — no deviation in section order,
  naming, or checker invocation (issue #1932 body, "Apply the frozen
  recipe verbatim").
- Zero rule-line loss: all 8 `## R1`-`## R8` rule lines in the current
  skill body (docs/issue-1932/reports/implementation/survey.md, "Target
  skill, current shape") must survive into the authored version,
  verified by the sweep.
- Write set stays exactly the two paths listed in this proposal's
  `files:` — no checker-logic edits, no other skill touched (issue
  #1932 body, "Non-goals").
- `description:` must keep a checker trigger-marker substring ("use
  when"), per the frozen recipe's step 3 (docs/issue-1790/reports/implementation.md,
  WAVE RECIPE authoring-pattern list).

## Rationale

The frozen recipe itself is not up for reconsideration in this wave —
issue #1932 mandates verbatim reuse, and the survey found no shape
already present that would make this a no-op. The one real choice this
wave does carry is where to attach the `## Trigger` /`## Procedure`/
`## Output shape` block:

- **Chosen: insert between the opening framing paragraph and the first
  `## R1` rule heading**, mirroring the #1790 pilot's placement (between
  framing paragraph and `## Rules`). This keeps the block acting purely
  as a navigational layer over the existing rules, consistent across all
  procedure-authored skills in the manifest so a reader scanning any
  authored skill finds Trigger/Procedure/Output-shape in the same
  relative position.
- **Rejected alternative: insert after the `## Rule table` quick-reference
  block, immediately before `## Provenance`.** This skill's structure
  differs slightly from the #1790 pilot skills in having a `## Rule
  table` section the pilot skills lacked; placing Trigger/Procedure/
  Output-shape after it (at the tail of the rules, right before
  Provenance) was considered because it would keep the numbered
  `## R<n>` rules and their quick-reference table adjacent. Rejected
  because it breaks the one placement invariant the #1790 recipe
  established across the manifest (Trigger/Procedure/Output-shape always
  precedes the rule content) — introducing a second placement convention
  this early in the wave would fragment the manifest's skills into two
  incompatible layouts for no benefit the issue asked for, and the
  `## Rule table` block reads fine either immediately after `## R8` or
  after the new sections, since it is a reference index, not part of the
  rule numbering the Procedure steps cite.

## What will be done

1. Read `## R1`-`## R8` in full (already done in the survey) to derive
   Trigger conditions distinguishing this skill from sibling interaction-
   design axes, Procedure steps each citing the rule number(s) they draw
   on, and an Output-shape description of what applying the skill
   produces.
2. Insert `## Trigger` / `## Procedure` / `## Output shape` between the
   `# Playbook: ...` framing paragraph and `## R1`, per the Rationale's
   chosen placement.
3. Rewrite `description:` in the frontmatter as a sentence derived from
   the authored `## Trigger` content, keeping "use when" as the trigger
   marker.
4. Append `interaction-design-form-control-and-layout` to
   `scripts/procedure_authored_skills.txt`.
5. Run, in /tmp/skill-repository:
   - `python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt` (expect exit 0)
   - the rule-retention grep sweep (pre-change `## R<n>` line prefixes
     against the post-change file, all 8 expected retained)
   - `git diff --stat` scoped to the two write-set paths
   - `python3 scripts/check_skill_conformance.py` (full tree, no
     `--manifest`, expect exit 0, 234-skill baseline to compare against)
6. Commit on branch `issue-1932-procedural-body-interaction-design-form-control-and-layout`
   in the skill-repository checkout, open a PR there, and paste all four
   check outputs plus the `git diff --stat` into this issue's phase-2
   record once approved.

## Out of scope

- Any other skill family (issue #1932 Non-goals).
- Any change to `scripts/check_skill_conformance.py`'s logic (issue
  #1932 Non-goals; the checker is invoked, not modified).
- Any hook file (issue #1932 Non-goals).
- Reconciling the stray `issue-1906-wave2a-data-modeling` branch change
  found during the survey (docs/issue-1932/reports/implementation/survey.md,
  "Checkout state at survey time") — that belongs to a different
  session's issue, not this one.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt` exits 0.
- The rule-retention sweep reports 8/8 retained for
  `interaction-design-form-control-and-layout`.
- `git diff --stat` (scoped, in the skill-repository checkout) shows only
  `skills/interaction-design-form-control-and-layout/SKILL.md` and
  `scripts/procedure_authored_skills.txt`.
- `python3 scripts/check_skill_conformance.py` (full tree) exits 0.
