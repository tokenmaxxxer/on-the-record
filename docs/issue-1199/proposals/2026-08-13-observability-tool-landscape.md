---
status: proposed
files:
  - observability-rulebook: observability-cardinality-budget/README.md
  - observability-rulebook: observability-explorability/README.md
  - observability-rulebook: observability/README.md
  - observability-rulebook: observability-signal-red/README.md
  - observability-rulebook: observability-signal-golden/README.md
  - docs/issue-1199/reports/observability.md
---

# Proposal: fold observability's surveyed tool landscape into the rulebook (issue-1199)

All target files above (except this repo's own record) live in the
separate rulebook repo tokenmaxxxer/observability-rulebook at
`/home/jwjung/tokenmaxxxer/rulebooks/observability-rulebook` — see
docs/issue-1199/reports/observability/survey.md for the full evidence
trail. Phase 2 branches and commits there directly, once approved.

## Signal methodology and surface classification

This proposal touches no new instrumented service surface — it edits
the observability-rulebook's own doc plugins. Treating the rulebook
repo as the touched surface: classification is service-rollup (a
shared artifact multiple roles roll up into, not one request path or
one resource). Signal methodology named for it: golden signals
(closest fit for a service-rollup surface). No new instrumentation
point is added by this change — no latency/traffic/errors/saturation
histogram is placed — this section exists only to satisfy phase-1
methodology naming for a documentation-only surface.

## Request

Per issue-1199 (northpole req#1/req#5, consult-log 2026-08-13T06:10:35
entry), add a bounded "Tool learnings (issue-1199)" addition split
across five existing observability-rulebook plugin READMEs: five
surveyed o11y-stack tools, each with live-pulled adoption evidence,
problem/how/learning, and a named upgrade to an existing rule/checklist
— never a standalone tool catalog, never a gate-code change.

## Problem/Motivation

`observability-cardinality-budget`, `observability-explorability`, and
the signal plugins enforce structural presence (a keyword is mentioned,
a field is non-placeholder) but carry no design-move guidance on *how*
to decide a cardinality handling policy, *what* an ad-hoc query path
actually needs to be, or *where* a duration/latency histogram should
sit relative to a request's span tree. The o11y stacks practitioners
actually run (Prometheus, Grafana, OpenTelemetry, Loki, Jaeger) encode
exactly these design moves; the rulebook has never learned from them.

## Proposed surface decision

Five entries, one per surveyed tool, each landing in the plugin README
whose existing checklist it upgrades (see survey.md's fold-in mapping
table for full detail):

1. **Prometheus** (65,724 GitHub stars, live-pulled — see survey
   Sources) → `observability-cardinality-budget/README.md`: add one
   sentence to the phase-1/phase-2 checklist that cardinality handling
   policy is decided at instrumentation-point *naming* time, not
   retrofitted after a series exists.
2. **Grafana Loki** (28,722 stars) → same file: add the
   structured-label-vs-unindexed-content distinction as an explicit
   handling-policy option alongside drop/hash/bucket/aggregate-away.
3. **Grafana** (76,283 stars) → `observability-explorability/README.md`:
   tighten the phase-2 ad-hoc-query requirement to specifically require
   a live query path (Explore-style), not a dashboard-panel reference.
4. **OpenTelemetry Collector** (7,385 stars on the collector repo;
   CNCF-graduated 2026-05-11, 27,000+ contributors / 5,200+ orgs per
   cncf.io) → `observability/README.md`'s spec-field table: tie the
   `attribute_name` requirement explicitly to "resolves against OTel
   semconv or a documented custom extension" as the orphan-reference
   test.
5. **Jaeger** (23,098 stars) → `observability-signal-red/README.md` and
   `observability-signal-golden/README.md`: add that the duration/
   latency instrumentation-point statement should name where in a
   request's span tree the histogram sits, not just that one exists.

docs/issue-1199/reports/observability.md is phase-2 output, written
only after approval opens phase 2, per contract v3 s19.

## Alternatives considered

Considered a single standalone `tool-learnings.md` file in the
rulebook (mirroring the issue text's suggested bounded section as one
option). Rejected: the rulebook's existing convention is one plugin =
one owned norm with its own README; a parallel catalog file would
duplicate scope already split across five plugin READMEs and risks
becoming exactly the "tool catalog" the issue prohibits. Landing each
learning inside the plugin whose checklist it upgrades keeps the fold-in
traceable to a specific rule, per requirement 4.

## Out of scope

- Datadog/other SaaS-class tools: no GitHub star signal available and
  this session's budget did not stretch to a second adoption-evidence
  method (e.g. G2 review counts) for a SaaS product; left for a future
  round if requested.
- Any gate-code change (`observability-produces-gate.sh` or sibling
  hooks) — this is content/checklist guidance only, no new required
  field.

## How you'll know it worked

- Each of the five target READMEs gains one short paragraph under a
  "Tool learnings (issue-1199)" heading, capped to what's listed above
  — no tool name repeated more than once, no catalog table added.
- docs/issue-1199/reports/observability.md carries the full
  {tool, adoption evidence, problem, how, learning→rule} trail already
  captured in survey.md, restated as phase-2 record.
