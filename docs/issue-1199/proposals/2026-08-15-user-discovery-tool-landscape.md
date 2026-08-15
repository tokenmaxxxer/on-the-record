---
status: approved
files:
  - docs/issue-1199/reports/user-discovery.md
  - docs/issue-1199/reports/user-discovery/scout-brief.md
  - docs/issue-1199/reports/user-discovery/current-state.md
---

## Intent
Survey the Claude Code plugin/skill ecosystem for the user-discovery
domain, extract adoption-evidenced design moves, and fold them natively
(no tool attribution) into the mounted `user-discovery-rulebook`.

## Constraints stated so far
- Survey target restricted to Claude Code plugins/skills (2026-08-14
  amendment), not general practitioner tools.
- Native application only — no `source:`/tool-catalog text in the
  rulebook itself (2026-08-13 amendment); tool names and evidence live
  only in this repo's record.
- Each learning must name which existing rulebook file/rule it upgrades.

## What will be done
Fold one paraphrased learning into the mounted rulebook repo, on branch
`issue-1199/user-discovery`:

1. **Fatal-assumption-first hypothesis ordering** (paraphrased from
   `guia-matthieu/clawfu-skills`'s `customer-discovery` skill's
   hypothesis-prioritization-matrix move) →
   `playbook/question-design-past-behavior.md` rule 10.
   RICE: Reach 5/5 (fires on every multi-hypothesis discovery study),
   Impact 4/5 (prevents burning saturation budget on a low-risk
   hypothesis while a fatal one goes untested), Confidence 4/5 (direct
   match to the current-state survey's one named gap), Effort 1/5 (one
   paraphrased rule, no restructuring) → score 5×4×4/1 = 80.

A second candidate surfaced during scouting (`wondelai/skills`
`jobs-to-be-done` functional/emotional/social taxonomy) was scored and
left aside — RICE: Reach 3/5, Impact 2/5 (overlaps existing
push/pull/anxiety/habit coverage in `switch-timeline-causal-forces.md`
rather than closing an open gap), Confidence 2/5, Effort 2/5 → score
3×2×2/2 = 6, well below the bar. Only the fatal-assumption-first rule
proceeds.

## Guardrail metrics
Named at this same registration step, distinct from the "worked"
criteria above:
- **`rule_count_floor` non-regression**: `question-design-past-behavior.md`'s
  rule count may not drop below its existing `rule_count_floor` of 8 at
  any point during this delivery — the fold-in only appends, it never
  replaces or removes an existing numbered rule.
- **Zero tool-attribution leakage**: the rulebook diff must not contain
  the string `clawfu`, `guia-matthieu`, `wondelai`, or any `source:`-style
  line naming either surveyed repo — the native-application constraint
  above is a guardrail, not just an intent.

## Hypothesis
We believe folding this paraphrased design move into the rulebook will
improve hypothesis-ordering judgment quality for multi-hypothesis
discovery studies. Metric: `question-design-past-behavior.md`'s rule
count. Threshold 10: the file's rule count must reach 10 (up from its
current 9). Decision rule: go (land the fold-in) if the file's metric
reaches threshold 10 with the guardrails above holding; kill (revert, do
not open the rulebook PR) if the threshold is not reached or a guardrail
breaches.

ITWWS: if this works (the fold-in lands clean, file at 10 rules, no
guardrail breach), future fold-ins on this issue should keep sourcing
candidate rules from direct-domain-match plugin skills scored against
the current-state survey's named gaps, since narrow gap-targeted sourcing
converged in one sweep round here and a second, gap-overlapping
candidate was correctly screened out by RICE scoring rather than folded
in anyway.

## Out of scope
The other five axes (`evidence-strength-tagging.md`,
`follow-up-ladder-depth.md`, `saturation-stopping-rule.md`,
`switch-timeline-causal-forces.md`, `verdict-prevalence-reporting.md`) —
the scout sweep found no unaddressed gap at those axes this round (see
scout brief's Gap line); no rule count regresses below floor regardless.

## How you will know it worked
`question-design-past-behavior.md`'s rule count increases by exactly 1
(10, above the `rule_count_floor` threshold of 8); the rulebook repo
diff carries no tool name/repo URL/`source:` line naming either
surveyed plugin; the rulebook PR is opened against
`tokenmaxxxer/user-discovery-rulebook`; this repo's own record cites the
adoption evidence and the per-tool mapping.

## Approval
Authorized by the `APPROVE issue-1199/user-discovery` comment posted by
JiwonJung94 (approvers.md account) on issue #1199, single-account mode
(author and approver are the same account this session runs under).
canonical: `gh issue view 1199 --comments`, read this session — a
comment body exactly `APPROVE issue-1199/user-discovery`. Proceeding
directly to phase-2 delivery in the same session, following the
implementation role's precedent for this issue (per
`docs/issue-1199/reports/conformance-review.md`, "Rework" section) and
the `product-discovery` role's precedent on this same issue (per
`docs/issue-1199/proposals/2026-08-15-product-discovery-tool-landscape.md`).
