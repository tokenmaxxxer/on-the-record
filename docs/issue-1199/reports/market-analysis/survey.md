---
subject: issue-1199
role: market-analysis
kind: survey
loop_state: surveyed
---

# Current-state survey: market-analysis rulebook (issue-1199)

canonical: /home/jwjung/tokenmaxxxer/rulebooks/market-analysis-rulebook
(read this session — docs/handbooks/market-analysis-norms.md and the five
market-analysis/plugins/*/README.md files, all outside this working tree
in the separate rulebook repo).

## Where the rulebook lives

Separate repo tokenmaxxxer/market-analysis-rulebook
(/home/jwjung/tokenmaxxxer/rulebooks/market-analysis-rulebook, branch
issue-1174/operational-playbook at HEAD 20f8b2c). This working tree
(on-the-record) holds only this role's phase-1/phase-2 record files
under docs/issue-1199/.

## Write surfaces this role owns in that repo

- docs/handbooks/market-analysis-norms.md — the methodology handbook:
  (a) phase-1 proposal MECE norm, (b) phase-2 deliverable norm
  (five-forces-summary, competitor-list, jtbd-landscape-verdict, evidence
  appendix), (c) spec vocabulary.
- Five plugins, each a PreToolUse shape gate on the phase-1 proposal or
  phase-2 record: mece-proposal (phase-1 structure), evidence-rigor
  (citation presence, both phases), five-forces, competitor-mapping,
  jtbd-fit (each one phase-2 section).

## What the current checklist wording does NOT yet ask for

- five-forces gate: checks a citation exists near each force phrase, but
  not that the citation is dated or that any force carries a quantified
  proxy metric — a verdict can be "high" with only a prose citation, no
  number behind it.
- competitor-mapping gate: checks a citation marker exists per entry, but
  the handbook does not ask for a fixed per-competitor field structure
  (pricing / positioning / why-they-win-or-lose) — entries can be
  freeform prose as long as a link trails them.
- evidence-rigor gate: checks an evidence block/heading exists, but does
  not ask citations to carry an as-of/observed date — a competitor
  pricing-page citation with no date cannot later be told apart from a
  stale one.
- jtbd-fit gate: checks a job statement and a verdict clause exist, but
  the handbook does not require the verdict to rest on more than one
  independent evidence point, or to separate a "users actually prefer it"
  signal from a "users can actually find/reach it" signal.
- mece-proposal gate: checks the "Evidence plan" element is present, but
  the handbook does not ask the plan to name which claims need primary
  vs. secondary sourcing, or how many independent sources per claim.

These five gaps are the targets the scout sweep below checks against.
