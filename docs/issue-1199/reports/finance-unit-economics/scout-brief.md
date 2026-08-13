---
subject: issue-1199
role: finance-unit-economics
kind: scout-brief
---

# issue-1199 (finance-unit-economics): tool-landscape scout brief

Mode: one foreground research agent ran the four search angles below as
genuine WebSearch/WebFetch queries (batched-sequential fallback inside
that agent, not orchestrator-level parallel dispatch — stated per the
scout directive's fallback-disclosure rule); one sweep stage, saturation
reached at judge point 1 (the cross-cutting rules below stopped changing
after angle 4).

## Angles

1. SaaS metrics/subscription-analytics platforms (Baremetrics,
   ChartMogul, ProfitWell/Paddle).
2. FP&A/financial-modeling tools for startups (Causal, Mosaic.tech,
   Runway, Pry Financials, Finmark).
3. Cohort-LTV/unit-economics analytics tooling (Amplitude N-Day LTV,
   Mixpanel Revenue Analytics).
4. SaaS benchmark/valuation data sources (SaaS Capital, Bessemer Cloud
   100, cross-cited CAC-payback-by-ACV-tier syntheses).

## Must-bes the field converges on

- LTV is margin-adjusted (net of cost-to-serve), never raw ARPU/revenue
  — ChartMogul's explicit gross-margin adjustment vs. a naive ARPU/churn
  formula.
- Metric segmentation before aggregation: cohort, acquisition channel,
  and deal-size/ACV tier all recur as mandatory cuts (Baremetrics
  cohorting, Mixpanel channel-joined revenue, cross-cited ACV-tiered CAC
  payback bands) — a single blended figure is treated as a category
  error across all four angles.
- Churn/acquisition event definitions anchored to economic substance
  (paid-period end, true first acquisition) rather than user action, to
  resist gaming (ProfitWell Metrics' churn definition).
- Driver-based modeling: assumptions as named, reusable variables that
  propagate to every dependent output (Causal), continuously reconciled
  against actuals rather than a periodic manual snapshot (Mosaic, Pry/
  Finmark).
- Scenario bands (best/expected/downside) over point estimates for any
  forward-looking unit-economics verdict (Runway).
- Benchmark citations carry a distribution position (median vs.
  top-quartile) and a measurement period, not a bare cutoff (SaaS
  Capital); and joint, not isolated, thresholds — payback, burn
  multiple, and gross margin read together (Bessemer Cloud 100
  "winning profile").

## Gap line

This rulebook's five existing playbook axes (ltv-cac-band, cac-payback,
churn-assumption, sensitivity-scenario, evidence-chain — issue #1174)
already cover: segment/ACV-tiered thresholds for both the ratio and the
payback axes, a measured-vs-comparable-vs-labeled-guess sourcing ladder,
and base/best/worst scenario triads with dominant-variable sensitivity
selection.

Missing, and what this fold-in adds: (a) LTV's own computation input
was never required to be margin-adjusted or time-window-normalized —
only the resulting ratio was banded; (b) no rule required a payback
verdict to be checked jointly against gross margin/burn multiple before
calling unit economics "healthy"; (c) no rule defined churn/acquisition
events by economic substance vs. user action; (d) no rule required
shared, single-defined variables across sections that both consume the
same driver (a scenario-triad requirement existed, but not a
same-variable-one-definition requirement across the payback and ratio
sections); (e) no rule required a cited benchmark to state its
distribution position/period.

## Adopt / skip

Adopt: all six gap items above, each folded as a native rule into the
one existing playbook file whose axis it upgrades (see proposal).
Skip: OSS/vendor tool names, star counts, and pricing/funding figures
themselves — per the issue's native-application amendment these stay in
this on-the-record evidence trail only, never in the public rulebook.

## Sources

- https://baremetrics.com/academy/saas-calculating-ltv
- https://baremetrics.com/academy/churn
- https://baremetrics.com/blog/do-churn-based-ltv-calculations-mislead-us
- https://chartmogul.com/saas-metrics/ltv/
- https://chartmogul.com/blog/saas-metrics-refresher-cohort-analysis/
- https://ramp.com/vendors/chartmogul
- https://www.paddle.com/profitwell-metrics
- https://developer.paddle.com/concepts/retain/metrics/
- https://www.cfoshortlist.com/vendors/causal
- https://www.crunchbase.com/organization/causal-4a43
- https://www.cubesoftware.com/blog/mosaic-fpa
- https://www.drivetrain.ai/post/mosaic-competitors-and-alternatives
- https://www.cfoshortlist.com/vendors/runway
- https://tracxn.com/d/companies/runway/__vhBnElE1V7XdbRzVmmpiHoTvQnjiEeEjFcQvmRbIttw
- https://www.startuphub.ai/startups/pry-financials
- https://compassapp.ai/compare/best-financial-modelling-software-2026
- https://amplitude.com/docs/analytics/charts/retention-analysis/retention-analysis-n-day-ltv
- https://amplitude.com/docs/analytics/charts/revenue-ltv/revenue-ltv-interpret
- https://docs.mixpanel.com/docs/features/revenue-analytics
- https://linkrunner.io/blog/best-6-mobile-app-cohort-analysis-techniques-for-growth-teams
- https://www.saas-capital.com/research/private-saas-company-growth-rate-benchmarks/
- https://www.saas-capital.com/blog-posts/what-is-a-good-retention-rate-for-a-private-saas-company/
- https://www.t2d3.pro/learn/the-great-recalibration-b2b-saas-performance-metrics-and-the-hybrid-mandate-in-2025
- https://bantrr.com/business-model/saas-metrics/cac-payback-benchmarks-for-saas-companies/
