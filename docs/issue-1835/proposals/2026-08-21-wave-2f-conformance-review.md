---
status: proposed
files:
  - docs/issue-1835/reports/implementation.md
  - /tmp/skill-repository-1835/skills/conformance-review-finding-record/SKILL.md
  - /tmp/skill-repository-1835/skills/conformance-review-requirement-extraction/SKILL.md
  - /tmp/skill-repository-1835/skills/conformance-review-sampling-derivation/SKILL.md
  - /tmp/skill-repository-1835/skills/conformance-review-severity-classification/SKILL.md
  - /tmp/skill-repository-1835/skills/conformance-review-traceability-and-evidence/SKILL.md
  - /tmp/skill-repository-1835/skills/conformance-review-verdict-assignment/SKILL.md
  - /tmp/skill-repository-1835/skills/conformance-review-verification-method-selection/SKILL.md
  - /tmp/skill-repository-1835/scripts/procedure_authored_skills.txt
---

## Request

Apply the frozen wave recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 7 `conformance-review-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger` / `## Procedure` /
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt` with the 7
names, keep every pre-existing content line, and deliver as a
skill-repository PR plus this role's record, scoped to only these 7
skill files + the manifest.

## Constraints

- Zero rule-line/content loss (issue requirement 1 + record-shape
  frontmatter's `## What did not work` accounting).
- No path outside the 7 family skills + manifest touched (issue
  requirement 2, `git diff --stat` must prove it).
- No checker-logic changes, no hook changes (issue non-goals).
- Guidance-only: the authored sections steer usage, they do not change
  what each skill's Rules/narrative content resolves.
- The manifest check requires exactly the 3 headings
  (`## Trigger`/`## Procedure`/`## Output shape`, any order) per
  `check_skill_conformance.py` — nothing else is mechanically enforced
  about Procedure's internal citation style.

## Rationale

The survey (docs/issue-1835/reports/implementation/survey.md) found this
family has a Shape A/B split like wave-2a/2b/2c, not the single-shape
case wave-2d turned out to be: 5 of the 7 skills
(`requirement-extraction`, `sampling-derivation`,
`traceability-and-evidence`, `verdict-assignment`,
`verification-method-selection`) carry `rule_count_floor:` frontmatter
and a numbered `## Rules` block (Shape A); the other 2
(`finding-record`, `severity-classification`) are narrative
role-state-machine skills with no numbered rules to cite (Shape B).

Two alternatives were considered and rejected:

1. **Cite the 2 Shape-B skills' own numbered-rule-style Procedure
   language anyway, forcing artificial rule numbers onto their
   Refusal/checklist content to match the Shape-A citation style.**
   Rejected: `finding-record` and `severity-classification` have no
   `## Rules` block at all — there is nothing numbered to cite, and
   inventing numbering not present in the source content would
   misrepresent structure the survey found does not exist, and would
   diverge from the citation convention wave-2b already established for
   this exact shape (`release-engineering-postmortem`, which cites named
   section headings instead).
2. **Treat the Program-context paragraph's stated count of "10 skills"
   as authoritative and look for 3 more `conformance-review-*` skills
   beyond the 7 the checkout has.** Rejected: the survey found the live
   checkout has exactly 7 `conformance-review-*` directories, matching
   both the issue title ("7 skills") and Requirement 1 ("All 7
   conformance-review-* skills"); the Program-context "10" is the same
   class of stale-text artifact wave-2c and wave-2d each found in their
   own issue bodies, and inventing work items to reach a number found
   nowhere in the checkout, the title, or the acceptance-relevant
   Requirement text would be scope invention, not scope-following.

Chosen instead: apply the frozen recipe to all 7 skills, branching only
on citation target per the shape already found — rule numbers from
`## Rules` for the 5 Shape-A skills, named section headings (in
parentheses, per the wave-2b `release-engineering-postmortem` precedent)
for the 2 Shape-B skills — with no new citation convention invented for
either shape.

## What will be done

1. For each of the 7 skills, insert `## Trigger` / `## Procedure` /
   `## Output shape` between the framing paragraph and the skill's
   existing first substantive heading (`## Rules` for the 5 Shape-A
   skills; `## What it asks the user for` for the 2 Shape-B skills).
   - `## Trigger`: concrete conditions distinguishing the skill from its
     sibling axes/states in the family — not a title restatement —
     derived from each skill's current `description:` and framing text.
   - `## Procedure`: ordered steps citing rule numbers from `## Rules`
     for the 5 Shape-A skills, or citing named section headings in
     parentheses for the 2 Shape-B skills, per the wave-2b precedent.
   - `## Output shape`: what the skill produces, derived from each
     skill's existing content (e.g. `review-record.md` requirement
     blocks for `finding-record`, a severity band attached to an
     existing finding for `severity-classification`).
2. Rewrite each `description:` as a sentence derived from that skill's
   authored `## Trigger`, keeping the checker's trigger-marker substring
   ("use when").
3. Append all 7 directory names to `procedure_authored_skills.txt`, after
   the existing 39 entries (incremental, not a replacement).
4. Run, from the skill-repository checkout, in this order: (a) `python3
   scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention sweep — diff pre- and post-change content per skill and
   confirm every pre-existing rule/content line from the survey's
   baseline (27 rule lines across the 5 Shape-A skills, plus every
   pre-existing line in the 2 Shape-B skills' 164- and 80-line bodies) is
   still present, (c) `git diff --stat` scoped to the 7 skill paths +
   manifest (expect no other paths), (d) `python3
   scripts/check_skill_conformance.py` with no flag (full-tree, expect
   exit 0).
5. Paste all four check outputs plus the `git diff --stat` into
   `docs/issue-1835/reports/implementation.md` (phase 2, after approval),
   matching the pilot record's structure.

## Out of scope

- Any skill outside the 7 `conformance-review-*` family.
- Checker logic changes (`check_skill_conformance.py`) or hook changes.
- Reconciling the issue body's stale "10 skills" Program-context text —
  noted in the survey, not corrected in the issue itself (this role does
  not edit issues).
- Restructuring existing `## Rules`/narrative content beyond inserting
  the 3 mandated headings.
- Touching the concurrent, uncommitted wave-2d observability changes on
  the separate `/tmp/skill-repository` checkout — this wave works from
  its own fresh clone.

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 with all 7 new names included and passing.
- The rule-retention sweep shows zero lost lines against the survey's
  pre-change baseline (27 rule lines across the 5 Shape-A skills, plus
  full content retention for the 2 Shape-B skills).
- `check_skill_conformance.py` (full-tree, no flag) exits 0.
- `git diff --stat` lists only the 7 SKILL.md paths + the manifest file.
- All four outputs and the diff --stat are pasted live into
  docs/issue-1835/reports/implementation.md per the issue's acceptance
  checks.
