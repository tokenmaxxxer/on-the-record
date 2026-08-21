# Current-state survey — issue-1896, brand-design procedural-body wave

subject: issue-1896

## Checkout basis

canonical: `/tmp/skill-repository` fetched and checked out at
`origin/main` = commit `4ec5882` ("Author procedural bodies for wave
2a: capacity-planning family (issue-1884) (#29)") — the same commit the
role-source-allowlist mapping cited. Working branch created off that
commit: `issue-1896-wave2a-brand-design`.

## The 5 brand-design skills

```
$ ls skills | grep ^brand-design-
brand-design-brand-consistency-governance
brand-design-brand-identity-strategy
brand-design-color-visibility
brand-design-logo-clear-space-size
brand-design-typography-pairing
```

## Shape classification (Shape A = no existing Trigger/Procedure/Output
shape headings; Shape B = already procedure-shaped, no-op candidate)

canonical: `grep -n "^## \|^### " skills/brand-design-*/SKILL.md` and
per-file `grep -c` rule/source counts, both executed live during this
survey (table below).
| skill | heading(s) found | rule headers (`### N.`) | source lines |
|---|---|---|---|
| brand-design-brand-consistency-governance | `## Decision rules` | 3 | 3 |
| brand-design-brand-identity-strategy | `## Decision rules` | 3 | 3 |
| brand-design-color-visibility | `## Decision rules` | 3 | 3 |
| brand-design-logo-clear-space-size | `## Decision rules` | 3 | 3 |
| brand-design-typography-pairing | `## Decision rules` | 3 | 3 |

All 5 are **Shape A** — each file has exactly one structural heading,
`## Decision rules`, with no `## Trigger`, `## Procedure`, or
`## Output shape` present (per the table above). Total: 15 numbered
rules across the 5 files, all with a `**Source**:` citation line (0
missing, unlike the localization wave's 2 files with a lower
source-count than rule-count).

## Rule citation convention

canonical: `skills/brand-design-color-visibility/SKILL.md` read live
(rules 1-3, lines 17-31). Rules are headed `### N. <title>` under
`## Decision rules` (not the localization wave's `1. **when** ...
**choose** ...` inline-numbered paragraph style). Each rule block
carries `**Condition**`, `**Choice**`, `**Why**`, `**Source**`, and
`**Counter-example test**` sub-bullets.

canonical: `scripts/procedure_authored_skills.txt` read live, and
`grep -l "^## Decision rules" skills/*/SKILL.md` executed live during
this survey. This is the same `### N.` + Decision-rules convention
already used by the `legal-compliance-*`, `finance-unit-economics-*`,
`partnerships-bd-*`, and `pricing-*` families, all of which are already
listed in `scripts/procedure_authored_skills.txt` (authored in prior
waves).

canonical: `skills/legal-compliance-vendor-dpa/SKILL.md` (already
authored, lines 1-45) read live to confirm the citation pattern — its
`## Procedure` step 1 reads "Require a signed DPA covering all eight
Art 28(3) topics before data flows to any vendor handling personal data
(rule 1)." citing the `### 1.` heading number directly, exactly the
citation form this wave will reuse.

## `procedure_authored_skills.txt` current tail

canonical: `scripts/procedure_authored_skills.txt` read live — current
last 5 entries are the localization family
(`localization-locale-convention-formatting` through
`localization-text-expansion-and-layout`); no `brand-design-*` entry
present yet. All 5 brand-design names are absent, confirming none of
the 5 has been authored in any prior wave.

## Checker script

canonical: `find . -maxdepth 2 -name "*.py"` executed live — only
`scripts/check_skill_conformance.py` and
`scripts/normalize_skill_frontmatter.py` present; no other checker
script found. No checker-logic change is in scope for this wave (issue
non-goal).

## Frozen recipe basis

canonical: `docs/issue-1790/reports/implementation.md`, `## WAVE
RECIPE` section, read live — the 5-step authoring pattern (check for
existing headings; insert Trigger/Procedure/Output shape; rewrite
`description:` from Trigger; append to the manifest; run both checker
modes + the rule-retention sweep) and the four required checks (manifest
run, sweep, scoped `git diff --stat`, full-tree run) are applied
verbatim.

canonical: `docs/issue-1892/proposals/localization-wave2a.md` read live
as the most recent precedent, matching the localization wave's own
reuse of the same recipe.

## No-op check

canonical: shape-classification table above (this survey, executed
live). None of the 5 skills is already procedure-shaped — all 5 require
authoring; no no-op empty-state applies to this wave.
