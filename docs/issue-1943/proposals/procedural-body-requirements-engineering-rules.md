---
status: proposed
files:
  - skill-repository/skills/requirements-engineering-rules/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural body for requirements-engineering-rules

## Request

Author the single skill `requirements-engineering-rules` in
`tokenmaxxxer/skill-repository` per the frozen wave recipe (docs/
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
- Every one of the 27 pre-existing numbered rule lines (1-27, including
  sub-rules 11a/11b) under Axes 1-7 (survey's Body-shape section) must
  remain present, byte-identical, post-change.
- `description:` must keep a trigger-marker substring the checker relies
  on ("use when"), per the frozen recipe's step 3.
- The four checks from the #1790 pilot record repeat for this wave:
  manifest checker (exit 0), rule-retention sweep (27/27 retained),
  `git diff --stat` scoped to the two files above, full-tree checker
  (exit 0) — all executed live from the skill-repository checkout and
  pasted into the phase-2 record.

## Rationale

Considered flattening the existing 7-axis grouping into one
undifferentiated numbered `## Rules` list before adding the procedural
sections — rejected because the issue's non-goals scope this wave to
guidance-only authoring, and because the survey's Pattern-precedent
finding shows both prior single-skill waves
(`performance-engineering-operational-playbook`, #1937;
`issue-retrospective-timeline-comprehensibility-and-subtraction-rules`,
#1934) kept their existing multi-axis/layer grouping and mapped it
one-step-per-axis in `## Procedure` rather than flattening first. This
skill's 7 axes are already a clean group boundary (EARS-pattern
selection, Verification-method selection, Ambiguity detection &
resolution, Singularity/atomicity, Traceability-link granularity,
Prioritization, REMOVAL), so flattening would add scope and rule-line
churn the recipe does not call for, purely to force a shape two sibling
skills already show is unnecessary.

Also considered a scout sweep of external requirements-engineering
prior art before drafting Trigger wording — rejected (and recorded as a
skip in the survey) because the frozen recipe from #1790 is itself the
scoped prior art for this wave: the issue explicitly instructs "apply
the frozen recipe verbatim," and the recipe was already scouted once
(sourced from ISO/IEC/IEEE 29148, EARS, INCOSE, and other requirements-
engineering literature already cited per-rule in the skill's own `##
Rules` body) — re-scouting the same field for a fourth application of
an already-frozen recipe would not change any Trigger-wording decision
this wave needs to make.

## What will be done

1. Insert `## Trigger` / `## Procedure` / `## Output shape` between the
   existing framing paragraph and `## Axis 1 — EARS-pattern selection`:
   - `## Trigger`: name the concrete conditions spanning the skill's 7
     axes — selecting an EARS sentence template while drafting a
     requirement, assigning a requirement's verification method,
     spotting a weak/ambiguous word or double reading, spotting a
     conjunction or mixed-verification-method requirement, deciding
     traceability-link granularity, breaking a MoSCoW-tier tie, or
     reviewing a spec for gold-plating/redundancy/staleness — each
     clause citing its axis's rule number range.
   - `## Procedure`: one numbered step per axis (Axis 1 rules 1-6, Axis
     2 rules 7-11b, Axis 3 rules 12-15, Axis 4 rules 16-17, Axis 5 rules
     18-20, Axis 6 rules 21-22, Axis 7 rules 23-27), each step citing
     the rule number(s) it draws on, mirroring the existing Axis 1-7
     order.
   - `## Output shape`: what applying the skill produces — a cited
     condition→choice→source decision per requirement-engineering
     judgment point (EARS template, verification method, ambiguity
     resolution, singularity split, traceability granularity, MoSCoW+
     Kano tie-break, or removal/merge/archive action), each traceable
     to its rule number.
2. Rewrite `description:` as a sentence derived from the `## Trigger`
   content, keeping the "use when" trigger-marker substring the checker
   relies on.
3. Append `requirements-engineering-rules` to
   `scripts/procedure_authored_skills.txt`, after the existing 196
   lines, incrementally (no reordering of prior entries).
4. Run `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` and the full-tree run with no
   flag; run the rule-retention grep sweep (27 pre-change rule-line
   substrings against the post-change file) before committing.
5. Commit on a new branch (`issue-1943-requirements-engineering-
   procedural-body` or similar) in the skill-repository checkout, open a
   PR against `tokenmaxxxer/skill-repository` `main`, and paste all four
   check outputs plus `git diff --stat` into
   `docs/issue-1943/reports/implementation.md` in this repository (phase
   2, after approval).

## Out of scope

- Any family other than `requirements-engineering-rules` (issue's own
  non-goal).
- Any change to `scripts/check_skill_conformance.py`'s checker logic —
  the existing `--manifest` opt-in check already covers this skill once
  listed (survey's Checker-script section).
- Any hook change.
- Restructuring or renumbering the existing 27 rules, or altering their
  wording/sources.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 in the skill-repository
  checkout, post-change.
- `python3 scripts/check_skill_conformance.py` (full tree, no
  `--manifest`) exits 0, post-change.
- The rule-retention sweep shows 27/27 pre-change rule-line substrings
  present in the post-change `SKILL.md`.
- `git diff --stat` (staged, in the skill-repository checkout) shows
  only `skills/requirements-engineering-rules/SKILL.md` and
  `scripts/procedure_authored_skills.txt` changed.
- All four outputs above are pasted verbatim into
  `docs/issue-1943/reports/implementation.md` per this issue's Acceptance
  criteria.
