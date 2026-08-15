---
status: proposed
files:
  - docs/issue-1199/reports/pricing/survey.md
  - docs/issue-1199/reports/pricing/scout-brief.md
  - docs/issue-1199/reports/pricing.md
---

# issue-1199 (pricing): Claude Code plugin tool-landscape fold-in

scope-gate result: proceed

inputs needed: none of these

(No quantity/purchase-intent/cost input is being collected — this is a
rulebook tool-landscape fold-in for issue #1199, not a product pricing
decision, so no research method or family is being fielded.)

## Intent

Survey the most-adopted Claude Code plugins/skills in the pricing domain
and fold what they solve — natively, with no tool attribution in
rulebook text — into `tokenmaxxxer/pricing-rulebook` as new decision
judgment, per issue #1199's 2026-08-14 plugin-ecosystem amendment and
2026-08-13 native-application amendment.

## Constraints

- Survey target restricted to Claude Code plugins/skills (not general
  domain tools); adoption evidence via the tech-feasibility
  stars/downloads/multi-source method.
- Fold-in must be bounded (no tool catalog), each learning traceable to
  a surveyed tool in the phase-1 survey/scout-brief, and no `source:`
  line in the rulebook may name the surveyed Claude Code
  tool/repo/marketplace itself.
- Rulebook edits land in the separate `pricing-rulebook` repo, on its
  own branch, per the sibling finance-unit-economics execution.

## What will be done

Two learnings, both traced in
`docs/issue-1199/reports/pricing/survey.md` and
`docs/issue-1199/reports/pricing/scout-brief.md`:

1. New file `playbook/tier-structure.md` in the rulebook: a checkable
   value-metric validity test, and Good-Better-Best anchor/decoy tier
   assembly — closing the gap that this role's own PRODUCES line names
   "tier structure" as an output while no existing rulebook file has a
   rule about assembling one.
2. One added rule to `playbook/scope-gate.md`: operationalize the
   currently-undefined "decision's shelf life" in existing rule 2 with
   a concrete revisit-cadence test.

## Out of scope

Pricing-page teardown/AI-readability audits and price-increase-signal
checklists surfaced by the survey — real capabilities in the surveyed
skill, but outside this chain's scope (verdict + tier structure +
rationale, not an ongoing page/GTM audit).

## Verdict-report fields (n/a-with-reason)

This proposal is rulebook-tooling work (a tool-landscape survey and two
native rule additions), not a priced-product pricing verdict, so the
chain's six-element verdict fields are stated n/a-with-reason rather
than fabricated:

- method / family: n/a — no WTP method was fielded this cycle.
- what it collects / what it cannot answer: n/a — no study ran.
- labeled-numbers: n/a — no verdict numbers are produced by this
  proposal; the only quantitative figures in this record are GitHub
  adoption-evidence star counts (44,320 and 1,247), each already
  labeled by source and verified via `gh api` in
  `docs/issue-1199/reports/pricing/survey.md`, not pricing-verdict
  numbers.
- residual list: n/a — this proposal produces no pricing verdict to
  carry a residual; the resulting rulebook rules apply prospectively to
  future pricing verdicts fielded through this chain.

## How you'll know it worked

- `docs/issue-1199/reports/pricing/survey.md` and `scout-brief.md`
  exist with fetched-source citations and verified adoption evidence
  (`gh api` star counts, not marketplace-page claims alone).
- `pricing-rulebook` gains the two rule additions described above, no
  rule text names a Claude Code tool/repo, and `docs/issue-1199/reports/pricing.md`
  records the applied rules and their upstream basis.
