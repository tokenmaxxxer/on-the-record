# Current-state survey — issue-1866 (secure-coding family, wave 2a)

subject: issue-1866

## Scope confirmation

Checked out `tokenmaxxxer/skill-repository` at `/tmp/skill-repository`,
`git pull` to latest `main` (commit `aa8bbd3`, the just-landed
finance-unit-economics wave, PR #20). The issue body names "secure-coding
(10 skills)" in its Program context line but the Requirements section and
this repo's own skill listing both enumerate exactly 5
`secure-coding-*` directories:

canonical: `ls skills | grep secure-coding` run in /tmp/skill-repository —
output:
```
secure-coding-authorization-access-control
secure-coding-cryptography-secrets-management
secure-coding-dependency-supply-chain-security
secure-coding-input-validation-injection-defense
secure-coding-session-authentication
```

The "10 skills" figure in the Program context line does not match the
live tree; the Requirements list ("All 5 secure-coding-* skills") and the
issue's own scope/write-set lines govern. This survey treats the 5
skills above as the family, per Requirement 1's own wording.

## Body shape — all 5 are Shape A (procedure-shaped edit required)

canonical: `grep -n '^## ' skills/secure-coding-*/SKILL.md` run in
/tmp/skill-repository — every file reports exactly one heading, `## Rules`.
None carries `## Trigger`, `## Procedure`, or `## Output shape` per that
live grep output. All 5 are therefore live edits under the frozen recipe
(Shape A, matching the finance-unit-economics/customer-support/
incident-response/ml-engineering wave precedents at
docs/issue-1861/reports/implementation/survey.md,
docs/issue-1862/reports/implementation/survey.md,
docs/issue-1854/reports/implementation/survey.md,
docs/issue-1853/reports/implementation/survey.md) — none is Shape B
(already procedure-shaped, no-op candidate).

| skill | frontmatter `rule_count_floor` | heading before `## Rules` |
|---|---|---|
| secure-coding-authorization-access-control | 8 | none (only `## Rules`) |
| secure-coding-cryptography-secrets-management | 10 | none |
| secure-coding-dependency-supply-chain-security | 8 | none |
| secure-coding-input-validation-injection-defense | 9 | none |
| secure-coding-session-authentication | 9 | none |

## Rule shape within `## Rules`

canonical: `sed -n '1,40p'` on each of the 5 files, run in
/tmp/skill-repository. Each skill's `## Rules` body is a flat numbered
list (`1. When ... — ...`, `2. When ... — ...`, etc.), the same numbered
convention as the #1790 pilot family (api-design-*,
upstream-defect-report-*) — not the unordered
`- **ADDITION**/**REMOVAL**:` bullet convention used by the pricing and
finance-unit-economics families. This means Procedure-step citations in
this wave should cite printed rule numbers directly ("rule 3"), matching
the pilot's own citation convention, rather than the bullet-position
convention the pricing/finance-unit-economics waves needed for their
different rule shape.

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
$ cd /tmp/skill-repository && python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo "exit: $?"
exit: 0
```
canonical: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt (run in /tmp/skill-repository, pre-change, current manifest has 100 entries across 9 prior waves).

## Write-set confirmation

The frozen recipe's write set for this wave is exactly:
- `skills/secure-coding-authorization-access-control/SKILL.md`
- `skills/secure-coding-cryptography-secrets-management/SKILL.md`
- `skills/secure-coding-dependency-supply-chain-security/SKILL.md`
- `skills/secure-coding-input-validation-injection-defense/SKILL.md`
- `skills/secure-coding-session-authentication/SKILL.md`
- `scripts/procedure_authored_skills.txt`

No checker-script change is needed (the `--manifest` flag already exists
from the #1790 pilot); no hook change; no other family touched — matching
the issue's stated non-goals.
