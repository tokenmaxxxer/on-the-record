---
subject: issue-1847
type: survey
---

# Survey: pricing family (wave 2h)

## Scope-field note

canonical: `gh issue view 1847` (read live) — the issue body's `scope:`
line reads `docs/issue-1847/proposals/, docs/issue-1847/reports/`,
matching this issue's own buckets. No correction needed.

## Count discrepancy in the issue body

canonical: `gh issue view 1847` (read live) — the "Program context"
paragraph states "Family: pricing (10 skills — the largest remaining
family per the pilot survey)", but the issue title says "(6 skills)" and
Requirement 1 says "All 6 pricing-* skills". derived: `find
/tmp/skill-repository-1847/skills -maxdepth 1 -iname "pricing-*"` lists
exactly 6 directories (below) — the live checkout matches the title and
Requirement 1's count of 6, not the Program-context paragraph's 10.
canonical: `docs/issue-1838/reports/implementation/survey.md` (read live
in this session) records the identical wording — "Family: ux-engineering
(10 skills — the largest remaining family per the pilot survey)" against
a 6-skill title/Requirement-1/live-checkout count — for issue #1838. The
two issues' Program-context paragraphs share the same "10 skills —
largest remaining family" phrase verbatim, which reads as boilerplate
carried across issues without updating the count, not a fact specific to
either family. This wave proceeds against the 6-skill count the title,
Requirements, and live checkout all agree on.

## Checkout and manifest state

canonical: fresh clone at `/tmp/skill-repository-1847` off
`origin/main`, read live via `git log -1 --format=%H` and `git log
--oneline -3` — HEAD `cc63dd406b6d9c590d830c033ae5a5c0c87269e1`
("Author procedural bodies for wave 2g: ux-engineering family
(issue-1838) (#14)"), matching the commit named in this role's
source-allowlist mapping (cc63dd4). The two commits immediately prior on
that log (`git log --oneline -3`, read live) are wave-2f
(`conformance-review`, #12) and wave-2e (`legal-compliance`, #13) — both
now landed on `origin/main`. This wave used its own fresh clone rather
than reusing the pre-existing `/tmp/skill-repository` checkout, per the
isolation convention established by wave-2e/2f/2g (each of those waves'
own records, read live, describe the same practice).

canonical: `wc -l scripts/procedure_authored_skills.txt` and `grep -c
"^<family>-" scripts/procedure_authored_skills.txt` per family prefix
(both read live) — the manifest currently lists 66 names: 3 pilot
`upstream-defect-report-*`, 6 pilot `api-design-*`, 10 wave-2a
`technical-feasibility-*`, 10 wave-2b `release-engineering-*`, 10
wave-2c `product-discovery-*`, 7 wave-2d `observability-*`, 7 wave-2e
`legal-compliance-*`, 7 wave-2f `conformance-review-*`, and 6 wave-2g
`ux-engineering-*` (3+6+10+10+10+7+7+7+6 = 66, matching the file's line
count exactly). None of the 6 `pricing-*` skills are present yet
(derived: `grep -c "^pricing-" scripts/procedure_authored_skills.txt` =
0).

## Family enumeration

derived: `find skills -maxdepth 1 -iname "pricing-*" | sort` — 6
directories, matching the issue title and Requirement 1's count:

```
skills/pricing-design-rigor
skills/pricing-method-family
skills/pricing-research
skills/pricing-scope-gate
skills/pricing-tier-structure
skills/pricing-verdict-report
```

## Shape split — a third shape not seen in wave-2e/2f/2g

canonical: `sed -n '1,8p' skills/pricing-*/SKILL.md` and `grep -n "^## "
skills/pricing-*/SKILL.md` (both read live from the checkout) — checked
each file's own YAML frontmatter and heading list directly, not a bare
substring grep.

**Shape A** (pilot's structure, `rule_count_floor:` present in YAML
frontmatter, single heading `## Decision rules`):

```
pricing-design-rigor:    rule_count_floor: 3, "## Decision rules"
pricing-method-family:   rule_count_floor: 3, "## Decision rules"
pricing-scope-gate:      rule_count_floor: 2, "## Decision rules"
pricing-tier-structure:  rule_count_floor: 2, "## Decision rules"
pricing-verdict-report:  rule_count_floor: 3, "## Decision rules"
```

canonical: `sed -n '1,8p' skills/pricing-<name>/SKILL.md` per file (read
live, above) — each of these 5 files' own YAML frontmatter carries
`rule_count_floor:`, confirming the shape directly per file.

**Shape C** (new this wave — not the Shape B evidence-trail/research-log
pattern; a fully-authored, free-standing skill that already carries one
of the three recipe headings):

```
pricing-research: no `axis:`/`rule_count_floor:` in frontmatter; headings
  "## First: does this even need the procedure?", "## Evidence grade —
  read before citing this to anyone", "## Procedure" (its own 6-step Van
  Westendorp/CBC routing procedure), "## Report format" — 273 lines
  total, 0 numbered `## Decision rules` lines.
```

canonical: `sed -n '1,8p' skills/pricing-research/SKILL.md` (read live,
above) — its frontmatter has only `name:` and a block-scalar
`description:` already containing a full "Use whenever…Do NOT use
for…" trigger clause, no `axis:` or `rule_count_floor:` field, unlike
the 5 Shape-A files. canonical: `grep -n "^## " skills/pricing-research/
SKILL.md` (read live, above) shows the file already contains a literal
`## Procedure` heading (its own pre-existing 6-step method-routing
procedure, unrelated in content to the wave recipe's rule-citing
procedure) but no `## Trigger` or `## Output shape` heading. This is
neither the Shape A pattern (all 3 headings absent, numbered rules to
cite) nor the Shape B pattern seen in wave-2e/2g (all 3 headings absent,
axis sections to cite) — it is partially recipe-conformant already,
missing exactly the other 2 mandated headings. canonical:
`scripts/check_skill_conformance.py` lines 26 and 41 (read live) define
`PROCEDURE_HEADINGS = ("## Trigger", "## Procedure", "## Output
shape")` and `missing = [h for h in PROCEDURE_HEADINGS if h not in
text]`. canonical: `grep -n "^## " skills/pricing-research/SKILL.md`
(read live, above) is the heading list that logic is applied to; a
manifest run today would report `pricing-research` as `missing
procedure section(s): ## Trigger, ## Output shape`.

5 Shape A + 1 Shape C accounts for all 6 family members. canonical:
`docs/issue-1834/proposals/2026-08-21-wave-2e-legal-compliance.md` and
`docs/issue-1838/reports/implementation/survey.md` (both read live in
this session) — both prior waves' outlier skill
(`legal-compliance-research-log`, `ux-engineering-research-log`) had
zero pre-existing recipe headings before authoring. canonical: `grep -n
"^## " skills/pricing-research/SKILL.md` (read live, above) confirms
`pricing-research`'s different current state — one heading (`##
Procedure`) already present. The acceptance check's own contemplated
"empty state: a family skill already procedure-shaped is recorded as
no-op with evidence" (canonical: `gh issue view 1847`, Acceptance item
1, read live) applies here in partial form: `pricing-research` needs
only the 2 missing headings added, and its existing `## Procedure`
section is left untouched (adding `## Procedure` again, or restructuring
the existing one, is not required — the checker only requires the
heading string to be present once, and it already is).

None of the 5 Shape-A files carry `## Trigger`/`## Output shape` yet
(derived: `grep -c "^## Trigger\|^## Output shape"
skills/pricing-design-rigor/SKILL.md skills/pricing-method-family/SKILL.md
skills/pricing-scope-gate/SKILL.md skills/pricing-tier-structure/SKILL.md
skills/pricing-verdict-report/SKILL.md` — 0 for every file), so none of
the 6 qualifies for a full no-op/empty-state skip.

## Precedent for the Shape C partial-conformance handling

canonical: `docs/issue-1834/proposals/2026-08-21-wave-2e-legal-compliance.md`
and `docs/issue-1838/proposals/2026-08-21-wave-2g-ux-engineering.md`
(both read live in this session) — both prior waves' Shape B handling
established the convention of citing named section headings in
parentheses when a skill has no numbered rules block, rather than
inventing one. No prior wave's survey recorded a skill that already
carried one of the three mandated headings under unrelated pre-existing
content, so there is no direct Shape-C precedent to cite for the
heading-insertion mechanics themselves; the applicable precedent is the
recipe's own "guidance-only" instruction (canonical:
`docs/issue-1790/reports/implementation.md`, WAVE RECIPE section, read
live) plus the same zero-content-loss discipline every prior wave
applied — `pricing-research`'s existing `## Procedure` section is
treated as pre-existing content to retain unmodified, and only the 2
missing headings (`## Trigger`, `## Output shape`) are inserted, each
derived from the file's own existing description/report-format content
rather than duplicating or rewriting the existing Procedure.

## Checker mechanics

canonical: `git log -1 --format=%H -- scripts/check_skill_conformance.py`
(read live) returns `bb89bdc1ba7458fdf7c4ee494a3c0ea70cd65322` — the
pilot commit — confirming the checker has had zero logic edits across
the pilot and every wave merged to `origin/main` through this checkout's
HEAD `cc63dd4`. `--manifest <path>` requires `## Trigger`,
`## Procedure`, `## Output shape` (any order) in a listed skill's
SKILL.md body via a fixed `PROCEDURE_HEADINGS` tuple; skills not listed
are unaffected.

## Rule-retention baseline (pre-change)

derived: per-skill numbered-rule count for the 5 Shape-A skills, `awk
'/^## Decision rules/{flag=1;next} /^## /{flag=0}flag'
skills/pricing-<name>/SKILL.md | grep -c '^[0-9]\+\.'` run per skill:

```
design-rigor:     5 rules
method-family:    5 rules
scope-gate:       4 rules
tier-structure:   3 rules
verdict-report:   5 rules
```

derived: sum of the above (5+5+4+3+5) = 22 numbered rule lines total
across the 5 Shape-A skills, to retain post-change. For the 1 Shape-C
skill, the retention target is content-level rather than rule-numbered:
every pre-existing line in `pricing-research` (derived: `wc -l
skills/pricing-research/SKILL.md` = 273 lines) — frontmatter, both
existing gate sections, the full 6-step `## Procedure`, and `## Report
format` — same zero-loss guarantee applied to earlier waves' non-Shape-A
skills, with the added constraint that the existing `## Procedure`
heading and its content are left as-is rather than replaced.

## Skip-condition check

Neither mandatory scout-directive skip condition applies on its face —
this is not a pure bugfix — but the design decision this survey exists
to resolve (the shape split, and how to handle the one skill that is
already partially recipe-conformant) is settled by direct precedent plus
the recipe's own guidance-only instruction: the classification above (5
Shape A, 1 Shape C) and the retention/no-duplication handling for
`pricing-research`'s existing `## Procedure` leave no open choice for
this wave to invent. Scouting is not run as a separate external sweep,
for the same reason the earlier waves gave: the applicable guidance is
this repository's own frozen recipe plus the commit named in the role's
source-allowlist mapping — there is no external field to sweep for
authoring an internal skill file's procedural body, and this wave has no
unresolved shape-classification question left to scout against; the
classification and precedent above **are** the direction-setting
findings this survey exists to produce, and the proposal is drafted
directly from them.
