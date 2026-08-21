---
status: proposed
files:
  - skill-repository/skills/performance-engineering-operational-playbook/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural body for performance-engineering-operational-playbook

## Request

Author the single skill `performance-engineering-operational-playbook`
in `tokenmaxxxer/skill-repository` per the frozen wave recipe (docs/
issue-1790/reports/implementation.md, WAVE RECIPE section, from the #1790
pilot): insert `## Trigger` / `## Procedure` / `## Output shape` at the
top of the body (Procedure steps citing rule numbers), rewrite
`description:` from the authored Trigger section, extend
`scripts/procedure_authored_skills.txt` incrementally, with zero
pre-existing rule-line loss. Guidance-only wave; no checker-logic or
hook changes.

## Constraints

- Family-bounded: only this one skill's `SKILL.md` plus
  `scripts/procedure_authored_skills.txt` may be touched in the
  skill-repository PR (issue's own non-goals list: no other family, no
  checker-logic changes, no hooks).
- Every one of the 10 pre-existing numbered rule lines under `## Layer
  A/B/C` (survey's Rule-retention baseline) must remain present,
  byte-identical, post-change.
- `description:` must keep a trigger-marker substring the checker relies
  on ("use when"), per the frozen recipe's step 3.
- The four checks from the #1790 pilot record repeat for this wave:
  manifest checker (exit 0), rule-retention sweep (10/10 retained),
  `git diff --stat` scoped to the two files above, full-tree checker
  (exit 0) — all executed live from the skill-repository checkout and
  pasted into the phase-2 record.

## Rationale

Considered authoring a flat `## Rules` restructuring first (collapsing
the existing `Layer A/B/C` grouping into one undifferentiated numbered
list before adding the procedural sections) — rejected because the issue's
non-goals explicitly scope this wave to guidance-only authoring, and
because the survey's Pattern precedent found `content-design-operational-
playbook` (issue #1928) already reused the multi-layer/axis grouping
successfully under the same recipe: Trigger names conditions per axis
with inline rule-range citations, Procedure is one step per axis. Since
this skill's own three research layers (A: practitioner rules 1-7, B:
named methodologies 8-9, C: academic grounding 10) map cleanly onto that
same one-step-per-axis Procedure shape, restructuring the existing layer
grouping would add scope and rule-line churn the recipe does not call
for, purely to force a flat-list shape that a sibling skill already shows
is not required.

Also considered writing the two REMOVAL rules (5, 6) as their own
Procedure step, separate from Layer A's other five rules — rejected
because both REMOVAL rules are connection-pool/N+1-specific sub-cases of
Layer A's practitioner-rules axis, not a distinct trigger condition of
their own; splitting them out would fragment one axis into two Procedure
steps for no condition-level reason, diverging from the recipe's
per-axis granularity without a stated need.

## What will be done

1. Insert `## Trigger` / `## Procedure` / `## Output shape` between the
   existing framing paragraph and `## Layer A — practitioner decision
   rules`, following `content-design-operational-playbook`'s shape:
   - `## Trigger`: name the concrete conditions spanning the skill's
     three layers — diagnosing an unexplained slowdown with no prior
     hypothesis, setting or reporting a latency/SLO/error-budget target,
     assessing queue/pool/connection-pool pressure, or choosing between a
     removal-shaped and addition-shaped fix — each clause citing its
     rule number(s).
   - `## Procedure`: one numbered step per layer/axis (practitioner
     rules 1-7, named methodologies 8-9, academic grounding 10), each
     step citing the rule number(s) it draws on, mirroring the existing
     Layer A/B/C order.
   - `## Output shape`: what applying the skill produces — a cited
     condition→choice→source decision plus, where relevant, which
     REMOVAL-category rule took precedence over an addition-shaped
     alternative.
2. Rewrite `description:` as a single sentence derived from the
   authored Trigger section's opening clause, keeping "use when".
3. Append `performance-engineering-operational-playbook` to
   `scripts/procedure_authored_skills.txt`.
4. Run, live, from `/tmp/skill-repository`: `check_skill_conformance.py
   --manifest scripts/procedure_authored_skills.txt` (expect exit 0);
   the rule-retention grep sweep (expect 10/10 lines retained); `git
   diff --stat` (expect only the two files above); the full-tree
   `check_skill_conformance.py` with no flag (expect exit 0). Paste all
   four outputs into `docs/issue-1937/reports/implementation.md`.
5. Open the skill-repository PR carrying this one skill's diff plus the
   manifest line, referencing issue #1937 (no Closes/Fixes trailer at
   this phase-1 stage).

## Out of scope

- Any other skill family (issue's own non-goals).
- `scripts/check_skill_conformance.py` logic changes (issue's own
  non-goals) — the manifest-gated check added in #1790 is reused as-is.
- Hooks (issue's own non-goals).
- Restructuring the existing `## Layer A/B/C` grouping into a flat
  `## Rules` list (see Rationale) or the Evidence trail table.
- Rewording any existing rule's Condition/Choice/Source text — only new
  sections are inserted and `description:` is rewritten.

## How you'll know it worked

The four executed-live checks from `## What will be done` step 4 all
pass as specified (manifest checker exit 0, 10/10 rules retained, `git
diff --stat` showing only the skill's `SKILL.md` and the manifest file,
full-tree checker exit 0), pasted into the phase-2 record together with
the skill-repository PR link — matching issue #1937's Acceptance
criteria 1 and 2 verbatim.
