---
status: proposed
files:
  - docs/issue-1853/reports/implementation.md
  - /tmp/skill-repository-1853/skills/ml-engineering-evaluation-discipline/SKILL.md
  - /tmp/skill-repository-1853/skills/ml-engineering-ml-test-score-scoring/SKILL.md
  - /tmp/skill-repository-1853/skills/ml-engineering-model-provenance-versioning/SKILL.md
  - /tmp/skill-repository-1853/skills/ml-engineering-rollout-promotion-rollback/SKILL.md
  - /tmp/skill-repository-1853/skills/ml-engineering-serving-pattern-selection/SKILL.md
  - /tmp/skill-repository-1853/skills/ml-engineering-slo-definition-tradeoffs/SKILL.md
  - /tmp/skill-repository-1853/scripts/procedure_authored_skills.txt
---

## Request

Apply the frozen wave recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 6 `ml-engineering-*` skills in
`tokenmaxxxer/skill-repository`: author `## Trigger` / `## Procedure` /
`## Output shape` in each body, rewrite each `description:` from the
authored Trigger, extend `procedure_authored_skills.txt` with the 6
names, keep every pre-existing content line, and deliver as a
skill-repository PR plus this role's record, scoped to only these 6
skill files + the manifest.

## Constraints

- Zero content loss (issue requirement 1 + record-shape frontmatter's
  `## What did not work` accounting) — every one of the 30 pre-existing
  rule lines (docs/issue-1853/reports/implementation/survey.md,
  "Pre-existing rule content" section) must survive unmodified.
- No path outside the 6 family skills + manifest touched (issue
  requirement 2, `git diff --stat` must prove it).
- No checker-logic changes, no hook changes (issue non-goals).
- Guidance-only: the authored sections steer usage, they do not change
  what each skill's rule/axis content resolves.
- The manifest check requires exactly the 3 headings (`## Trigger`/
  `## Procedure`/`## Output shape`, any order) per
  `check_skill_conformance.py` — nothing else is mechanically enforced
  about a particular pre-existing heading name or the presence of any
  heading at all above the rules content.

## Rationale

The survey (docs/issue-1853/reports/implementation/survey.md) found
this family is uniform **Shape A** (the pilot's own `## Rules`-heading
structure) across all 6 skills, with zero shape variance — no
`-research-log` or `-tool-landscape` outlier the way wave-2e/2f/2g/2h
each had to resolve for their own families. This makes the authoring
decision itself narrow: apply the frozen recipe's step 2 verbatim to
each of the 6 identically-shaped bodies (insert 3 headings between the
"Research trail" paragraph and `## Rules`), with no per-skill structural
branching needed.

Two alternatives were considered and rejected:

1. **Treat this as 6 independent single-skill authoring tasks** (one PR
   or one review pass per skill) rather than one bounded family wave.
   Rejected: the frozen recipe's own wave-partition rationale (issue
   #1790's WAVE RECIPE section) bounds review surface to one role's
   rule set per wave specifically to keep the review surface bounded
   and the diff scoped; splitting into 6 separate deliverables multiplies
   PR/record overhead six-fold for a family whose survey shows zero
   shape variance to justify per-skill handling, and diverges from every
   prior wave (2d through 2h) which each delivered one wave = one PR.

2. **Insert a synthetic differentiator between the 6 near-identical
   Trigger sections** (e.g. force each Trigger to explicitly cross-reference
   all 5 sibling axes by name, beyond what the frozen recipe requires)
   to make the 6 skills more clearly distinguishable from each other.
   Rejected: the frozen recipe's step 2 already requires each Trigger to
   state "concrete conditions distinguishing this skill from its sibling
   axes in the same family," which is sufficient per every prior wave's
   accepted output (e.g. docs/issue-1844's technical-writing family,
   whose 6 accepted Triggers use plain axis-boundary language, not a
   forced cross-reference template); adding a stricter format not in the
   frozen recipe would diverge from the recipe this issue asks to apply
   "verbatim."

## What will be done

1. For each of the 6 `ml-engineering-*` skill bodies, insert `## Trigger`
   (concrete conditions distinguishing the axis from its 5 siblings in
   the family — SLO tradeoffs vs. rollout/promotion vs. serving-pattern
   selection vs. model-provenance/versioning vs. ML-Test-Score scoring
   vs. evaluation discipline), `## Procedure` (ordered steps citing rule
   numbers 1-5 from each skill's own `## Rules`), and `## Output shape`
   between the "Research trail" paragraph and `## Rules`.
2. Rewrite each `description:` frontmatter field as a sentence derived
   from that skill's own authored `## Trigger` content, keeping the
   checker's trigger-marker substring ("use when").
3. Append the 6 skill directory names to
   `scripts/procedure_authored_skills.txt` (append-only, incremental —
   no existing lines removed or reordered).
4. Run, in this order, on the live `/tmp/skill-repository-1853`
   checkout: the rule-retention sweep (compare post-change numbered-rule
   lines against the 30-line pre-change baseline in the survey), the
   manifest-scoped checker (`--manifest
   scripts/procedure_authored_skills.txt`), the full-tree checker (no
   flag), and `git diff --stat` scoped to the 6 skill files + manifest.
5. Paste all four check outputs plus the `git diff --stat` output into
   docs/issue-1853/reports/implementation.md, open the skill-repository
   PR, and land this role's own phase-2 record referencing that PR.

## Out of scope

- Any family other than `ml-engineering-*` (issue non-goal 1).
- Any change to `scripts/check_skill_conformance.py` or its checker
  logic (issue non-goal 2).
- Any hook change (issue non-goal 3).
- Any edit inside `## Rules` content itself (rule wording, sources,
  `**REMOVAL**` tags) beyond what is strictly required to insert the 3
  new headings above it — the recipe is additive, not corrective.

## How you'll know it worked

- All 6 `ml-engineering-*` `SKILL.md` files carry `## Trigger`,
  `## Procedure`, and `## Output shape`, each `description:` rewritten
  from its own Trigger, and the 6 names appended to
  `procedure_authored_skills.txt`.
- The rule-retention sweep shows all 30 pre-change numbered rule lines
  present, unmodified, post-change.
- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0.
- `python3 scripts/check_skill_conformance.py` (full-tree) exits 0.
- `git diff --stat` against the fresh-clone base shows only the 6 skill
  files + `scripts/procedure_authored_skills.txt` changed — no other
  path touched.
