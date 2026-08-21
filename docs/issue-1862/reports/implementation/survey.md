---
subject: issue-1862
type: survey
---

# Survey: customer-support family (wave 2a)

## Role mapping vs. checked-out HEAD

canonical: `gh issue view 1862` (read live) — this role is mapped by
role-source-allowlist (issue #1758) to skill-repository guidance skills
(`implementation-complexity-coupling-management`,
`implementation-design-pattern-selection`,
`implementation-performance-data-structure-choice`,
`implementation-blueprint`, commit `e4e01a9`). derived: `git -C
/tmp/skill-repository log --oneline -3` on the checkout used for this
survey shows HEAD `87f3961` ("Author procedural bodies for wave 2h:
technical-writing family (issue-1844) (#16)") — the most recent wave
commit present on this checkout's `origin/main` at the time this survey
was run.

## Count discrepancy in the issue body

canonical: `gh issue view 1862` (read live) — the "Program context"
paragraph states "Family: customer-support (10 skills — the largest
remaining family per the pilot survey)", but the issue title says "(6
skills)" and Requirement 1 says "All 6 customer-support-* skills".
derived: `find /tmp/skill-repository/skills -maxdepth 1 -iname
"customer-support-*"` lists exactly 6 directories (below) — the live
checkout matches the title and Requirement 1's count of 6, not the
Program-context paragraph's 10. canonical:
docs/issue-1854/reports/implementation/survey.md (repo-local path in
this same working tree, read live), "Count discrepancy in the issue
body" section — wave-2a's incident-response survey found the identical
stale-"10 skills" Program-context wording for its own family and
resolved it the same way: proceed against the 6-skill count
title/Requirements/checkout agree on.

## Checkout and manifest state

canonical: `/tmp/skill-repository` (existing local checkout of
`git@github.com:tokenmaxxxer/skill-repository.git`, `origin/main`), read
live via `git log --oneline -3` — HEAD `87f3961`; `git status` (read
live) reports "nothing to commit, working tree clean".

canonical: `wc -l scripts/procedure_authored_skills.txt` and `grep -c
"^customer-support-" scripts/procedure_authored_skills.txt` (both read
live) — the manifest currently lists 78 names (9 pilot plus 69 prior-wave
entries through wave-2h technical-writing). 0 `customer-support-*`
entries present yet.

canonical: `python3 scripts/check_skill_conformance.py` (full-tree,
executed live, exit code checked via `$?`) — exit 0, "234 skills
checked", confirming the checker is currently green before this wave's
changes. canonical: `python3 scripts/check_skill_conformance.py
--manifest scripts/procedure_authored_skills.txt` (executed live, exit
code checked via `$?`) — exit 0, "234 skills checked", confirming the
manifest-scoped check is also green before this wave's changes.

## Family enumeration

derived: `find skills -maxdepth 1 -iname "customer-support-*" | sort` —
6 directories, matching the issue title and Requirement 1's count:

```
skills/customer-support-escalation-path
skills/customer-support-five-whys-recurring-scope
skills/customer-support-kcs-article-authoring
skills/customer-support-research-log
skills/customer-support-sla-tier-priority
skills/customer-support-subtraction-comprehensibility
```

## Shape split — 5 Shape A, 1 Shape B (`-research-log`), no headless member

canonical: `grep -n "^## " skills/customer-support-*/SKILL.md` (read
live) — 5 of the 6 files carry a single heading, `## Rules`, over a flat
bullet list (`- ` items, not numbered). derived: per-file bullet count
via `awk '/^## Rules/{flag=1;next} /^## /{flag=0}flag'
skills/customer-support-<name>/SKILL.md | grep -c '^- '`:

```
customer-support-escalation-path:              "## Rules", 5 rule bullets, 38 total lines
customer-support-five-whys-recurring-scope:     "## Rules", 5 rule bullets, 41 total lines
customer-support-kcs-article-authoring:         "## Rules", 5 rule bullets, 40 total lines
customer-support-sla-tier-priority:             "## Rules", 6 rule bullets, 42 total lines
customer-support-subtraction-comprehensibility: "## Rules", 5 rule bullets, 51 total lines
```

The 6th, `customer-support-research-log`, is Shape B: canonical:
`skills/customer-support-research-log/SKILL.md` (read live) — no `##
Rules` heading; instead `## Queries run (WebSearch, this session)`, `##
Sources read (practitioner / methodology / academic layers)`, `## Per-rule
mapping`, and `## rule_count_floor derivation` (86 total lines per `wc
-l`), with YAML frontmatter carrying `role: customer-support`,
`rule_count_floor: 5`, an `axes:` list naming the other 5 skills, and
`tier: sparse`.

This is the same Shape-B `-research-log` pattern wave-2e's
legal-compliance family already carried and resolved a citation target
for: acceptance: python3 scripts/check_skill_conformance.py --manifest
scripts/procedure_authored_skills.txt — result: "234 skills checked" /
"exit=0" (canonical: docs/issue-1834/reports/implementation.md,
repo-local path in this same working tree, read live, pasted verbatim
under that record's "### (a) Manifest checker" heading, post-authoring
run including `legal-compliance-research-log` in the manifest), where
that skill was authored citing "its own `## Axis: <name>` sections per
the proposal's Rationale" (same record, "What was" section, first
paragraph). That precedent's citation target — cite the research-log's
own section headings, not a rule-number scheme it does not have — is the
one this wave's proposal will reuse for `customer-support-research-log`.

None of the 6 files carry `## Trigger`/`## Procedure`/`## Output shape`
yet (derived: `grep -c "^## Trigger\|^## Procedure\|^## Output shape"
skills/customer-support-*/SKILL.md` — 0 for every file), so none
qualifies for the recipe's no-op/empty-state clause.

## Checker mechanics

canonical: `git log -1 --format=%H -- scripts/check_skill_conformance.py`
(read live) returns `bb89bdc1ba7458fdf7c4ee494a3c0ea70cd65322` — the
pilot commit — confirming the checker has had zero logic edits across the
pilot and every wave merged to this checkout's `origin/main` through HEAD
`87f3961`. `--manifest <path>` requires `## Trigger`, `## Procedure`,
`## Output shape` (any order) in a listed skill's SKILL.md body via a
fixed `PROCEDURE_HEADINGS` tuple (canonical:
`scripts/check_skill_conformance.py` lines 1-19, read live, module
docstring); it does not require any particular pre-existing heading
name, so the 5 Shape-A / 1 Shape-B split poses no classification
ambiguity for `--manifest` conformance — only the 3 new headings matter.

## Rule-retention baseline (pre-change)

derived: per-skill bullet-rule count under `## Rules` (`awk '/^## Rules/
{flag=1;next} /^## /{flag=0}flag' skills/customer-support-<name>/SKILL.md
| grep -c '^- '`) for the 5 Shape-A skills, alongside each file's total
line count (`wc -l`):

```
escalation-path:               5 rules, 38 total lines
five-whys-recurring-scope:     5 rules, 41 total lines
kcs-article-authoring:         5 rules, 40 total lines
sla-tier-priority:             6 rules, 42 total lines
subtraction-comprehensibility: 5 rules, 51 total lines
```

derived: sum of the above (5+5+5+6+5) = 26 rule bullets across the 5
Shape-A skills, 212 total pre-change lines across those 5 files (per-file
`wc -l` sum: 38+41+40+42+51). `research-log` (Shape B, no rule bullets,
tracked separately) adds 86 pre-change lines per `wc -l`. Retention
target for phase 2 is all 26 rule bullets plus every other pre-existing
line across all 6 files (298 total pre-change lines), the same zero-loss
guarantee the pilot and every wave since have applied.

## Skip-condition check

Neither mandatory scout-directive skip condition applies on its face —
this is not a pure bugfix — but the direction decision this survey
exists to resolve (shape classification for this family) is settled by
the direct in-repo evidence gathered above: derived, from the "Shape
split" section's own `grep`/`awk` output, that 5 of the 6 skills carry
the pilot's plain Shape-A structure (uniform `## Rules` bullet list, no
numbering, no headless member — see the per-file table above), and the
6th (`customer-support-research-log`) matches the Shape-B `-research-log`
pattern wave-2e already resolved, citation target and all (canonical:
docs/issue-1834/reports/implementation.md, cited above). This leaves no
open sub-case requiring a new convention. Scouting is not run as a
separate external sweep, for the same reason every prior wave (2a-2h)
gave: the direction decision is a recipe-reuse classification against a
family already surveyed and enumerated above, not a product-facing or
external-research question — the frozen WAVE RECIPE
(docs/issue-1790/reports/implementation.md) is the governing
design-research basis and is cited as such in the proposal.
