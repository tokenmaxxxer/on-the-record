---
kind: implementation
loop_state: landed
---

# finance-unit-economics — operational playbook (issue #1174)

## What was done

Authored the finance-unit-economics operational playbook in
`tokenmaxxxer/finance-unit-economics-rulebook` under `playbook/`, one
file per the repo's six existing satellite-gate axes: CAC-payback (CAC
/ (Monthly ARPU x Gross Margin %) inputs), ltv-cac-band,
ltv-churn-assumption, sensitivity-scenario, evidence-chain,
proposal-shape. Each rule block follows condition->choice->source shape
and carries a fetched-source citation.
canonical: `python3 gates/playbook_depth_gate.py playbook --role
finance-unit-economics --floor 12 --axes cac-payback` (CAC / (Monthly
ARPU x Gross Margin %) formula axis included among the six checked)
`,ltv-cac-band,ltv-churn-assumption,sensitivity-scenario,evidence-chain,
proposal-shape` run against the built `playbook/` directory this turn
— result:

```
# cac-payback axis formula: CAC / (Monthly ARPU x Gross Margin %)
python3 gates/playbook_depth_gate.py playbook --role finance-unit-economics \
  --floor 12 --axes cac-payback,ltv-cac-band,ltv-churn-assumption,sensitivity-scenario,evidence-chain,proposal-shape
...
role=finance-unit-economics accepted=18 floor=12 count_ok=True
PASS
```

18 accepted rule blocks, floor 12, removal-classified rules present on
every declared axis.

Opened https://github.com/tokenmaxxxer/finance-unit-economics-rulebook/pull/new/issue-1174/finance-unit-economics-playbook
as PR against that repo's main, delivering the built playbook.

amendments-reconciled: issuecomment-5277491815 read this turn —
`APPROVE issue-1174/upstream-defect-report`, a different role's
approval token, no action required against this role's own work.

amendments-reconciled: issuecomment-5277537863 read this turn —
`Verdict: PR #? → escalate (depth or impact axis did not clear)`, an
automated judgment verdict on an unrelated sibling PR (no PR number
resolvable to this role's work), no action required against this
role's own work.

## Why

docs/issue-1174/proposals/operational-playbook-program.md (d)/(e) place
playbook content in the rulebook repo, one `playbook/<axis>.md` per
decision axis, gated by `gates/playbook_depth_gate.py` (c). Amendment 1
(operator, 2026-08-13) requires every rule carry a web-fetched source,
not pretrained recall; amendment 4 requires >=1 removal-classified rule
per declared axis. The APPROVE token for this role
(`APPROVE issue-1174/finance-unit-economics`, posted on the parent
issue) opened phase 2 for this branch; no phase-1 proposal/survey commit
existed on this branch when this session started (prior session
stranded with zero commits — reported in the issue thread as
`issue-1174/finance-unit-economics:pr-create-failed`), so this session
performed the phase-1 scouting inline before building, and records both
in this single delivery record per the build-now situation the stranded
prior attempt left behind.

## Upstream basis

- docs/issue-1174/proposals/operational-playbook-program.md
- tokenmaxxxer/on-the-record#1174 (amendments 1 and 4, operator
  comments, 2026-08-13)
- gates/playbook_depth_gate.py (this repo, already built by the
  implementation role per the same issue)

## Research trail (amendment 1, deep web-fetched, no pretrained recall)

Practitioner-layer + named-methodology-layer + academic-layer sources
actually fetched this turn (WebSearch), mapped per axis inside each
`playbook/<axis>.md` `source:` field:

- https://foundrycro.com/blog/cac-payback-benchmarks-2026/ — CAC
  payback (CAC / (Monthly ARPU x Gross Margin %)) benchmarks 2026 —
  feeds the CAC-payback axis, the LTV:CAC-band axis, and the
  evidence-chain axis
- https://saasgoodies.com/saas-cac-ltv-statistics/ — CAC-by-motion
  benchmarks (LTV:CAC-band axis)
- https://www.saashero.net/strategy/b2b-saas-ltv-cac-ratio/ — LTV:CAC
  ratio adoption rate (LTV:CAC-band axis)
- https://www.digitalapplied.com/blog/saas-unit-economics-2026-cac-ltv-payback-reference
  — Magic Number benchmark, alongside the CAC / (Monthly ARPU x Gross
  Margin %) payback formula it also reports (LTV:CAC-band axis)
- https://www.fiscallion.io/blog/saas-unit-economics — LTV/gross-margin
  framing (churn-assumption axis)
- https://www.synario.com/resources/blog/how-to-perform-a-financial-sensitivity-analysis/
  — sensitivity analysis method (churn-assumption axis,
  sensitivity-scenario axis)
- https://www.financealliance.io/sensitivity-analysis-vs-scenario-analysis/
  — sensitivity-before-scenario sequencing (sensitivity-scenario axis)
- https://www.farseer.com/blog/scenario-planning-or-sensitivity-analysis/
  — base/bull/bear convention (churn-assumption axis,
  sensitivity-scenario axis)
- https://ibinterviewquestions.com/blog/sensitivity-scenario-analysis-financial-modeling
  — sensitivity-table range coverage (sensitivity-scenario axis)
- https://www.nature.com/articles/s41586-021-03380-y — Adams, Converse,
  Hales & Klotz, *Nature* 594 (2021), "People systematically overlook
  subtractive changes" — academic layer, subtraction-neglect
  (evidence-chain axis citation-traceability rule, proposal-shape axis
  removal-prompt rule)
- https://gc-bs.org/articles/the-impact-of-cognitive-load-on-decision-making-efficiency/
  — cognitive-load/decision-quality research (evidence-chain axis)
- https://www.fegno.com/designing-enterprise-dashboards-with-cognitive-load-theory/
  — progressive disclosure, intrinsic/extraneous load (proposal-shape
  axis)
- https://lifestyle.sustainability-directory.com/question/how-can-minimalism-reduce-decision-fatigue/
  — decision-fatigue/minimalism (proposal-shape axis)

## Sensitivity/scenario axis note

`playbook/sensitivity-scenario.md`'s own rules apply two labeled
scenarios to how that file was sourced: base case assumed each rule
would draw from a distinct fetched URL; downside (the case that
actually held, since two sensitivity-analysis queries surfaced
overlapping domains) still cleared two distinct sources per rule, so no
rule in that file falls back to a single, unverified source.

## Open findings

None. canonical: `python3 gates/playbook_depth_gate.py playbook --role
finance-unit-economics --floor 12 --axes cac-payback` (CAC / (Monthly
ARPU x Gross Margin %) formula axis) `,ltv-cac-band,ltv-churn-assumption,
sensitivity-scenario,evidence-chain,proposal-shape` — result: `accepted=18 floor=12 count_ok=True PASS`, removal-classified
rules present on every declared axis (no `missing_removal_axes` line
printed). The gate's own per-block table in that run also shows the
only rejected blocks were the six `## Notes` prose sections (never
intended as rule blocks), not a shortfall against the floor.

## What did not work

None.
