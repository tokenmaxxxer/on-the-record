---
status: approved
files:
  - docs/issue-1199/reports/product-discovery.md
  - docs/issue-1199/reports/product-discovery/scout-brief.md
  - docs/issue-1199/reports/product-discovery/current-state.md
---

## Intent
Survey the Claude Code plugin/skill ecosystem for the product-discovery
domain, extract adoption-evidenced design moves, and fold them natively
(no tool attribution) into the mounted `product-discovery-rulebook`.

## Constraints stated so far
- Survey target restricted to Claude Code plugins/skills (2026-08-14
  amendment), not general practitioner tools.
- Native application only — no `source:`/tool-catalog text in the
  rulebook itself (2026-08-13 amendment); tool names and evidence live
  only in this repo's record.
- Each learning must name which existing rulebook file/rule it upgrades.

## What will be done
Fold two paraphrased learnings, evaluated as two candidate opportunities
and scored below, into the mounted rulebook repo, on branch
`issue-1199/product-discovery`:

1. **Risk-ranked assumption ordering with a named next-experiment**
   (paraphrased from `phuryn/pm-skills`' `prioritize-assumptions`
   skill) → `playbook/hypothesis-preregistration.md` rule 11.
   RICE: Reach 5/5 (every registered hypothesis passes through this
   ordering step), Impact 4/5 (prevents deferring the plan's riskiest
   assumption), Confidence 4/5 (direct match to an existing rulebook
   gap, per the current-state survey), Effort 1/5 (one paraphrased
   rule, no restructuring) → score 5×4×4/1 = 80.
2. **Learning-value-per-experiment-cost ordering among sibling solution
   branches** (paraphrased from `deanpeters/Product-Manager-Skills`'
   `opportunity-solution-tree` skill) →
   `playbook/opportunity-solution-tree-branching.md` rule 11.
   RICE: Reach 3/5 (only fires once an opportunity already has 2+
   candidate solutions), Impact 4/5 (stops size-biased test selection),
   Confidence 4/5, Effort 1/5 → score 3×4×4/1 = 48.

Both clear the bar (Reach/Impact/Confidence all ≥3, Effort ≤2) and are
both applied — this is a fold-in, not a single-pick prioritization
decision, so both proceed rather than only the higher-scored one.

## Guardrail metrics
Named at this same registration step, distinct from the "worked"
criteria above:
- **`rule_count_floor` non-regression**: neither target playbook file's
  rule count may drop below its existing `rule_count_floor` threshold
  of 10 at any point during this delivery — the fold-in only appends,
  it never replaces or removes an existing numbered rule.
- **Zero tool-attribution leakage**: the rulebook diff must not contain
  the string `phuryn`, `pm-skills`, `deanpeters`, `Product-Manager-Skills`,
  or any `source:`-style line naming either surveyed repo — the
  native-application constraint above is a guardrail, not just an
  intent, so a violation here voids the delivery even if both rules
  otherwise read well.

## Hypothesis
We believe folding these two paraphrased design moves into the
rulebook will improve tie-breaking judgment quality at the two named
axes. Metric: rulebook rule count at the two target files. Threshold
11: each file's rule count must reach 11 (up from its current 10).
Decision rule: go (land the fold-in) if both files' metric reaches
threshold 11 with the guardrails above holding; kill (revert, do not
open the rulebook PR) if either target file's rule count fails to
reach the 11 threshold or a guardrail breaches.

ITWWS: if this works (the fold-in lands clean, both files at 11 rules,
no guardrail breach), the next per-role fold-in units on this issue
should keep sourcing candidate rules from direct-domain-match plugin
skills (RICE-scored against the current-state survey's named gaps)
rather than a broader tool sweep, since narrow gap-targeted sourcing
converged in one sweep round here.

## Out of scope
The other three axes (`guardrail-metric-status.md`,
`jtbd-problem-framing.md`, `rice-ice-prioritization.md`) — the scout
sweep found no unaddressed gap at those axes this round (see scout
brief's Gap line); no rule count regresses below the 10 floor
regardless.

## How you will know it worked
Both target files' rule counts increase by exactly 1 (11 each, above
the `rule_count_floor` threshold of 10); the rulebook repo diff carries
no tool name/repo URL/`source:` line naming either surveyed plugin;
the rulebook PR is opened against `tokenmaxxxer/product-discovery-rulebook`;
this repo's own record cites the adoption evidence and per-tool mapping.

## Approval
Authorized by the `APPROVE issue-1199/product-discovery` comment posted
by JiwonJung94 (approvers.md account) on issue #1199, single-account
mode (author and approver are the same account this session runs
under). canonical: `gh issue view 1199 --repo tokenmaxxxer/on-the-record
--json comments`, read this session — two matching comments,
2026-08-13T07:37:02Z and 2026-08-15T02:12:01Z. Proceeding directly to
phase-2 delivery in the same session, following the implementation
role's precedent for this issue (per
`docs/issue-1199/reports/conformance-review.md`, "Rework" section,
citing implementation commit 1bc41d13, read this session).
