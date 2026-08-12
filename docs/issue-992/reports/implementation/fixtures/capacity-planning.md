Subject: issue-992

# Live-fire seed tasks — capacity-planning (`external_burden` axis)

Per `docs/handbooks/architecture-methodology.md`'s new
"Axis evaluation procedure — external_burden" section.

## Fixture 1 — recomputation catches an asserted verdict mismatch

Hypothetical capacity-planning record under test:

```
resource: "checkout-queue"
demand_forecast: "1200 req/min peak"
capacity_threshold: "1000 req/min"
verdict: within-capacity
```

- Generic reasoning: the record states a verdict field explicitly, take
  it at face value -> supports.
- Methodology-correct (EXECUTE step 2, recompute verdict from
  demand_forecast vs. capacity_threshold rather than accepting the
  asserted field): 1200 exceeds 1000, so the recomputed verdict is
  over-capacity, not within-capacity as asserted. Axis verdict:
  contradicts — `finding.required_fix`: correct the asserted verdict
  field to match the recomputation, or revise the forecast/threshold if
  either input was mistyped.

Divergence: taking the asserted field at face value reaches "supports";
recomputing the ITIL forecast-vs-threshold relationship reaches
"contradicts" on the same numbers.

## Fixture 2 — new demand source not accounted for

Hypothetical scenario: the reviewed artifact adds a new scheduled batch
job that queries the "checkout-queue" resource every 5 minutes. The
capacity-planning record's `demand_forecast` field cites only the
pre-existing interactive traffic pattern, dated before the batch job was
added to the codebase.

- Generic reasoning: a capacity-planning record already exists for this
  resource, so the axis check has something to point at -> supports.
- Methodology-correct (EXECUTE step 3, check whether the artifact under
  review is itself a source of new demand and whether the forecast
  accounts for it): the new batch job is a new demand source the cited
  forecast predates and does not mention. Axis verdict: contradicts —
  `finding.required_fix`: name the new batch-job demand and require an
  updated forecast that includes it before the resource is treated as
  covered.

Divergence: a generic check only verifies a record is present and stops
there; the methodology requires checking whether *this specific change*
is reflected in that record's own forecast, which it is not.
