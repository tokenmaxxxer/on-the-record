---
status: proposed
files:
  - skill-repository/skills/finance-unit-economics-cac-payback/SKILL.md
  - skill-repository/skills/finance-unit-economics-evidence-chain/SKILL.md
  - skill-repository/skills/finance-unit-economics-ltv-cac-band/SKILL.md
  - skill-repository/skills/finance-unit-economics-ltv-churn-assumption/SKILL.md
  - skill-repository/skills/finance-unit-economics-proposal-shape/SKILL.md
  - skill-repository/skills/finance-unit-economics-sensitivity-scenario/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural-body wave 2a — finance-unit-economics family

subject: issue-1861

## Request

Apply the procedural-body recipe frozen in `docs/issue-1790/reports/implementation.md`
(the #1790 pilot) to the 6 `finance-unit-economics-*` skills in
`tokenmaxxxer/skill-repository`: insert `## Trigger` / `## Procedure` /
`## Output shape` sections, each Procedure step citing the rule(s) it
draws on; rewrite each skill's `description:` from its own new Trigger
section; append the 6 skill names to
`scripts/procedure_authored_skills.txt`; verify with the manifest
checker, a rule-retention sweep, a full-tree checker run, and a scoped
`git diff --stat`. No checker-logic change, no other family, no hooks
(issue non-goals).

## Constraints

- Zero rule-line loss: every pre-change bullet in each skill's
  `## Decision rules` section must survive verbatim in the post-change
  file (`## Rules`-equivalent content is `## Decision rules` here; the
  section heading itself is unchanged, only new sections are inserted
  around it).
- Write set is exactly the 6 SKILL.md files plus
  `scripts/procedure_authored_skills.txt` — no other skill, no checker
  script edit, no hook.
- Guidance-only: Procedure steps describe when/how to apply a rule: they
  do not restate or paraphrase the rule's content, matching the pilot's
  navigational-layer framing.
- Both checker runs (`--manifest` and full-tree) must exit 0.

## Rationale

**Chosen approach**: reuse the frozen recipe verbatim, citing rule
bullets by their `- **ADDITION**:` / `- **REMOVAL**:` position (1st,
2nd, ... within `## Decision rules`) rather than a printed rule number,
since this family's rules are unordered bullets, not the pilot's
numbered `1. When ...` lines. This is the same bullet-tagged citation
approach the pricing wave (issue-1847) already used successfully against
the same rule shape — the survey confirms cac-payback, ltv-cac-band, etc.
use the identical `- **ADDITION**/**REMOVAL**:` bullet convention pricing
skills use.

**Rejected alternative — invent a new numbered-rule convention for this
family** (renumber each `## Decision rules` bullet with an explicit
`1.`/`2.` prefix before authoring Procedure steps, so citations read
"rule 3" instead of "the 3rd ADDITION bullet"): rejected because it
would touch every rule bullet's own line (not just add new sections
around them), multiplying the diff surface subject to the zero-rule-loss
sweep and increasing the chance of an accidental content edit inside
`## Decision rules` itself — a risk the frozen recipe's "guidance-only"
constraint and the #1790 pilot's file-untouched-except-inserted-sections
pattern were designed to avoid. The pricing wave already proved
bullet-position citation reads clearly without renumbering, so the
rejected alternative buys no clarity for real risk.

**Rejected alternative — treat any already-Trigger-shaped skill as no-op
without re-verifying**: rejected because the survey found (not assumed)
that none of the 6 currently carries `## Trigger`/`## Procedure`/
`## Output shape` — treating this as given rather than confirming it
live would violate the acceptance criterion's own empty-state
requirement ("recorded as no-op with evidence"), which needs a check
result, not an inference from the family being new.

## What will be done

1. For each of the 6 skills, read the existing `## Decision rules`
   bullets and `## Notes` section, then insert `## Trigger` /
   `## Procedure` / `## Output shape` between the framing paragraph and
   `## Decision rules`, with each Procedure step citing the ADDITION/
   REMOVAL bullet(s) it draws on by position.
2. Rewrite each skill's frontmatter `description:` as a sentence derived
   from that skill's own new `## Trigger` section (matching the pilot's
   "description derived from Trigger" step).
3. Append the 6 skill directory names to
   `scripts/procedure_authored_skills.txt` (alphabetical, consistent with
   the existing file's per-wave grouping).
4. Run `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (must exit 0).
5. Run the rule-retention sweep: for each of the 6 files, diff
   pre-change vs. post-change `## Decision rules` bullets and confirm
   every pre-change bullet's leading substring is present post-change.
6. Run `python3 scripts/check_skill_conformance.py` (full-tree, no
   manifest arg) and confirm it still exits 0.
7. Run `git diff --stat` scoped to the working tree and confirm it lists
   only the 6 SKILL.md paths plus
   `scripts/procedure_authored_skills.txt`.
8. Commit, push branch `issue-1861-wave2a-finance-unit-economics`, open
   a PR against `tokenmaxxxer/skill-repository` main.
9. Paste all four check outputs plus the `git diff --stat` output into
   `docs/issue-1861/reports/implementation.md` (this repo), citing the
   skill-repository PR.

## Out of scope

- Any skill outside the 6 `finance-unit-economics-*` skills.
- Any edit to `scripts/check_skill_conformance.py` (checker logic).
- Any hook, gate, or CI config change.
- Renumbering or rewording existing `## Decision rules` bullets.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 and reports the 6 new
  skills conformant.
- `python3 scripts/check_skill_conformance.py` (full-tree) exits 0.
- The rule-retention sweep shows every pre-change `## Decision rules`
  bullet present post-change for all 6 files (26/26 rule bullets
  retained per the survey's count).
- `git diff --stat` lists exactly the 6 SKILL.md paths plus
  `scripts/procedure_authored_skills.txt`, nothing else.
