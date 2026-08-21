---
status: proposed
files:
  - docs/issue-1847/reports/implementation.md
  - /tmp/skill-repository-1847/skills/pricing-design-rigor/SKILL.md
  - /tmp/skill-repository-1847/skills/pricing-method-family/SKILL.md
  - /tmp/skill-repository-1847/skills/pricing-research/SKILL.md
  - /tmp/skill-repository-1847/skills/pricing-scope-gate/SKILL.md
  - /tmp/skill-repository-1847/skills/pricing-tier-structure/SKILL.md
  - /tmp/skill-repository-1847/skills/pricing-verdict-report/SKILL.md
  - /tmp/skill-repository-1847/scripts/procedure_authored_skills.txt
---

## Request

Apply the frozen wave recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 6 `pricing-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger` / `## Procedure` /
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt` with the 6
names, keep every pre-existing content line, and deliver as a
skill-repository PR plus this role's record, scoped to only these 6
skill files + the manifest.

## Constraints

- Zero content loss (issue requirement 1 + record-shape frontmatter's
  `## What did not work` accounting).
- No path outside the 6 family skills + manifest touched (issue
  requirement 2, `git diff --stat` must prove it).
- No checker-logic changes, no hook changes (issue non-goals).
- Guidance-only: the authored sections steer usage, they do not change
  what each skill's rule/procedure content resolves.
- The manifest check requires exactly the 3 heading strings (`##
  Trigger`/`## Procedure`/`## Output shape`, any order) per
  `check_skill_conformance.py` — nothing else is mechanically enforced
  about a heading's internal content, so `pricing-research`'s
  pre-existing `## Procedure` heading already satisfies that one clause
  and is not to be duplicated or rewritten.

## Rationale

The survey (docs/issue-1847/reports/implementation/survey.md) found this
family splits into two shapes, not the usual Shape A / Shape B pair:
5 of 6 skills (`design-rigor`, `method-family`, `scope-gate`,
`tier-structure`, `verdict-report`) are Shape A — the pilot's structure,
`rule_count_floor:` in frontmatter and a `## Decision rules` block to
cite by number. The 6th, `pricing-research`, is a new Shape C: a
fully-authored, free-standing skill (273 lines, its own multi-step
Van Westendorp/CBC routing method) that already carries a literal `##
Procedure` heading from its own prior authoring, unrelated in content to
the wave recipe's rule-citing procedure, and is missing only `##
Trigger` and `## Output shape`.

Two alternatives were considered and rejected:

1. **Replace `pricing-research`'s existing `## Procedure` section with a
   new rule-citing procedure matching the recipe's usual shape, to make
   all 6 skills structurally uniform.** Rejected: `pricing-research`'s
   existing Procedure is the skill's actual content — a 6-step method
   gate with its own citations and evidence-grade discipline — not a
   stand-in that needs replacing. Overwriting it would violate both the
   zero-content-loss constraint and the "guidance-only" instruction; the
   checker only requires the heading string to be present once, and it
   already is, so replacing it buys no conformance benefit and destroys
   real content.
2. **Treat `pricing-research` as a full no-op / empty-state skip since
   it is "already procedure-shaped," and add no headings to it at
   all.** Rejected: the file is only partially conformant — it has
   `## Procedure` but not `## Trigger` or `## Output shape`; running
   `check_skill_conformance.py --manifest` against it today would still
   report the 2 missing headings. A full skip would leave the manifest
   check failing for this skill, contradicting Requirement 1 ("All 6
   pricing-* skills... authored per the frozen recipe") and Acceptance
   item 1's exit-0 requirement.

Chosen instead: apply the recipe's headings, description rewrite, and
manifest entry uniformly across all 6, but for `pricing-research`
insert only the 2 missing headings (`## Trigger`, `## Output shape`)
around its existing, untouched `## Procedure` section — a partial
insertion rather than the full 3-heading insertion the other 5 skills
get — following the same "cite rather than invent" discipline wave-2e
and wave-2g applied to their own Shape B skills, adapted to a case where
one heading is already present instead of none.

## What will be done

1. For the 5 Shape-A skills, insert `## Trigger` / `## Procedure` / `##
   Output shape` between the framing paragraph and the existing `##
   Decision rules` heading:
   - `## Trigger`: concrete conditions distinguishing the skill from its
     sibling axes in the family (not a title restatement) — derived from
     each skill's current `description:` and framing text.
   - `## Procedure`: ordered steps citing rule numbers from `##
     Decision rules`.
   - `## Output shape`: what the skill produces, derived from each
     skill's existing rule content.
2. For `pricing-research` (Shape C), insert only `## Trigger` (derived
   from its existing block-scalar `description:`, which already states a
   full "Use whenever... Do NOT use for..." trigger clause) and `##
   Output shape` (derived from its existing `## Report format` section)
   around its untouched, pre-existing `## Procedure` section — no new
   `## Procedure` heading and no edits to the existing one.
3. Rewrite each `description:` as a sentence derived from that skill's
   authored `## Trigger`, keeping the checker's trigger-marker substring
   ("use when" / "use whenever" per `TRIGGER_MARKERS`); for
   `pricing-research`, tighten the existing description around the newly
   authored Trigger rather than discarding its existing "Do NOT use
   for..." routing clause.
4. Append all 6 directory names to `procedure_authored_skills.txt`,
   after the existing 66 entries (incremental, not a replacement).
5. Run, from the skill-repository checkout, in this order: (a) `python3
   scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention sweep — diff pre- and post-change content per skill and
   confirm every pre-existing rule/content line from the survey's
   baseline (22 rule lines across the 5 Shape-A skills, plus
   `pricing-research`'s 273 pre-existing lines including its untouched
   `## Procedure` section) is still present, (c) `git diff --stat`
   scoped to the 6 skill paths + manifest (expect no other paths), (d)
   `python3 scripts/check_skill_conformance.py` with no flag (full-tree,
   expect exit 0).
6. Paste all four check outputs plus the `git diff --stat` into
   `docs/issue-1847/reports/implementation.md` (phase 2, after approval),
   matching the pilot record's structure.

## Out of scope

- Any skill outside the 6 `pricing-*` family.
- Checker logic changes (`check_skill_conformance.py`) or hook changes.
- Restructuring existing rule/procedure content beyond inserting the
  mandated headings — no rewrite of `pricing-research`'s existing `##
  Procedure` section, no `## Decision rules` block invented anywhere it
  doesn't already exist.
- Reconciling the issue body's stale "10 skills" Program-context text —
  noted in the survey, not corrected in the issue itself (this role does
  not edit issues).
- The unrelated wave-2d (`observability-*`) checkout state present at
  `/tmp/skill-repository` — this wave works from its own fresh clone at
  `/tmp/skill-repository-1847` and does not touch that other checkout.

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 with all 6 new names included and passing (including
  `pricing-research` now carrying all 3 headings).
- The rule-retention sweep shows zero lost lines against the survey's
  pre-change baseline (22 rule lines across the 5 Shape-A skills, plus
  `pricing-research`'s 273 pre-existing lines, its `## Procedure` section
  byte-for-byte unchanged).
- `check_skill_conformance.py` (full-tree, no flag) exits 0.
- `git diff --stat` lists only the 6 SKILL.md paths + the manifest file.
- All four outputs and the diff --stat are pasted live into
  docs/issue-1847/reports/implementation.md per the issue's acceptance
  checks.
