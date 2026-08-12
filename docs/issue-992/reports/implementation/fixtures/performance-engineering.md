Subject: issue-992

# Live-fire seed tasks — performance-engineering (`performance` axis)

Per `docs/handbooks/architecture-methodology.md`'s new
"Axis evaluation procedure — performance" section.

## Fixture 1 — error-budget recomputation disagrees with asserted figure

Hypothetical performance-engineering record under test:

```
sli: "p99 latency, checkout API"
slo_target: "300ms p99, 30-day window"
measured p99 over the window: 340ms
asserted error_budget_remaining: "12% remaining"
asserted verdict: within-budget
```

- Generic reasoning: the record already states a remaining-budget
  percentage and a verdict field, take both at face value -> supports.
- Methodology-correct (EXECUTE step 2, recompute error_budget_remaining
  from the current sli measurement against slo_target per the SRE
  Workbook's error-budget-policy formula): a measured p99 above the
  slo_target for the window means the budget is exhausted for that
  window, not 12% remaining as asserted — the asserted figure does not
  follow from the cited measurement. Axis verdict: contradicts —
  `finding.required_fix`: recompute error_budget_remaining from the
  actual measured window and correct the verdict field to match.

Divergence: face-value acceptance of the asserted fields reaches
"supports"; recomputing from the cited raw measurement reaches
"contradicts" on the same inputs.

## Fixture 2 — unresolvable SLI reference

Hypothetical performance-engineering record under test:

```
sli: "overall system speed"
slo_target: "fast enough"
verdict: within-budget
```

- Generic reasoning: the record names an SLI and SLO and states a
  verdict, treat it as a normal filled-in entry -> supports.
- Methodology-correct (EXECUTE step 1, sli must resolve to an actual
  monitored, queryable metric per the SRE Workbook's SLO-implementation
  chapter): "overall system speed" and "fast enough" name no queryable
  metric or numeric target at all. Axis verdict: contradicts —
  `finding.required_fix`: replace both fields with a specific monitored
  SLI (e.g. a named percentile-latency metric) and a numeric target
  with an explicit measurement window.

Divergence: the entry has the right shape (all fields present) and a
generic completeness check would accept it; the methodology's
metric-resolution requirement rejects it because neither field names
anything measurable.
