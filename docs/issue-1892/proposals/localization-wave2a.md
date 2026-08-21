---
status: proposed
files:
  - skill-repository/skills/localization-locale-convention-formatting/SKILL.md
  - skill-repository/skills/localization-pluralization-and-grammar/SKILL.md
  - skill-repository/skills/localization-rtl-and-script-support/SKILL.md
  - skill-repository/skills/localization-string-externalization/SKILL.md
  - skill-repository/skills/localization-text-expansion-and-layout/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural-body wave 2a — localization family

subject: issue-1892

## Request

Apply the procedural-body recipe frozen in `docs/issue-1790/reports/implementation.md`
(the #1790 pilot) to the 5 `localization-*` skills in
`tokenmaxxxer/skill-repository`: insert `## Trigger` / `## Procedure` /
`## Output shape` sections, each Procedure step citing the rule(s) it
draws on; rewrite each skill's `description:` from its own new Trigger
section; append the 5 skill names to
`scripts/procedure_authored_skills.txt`; verify with the manifest
checker, a rule-retention sweep, a full-tree checker run, and a scoped
`git diff --stat`. No checker-logic change, no other family, no hooks
(issue non-goals).

## Constraints

- Zero rule-line loss: every pre-change numbered rule line in each
  skill's `## Rules` section (including inline `REMOVAL —` tagged items
  and each line's trailing `source:` citation, where present) must
  survive verbatim in the post-change file.
- Write set is exactly the 5 SKILL.md files plus
  `scripts/procedure_authored_skills.txt` — no other skill, no checker
  script edit, no hook.
- Guidance-only: Procedure steps describe when/how to apply a rule; they
  do not restate or paraphrase the rule's content, matching the pilot's
  navigational-layer framing.
- Both checker runs (`--manifest` and full-tree) must exit 0.

## Rationale

**Chosen approach**: reuse the frozen recipe verbatim, citing rules by
their printed number (rule 1, rule 2, ...) within `## Rules`, since the
survey confirms all 5 files already use the pilot's own numbered
`1. **when** ... **choose** ...` convention (unlike the finance/pricing
families' unordered `- **ADDITION**/**REMOVAL**:` bullets, which needed
position-based citation instead). All 5 are Shape A (single un-authored
`## Rules` heading, no existing Trigger/Procedure/Output shape) — the
same classification the market-analysis (#1875), refactoring-legacy
(#1873), and capacity-planning (#1884) waves recorded for their own
families.

**Rejected alternative — treat the two files with a lower `source:`
count than rule count (locale-convention-formatting: 6 of 7;
string-externalization: 7 of 9) as a defect to fix in this wave**:
rejected because filling in a missing citation is a content judgment
about sourcing, not a structural procedural-body edit — it is outside
this wave's frozen recipe (which only inserts
Trigger/Procedure/Output-shape and derives `description:`) and outside
the issue's non-goals boundary ("checker logic changes" implicitly
scopes this wave to structure, not rule-content repair). The
zero-rule-loss constraint only requires all rule lines, sourced or not,
survive verbatim, which they will.

**Rejected alternative — split `REMOVAL —`-tagged rules into their own
citation category** (cite inline-tagged removal rules, e.g. rule 4 in
`locale-convention-formatting`, as a separate addressable set instead of
by their existing line number): rejected because the tag is inline
prose within an already-numbered line, not a separate list —
introducing a second numbering scheme on top of the existing one would
let a Procedure step's citation drift from the line it actually points
to, the exact class of error the zero-rule-loss sweep exists to catch.
Citing by the single existing line number is unambiguous and needs no
new convention, matching the risk-management (#1867), market-analysis
(#1875), and capacity-planning (#1884) waves' same rejection.

## What will be done

1. For each of the 5 skills, read the existing numbered `## Rules`
   lines, then insert `## Trigger` / `## Procedure` / `## Output shape`
   between the framing paragraph and `## Rules`, with each Procedure
   step citing the rule number(s) it draws on.
2. Rewrite each skill's frontmatter `description:` as a sentence derived
   from that skill's own new `## Trigger` section (matching the pilot's
   "description derived from Trigger" step), keeping the "use when"
   trigger-marker substring.
3. Append the 5 skill directory names to
   `scripts/procedure_authored_skills.txt` (alphabetical, consistent
   with the existing file's per-wave grouping).
4. Run `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (must exit 0).
5. Run the rule-retention sweep: for each of the 5 files, diff
   pre-change vs. post-change `## Rules` numbered lines and confirm
   every pre-change line (rule text plus its `source:` URL where
   present) is present post-change.
6. Run `python3 scripts/check_skill_conformance.py` (full-tree, no
   manifest arg) and confirm it still exits 0.
7. Run `git diff --stat` scoped to the working tree and confirm it lists
   only the 5 SKILL.md paths plus
   `scripts/procedure_authored_skills.txt`.
8. Commit, push branch `issue-1892-wave2a-localization`, open a PR
   against `tokenmaxxxer/skill-repository` main.
9. Paste all four check outputs plus the `git diff --stat` output into
   `docs/issue-1892/reports/implementation.md` (this repo), citing the
   skill-repository PR.

## Out of scope

- Any skill outside the 5 `localization-*` skills.
- Any edit to `scripts/check_skill_conformance.py` (checker logic).
- Any hook, gate, or CI config change.
- Renumbering or rewording existing `## Rules` lines, filling in the
  missing `source:` citations noted in the survey, and any change to
  each file's `rule_count_floor:` frontmatter field.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 and reports the 5 new
  skills conformant.
- `python3 scripts/check_skill_conformance.py` (full-tree) exits 0.
- The rule-retention sweep shows every pre-change `## Rules` numbered
  line present post-change for all 5 files (32/32 rule lines retained
  per the survey's count).
- `git diff --stat` lists exactly the 5 SKILL.md paths plus
  `scripts/procedure_authored_skills.txt`, nothing else.
