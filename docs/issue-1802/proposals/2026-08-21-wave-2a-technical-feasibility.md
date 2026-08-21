---
status: proposed
files:
  - docs/issue-1802/reports/implementation.md
  - /tmp/skill-repository/skills/technical-feasibility-build-vs-buy/SKILL.md
  - /tmp/skill-repository/skills/technical-feasibility-build-vs-buy-dependency-health/SKILL.md
  - /tmp/skill-repository/skills/technical-feasibility-license-and-regulatory-risk/SKILL.md
  - /tmp/skill-repository/skills/technical-feasibility-license-scan/SKILL.md
  - /tmp/skill-repository/skills/technical-feasibility-reversibility-and-spike-scoping/SKILL.md
  - /tmp/skill-repository/skills/technical-feasibility-reversibility-tag/SKILL.md
  - /tmp/skill-repository/skills/technical-feasibility-spike-report/SKILL.md
  - /tmp/skill-repository/skills/technical-feasibility-stride-table/SKILL.md
  - /tmp/skill-repository/skills/technical-feasibility-threat-model-disposition/SKILL.md
  - /tmp/skill-repository/skills/technical-feasibility-verdict-and-timebox-selection/SKILL.md
  - /tmp/skill-repository/scripts/procedure_authored_skills.txt
---

## Request

Apply the frozen #1790 wave recipe to the 10 `technical-feasibility-*`
skills in `tokenmaxxxer/skill-repository`: author `## Trigger` /
`## Procedure` / `## Output shape` in each body, rewrite each
`description:` from the authored Trigger, extend
`procedure_authored_skills.txt` with the 10 names, keep every
pre-existing content line, and deliver as a skill-repository PR plus this
role's record, scoped to only these 10 skill files + the manifest.

## Constraints

- Zero rule-line/content loss (issue requirement 1 + record-shape
  frontmatter's `## What did not work` accounting).
- No path outside the 10 family skills + manifest touched (issue
  requirement 2, `git diff --stat` must prove it).
- No checker-logic changes, no hook changes (issue non-goals).
- Guidance-only: the authored sections steer usage, they do not change
  what each skill's Rules/Artifact/Field-list content resolves.
- The manifest check requires exactly the 3 headings
  (`## Trigger`/`## Procedure`/`## Output shape`, any order) per
  `check_skill_conformance.py` — nothing else is mechanically enforced
  about Procedure's internal citation style.

## Rationale

The survey (docs/issue-1802/reports/implementation/survey.md) found the
10-skill family is not uniform: 5 skills ("Shape A") already match the
#1790 pilot's `## Rules`-with-numbered-rules structure the recipe was
written against, but the other 5 ("Shape B": `build-vs-buy`,
`license-scan`, `reversibility-tag`, `spike-report`, `stride-table`) are
an older, structurally different convention — no `## Rules` heading, no
numbered rule lines, narrative headings like `## Artifact` / `## Field
list` / `## Resolution rule` instead.

Two alternatives were considered for Shape B and rejected:

1. **Add a `## Rules` section to each Shape-B skill so the recipe's
   "cite rule number(s) from `## Rules`" applies uniformly across all
   10.** Rejected: this invents new rule-numbered structure the current
   content does not have, which goes well past "guidance-only" — it
   would restructure the skill's actual content, not just add a
   navigation layer on top of it, and risks silently changing what each
   step resolves (the issue's "zero rule-line loss" framing assumes the
   Rules block is pre-existing, not synthesized).
2. **Skip the 5 Shape-B skills this wave and treat them as a follow-up
   wave, delivering only the 5 Shape-A skills against #1802.** Rejected:
   the issue's requirement 1 is explicit — "All 10
   technical-feasibility-* skills" — and the acceptance check counts all
   10 into the manifest; splitting silently would under-deliver against
   a named, countable requirement without the issue's approval to narrow
   scope.

Chosen instead: apply the recipe's headings and manifest/description
steps identically to all 10, but let `## Procedure`'s per-step citations
point at rule numbers for the 5 Shape-A skills (recipe verbatim) and at
the existing named sections (`## Artifact`, `## Field list`,
`## Resolution rule`, etc.) for the 5 Shape-B skills — the citation
target changes to match what each skill actually has, while the
mechanically-checked 3 headings, the description rewrite, and the
manifest entry apply uniformly. This keeps the wave inside the issue's
stated scope (all 10, guidance-only, zero content loss) without
inventing structure Shape B doesn't have.

## What will be done

1. For each of the 10 skills, insert `## Trigger` / `## Procedure` /
   `## Output shape` between the framing paragraph and the skill's
   existing first structural heading (`## Rules` for Shape A; `## What
   it asks the user for` or equivalent for Shape B).
   - `## Trigger`: concrete conditions distinguishing the skill from its
     sibling axes/probes in the family (not a title restatement) —
     derived from each skill's current `description:` and framing text.
   - `## Procedure`: ordered steps citing rule numbers (Shape A) or
     existing section names (Shape B) per the Rationale above.
   - `## Output shape`: what the skill produces, derived from each
     skill's existing `## Artifact`/`## Field list`/resolution-rule
     content (Shape B) or its rules' stated outcomes (Shape A).
2. Rewrite each `description:` as a sentence derived from that skill's
   authored `## Trigger`, keeping the checker's trigger-marker substring
   ("use when").
3. Append all 10 directory names to `procedure_authored_skills.txt`,
   after the existing 9 pilot entries (incremental, not a replacement).
4. Run, from the skill-repository checkout, in this order: (a)
   `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (expect exit 0), (b) the
   rule-retention sweep — diff pre- and post-change content per skill
   and confirm every pre-existing rule/content line from the survey's
   baseline is still present, (c) `git diff --stat` scoped to the 10
   skill paths + manifest (expect no other paths), (d) `python3
   scripts/check_skill_conformance.py` with no flag (full-tree, expect
   exit 0).
5. Paste all four check outputs plus the `git diff --stat` into
   `docs/issue-1802/reports/implementation.md` (phase 2, after
   approval), matching the #1790 record's structure.

## Out of scope

- Any skill outside the 10 `technical-feasibility-*` family.
- Checker logic changes (`check_skill_conformance.py`) or hook changes.
- Restructuring Shape-B skills' existing content (Rules-block invention,
  section renames/merges) beyond inserting the 3 mandated headings.
- Re-litigating the #1790 recipe itself — this wave applies it, citing
  the Shape A/B split as an extension of citation style only.

## How you'll know it worked

- `check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt`
  exits 0 with all 10 new names included and passing.
- The rule-retention sweep shows zero lost lines against the survey's
  pre-change baseline (55 Shape-A rule lines + all Shape-B content lines).
- `check_skill_conformance.py` (full-tree, no flag) exits 0.
- `git diff --stat` lists only the 10 SKILL.md paths + the manifest file.
- All four outputs and the diff --stat are pasted live into
  docs/issue-1802/reports/implementation.md per the issue's acceptance
  checks.
