# Current-state survey — issue-1873 (refactoring-legacy family, wave 2a)

subject: issue-1873

## Scope confirmation

Checked out `tokenmaxxxer/skill-repository` at `/tmp/skill-repository-1873`,
cloned fresh from `/tmp/skill-repository` at commit `2020665` (the
just-landed secure-coding wave, issue-1866). The issue body names
"refactoring-legacy (10 skills)" in its Program context line but the
Requirements section and this repo's own skill listing both enumerate
exactly 5 `refactoring-legacy-*` directories — the same "stated 10, live
5" discrepancy the secure-coding wave (issue-1866) survey already
recorded for its own family:

canonical: `ls skills | grep refactoring-legacy` run in
/tmp/skill-repository-1873 — output:
```
refactoring-legacy-characterization-test-scope
refactoring-legacy-refactoring-step-decomposition
refactoring-legacy-seam-selection
refactoring-legacy-strangler-fig-migration
refactoring-legacy-verification-cadence
```

The "10 skills" figure in the Program context line does not match the
live tree; the Requirements list ("All 5 refactoring-legacy-* skills")
and the issue's own scope/write-set lines govern. This survey treats the
5 skills above as the family, per Requirement 1's own wording.

## Body shape — all 5 are Shape A (procedure-shaped edit required)

canonical: `grep -n '^## ' skills/refactoring-legacy-*/SKILL.md` run in
/tmp/skill-repository-1873 — output:
```
skills/refactoring-legacy-verification-cadence/SKILL.md:12:## Rules
skills/refactoring-legacy-refactoring-step-decomposition/SKILL.md:12:## Rules
skills/refactoring-legacy-strangler-fig-migration/SKILL.md:12:## Rules
skills/refactoring-legacy-seam-selection/SKILL.md:12:## Rules
skills/refactoring-legacy-characterization-test-scope/SKILL.md:12:## Rules
skills/refactoring-legacy-characterization-test-scope/SKILL.md:28:## Open findings
```
Every file's only pre-`## Rules` heading is the `## Rules` heading
itself (none carries `## Trigger`, `## Procedure`, or `## Output shape`).
One file (`characterization-test-scope`) additionally carries a
pre-existing `## Open findings` heading after its rule list — that
heading is untouched by this wave; the recipe inserts the three new
sections only between the framing paragraph and `## Rules`. All 5 are
therefore live edits under the frozen recipe (Shape A), matching the
secure-coding/finance-unit-economics/customer-support/incident-response/
ml-engineering wave precedents at
docs/issue-1866/reports/implementation/survey.md,
docs/issue-1861/reports/implementation/survey.md,
docs/issue-1862/reports/implementation/survey.md,
docs/issue-1854/reports/implementation/survey.md,
docs/issue-1853/reports/implementation/survey.md — none is Shape B
(already procedure-shaped, no-op candidate).

| skill | frontmatter `rule_count_floor` | live rule-line count | heading before `## Rules` |
|---|---|---|---|
| refactoring-legacy-characterization-test-scope | 5 | 7 | none |
| refactoring-legacy-refactoring-step-decomposition | 5 | 7 | none |
| refactoring-legacy-seam-selection | 5 | 7 | none |
| refactoring-legacy-strangler-fig-migration | 5 | 7 | none |
| refactoring-legacy-verification-cadence | 5 | 6 | none |

canonical: `grep -c '^[0-9]\+\. ' skills/refactoring-legacy-*/SKILL.md`
run in /tmp/skill-repository-1873 for the "live rule-line count" column.

## Rule shape within `## Rules`

canonical: `grep -n '^[0-9]\+\. \|^## '
skills/refactoring-legacy-*/SKILL.md` run in /tmp/skill-repository-1873.
Each skill's `## Rules` body is a flat numbered list (`1. When ... —
...`, `2. When ... — ...`, etc., with some entries prefixed
`**REMOVAL**:`), the same numbered convention as the #1790 pilot family
and the secure-coding wave — not the unordered
`- **ADDITION**/**REMOVAL**:` bullet convention used by the pricing and
finance-unit-economics families. Procedure-step citations in this wave
therefore cite printed rule numbers directly ("rule 3"), matching the
pilot's own citation convention and the immediately preceding
secure-coding wave, rather than the bullet-position convention the
pricing/finance-unit-economics waves needed for their different rule
shape.

## Frozen recipe and check commands (from #1790 pilot record)

canonical: docs/issue-1790/reports/implementation.md, "WAVE RECIPE"
section — the recipe this wave reuses verbatim:
1. Confirm no existing Trigger/Procedure/Output-shape heading, per the
   "Body shape" section's live `grep` output above (none found, so no
   no-op candidates in this family).
2. Insert `## Trigger` / `## Procedure` / `## Output shape` between the
   framing paragraph and `## Rules`, each Procedure step citing rule
   number(s).
3. Rewrite `description:` from the new `## Trigger` content.
4. Append the 5 directory names to `scripts/procedure_authored_skills.txt`.
5. Run `python3 scripts/check_skill_conformance.py --manifest
   scripts/procedure_authored_skills.txt` (must exit 0) and the full-tree
   run with no flag (must exit 0); run the rule-retention sweep before
   committing; run `git diff --stat` scoped to the 5 files + manifest.

Pre-change manifest checker baseline, run before any edit:
```
$ cd /tmp/skill-repository-1873 && python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo "exit: $?"
exit: 0
```
canonical: python3 scripts/check_skill_conformance.py --manifest
scripts/procedure_authored_skills.txt (run in /tmp/skill-repository-1873,
pre-change; current manifest has 107 lines across 10 prior waves,
`wc -l scripts/procedure_authored_skills.txt`).

## Write-set confirmation

The frozen recipe's write set for this wave is exactly:
- `skills/refactoring-legacy-characterization-test-scope/SKILL.md`
- `skills/refactoring-legacy-refactoring-step-decomposition/SKILL.md`
- `skills/refactoring-legacy-seam-selection/SKILL.md`
- `skills/refactoring-legacy-strangler-fig-migration/SKILL.md`
- `skills/refactoring-legacy-verification-cadence/SKILL.md`
- `scripts/procedure_authored_skills.txt`

No checker-script change is needed (the `--manifest` flag already exists
from the #1790 pilot); no hook change; no other family touched — matching
the issue's stated non-goals.
