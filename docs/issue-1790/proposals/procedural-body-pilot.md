---
status: proposed
files:
  - skill-repository/skills/upstream-defect-report-comprehensibility/SKILL.md
  - skill-repository/skills/upstream-defect-report-convention/SKILL.md
  - skill-repository/skills/upstream-defect-report-subtraction/SKILL.md
  - skill-repository/skills/api-design-error-design/SKILL.md
  - skill-repository/skills/api-design-http-semantics/SKILL.md
  - skill-repository/skills/api-design-payload-design/SKILL.md
  - skill-repository/skills/api-design-resource-modeling/SKILL.md
  - skill-repository/skills/api-design-tool-landscape/SKILL.md
  - skill-repository/skills/api-design-versioning-evolution/SKILL.md
  - skill-repository/scripts/check_skill_conformance.py
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Procedural-body authoring: pilot wave

## Request

Fix the second half of the operator finding from #1784: the 9 pilot
skills (upstream-defect-report family x3, api-design family x6) have
playbook-shaped bodies (numbered rule lists with citations) and template
descriptions ("Use when you need guidance on X") that name no concrete
trigger. Author a trigger/procedure/output-shape section at the top of
each body, rewrite each description into a real when-to-use sentence
derived from that trigger section, extend the checker with an opt-in
manifest-gated procedure-section check covering all 9, and record a wave
recipe (pattern + effort + partition) for the ~225 remaining skills.
Frozen constraints from the issue: guidance-only (no hooks), zero rule
loss (every existing rule line preserved, reorganization allowed).

## Constraints

- No rule text may be deleted; the survey confirms none of the 9 bodies
  already contain a procedure section, so all 9 are live edits, not no-ops.
- The checker's existing frontmatter-only checks must keep exiting 0 for
  all 234 skills; a procedure-section check applies only to skills listed
  in a new manifest.
- Descriptions must satisfy the checker's existing trigger-marker test
  (`use when`/`trigger`/etc.) as well as carry real when-to-use content —
  the new check must not be weaker than status quo for the pilot skills.
- No hooks, no enforcement outside the checker script; this is guidance
  authoring, not policy execution (per role-source-allowlist mapping for
  this issue).

## Rationale

Two decisions were open: how to gate the new procedure-section check, and
how to shape the procedure section itself.

**Gating.** Considered making the procedure-section check apply
repo-wide immediately (skip the manifest, require trigger/procedure/output
in every SKILL.md right away). Rejected: 225 skills outside the pilot have
not been authored to this shape yet, so a repo-wide requirement would fail
the checker for the whole tree the moment this PR lands — the opposite of
the issue's explicit pilot-first sequencing ("this issue is the PILOT WAVE
ONLY... the remaining roles batch-migrate in follow-up waves"). A
manifest-gated opt-in check lets the pilot 9 be checked strictly while
leaving the other 225 exactly as conformant as they are today, matching
the issue's requirement 3 verbatim ("non-manifest skills keep passing the
existing checks unchanged").

**Procedure section shape.** Considered generating an abstract
"apply this skill" procedure that doesn't reference the existing rules at
all (a fully separate summary layer). Rejected: the issue requires rules
to be "cited from the steps," and a procedure section with no linkage
back into `## Rules` would leave two disconnected layers — an agent could
follow the procedure and never notice the rules exist, defeating the
"zero content loss" intent (content present in the file but functionally
orphaned). Instead each step in the authored procedure cites the rule
number(s) it draws on, so the procedure is a navigational layer over the
existing rules, not a replacement for them.

## What will be done

1. For each of the 9 pilot `SKILL.md` files, insert a new top-of-body
   section between the frontmatter and the existing `# <Title>` heading
   (or immediately after it, whichever reads better per file):
   - `## Trigger` — concrete conditions under which this skill applies,
     derived from the union of the existing rules' "When" clauses,
     compressed to the situations that actually distinguish this skill
     from its sibling axes in the same family.
   - `## Procedure` — an ordered list of steps the agent executes,
     each step citing the rule number(s) in `## Rules` it draws on
     (e.g. "3. Check the project's commit-linking convention (rule 3)").
   - `## Output shape` — what applying the skill produces (e.g. "a filled
     issue-template body with every required field stated, plus the
     pre-submission-step result line").
   All existing body content (title, framing paragraph, `## Rules` list)
   is preserved unchanged below the new section — reorganization of
   section order only, no deletion.
2. Rewrite each pilot skill's `description:` frontmatter field from the
   template into a sentence derived from that skill's own `## Trigger`
   section, still satisfying the checker's existing trigger-marker
   substring test.
3. Add `scripts/procedure_authored_skills.txt` listing the 9 pilot
   skill directory names, one per line.
4. Extend `scripts/check_skill_conformance.py` with an additive check:
   for any skill directory listed in `procedure_authored_skills.txt`,
   its `SKILL.md` body must contain `## Trigger`, `## Procedure`, and
   `## Output shape` headings (case-sensitive, in that order or any
   order — exact ordering constraint to be finalized during
   implementation against what reads best); skills not listed are
   unaffected by this new check.
5. Run the rule-retention sweep (grep each pre-change rule line's
   distinguishing substring against the post-change file) and the full
   manifest + full-tree checker runs, and paste all of it into
   `docs/issue-1790/reports/implementation.md` per the acceptance
   criteria's `check:` lines.
6. Write the WAVE RECIPE section into the same phase-2 record: the
   authoring pattern above, observed per-skill effort (lines
   added/changed, wall-clock if tracked), and a proposed partition of
   the remaining ~225 skills into follow-up waves — the survey found
   family sizes ranging 2-10 skills grouped by directory-name prefix
   (e.g. `technical-feasibility` 10, `release-engineering` 10,
   `product-discovery` 10, down to families of 2); the recipe will
   propose waving by family, largest families first, to keep each wave's
   review surface bounded to a single role's rule set.

## Out of scope

- Actually authoring procedure sections for any of the ~225 non-pilot
  skills — this issue is pilot-only per its own text.
- Any change to skill frontmatter fields other than `description:`
  (`name`, `axis`, `rule_count_floor`, `role` are untouched).
- Any hook, CI gate, or enforcement mechanism beyond the checker script
  itself — this is guidance content, not execution policy.
- Changing the checker's existing frontmatter checks (name-match,
  trigger-marker substring test) for any skill, pilot or non-pilot.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` (or equivalent invocation
  finalized in phase 2) exits 0 against the 9 pilot skills' new
  trigger/procedure/output sections.
- For each pilot skill, every rule line present before the change greps
  successfully in the post-change file (rule-retention sweep), pasted
  live in the phase-2 record.
- `git diff --stat` restricted to the 9 pilot paths plus
  `scripts/check_skill_conformance.py` and
  `scripts/procedure_authored_skills.txt` shows no other file touched.
- A full-tree run of the (now-extended) checker still exits 0 for all
  234 skills, confirming non-manifest skills are unaffected.
- The phase-2 record contains a WAVE RECIPE section usable as a citable
  basis for follow-up wave issues.
