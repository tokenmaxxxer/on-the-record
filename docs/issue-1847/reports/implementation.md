---
subject: issue-1847
code_under_review:
  - skills/pricing-design-rigor/SKILL.md
  - skills/pricing-method-family/SKILL.md
  - skills/pricing-research/SKILL.md
  - skills/pricing-scope-gate/SKILL.md
  - skills/pricing-tier-structure/SKILL.md
  - skills/pricing-verdict-report/SKILL.md
  - scripts/procedure_authored_skills.txt
loop_state: landed
type: implementation
breaking: false
verdict: pass
---

# Implementation record: pricing family (wave 2h)

## What was done

Applied the frozen wave recipe (docs/issue-1790/reports/implementation.md
WAVE RECIPE section) to all 6 `pricing-*` skills in
`tokenmaxxxer/skill-repository`, per the approved proposal
(docs/issue-1847/proposals/2026-08-21-wave-2h-pricing.md), from a fresh
checkout at `/tmp/skill-repository-1847`:

- 5 Shape-A skills (`pricing-design-rigor`, `pricing-method-family`,
  `pricing-scope-gate`, `pricing-tier-structure`, `pricing-verdict-report`):
  inserted `## Trigger` / `## Procedure` / `## Output shape` between each
  file's framing paragraph and its existing `## Decision rules` heading,
  with `## Procedure` citing that file's own numbered rules by number.
  Each `description:` frontmatter field was rewritten from the newly
  authored `## Trigger` text, keeping the checker's trigger-marker
  substring ("use when"/"use whenever").
- 1 Shape-C skill (`pricing-research`): inserted only `## Trigger` (before
  its existing content, derived from its own pre-existing block-scalar
  `description:`) and `## Output shape` (near its existing `## Report
  format` section) — its existing `## Procedure` section (a 6-step Van
  Westendorp/CBC routing method) was left byte-for-byte untouched, per
  the proposal's partial-insertion plan for this shape.
- `scripts/procedure_authored_skills.txt` extended with the 6 new names,
  appended after the existing 66 entries.

canonical: `/tmp/skill-repository-1847` git log, read live — commit
`6861644` ("Author procedural bodies for wave 2h: pricing family
(issue-1847)"), on branch `issue-1847-wave-2h-pricing`, pushed and
delivered as skill-repository PR
https://github.com/tokenmaxxxer/skill-repository/pull/17 (state: OPEN,
+212/-5, 7 files changed).

## Why

Delivering the phase-1 proposal approved via the issue-comment
`APPROVE issue-1847/implementation` gate (single-account mode). basis:
docs/issue-1847/proposals/2026-08-21-wave-2h-pricing.md.

## Upstream / basis

basis: docs/issue-1847/proposals/2026-08-21-wave-2h-pricing.md (approved
phase-1 proposal), itself built from
docs/issue-1847/reports/implementation/survey.md and the frozen recipe at
docs/issue-1790/reports/implementation.md.

## Acceptance checks — all four, executed live from the skill-repository checkout

canonical: commands run directly in `/tmp/skill-repository-1847` this
session, pasted verbatim below.

**(a) Manifest-scoped conformance check**

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
EXIT: 0
```

**(b) Rule-retention sweep** — every pre-existing rule/content line
retained; the only deletions across all 6 files are the 5 intentional
Shape-A `description:` line rewrites (one line removed, one line added,
per Shape-A file), and `pricing-research` has zero deletions:

```
$ git diff HEAD~1 HEAD -- skills/pricing-*/SKILL.md | grep -n '^-' | grep -v '^--- '
3:--- a/skills/pricing-design-rigor/SKILL.md
8:-description: Use when you need guidance on Design-rigor decision rules. Applies to the design-rigor axis.
62:--- a/skills/pricing-method-family/SKILL.md
67:-description: Use when you need guidance on Method-family selection decision rules. Applies to the method-family-selection axis.
120:--- a/skills/pricing-research/SKILL.md
158:--- a/skills/pricing-scope-gate/SKILL.md
163:-description: Use when you need guidance on Scope-gate decision rules. Applies to the scope-gate axis.
211:--- a/skills/pricing-tier-structure/SKILL.md
216:-description: Use when you need guidance on Tier-structure decision rules. Applies to the tier-structure axis.
261:--- a/skills/pricing-verdict-report/SKILL.md
266:-description: Use when you need guidance on Verdict-assembly decision rules. Applies to the verdict-assembly axis.
```

(the `---` lines above are diff file headers, not content deletions;
`pricing-research`'s file header appears at line 120 with no
`-description` or other content-deletion line under it. canonical:
`git diff HEAD~1 HEAD -- skills/pricing-research/SKILL.md`, pasted in
full, read live, immediately below — it shows only two `+`-hunks and
zero `-` content lines.)

```
$ git diff HEAD~1 HEAD -- skills/pricing-research/SKILL.md
diff --git a/skills/pricing-research/SKILL.md b/skills/pricing-research/SKILL.md
index 1e74b66..6afcc3d 100644
--- a/skills/pricing-research/SKILL.md
+++ b/skills/pricing-research/SKILL.md
@@ -16,6 +16,16 @@ description: >-
 
 # Pricing Research (Willingness to Pay)
 
+## Trigger
+
+Use whenever someone needs to set, test, or audit a price or price range
+for a defined product, or is about to pick a pricing method, design one,
+or hand off pricing numbers as if they answer a question the method
+didn't collect data for. Do NOT use for competitor pricing (route to
+`market-recon`), for pricing decisions with no enumerable product yet
+(too early), or for general market-sizing questions with no price
+variable at their center.
+
 ## First: does this even need the procedure?
 
 Run this gate before touching any method — the whole point of this skill is matching the method
@@ -240,6 +250,16 @@ revenue optimum"; OPP is never reported as "the optimal price." The residual lis
 questions the chosen method structurally cannot answer (for PSM: any revenue/volume/profit question;
 for CBC: unit volume and profit without external market-size and cost inputs).
 
+## Output shape
+
+Applying this skill produces a six-element report per pricing study: the
+scope-gate result, the input the decision needed and the method chosen
+for it, the conjoint family named where relevant, the design parameters
+and their gate band, the incentive-alignment decision and its cost, and
+the final numbers with correctly scoped labels plus the residual list of
+what the method cannot answer. See `## Report format` below for the full
+per-step layout and the high-stakes/directional weighting rule.
+
 ## Report format
 
 Report, per pricing study:
```

Manifest tail, confirming incremental append of all 6 names after the
pre-existing 66 entries:

```
$ tail -8 scripts/procedure_authored_skills.txt
ux-engineering-research-log
ux-engineering-surface-contrast
pricing-design-rigor
pricing-method-family
pricing-research
pricing-scope-gate
pricing-tier-structure
pricing-verdict-report
```

**(c) `git diff --stat` scoped to the 6 skill paths + manifest**

```
$ git diff --stat HEAD~1 HEAD -- skills/pricing-*/SKILL.md scripts/procedure_authored_skills.txt
 scripts/procedure_authored_skills.txt  |  6 +++++
 skills/pricing-design-rigor/SKILL.md   | 42 +++++++++++++++++++++++++++++++++-
 skills/pricing-method-family/SKILL.md  | 41 ++++++++++++++++++++++++++++++++-
 skills/pricing-research/SKILL.md       | 20 ++++++++++++++++
 skills/pricing-scope-gate/SKILL.md     | 36 ++++++++++++++++++++++++++++-
 skills/pricing-tier-structure/SKILL.md | 33 +++++++++++++++++++++++++-
 skills/pricing-verdict-report/SKILL.md | 39 ++++++++++++++++++++++++++++++-
 7 files changed, 212 insertions(+), 5 deletions(-)
```

**(d) Full-tree conformance check (no manifest flag)**

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
EXIT: 0
```

`git diff --stat` over the whole commit (`HEAD~1 HEAD`, no path filter)
is identical to (c) above, confirming no path outside the 6 skill files
+ manifest was touched:

```
$ git diff --stat HEAD~1 HEAD
 scripts/procedure_authored_skills.txt  |  6 +++++
 skills/pricing-design-rigor/SKILL.md   | 42 +++++++++++++++++++++++++++++++++-
 skills/pricing-method-family/SKILL.md  | 41 ++++++++++++++++++++++++++++++++-
 skills/pricing-research/SKILL.md       | 20 ++++++++++++++++
 skills/pricing-scope-gate/SKILL.md     | 36 ++++++++++++++++++++++++++++-
 skills/pricing-tier-structure/SKILL.md | 33 +++++++++++++++++++++++++-
 skills/pricing-verdict-report/SKILL.md | 39 ++++++++++++++++++++++++++++++-
 7 files changed, 212 insertions(+), 5 deletions(-)
```

acceptance: All 6 pricing-* skills have the three sections, derived
descriptions, and every pre-existing rule line retained; manifest +
full-tree checker both exit 0 — result: met, canonical: outputs (a)/(d)
above, both `EXIT: 0`, executed live this session directly against
`/tmp/skill-repository-1847`.

acceptance: No path outside the 6 family skills + manifest is touched in
the skill-repository PR — result: met, canonical: `git diff --stat`
outputs (c) and the unfiltered `HEAD~1 HEAD` diff above, both listing
exactly the same 7 paths, executed live this session.

## Doc-placement ladder

- [x] proposal: `docs/issue-1847/proposals/2026-08-21-wave-2h-pricing.md` (phase 1, landed via PR #1850)
- [x] survey: `docs/issue-1847/reports/implementation/survey.md` (phase 1, landed via PR #1850)
- [x] record: this file (phase 2)
- [x] delivery: skill-repository PR https://github.com/tokenmaxxxer/skill-repository/pull/17 (external deliverable, 7 paths: 6 SKILL.md + manifest)

## What did not work

None. canonical: acceptance checks (a)-(d) above, all executed live this
session against `/tmp/skill-repository-1847` and all passing on the
first run (both conformance checks exit 0, the diff-stat scope matches
exactly, and the rule-retention diff above shows zero unintended
content loss) — no rework was needed.

## Open findings

None discovered during this delivery. The issue body's own stale
"pricing (10 skills)" Program-context wording (vs. the title/Requirement
1/live-checkout's 6) was already flagged as a non-actionable note in the
phase-1 survey (docs/issue-1847/reports/implementation/survey.md) and is
not repeated here as a new finding.

## loop_state

landed
