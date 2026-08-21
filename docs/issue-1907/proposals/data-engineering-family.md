---
status: proposed
files:
  - skill-repository/skills/data-engineering-data-quality/SKILL.md
  - skill-repository/skills/data-engineering-failure-handling/SKILL.md
  - skill-repository/skills/data-engineering-pipeline-design/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural-body wave — data-engineering family (issue #1907)

## Request

Apply the procedural-body wave recipe frozen in
`docs/issue-1790/reports/implementation.md` (`WAVE RECIPE` section) to
the `data-engineering` family's 3 skills in `tokenmaxxxer/skill-repository`:
insert `## Trigger` / `## Procedure` / `## Output shape` at the top of
each body, cite rule numbers in each Procedure step, rewrite each
`description:` from its own Trigger content, and extend
`scripts/procedure_authored_skills.txt` incrementally. Deliver as a
skill-repository PR plus this issue's phase-2 record. No other family,
no checker-logic change, no hooks change.

## Constraints

- Write set limited to the 3 `data-engineering-*` `SKILL.md` files plus
  `scripts/procedure_authored_skills.txt` — no other path in the
  skill-repository checkout, per the issue's requirement 2 and the
  survey's note on the 4 unrelated in-flight `defect-verification-*`
  modifications already present in the checkout (must stay untouched).
- Zero rule-line loss: every pre-change numbered rule line
  (`**addition**`/`**REMOVAL**`) must survive verbatim in the post-change
  file, verified by the same rule-retention grep sweep the pilot and
  every subsequent wave used.
- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  and the same script with no flag (full-tree) must both exit 0 after
  the change.
- Guidance-only: no change to checker logic, no hook change, per the
  issue's stated non-goals.

## Rationale

The frozen recipe (`docs/issue-1790/reports/implementation.md`) is the
established basis for every wave 2a family delivered so far (marketing,
brand-design, localization, capacity-planning, knowledge-management, and
others visible in `scripts/procedure_authored_skills.txt`'s existing
164+ entries). The alternative considered was designing a
data-engineering-specific authoring template — e.g. a heavier structure
that also cross-references the family's 3 sibling axes explicitly in
every Trigger section, since data-quality, failure-handling, and
pipeline-design rules already cross-reference each other inline (e.g.
`failure-handling` item 9 references the `pipeline-design` axis by
name). This was rejected: the survey found no frontmatter or structural
difference between these 3 skills and the pilot's `api-design-*` skills
(same bare-numbered-rules-list shape, same `description:` template), so
a bespoke template would diverge from the recipe with no discovered
justification, breaking the "recipe reuse" premise the wave's own design
basis (`design-research` field in issue #1907) rests on — cross-axis
references are already handled at the rule-text level (e.g. failure-
handling item 9's own inline note) and don't require a structural
deviation.

## What will be done

1. For each of the 3 skills, insert `## Trigger` (concrete conditions
   distinguishing this axis from its 2 siblings in the family — not a
   restatement of the title), `## Procedure` (ordered steps, each citing
   the rule number(s) it draws from — the 13/13/15 rule lines the survey
   inventoried per skill), and `## Output shape` between the framing
   paragraph and the numbered rules list.
2. Rewrite each `description:` as a sentence derived from that skill's
   own `## Trigger` content, keeping a "use when" trigger-marker
   substring for the checker.
3. Append `data-engineering-data-quality`, `data-engineering-failure-
   handling`, and `data-engineering-pipeline-design` to
   `scripts/procedure_authored_skills.txt`.
4. Run, in `/tmp/skill-repository`: the manifest checker
   (`--manifest scripts/procedure_authored_skills.txt`), the
   rule-retention grep sweep (pre-change rule-line substrings against
   post-change files), `git diff --stat` scoped to the 4 changed paths,
   and the full-tree checker with no flag — paste all 4 outputs, executed
   live, into `docs/issue-1907/reports/implementation.md`.
5. Open the skill-repository PR carrying the 4 changed paths; commit
   this issue's phase-2 record referencing that PR.

## Out of scope

- Any family other than `data-engineering`.
- Any change to `scripts/check_skill_conformance.py` or checker logic.
- Any hook change.
- The 4 unrelated in-flight `defect-verification-*` modifications
  already present (uncommitted) in the `/tmp/skill-repository` checkout.

## How you'll know it worked

- The manifest checker and full-tree checker both exit 0, pasted live.
- The rule-retention sweep shows every pre-change rule line (13 + 13 +
  15 across the 3 skills, per the survey's inventory) present post-change.
- `git diff --stat` shows only the 3 `SKILL.md` paths plus
  `scripts/procedure_authored_skills.txt` changed.
- All 3 names appear in `scripts/procedure_authored_skills.txt` post-change.
