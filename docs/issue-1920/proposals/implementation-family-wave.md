---
status: proposed
files:
  - skill-repository/skills/implementation-complexity-coupling-management/SKILL.md
  - skill-repository/skills/implementation-design-pattern-selection/SKILL.md
  - skill-repository/skills/implementation-performance-data-structure-choice/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural-body wave — implementation role family (3 skills)

## Request

Apply the procedural-body authoring recipe frozen in the #1790 pilot
(`docs/issue-1790/reports/implementation.md`, WAVE RECIPE section)
verbatim to the 3 role-migrated `implementation-*` skills in
`tokenmaxxxer/skill-repository`:
`implementation-complexity-coupling-management`,
`implementation-design-pattern-selection`,
`implementation-performance-data-structure-choice`. (The other two
`implementation-*` directories in the tree, `implementation-audit` and
`implementation-blueprint`, are personal-workflow skills outside this
role-source-allowlist mapping and are out of scope.) For each: insert
`## Trigger`/`## Procedure`/`## Output shape`, rewrite `description:` from
the authored Trigger, and append the skill name to
`scripts/procedure_authored_skills.txt`. Deliver as a skill-repository PR
plus this record's phase-2 report, repeating the pilot's four checks.

## Constraints

- Zero rule-line loss: every pre-change numbered rule line under each
  skill's `## Rules` (21 total: 9 + 6 + 6, per the survey) must be
  present, unmodified in substance, after authoring.
- Guidance-only: no change to `## Rules` content, `## Counter-example
  tests`, or any semantics beyond adding the 3 new headings and rewriting
  `description:`.
- Write set frozen to the 3 skill `SKILL.md` files plus
  `scripts/procedure_authored_skills.txt` — no checker-logic change
  (`scripts/check_skill_conformance.py` is explicitly out of scope per the
  issue's non-goals, unlike the pilot which had to extend it once).
- `procedure_authored_skills.txt` is extended incrementally (append, not
  replace) — the file already carries ~172 entries from the pilot and
  prior wave-2a families.

## Rationale

**Chosen: reuse the frozen recipe verbatim.** **Rejected alternative:
redesign the section shape for this family** — considered and rejected
because the issue explicitly instructs verbatim reuse, and the survey
found no family-specific reason to deviate: like the pilot's api-design
and upstream-defect-report skills, all 3 implementation skills already
have a single flat `## Rules` list with numbered, REMOVAL-tagged entries —
the shape the recipe's Procedure-step rule-citation convention was
designed around. A bespoke section shape for this family would break the
cross-family consistency the recipe exists to produce, for no offsetting
benefit — this family does not raise a new structural case (e.g. no
sub-headings under `## Rules`, no rule ranges) that the pilot's convention
doesn't already handle.

**Chosen: author all 3 skills as live edits.** **Rejected alternative:
treat one or more as no-op** — considered and rejected because the survey
(per recipe step 1) confirmed none of the 3 skills carries
`## Trigger`/`## Procedure`/`## Output shape` already; a no-op record for
any of the 3 would misrepresent the pre-change state, so all 3 require
authoring.

**Chosen: reuse the pilot's already-landed `--manifest` checker flag
as-is.** **Rejected alternative: extend `check_skill_conformance.py`
further for this family, as the pilot did** — considered and rejected
because the pilot only had to add the `--manifest` flag once, to make it
exist at all; this wave's 3 skills fit that existing flag's contract with
no gap to close, and re-touching checker logic here would violate the
issue's own non-goal ("checker logic changes") for no requirement that
calls for it.

## What will be done

1. On a fresh `skill-repository` checkout (isolated from any other
   in-flight branch's working tree), create branch
   `issue-1920-wave2a-implementation-family` off `origin/main`.
2. For each of the 3 skills, insert `## Trigger` (concrete conditions
   distinguishing this skill from its implementation-family siblings —
   not a restatement of the title), `## Procedure` (ordered steps, each
   citing the rule number(s) it draws from that skill's own `## Rules`),
   and `## Output shape` (what applying the skill produces) between the
   framing paragraph and `## Rules`.
3. Rewrite each skill's `description:` frontmatter field as a sentence
   derived from its own newly authored `## Trigger` content, retaining
   the checker's "use when" trigger-marker substring.
4. Append the 3 skill directory names to
   `scripts/procedure_authored_skills.txt` (append only).
5. Run, in this order, before committing: the rule-retention grep sweep
   (compare pre-change `git show origin/main:<path>` rule lines against
   post-change file, per skill); `check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt`; `check_skill_conformance.py`
   with no flag (full tree); `git diff --stat` scoped to the 4 changed
   paths.
6. Commit with a message citing issue-1920, push the branch, open a PR
   against `tokenmaxxxer/skill-repository` main.
7. Paste all four check outputs plus the `git diff --stat` output into
   this record's phase-2 report (`docs/issue-1920/reports/implementation.md`),
   which is written only after approval, per contract v3 s19.

## Out of scope

- `implementation-audit` and `implementation-blueprint` (personal
  skills, not part of this role's allowlist mapping).
- Any other role family (technical-feasibility, release-engineering,
  product-discovery, etc. — future waves per the pilot's proposed
  partition).
- Any change to `scripts/check_skill_conformance.py` or any hook.
- Any change to `## Rules` or `## Counter-example tests` content beyond
  what authoring the 3 new headings requires (i.e. no rewording of
  existing rule text).

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 post-change.
- `check_skill_conformance.py` (full tree, no flag) exits 0 post-change.
- The rule-retention sweep shows all 21 pre-change rule lines (9 + 6 + 6)
  present post-change, one skill at a time.
- `git diff --stat` against `origin/main` shows only the 3 `SKILL.md`
  paths plus `scripts/procedure_authored_skills.txt` — no other file
  touched.
