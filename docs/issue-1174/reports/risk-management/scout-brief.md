---
name: risk-management-playbook-scout-brief
---

# Scout brief — risk-management operational playbook (issue #1174 fan-out)

Mode: batched-sequential WebSearch (5 calls, one per axis candidate) in
one turn — no parallel-subagent fan-out used for the sweep stage; single
round, judgment applied after.

## Decision axes (moderate tier per operational-playbook-program.md (b);
rulebook already owns ISO 31000 process-shape + register-schema
methodology, so axes below are the *operational* layer on top of that,
not a restatement of it)

1. `likelihood-impact-scale` — how to calibrate a qualitative/numeric
   likelihood x impact rating band so scores are comparable across
   raters.
2. `response-strategy-selection` — avoid/mitigate/transfer/accept
   choice by risk score + cost-of-control.
3. `appetite-tolerance-threshold` — how appetite (entity-level) breaks
   into category/objective-level tolerance thresholds.
4. `monitoring-review-cadence` — review frequency by risk score and
   velocity.
5. `aggregation-consolidation` — correlated/concentrated risk handling
   and register pruning (removal-heavy axis).

rule_count_floor: max(8, 5x2) = 10 (moderate tier). Delivered: 15 rules
(3/axis), >=1 removal-classified rule per axis.

## Must-bes / performance axes extracted

- 5-level likelihood and 5-level impact bands are the de facto standard
  shape (rare/unlikely/possible/likely/almost-certain x
  negligible/minor/moderate/major/severe), score = L x I, color-banded
  into low/moderate/high/extreme zones.
- Response choice is cost-of-control-driven, not severity-alone: high
  L x I -> avoid/mitigate; low L x I -> accept; the deciding test in
  practice is "does mitigation cost exceed the value at risk."
- COSO distinguishes appetite (entity-level, strategic) from tolerance
  (objective-level, operational) — tolerance is appetite decomposed per
  category/objective, not a separate number invented independently.
- Review cadence tracks risk score AND velocity, not score alone — a
  fast-materializing risk gets shortened cadence even at a moderate
  score.
- Aggregation is not simple summation once risks correlate — positively
  correlated risks concentrate; register hygiene (duplicate/stale entry
  retirement) is a named, separate practice from aggregation.

## Adopt / skip

- Adopt: score = L x I with named 5-band scales (traceable, checkable
  by a reviewer) over unstructured/verbal-only risk severity language.
- Adopt: cadence keyed to both score and velocity (two inputs), per
  sbnsoftware.com and wolterskluwer.com sources below.
- Skip: inventing a numeric risk-appetite formula — sourced material
  (wolterskluwer.com, quantivate.com) frames appetite-setting as a
  governance/board judgment input, not a formula.

## Gap line

Existing rulebook methodology (ISO 31000 process clauses,
ISO-31000-derived register schema) already covers *document shape*; it
names none of the above five operational calibration/selection/cadence/
aggregation rules at decision-rule granularity — this is the gap the
playbook fills, not a restatement of the existing plugin methodology.

## Sources

- https://mindsetcyber.com.au/iso-31000-risk-matrix/
- https://risguard.com/en/create-a-risk-matrix/
- https://internalauditor.theiia.org/en/articles/2022/february/risk-acceptance/
- https://twproject.com/blog/risk-response-strategies-mitigation-transfer-avoidance-acceptance/
- https://decobeconsulting.com/risk-response-strategies-avoid-mitigate-transfer-or-accept/
- https://www.wolterskluwer.com/en/expert-insights/risk-appetite-and-risk-tolerance-whats-the-difference
- https://quantivate.com/developing-risk-appetite-and-tolerances/
- https://sbnsoftware.com/blog/how-often-should-risk-assessments-be-reviewed-and-updated/
- https://www.wolterskluwer.com/en/expert-insights/what-is-risk-velocity-and-should-you-track-it
- https://www.britannica.com/money/concentration-risk-management
- https://fastercapital.com/content/Risk-Aggregation-Data--How-to-Aggregate-and-Consolidate-Your-Risk-Data-across-Different-Sources-and-Dimensions.html
