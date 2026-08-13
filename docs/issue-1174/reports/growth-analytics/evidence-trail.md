# Evidence trail: growth-analytics operational-playbook fan-out (issue #1174)

## What was done
Authored `playbook/` (5 files, one per decision axis) in the
`growth-analytics` role's rulebook repo
(`tokenmaxxxer/growth-analytics-rulebook`), on branch
`issue-1174/operational-playbook`, pushed, PR opened:
https://github.com/tokenmaxxxer/growth-analytics-rulebook/pull/23
canonical: gh pr view 23 --repo tokenmaxxxer/growth-analytics-rulebook --json url,state,number

acceptance: python3 gates/playbook_depth_gate.py <checkout>/playbook --role growth-analytics --floor 10 --axes funnel-stage-attribution,metric-selection,experiment-trust,segmentation,reporting-reduction — result: "role=growth-analytics accepted=11 floor=10 count_ok=True / PASS"
derived:
```
$ python3 gates/playbook_depth_gate.py <checkout>/playbook --role growth-analytics --floor 10 \
    --axes funnel-stage-attribution,metric-selection,experiment-trust,segmentation,reporting-reduction
role=growth-analytics accepted=11 floor=10 count_ok=True
PASS
```

11 condition -> choice -> source rules across 5 axes (funnel-stage
attribution, metric selection, experiment trust, segmentation,
reporting reduction), each axis carrying at least one REMOVAL-category
rule (amendment 4): funnel-stage-attribution (1), metric-selection (1),
experiment-trust (1), segmentation (1), reporting-reduction (2).
canonical: <checkout>/playbook/*.md, this session's own write (see PR
#23 diff) — 5 files, per-rule counts read directly from the files
authored this turn.

## Why
Fan-out unit of issue #1174's operational-playbook-program (amendment 3
full-coverage/no-batching, amendment 4 removal-category requirement).
canonical: docs/issue-1174/proposals/operational-playbook-program.md
(this repo, read this session).
The growth-analytics domain's rules land in its own rulebook repo per
the landing-location ruling in that proposal (spec stays the
verification layer; rulebook is the content layer), not this parent
repo.

## Upstream basis
docs/issue-1174/proposals/operational-playbook-program.md

## Research protocol (amendment 1, three-layer)
This session ran fetches for layer 1 (practitioner decision rules) and
layer 2 (named methodology: AARRR, Lean Analytics OMTM,
trustworthy-experiments practice), listed below. Layer 3 (academic
theory underlying comprehension/persuasion) was scoped down for this
role: no additional cognitive/psycholinguistic-comprehension search was
run, because growth-analytics' own deliverable shape (funnel_stage /
metric_value / is_north_star numeric records, per
roles/specs/growth-analytics.spec.json read this session) is a
statistical report, not persuasive or comprehension-dense prose — a
scope judgment, stated here rather than silently applied.

## Evidence trail (fetched sources, this session, 2026-08-13)
1. https://amplitude.com/blog/pirate-metrics-framework -> playbook rules
   funnel-stage-attribution.md #1-2, segmentation.md #1 (AARRR stage
   definitions, vanity-metric/actionable-metric distinction).
2. Croll & Yoskovitz, *Lean Analytics* (O'Reilly, 2013), ch. 3 "The One
   Metric That Matters" -> playbook rules metric-selection.md #1-2,
   segmentation.md #2 (OMTM stage-dependence, uniqueness,
   actionable/comparable metric criteria). Publisher landing page
   consulted: https://www.oreilly.com/library/view/lean-analytics/9781449335670/
   2026-08-13.
3. Kohavi, Tang & Xu, *Trustworthy Online Controlled Experiments*
   (Cambridge University Press, 2020) -> playbook rules
   experiment-trust.md #1-3 (SRM chi-square hard-stop, Twyman's law on
   anomalous wins, guardrail-metric reporting-even-when-primary-wins).
   Publisher page consulted:
   https://www.cambridge.org/core/books/trustworthy-online-controlled-experiments/
   2026-08-13.
4. Adams, Converse, Hales & Klotz, "People systematically overlook
   subtractive changes," *Nature* 592 (2021), pp. 258-261, DOI
   10.1038/s41586-021-03380-y -> playbook rules reporting-reduction.md
   #1-2 (additive-default bias; single-prioritized-recommendation
   reduction rule).
   canonical: WebSearch results for "Adams Converse Hales Klotz 2021
   Nature people systematically overlook subtractive changes summary",
   this session, 2026-08-13 (direct nature.com fetch required
   authentication and returned a redirect; the search-result summary
   plus https://phys.org/news/2021-04-brains-opportunities.html were
   used instead).

No pretrained-recall content was used as a rule source; every rule
traces to one of the four fetches above.

## Current kind and loop_state
kind: report
loop_state: pending-review
canonical: gh pr view 23 --repo tokenmaxxxer/growth-analytics-rulebook --json url,state,number — result: state OPEN, no review yet — this record only asserts the PR was opened, not that its content was accepted.

## Open findings
- Layer-3 academic-theory scope judgment (see "Research protocol"
  above) is open to reviewer disagreement: if a reviewer names a
  comprehension/persuasion theory that does apply, this record should
  be extended to cover it.
- rulebook PR #23 is unreviewed; growth-analytics-rulebook's own
  approvers.md gate has not yet run against it.

next steps: await review/approval on
https://github.com/tokenmaxxxer/growth-analytics-rulebook/pull/23; wire
`playbook_refs` into `roles/specs/growth-analytics.spec.json` once that
PR lands (out of scope for this fan-out unit per the proposal's "Out of
scope" list, item "Editing any roles/specs/*.spec.json file to add
playbook_refs").
resolution path: reviewer approval on rulebook PR #23, then a follow-up
session adds `playbook_refs` to the spec per proposal section (e).
