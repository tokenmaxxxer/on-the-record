---
status: proposed
files:
  - skill-repository/skills/refactoring-legacy-characterization-test-scope/SKILL.md
  - skill-repository/skills/refactoring-legacy-refactoring-step-decomposition/SKILL.md
  - skill-repository/skills/refactoring-legacy-seam-selection/SKILL.md
  - skill-repository/skills/refactoring-legacy-strangler-fig-migration/SKILL.md
  - skill-repository/skills/refactoring-legacy-verification-cadence/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural-body wave 2a — refactoring-legacy family

subject: issue-1873

## Request

Apply the procedural-body recipe frozen in
`docs/issue-1790/reports/implementation.md` (the #1790 pilot) to the 5
`refactoring-legacy-*` skills in `tokenmaxxxer/skill-repository`: insert
`## Trigger` / `## Procedure` / `## Output shape` sections, each
Procedure step citing the rule number(s) it draws on; rewrite each
skill's `description:` from its own new Trigger section; append the 5
skill names to `scripts/procedure_authored_skills.txt`; verify with the
manifest checker, a rule-retention sweep, a full-tree checker run, and a
scoped `git diff --stat`. No checker-logic change, no other family, no
hooks (issue non-goals).

## Constraints

- Zero rule-line loss: every pre-change numbered line in each skill's
  `## Rules` section must survive verbatim in the post-change file.
- Write set is exactly the 5 SKILL.md files plus
  `scripts/procedure_authored_skills.txt` — no other skill, no checker
  script edit, no hook. `characterization-test-scope`'s pre-existing
  `## Open findings` heading is untouched.
- Guidance-only: Procedure steps describe when/how to apply a rule; they
  do not restate or paraphrase the rule's content, matching the pilot's
  navigational-layer framing.
- Both checker runs (`--manifest` and full-tree) must exit 0.

## Rationale

**Chosen approach**: reuse the frozen recipe verbatim, citing rule
bullets by their printed rule number (e.g. "rule 3") rather than bullet
position, since the survey found (canonical:
docs/issue-1873/reports/implementation/survey.md, "Rule shape within
`## Rules`" section) that all 5 refactoring-legacy skills use the same
flat numbered-list convention (`1. When ... — ...`) as the #1790 pilot
family and the immediately preceding secure-coding wave (issue-1866),
not the unordered `- **ADDITION**/**REMOVAL**:` bullet convention the
pricing and finance-unit-economics waves needed. Citing by printed
number is therefore both simpler and consistent with the two most
recent wave precedents — no translation layer is needed for this
family.

**Rejected alternative — reuse the finance-unit-economics wave's
bullet-position citation convention (issue-1861) uniformly across every
wave, regardless of a family's actual rule shape**: rejected because the
survey confirms this family's rules are already numbered (`1.`, `2.`,
...), so bullet-position citation would be a strictly worse fit —
inventing an artificial position count ("the 3rd rule") when a real,
printed rule number already exists in the source text. The recipe's own
principle is to reuse rule citations as they already appear, not to
standardize the citation form across families with different underlying
rule shapes.

**Rejected alternative — treat any of the 5 as already procedure-shaped
(Shape B) and skip authoring it as a no-op**: rejected because the survey
found (not assumed) that all 5 files carry no `## Trigger`/`##
Procedure`/`## Output shape` heading — canonical:
docs/issue-1873/reports/implementation/survey.md, "Body shape" section's
live `grep` output. Treating any skill as a no-op without that live
check would violate the acceptance criterion's own empty-state
requirement, which needs a check result, not an inference from family
membership.

## What will be done

1. For each of the 5 skills, read the existing `## Rules` numbered list
   and framing paragraph, then insert `## Trigger` / `## Procedure` /
   `## Output shape` between the framing paragraph and `## Rules`, with
   each Procedure step citing the rule number(s) it draws on.
   `characterization-test-scope`'s later `## Open findings` heading is
   left as-is.
2. Rewrite each skill's frontmatter `description:` as a sentence derived
   from that skill's own new `## Trigger` section (matching the pilot's
   "description derived from Trigger" step), keeping a checker
   trigger-marker substring ("use when").
3. Append the 5 skill directory names to
   `scripts/procedure_authored_skills.txt` (alphabetical, appended after
   the secure-coding wave's 5 entries).
4. Run `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (must exit 0).
5. Run the rule-retention sweep: for each of the 5 files, diff pre-change
   vs. post-change `## Rules` numbered lines and confirm every pre-change
   line's leading substring is present post-change.
6. Run `python3 scripts/check_skill_conformance.py` (full-tree, no
   manifest arg) and confirm it still exits 0.
7. Run `git diff --stat` scoped to the working tree and confirm it lists
   only the 5 SKILL.md paths plus `scripts/procedure_authored_skills.txt`.
8. Commit on branch `issue-1873-procedural-body-refactoring-legacy` in
   the skill-repository checkout, open a PR there, and paste all four
   check outputs plus the `git diff --stat` into the phase-2
   implementation record in this repo
   (`docs/issue-1873/reports/implementation.md`), matching the issue's
   Acceptance checks verbatim.

## Out of scope

- Any family other than the 5 `refactoring-legacy-*` skills.
- Any change to `scripts/check_skill_conformance.py`'s logic (the
  `--manifest` flag already exists from the #1790 pilot; no further
  checker change is needed).
- Any hook change.
- Editing `characterization-test-scope`'s `## Open findings` content —
  it predates this wave and is not part of the frozen recipe's insertion
  point.
- Reconciling the issue's Program-context "10 skills" figure against the
  live 5-skill tree beyond noting the discrepancy in the survey — the
  Requirements section's explicit "All 5 refactoring-legacy-* skills"
  wording is what this wave delivers against.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 post-change.
- `python3 scripts/check_skill_conformance.py` (full-tree) exits 0
  post-change.
- The rule-retention sweep shows every pre-change `## Rules` line
  retained verbatim across all 5 files.
- `git diff --stat` in the skill-repository checkout lists only the 5
  `refactoring-legacy-*/SKILL.md` paths plus
  `scripts/procedure_authored_skills.txt`.
