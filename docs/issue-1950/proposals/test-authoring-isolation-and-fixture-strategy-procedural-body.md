---
status: proposed
files:
  - skill-repository/skills/test-authoring-isolation-and-fixture-strategy/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

## Request

Author a procedural body for the single skill
`test-authoring-isolation-and-fixture-strategy` in
`tokenmaxxxer/skill-repository`, applying the WAVE RECIPE frozen in the
#1790 pilot record verbatim: insert `## Trigger` / `## Procedure` /
`## Output shape` sections, each Procedure step citing the rule number(s)
it draws on; rewrite `description:` from the authored Trigger section;
append the skill's directory name to `scripts/procedure_authored_skills.txt`;
zero rule-line loss; guidance-only (no checker-logic or hook changes).
Delivered as a skill-repository PR plus this record.

## Constraints

- Apply the #1790 recipe exactly as frozen — no new design decisions on
  section shape, ordering, or checker mechanics.
- Zero rule-line loss: every one of the 21 pre-change numbered rule lines
  (survey.md, "Rule inventory") must be verifiably present post-change.
- Write set limited to the one skill's `SKILL.md` and the manifest file —
  no checker-script changes, no hook changes, no other skill touched
  (issue #1950 non-goal 3).
- Both `check_skill_conformance.py` runs (manifest-scoped and full-tree)
  must exit 0 before landing.

## Rationale

Considered authoring a fresh Trigger/Procedure/Output-shape shape
tailored to this skill's 5-lettered-section (A-E) structure, since it
differs from the pilot's flatter numbered-rule skills. Rejected: the
issue text mandates the frozen recipe "verbatim," and the #1790 record
was itself produced specifically so later waves would not re-litigate
section shape per family — inventing a variant here would break that
reuse contract for no benefit, since the recipe's insertion point (before
the first rule-bearing heading) and step-citation format apply cleanly
regardless of whether rules are grouped under lettered subsections or
listed flat.

Considered treating this as a no-op (skip authoring) on the theory that a
5-section skill might already carry enough navigational structure via its
lettered headings to satisfy the acceptance criterion's empty-state
clause. Rejected after checking: the survey (survey.md, "Frontmatter
shape") confirms no `## Trigger`/`## Procedure`/`## Output shape` heading
exists anywhere in the body — the lettered A-E headings are rule-grouping,
not the procedural-navigation layer the recipe adds. This skill is a live
edit, not a no-op.

## What will be done

1. Read `## A. Fixture construction` through `## E. Test double
   selection` and derive `## Trigger` (concrete conditions for reaching
   for this skill, distinguishing it from adjacent test-authoring
   concerns like coverage or naming), `## Procedure` (ordered steps, each
   citing the rule number(s) it draws from across A-E), and `## Output
   shape` (what applying the skill produces — e.g. a fixture/isolation
   decision keyed to the condition that triggered it).
2. Insert those three sections between the framing paragraph and `## A.
   Fixture construction`, leaving all 5 lettered sections and `##
   Conflicts noted` untouched.
3. Rewrite `description:` in the frontmatter as a sentence derived from
   the new `## Trigger` content, keeping a "use when" trigger-marker
   substring for the checker.
4. Append `test-authoring-isolation-and-fixture-strategy` to
   `scripts/procedure_authored_skills.txt`.
5. Run, in `/tmp/skill-repository`: (a)
   `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`,
   expect exit 0; (b) the rule-retention grep sweep against
   `git show HEAD~1:<path>` (or the pre-change working copy) for all 21
   rule lines; (c) `git diff --stat` scoped to the two write-set paths;
   (d) `check_skill_conformance.py` with no `--manifest` flag (full
   234(+1)-tree), expect exit 0.
6. Commit on a new branch in `/tmp/skill-repository`, open the
   skill-repository PR, and paste all four check outputs plus the
   `git diff --stat` into `docs/issue-1950/reports/implementation.md` in
   phase 2.

## Out of scope

- Any other skill or family (issue non-goal).
- `scripts/check_skill_conformance.py` logic changes (issue non-goal).
- Hooks (issue non-goal).
- Re-deriving or disputing the frozen recipe's shape.

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 in `/tmp/skill-repository` post-change.
- `check_skill_conformance.py` (no flag, full tree) exits 0 post-change.
- The rule-retention sweep shows 21/21 pre-change rule lines present
  post-change.
- `git diff --stat` in the skill-repository checkout shows only
  `skills/test-authoring-isolation-and-fixture-strategy/SKILL.md` and
  `scripts/procedure_authored_skills.txt` changed.
