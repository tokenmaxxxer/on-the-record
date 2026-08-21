---
subject: issue-1844
type: survey
---

# Survey: technical-writing family (wave 2h)

## Role mapping vs. checked-out HEAD

canonical: `gh issue view 1844` (read live) — the prompt states this
role is mapped by role-source-allowlist (issue #1758) to skill-repository
commit `52cfae5` for guidance skills. derived: `git log --oneline -3` on
a fresh clone at `/tmp/skill-repository-1844` off `origin/main` shows
HEAD `cc63dd4` ("Author procedural bodies for wave 2g: ux-engineering
family (issue-1838) (#14)"), one commit ahead of `52cfae5` (wave-2e
legal-compliance). `52cfae5` is present in this HEAD's ancestry (`git
merge-base --is-ancestor 52cfae5 HEAD` — exit 0), so the mapped skills'
guidance content is unaffected by the one additional wave-2g commit;
this wave still works from the live `origin/main` HEAD (`cc63dd4`) for
the actual skill-repository write surface, per the same convention
wave-2f/2g used (fresh clone off live `origin/main`, not a pin to the
role-mapping commit) — the manifest and skill bodies must reflect the
real current state to avoid a stale-base conflict at PR time.

## Count discrepancy in the issue body

canonical: `gh issue view 1844` (read live) — the "Program context"
paragraph states "Family: technical-writing (10 skills — the largest
remaining family per the pilot survey)", but the issue title says "(6
skills)" and Requirement 1 says "All 6 ... skills". derived: `find
/tmp/skill-repository-1844/skills -maxdepth 1 -iname
"technical-writing-*"` lists exactly 6 directories (below) — the live
checkout matches the title and Requirement 1's count of 6, not the
Program-context paragraph's 10. canonical:
docs/issue-1838/reports/implementation/survey.md, "Count discrepancy in
the issue body" section (read live) — wave-2g's survey found the
identical stale-"10 skills" Program-context wording for its own family
and resolved it the same way: proceed against the 6-skill count
title/Requirements/checkout agree on.

## Checkout and manifest state

canonical: fresh clone at `/tmp/skill-repository-1844` off
`origin/main`, read live via `git log --oneline -3` — HEAD `cc63dd4`.
Branch `issue-1844-wave2h-technical-writing` created off `origin/main`
for this wave, isolated from the unrelated `/tmp/skill-repository`
(wave-2d) and other prior waves' scratch checkouts. canonical:
docs/issue-1838/reports/implementation/survey.md, "Checkout and
manifest state" section (read live) — wave-2e/2f/2g each established
this same fresh-clone-per-wave isolation convention in their own
records; this wave follows it.

canonical: `wc -l scripts/procedure_authored_skills.txt` and `grep -c
"^technical-writing-" scripts/procedure_authored_skills.txt` (both read
live) — the manifest currently lists 66 names: 9 pilot, 10 wave-2a
`technical-feasibility-*`, 10 wave-2b `release-engineering-*`, 10
wave-2c `product-discovery-*`, 7 wave-2d `observability-*`, 7 wave-2e
`legal-compliance-*`, 7 wave-2f `conformance-review-*`, 6 wave-2g
`ux-engineering-*`. 0 `technical-writing-*` entries present yet.

canonical: `python3 scripts/check_skill_conformance.py` (full-tree, read
live) — exit 0, "234 skills checked", confirming the checker is currently
green before this wave's changes.

## Family enumeration

derived: `find skills -maxdepth 1 -iname "technical-writing-*" | sort` —
6 directories, matching the issue title and Requirement 1's count:

```
skills/technical-writing-doc-type-selection
skills/technical-writing-minimalism-scoping
skills/technical-writing-persuasion-trust
skills/technical-writing-structure-comprehension
skills/technical-writing-style-guide-compliance
skills/technical-writing-tool-landscape
```

## Shape split — a new sub-shape, not the wave-2a-2g Shape-A/Shape-B split

canonical: `sed -n '1,16p' skills/technical-writing-*/SKILL.md` and
`grep -n "^## " skills/technical-writing-*/SKILL.md` (both read live).

**Shape A** (pilot-equivalent structure, `rule_count_floor:` present in
YAML frontmatter, single heading `## Rules` — this family uses the
heading name `## Rules`, not `## Decision rules` as wave-2e/2f/2g used):

```
technical-writing-doc-type-selection:       rule_count_floor: 12, "## Rules"
technical-writing-minimalism-scoping:       rule_count_floor: 11, "## Rules"
technical-writing-persuasion-trust:         rule_count_floor: 10, "## Rules"
technical-writing-structure-comprehension:  rule_count_floor: 10, "## Rules"
technical-writing-style-guide-compliance:   rule_count_floor: 11, "## Rules"
```

**Shape A-headless**: derived: `grep -c "^## "
skills/technical-writing-tool-landscape/SKILL.md` = 0 — of the 6 family
members, exactly `technical-writing-tool-landscape` (`rule_count_floor:
3` per its own frontmatter, read live) has a numbered rules list (3
entries, same content shape as the Shape-A skills' `## Rules` blocks)
but **no heading at all** before it: the file runs frontmatter -> `#
Tool-landscape learnings ...` title -> one framing paragraph -> the 3
numbered entries directly, with no `## Rules` (or `## Decision rules`)
line anywhere. This differs from the tool-landscape skills already
authored in other families: canonical: `grep -n "^## "
skills/api-design-tool-landscape/SKILL.md` and `skills/incident-
response-tool-landscape/SKILL.md` (both read live) — both carry an
explicit `## Rules` heading before their own numbered entries.
`technical-writing-tool-landscape` is the only tool-landscape variant in
the repository (checked against these two other instances) with no
heading marker at all.

No `## Axis: <name>`-style evidence-trail file (the wave-2e/2f/2g
Shape-B pattern, e.g. `research-log` skills) exists in this family — this
family has no `-research-log` member (derived: `find skills -maxdepth 1
-iname "technical-writing-research-log"` — no match). So this wave's
split is **5 Shape A + 1 Shape A-headless**, not the 5-A/1-B split
canonical: docs/issue-1838/reports/implementation/survey.md, "Shape A/B
split" section (read live) — the last three waves' surveys (2e/2f/2g)
each recorded for their own families.

None of the 6 files carry `## Trigger`/`## Procedure`/`## Output shape`
yet (derived: `grep -c "^## Trigger\|^## Procedure\|^## Output shape"
skills/technical-writing-*/SKILL.md` — 0 for every file), so none
qualifies for the recipe's no-op/empty-state clause.

## Precedent for the headless numbered-list citation target

canonical: `skills/api-design-tool-landscape/SKILL.md` and
`skills/incident-response-tool-landscape/SKILL.md` (both read live) —
both already-existing tool-landscape skills cite rule numbers from an
explicit `## Rules` heading; neither is headless, so neither is a direct
precedent for a heading-free numbered list. canonical: `grep -rl
"headless" docs/issue-1790/reports docs/issue-1802 docs/issue-1809
docs/issue-1812 docs/issue-1830 docs/issue-1834 docs/issue-1835
docs/issue-1838 2>/dev/null` (read live) — no match across any prior
wave's phase-1/phase-2 records, so no prior wave recorded a skill whose
numbered rules carry no heading at all; this is a genuinely new sub-case
within Shape A, not a repeat of an existing convention.

## Checker mechanics

canonical: `git log -1 --format=%H -- scripts/check_skill_conformance.py`
(read live) returns `bb89bdc1ba7458fdf7c4ee494a3c0ea70cd65322` — the
pilot commit — confirming the checker has had zero logic edits across
the pilot and every wave merged to `origin/main` through this checkout's
HEAD `cc63dd4`. `--manifest <path>` requires `## Trigger`, `##
Procedure`, `## Output shape` (any order) in a listed skill's SKILL.md
body via a fixed `PROCEDURE_HEADINGS` tuple; it does not require any
particular heading name for the pre-existing rules content, so the
headless numbered list in `tool-landscape` does not block the checker —
only the 3 new headings matter for `--manifest` conformance.

## Rule-retention baseline (pre-change)

derived: per-skill numbered-rule count for the 5 `## Rules` skills, `awk
'/^## Rules/{flag=1;next} /^## /{flag=0}flag'
skills/technical-writing-<name>/SKILL.md | grep -c '^[0-9]\+\.'` run per
skill:

```
doc-type-selection:       12 rules
minimalism-scoping:       11 rules
persuasion-trust:         10 rules
structure-comprehension:  10 rules
style-guide-compliance:   11 rules
```

derived: sum of the above (12+11+10+10+11) = 54 numbered rule lines
across the 5 `## Rules` skills. For `tool-landscape`, derived: `grep -c
'^[0-9]\+\.' skills/technical-writing-tool-landscape/SKILL.md` = 3
numbered entries, matching its `rule_count_floor: 3`; retention target
is those 3 entries plus every other pre-existing line (derived: `wc -l
skills/technical-writing-tool-landscape/SKILL.md` = 53 lines total),
same zero-loss guarantee the pilot and every wave since have applied.

## Skip-condition check

Neither mandatory scout-directive skip condition applies on its face —
this is not a pure bugfix — but the direction decision this survey
exists to resolve (shape classification and how to phrase `##
Procedure` citations for the headless skill) is settled by direct
in-repo precedent plus straightforward extension of the frozen recipe:
the classification above (5 Shape A, 1 Shape A-headless) leaves one
narrow open choice — how to cite the 3 headless numbered entries in `##
Procedure` — which the proposal resolves by citing the rule numbers
directly (they are still numbered, just not under a heading), the same
mechanism already used for every other Shape-A skill, rather than by
inventing a synthetic `## Rules` heading (content invention, the
alternative wave-2a's survey already rejected for its own Shape-B
skills) or by treating it as Shape B (there is no `## Axis:`-style
evidence-trail structure to cite instead). Scouting is not run as a
separate external sweep, for the same reason the earlier waves gave:
the applicable guidance is this repository's own frozen recipe plus the
four skills named in the role's source-allowlist mapping (issue #1758)
— there is no external field to sweep for authoring an internal skill
file's procedural body, and this wave has no unresolved
shape-classification or citation-convention question left open beyond
the narrow headless-citation point resolved directly above.
