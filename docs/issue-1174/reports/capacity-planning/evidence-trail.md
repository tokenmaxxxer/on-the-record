# capacity-planning operational playbook — evidence trail (issue #1174)

## What was done

Authored `playbook/*.md` into the `tokenmaxxxer/capacity-planning-rulebook`
checkout at
`/home/jwjung/tokenmaxxxer/rulebooks/capacity-planning-rulebook/playbook/`,
per the operational-playbook-program proposal section (d): playbook
lands as a top-level content dir peer to the rulebook's existing
plugin dirs, one file per decision axis. README's Layout section
updated to point at it.

derived: `ls /home/jwjung/tokenmaxxxer/rulebooks/capacity-planning-rulebook/playbook/`
```
cost-attribution-at-trigger.md
demand-shape-and-forecast-method.md
expansion-trigger-threshold-sizing.md
headroom-band-and-degradation-risk.md
safety-buffer-sizing-by-criticality.md
```

derived: `grep -c '^[0-9]\+\.' /home/jwjung/tokenmaxxxer/rulebooks/capacity-planning-rulebook/playbook/*.md`
```
cost-attribution-at-trigger.md:10
demand-shape-and-forecast-method.md:9
expansion-trigger-threshold-sizing.md:10
headroom-band-and-degradation-risk.md:10
safety-buffer-sizing-by-criticality.md:10
```

derived: `grep -c '\*\*REMOVAL\*\*' /home/jwjung/tokenmaxxxer/rulebooks/capacity-planning-rulebook/playbook/*.md`
```
cost-attribution-at-trigger.md:2
demand-shape-and-forecast-method.md:2
expansion-trigger-threshold-sizing.md:2
headroom-band-and-degradation-risk.md:2
safety-buffer-sizing-by-criticality.md:2
```

Each axis file exceeds its own `rule_count_floor: 8` and carries >= 2
REMOVAL-classified rules, satisfying amendment 4.

## Decision axes (moderate tier per proposal section (b): N_min = max(8, axes x 2))

- demand-shape-and-forecast-method — classify organic/inorganic/
  seasonal demand shape, pick the forecast method the shape calls for
- expansion-trigger-threshold-sizing — growth_rate x lead_time x
  safety_buffer decomposition, percentile-sized, Little's-Law-derived
- headroom-band-and-degradation-risk — USL-informed band, not a
  snapshot, contention/coherency-aware degradation shape
- safety-buffer-sizing-by-criticality — buffer driven by demand
  variability, lead-time variability, service level, and blast radius
- cost-attribution-at-trigger — incremental cost tied to the firing
  threshold, unit-economic framing, scale-in/cap discipline

Five axes at the moderate tier gives a role-level floor of
max(8, 5*2) = 10 rules total; the count above clears that by a wide
margin. Each axis file records its own `rule_count_floor: 8` in front
matter, following the per-axis-floor convention already used in the
api-design-rulebook exemplar playbook files (read this turn as the
format reference: playbook/error-design.md, playbook/http-semantics.md).

## Why

Issue #1174 requires practitioner-depth operational decision rules
(condition, choice, source) rather than methodology-name pointers,
landed in the role's own rulebook repo. basis: consult-log entry
2026-08-13T04:36:27 ruled the rulebook is the landing location and
spec stays the verification layer. Amendment 4, posted to issue #1174
by the operator on 2026-08-13, made subtraction/removal rules a
required category per axis, not optional.

## Upstream basis

- docs/issue-1174/proposals/operational-playbook-program.md in this
  repo — phase-1 proposal sections (a) N-floor formula, (b) tier
  classification, (c) depth-gate shape, (d) rulebook landing structure
- exemplar playbooks in the checked-out `tokenmaxxxer/api-design-rulebook`
  at `/home/jwjung/tokenmaxxxer/rulebooks/api-design-rulebook/playbook/`

## Research trail (three layers: practitioner, named methodology, academic)

canonical: WebSearch/WebFetch tool calls run this session (sweep +
deepening stages described below); every source listed here was
returned by or fetched through one of those calls this turn. Each
rule's own inline `source:` citation in the playbook files (see the
`ls`/`grep` output above for the file list) carries the specific URL
per rule; this section groups the same sources by research layer.

Practitioner layer:
- Torres et al., "SRE Best Practices for Capacity Management," USENIX
  ;login: Winter 2020 — organic/inorganic demand split, lead-time-aware
  forecast horizon, forecast-vs-actual divergence flagging.
  Source URL: https://sre.google/static/pdf/login_winter20_10_torres.pdf
- FinOps Foundation working group, shared-cost allocation guidance.
  Source URL: https://www.finops.org/wg/identifying-shared-costs/
- FinOps Foundation working group, EC2 autoscaling cost optimization.
  Source URL: https://www.finops.org/wg/cost-optimization-for-aws-ec2-autoscaling/
- usage.ai cloud cost optimization guide (autoscaling cap/scale-in
  discipline).
  Source URL: https://www.usage.ai/blogs/finops/cost-optimization/cloud-cost-optimization-guide/
- espresso.ai, "The FinOps Optimize Phase" (unit-economic cost
  framing, anomaly-threshold remediation).
  Source URL: https://espresso.ai/post/the-finops-optimize-phase-ensuring-cloud-cost-optimization/
- cloudaware.com, cloud cost allocation strategies (tagging/metadata
  attribution).
  Source URL: https://cloudaware.com/blog/most-effective-cloud-cost-allocation-strategies/

Named methodology / theory layer:
- Little's Law (L = lambda W), applied to capacity scaling — Dan
  Slimmon's applied writeup, "Using Little's Law to scale
  applications" (its full URL is the `source:` value on rules 1-3 and
  9-10 in playbook/expansion-trigger-threshold-sizing.md).
- Utilization-threshold behavior under queueing dynamics — Project
  Production Institute.
  Source URL: https://projectproduction.org/journal/littles-law-a-practical-approach-to-understanding-production-system-performance/
- Universal Scalability Law (Gunther), the X(N) equation and its
  alpha/beta terms — Performance Dynamics' "How to Quantify
  Scalability" (its full URL is the `source:` value on all ten rules
  in playbook/headroom-band-and-degradation-risk.md).
- Background on Gunther/USL versus Amdahl's Law framing — Wikipedia,
  "Neil J. Gunther."
  Source URL: https://en.wikipedia.org/wiki/Neil_J._Gunther

Academic / comparative layer:
- Holt-Winters versus ARIMA forecast-method comparison on
  inventory-optimization data, ScienceDirect.
  Source URL: https://www.sciencedirect.com/science/article/pii/S294986352400027X
- Holt-Winters versus ARIMA comparison in food-retail demand
  forecasting, ResearchGate.
  Source URL: https://www.researchgate.net/publication/286314562_Demand_forecasting_in_food_retail_A_comparison_between_the_Holt-Winters_and_ARIMA_models
- Safety-stock formula guide (demand variability, lead-time
  variability, service level as buffer drivers) — Working Capital Hub.
  Source URL: https://www.workingcapitalhub.com/inventory/safety-stock-explained/
- Safety-stock formula selection guide — SPS Commerce.
  Source URL: https://www.spscommerce.com/community/articles/how-to-calculate-safety-stock-formulas-and-methods-that-fit-your-data
- Criticality-weighted spare-parts safety-stock methodology —
  Verusen.
  Source URL: https://verusen.com/spare-parts-management/how-to-calculate-mro-safety-stock/

## Scout protocol note

Sweep stage: five concurrent WebSearch calls, one per decision axis,
in a single turn, per the scout-directive. Deepening stage: three
further WebFetch/WebSearch calls for primary-source detail (the USL
equation, the Little's-Law worked example, and a lookup for a
dedicated Google SRE-book capacity-planning chapter — that lookup
turned up no chapter titled "Capacity Planning" in the SRE book or
workbook tables of contents, so the Torres et al. USENIX piece was
used as the citable practitioner-layer primary source in its place).
Two stages total, under the five-stage/three-minute scout budget;
deepening stopped once further searches stopped changing which rules
would be written.

## kind: playbook-evidence
## loop_state: landed

## What did not work

None.

## Open findings

None open. A counter-example test and a human reviewer spot-check have
not run yet against these playbook files — expected next-step work
under the issue's own Acceptance section, not a defect in this
delivery.

## Next steps

- Run `gates/playbook_depth_gate.py`, once the executing step for
  proposal section (c) lands it in the parent repo, against these five
  files with `--role capacity-planning --floor 8` per axis.
- Wire `roles/specs/capacity-planning.spec.json`'s `playbook_refs`
  pointer per proposal section (e), one entry per axis.
- Have one live capacity-planning session cite a specific rule from
  one of these five files in a real judgment record, per the issue's
  Acceptance check 2.

## Resolution path

Tracked under issue #1174's own completion tracker and Acceptance
checks; no separate issue needed since #1174 already owns this
follow-up work.
