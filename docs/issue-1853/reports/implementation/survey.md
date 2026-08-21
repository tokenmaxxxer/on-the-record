---
subject: issue-1853
type: survey
---

# Survey: ml-engineering family (wave 2a)

## Role mapping vs. checked-out HEAD

canonical: `gh issue view 1853` (read live) — the prompt states this
role is mapped by role-source-allowlist (issue #1758) to skill-repository
commit `87f3961` for guidance skills (`implementation-complexity-coupling-management`,
`implementation-design-pattern-selection`,
`implementation-performance-data-structure-choice`,
`implementation-blueprint`). derived: `git log --oneline -3` on a fresh
clone at `/tmp/skill-repository-1853` off `origin/main` shows HEAD
`87f3961` itself ("Author procedural bodies for wave 2h: technical-writing
family (issue-1844) (#16)") — the mapping commit and the live tip
coincide, so no ancestry check is needed this time. This wave works from
the live `origin/main` HEAD (`87f3961`) for the actual skill-repository
write surface, per the same convention wave-2f/2g/2h used (fresh clone
off live `origin/main`, not a pin to the role-mapping commit).

## Count discrepancy in the issue body

canonical: `gh issue view 1853` (read live) — the "Program context"
paragraph states "Family: ml-engineering (10 skills — the largest
remaining family per the pilot survey)", but the issue title says "(6
skills)" and Requirement 1 says "All 6 ... skills". derived: `find
/tmp/skill-repository-1853/skills -maxdepth 1 -iname "ml-engineering-*"`
lists exactly 6 directories (below) — the live checkout matches the
title and Requirement 1's count of 6, not the Program-context
paragraph's 10. canonical: docs/issue-1844/reports/implementation/survey.md,
"Count discrepancy in the issue body" section (read live) — wave-2h's
technical-writing survey (and wave-2g/2f before it) found the identical
stale "10 skills" Program-context wording for their own families and
resolved it the same way: proceed against the 6-skill count that
title/Requirements/checkout agree on.

## The 6 family skills (write surface)

derived: `find /tmp/skill-repository-1853/skills -maxdepth 1 -iname
"ml-engineering-*" | sort`:
```
skills/ml-engineering-evaluation-discipline
skills/ml-engineering-ml-test-score-scoring
skills/ml-engineering-model-provenance-versioning
skills/ml-engineering-rollout-promotion-rollback
skills/ml-engineering-serving-pattern-selection
skills/ml-engineering-slo-definition-tradeoffs
```

## Frontmatter and body shape

derived: `grep -n "^## " skills/ml-engineering-*/SKILL.md` on the fresh
checkout — all 6 files carry the identical pre-authoring shape: YAML
frontmatter (`name`, `description`, `axis`, `rule_count_floor: 5`), a
one-line `#` title, a one-paragraph "Research trail" line, then a single
`## Rules` heading followed directly by 5 numbered rules (one of the 5
tagged `**REMOVAL**` in each file). None of the 6 carries `## Trigger`,
`## Procedure`, or `## Output shape` — none is a pre-existing no-op.
This is **Shape A** (the pilot's own `## Rules`-heading structure),
uniform across the whole family. canonical:
docs/issue-1844/reports/implementation/survey.md, "Frontmatter and body
shape" section (read live) — wave-2h's technical-writing family found a
5-Shape-A + 1-headless split, and earlier waves 2e/2f/2g found their own
Shape-B/headless variants in their own families; this family, by
contrast, has **zero shape variance** across all 6 members — no
`-research-log` or `-tool-landscape` member, no headless outlier to
resolve.

## Pre-existing rule content (retention baseline)

derived: `grep -c "^[0-9]\+\." skills/ml-engineering-*/SKILL.md` — 5
numbered rules per file, 30 rules total across the 6 files. This count
is the rule-retention sweep's pre-change baseline (Acceptance
requirement 1's "every pre-existing rule line retained").

## Manifest baseline

derived: `grep -c "^ml-engineering" scripts/procedure_authored_skills.txt`
on the fresh checkout returns 0 — none of the 6 family names is present
yet.

## Checker baseline (pre-change, executed live)

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo $?
0
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo $?
0
```
acceptance: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt — result: exit 0, "234 skills checked", pre-change
acceptance: python3 scripts/check_skill_conformance.py (full-tree, no flag) — result: exit 0, "234 skills checked", pre-change

Both checks return exit 0 pre-change (234 skills tree-wide; the 6
ml-engineering skills are not yet in the manifest, so the manifest run
does not yet require Trigger/Procedure/Output-shape headings on them).

## Applicability of the frozen recipe

canonical: docs/issue-1790/reports/implementation.md, WAVE RECIPE section,
steps 1-5 (read live) — the recipe's steps (check-for-no-op, insert 3
headings, rewrite description from Trigger, extend manifest, run the 4
checks) apply directly: step 1's no-op check finds nothing pre-authored
(canonical: this survey's "Frontmatter and body shape" section above),
so all 6 skills require authoring, none is a no-op.
