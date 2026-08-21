---
status: proposed
files:
  - skill-repository/skills/market-analysis-competitor-mapping/SKILL.md
  - skill-repository/skills/market-analysis-evidence-rigor/SKILL.md
  - skill-repository/skills/market-analysis-five-forces/SKILL.md
  - skill-repository/skills/market-analysis-jtbd-fit/SKILL.md
  - skill-repository/skills/market-analysis-mece-proposal/SKILL.md
  - skill-repository/scripts/procedure_authored_skills.txt
---

# Proposal: procedural-body wave 2a — market-analysis family

subject: issue-1875

## Request

Apply the procedural-body recipe frozen in `docs/issue-1790/reports/implementation.md`
(the #1790 pilot) to the 5 `market-analysis-*` skills in
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
  skill's `## Rules` section (including inline `**REMOVAL**:` tagged
  items and each line's trailing `source:` citation) must survive
  verbatim in the post-change file.
- Write set is exactly the 5 SKILL.md files plus
  `scripts/procedure_authored_skills.txt` — no other skill, no checker
  script edit, no hook.
- Guidance-only: Procedure steps describe when/how to apply a rule; they
  do not restate or paraphrase the rule's content, matching the pilot's
  navigational-layer framing.
- Both checker runs (`--manifest` and full-tree) must exit 0.

## Rationale

**Chosen approach**: reuse the frozen recipe verbatim, citing rules by
their printed number (rule 1, rule 2, ...) within `## Rules`, since this
family's rules are already the pilot's own numbered `1. When ...`
convention (unlike the finance-unit-economics and pricing families'
unordered `- **ADDITION**/**REMOVAL**:` bullets, which needed
position-based citation instead). The survey confirms all 5 files use
identical numbered-line formatting with a trailing `source:` URL per
line, so citation is a direct number reference with no adaptation
needed.

**Rejected alternative — split `**REMOVAL**:`-tagged rules into their
own citation category** (treat inline-tagged removal rules, e.g. rule 7
in competitor-mapping, as a separate addressable set from plain rules,
citing them as "removal rule 1" instead of "rule 7"): rejected because
the tag is inline prose within an already-numbered line, not a separate
list — introducing a second numbering scheme on top of the existing one
would let a Procedure step's citation drift from the line it actually
points to, the exact class of error the zero-rule-loss sweep exists to
catch. Citing by the single existing line number is unambiguous and
needs no new convention, matching the risk-management wave's (#1867)
same rejection.

**Rejected alternative — treat any already-Trigger-shaped skill as no-op
without re-verifying**: rejected because the survey found (not assumed)
that none of the 5 currently carries `## Trigger`/`## Procedure`/
`## Output shape` — treating this as given rather than confirming it
live would violate the acceptance criterion's own empty-state
requirement ("recorded as no-op with evidence"), which needs a check
result, not an inference from the family being new.

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
   every pre-change line (rule text plus its `source:` URL) is present
   post-change.
6. Run `python3 scripts/check_skill_conformance.py` (full-tree, no
   manifest arg) and confirm it still exits 0.
7. Run `git diff --stat` scoped to the working tree and confirm it lists
   only the 5 SKILL.md paths plus
   `scripts/procedure_authored_skills.txt`.
8. Commit, push branch `issue-1875-wave2a-market-analysis`, open a PR
   against `tokenmaxxxer/skill-repository` main.
9. Paste all four check outputs plus the `git diff --stat` output into
   `docs/issue-1875/reports/implementation.md` (this repo), citing the
   skill-repository PR.

## Out of scope

- Any skill outside the 5 `market-analysis-*` skills.
- Any edit to `scripts/check_skill_conformance.py` (checker logic).
- Any hook, gate, or CI config change.
- Renumbering or rewording existing `## Rules` lines, and any change to
  each file's `rule_count_floor:` frontmatter field.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 and reports the 5 new
  skills conformant.
- `python3 scripts/check_skill_conformance.py` (full-tree) exits 0.
- The rule-retention sweep shows every pre-change `## Rules` numbered
  line present post-change for all 5 files (50/50 rule lines retained
  per the survey's count).
- `git diff --stat` lists exactly the 5 SKILL.md paths plus
  `scripts/procedure_authored_skills.txt`, nothing else.
