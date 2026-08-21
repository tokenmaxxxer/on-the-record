---
status: proposed
files:
  - skills/customer-support-escalation-path/SKILL.md
  - skills/customer-support-five-whys-recurring-scope/SKILL.md
  - skills/customer-support-kcs-article-authoring/SKILL.md
  - skills/customer-support-research-log/SKILL.md
  - skills/customer-support-sla-tier-priority/SKILL.md
  - skills/customer-support-subtraction-comprehensibility/SKILL.md
  - scripts/procedure_authored_skills.txt
---

# Proposal: wave 2a, customer-support family (issue-1862)

## Request

Author `## Trigger` / `## Procedure` / `## Output shape` sections at the
top of the body of all 6 `customer-support-*` skills in
`tokenmaxxxer/skill-repository`, per the frozen WAVE RECIPE
(docs/issue-1790/reports/implementation.md), rewrite each
`description:` from its authored Trigger section, and append the 6
directory names to `scripts/procedure_authored_skills.txt` — zero
rule-line loss, guidance-only, no checker-logic or hooks changes,
delivered as a skill-repository PR plus this record.

## Constraints

- Frozen recipe only (docs/issue-1790/reports/implementation.md, WAVE
  RECIPE section) — no deviation in section names, ordering, or the
  `description:` derivation rule.
- Zero rule-line loss: every pre-existing line in all 6 files must
  survive, verified by the rule-retention sweep before commit.
- Write set bounded to the 6 family `SKILL.md` files plus the manifest —
  no other path in the skill-repository PR (Requirement 2 /
  Acceptance 2).
- No checker-logic edits, no hooks changes (issue's explicit
  non-goal 3).
- Both `check_skill_conformance.py` runs (full-tree, `--manifest`) must
  exit 0 after the change.

## Rationale

**Shape-A citation scheme: cite by `## Rules` bullet position** (e.g.
"Rules 1-2" or a short paraphrase naming the bullet), matching every
prior wave's numbered-rule citation convention adapted to this family's
un-numbered bullet list — considered but rejected: inventing a numbering
scheme by inserting literal digits into the 5 Shape-A skills' `## Rules`
bullets to match the pilot's `1.`/`2.` numbered-list precedent exactly.
Rejected because it would touch content lines the retention sweep must
treat as unchanged content, not cosmetic renumbering, and the pilot
recipe's step 2 only requires the `## Procedure` steps to cite "rule
number(s)" — it does not require the `## Rules` list itself to be
numbered; wave-2a's own incident-response precedent (canonical:
docs/issue-1854/reports/implementation/survey.md, "Shape split" section)
established that a family's pre-existing `## Rules` heading is accepted
as-is without reformatting, and this family's un-numbered bullets are
addressable by position/paraphrase the same way its own six-bullet
`sla-tier-priority` skill is enumerable without renumbering.

**Shape-B (`customer-support-research-log`) citation scheme: cite by the
research-log's own section headings** (`## Queries run`, `## Sources
read`, `## Per-rule mapping`, `## rule_count_floor derivation`) —
considered but rejected: forcing a rule-number citation onto
`research-log` by treating its "Per-rule mapping" paragraph as a
5-item numbered list to cite against. Rejected because the file carries
no `## Rules` heading and no numbered-rule content at all (canonical:
docs/issue-1862/reports/implementation/survey.md, "Shape split"
section) — the same shape wave-2e's `legal-compliance-research-log`
already resolved by citing its own section headings instead of
inventing rule numbers where none exist (canonical:
docs/issue-1834/reports/implementation.md, "What was done" section).
Reusing that resolved precedent keeps this wave's `## Procedure` writing
mechanical rather than reopening a decision already settled two waves
ago.

## What will be done

1. For each of the 5 Shape-A skills (`escalation-path`,
   `five-whys-recurring-scope`, `kcs-article-authoring`,
   `sla-tier-priority`, `subtraction-comprehensibility`): insert `##
   Trigger` (concrete distinguishing conditions for that axis, not a
   title restatement), `## Procedure` (ordered steps citing the
   relevant `## Rules` bullets by position/paraphrase), and `## Output
   shape` between the framing paragraph and `## Rules`; rewrite
   `description:` from the authored Trigger, keeping the "use when"
   trigger-marker substring the checker's base (non-manifest) check
   requires.
2. For `customer-support-research-log` (Shape B): insert the same three
   headings, with `## Procedure` citing the file's own `## Queries run`
   / `## Sources read` / `## Per-rule mapping` / `## rule_count_floor
   derivation` sections in place of rule numbers; rewrite `description:`
   the same way.
3. Append all 6 directory names to `scripts/procedure_authored_skills.txt`
   (incremental extension, existing 78 entries untouched).
4. Run the rule-retention sweep (`git diff -- skills/<skill>/SKILL.md |
   grep '^-[^-]' | grep -v '^-description:'`, expect empty output per
   skill) before committing.
5. Run `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` and the full-tree run with no
   flag; both must exit 0.
6. Paste all four check outputs (manifest run, sweep, `git diff --stat`
   scoped to the 7 changed paths, full-tree run) into
   `docs/issue-1862/reports/implementation.md` in phase 2.

## Out of scope

- Any other skill family (issue non-goal 3).
- Any edit to `scripts/check_skill_conformance.py` or repository hooks
  (issue non-goal 3).
- Renumbering or otherwise restructuring the existing `## Rules` bullet
  content beyond the three new headings and the `description:` rewrite.
- Resolving the issue body's stale "10 skills" Program-context wording —
  proceeding against the title/Requirements/checkout-agreed count of 6
  is the same resolution every prior wave (2a-2h) already applied
  (canonical: docs/issue-1862/reports/implementation/survey.md, "Count
  discrepancy in the issue body" section).

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py --manifest
  scripts/procedure_authored_skills.txt` exits 0 with all 6
  `customer-support-*` entries present.
- `python3 scripts/check_skill_conformance.py` (full-tree) exits 0.
- The rule-retention sweep shows empty removed-content diff (excluding
  the intentional `description:` line) for all 6 skills.
- `git diff --stat` lists exactly the 6 `skills/customer-support-*/SKILL.md`
  paths plus `scripts/procedure_authored_skills.txt` — nothing else.
