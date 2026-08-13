# issue-1199 observability tool-landscape survey

## Method
Adoption-evidence method (tech-feasibility): GitHub star counts pulled live
via `gh api repos/<org>/<repo> --jq .stargazers_count` (no pretrained
recall), plus one WebFetch source for CNCF project-maturity status. All
numbers below are this session's live reads, not memory.

```
$ gh api repos/prometheus/prometheus --jq .stargazers_count
65724
$ gh api repos/grafana/grafana --jq .stargazers_count
76283
$ gh api repos/open-telemetry/opentelemetry-collector --jq .stargazers_count
7385
$ gh api repos/grafana/loki --jq .stargazers_count
28722
$ gh api repos/jaegertracing/jaeger --jq .stargazers_count
23098
```

Sources:
- https://api.github.com/repos/prometheus/prometheus (gh api, this session)
- https://api.github.com/repos/grafana/grafana (gh api, this session)
- https://api.github.com/repos/open-telemetry/opentelemetry-collector (gh api, this session)
- https://api.github.com/repos/grafana/loki (gh api, this session)
- https://api.github.com/repos/jaegertracing/jaeger (gh api, this session)
- https://www.cncf.io/projects/opentelemetry/ (WebFetch, this session)

## Surveyed tools

### 1. Prometheus (65,724 stars)
- **Problem**: ad-hoc metric collection produces inconsistent naming and
  unbounded label sets that blow up storage.
- **How**: pull-based scraping of a fixed `/metrics` text-exposition
  format, with a naming convention (`_total`, `_seconds`, base units) and
  an explicit warning in its own docs against high-cardinality labels
  (e.g. never label by user ID or raw path).
- **Learning**: cardinality control is a *design-time* naming discipline,
  not a cleanup step — the handling policy for a candidate dimension
  should be decided at instrumentation-point naming time, not after the
  series already exists.

### 2. Grafana (76,283 stars)
- **Problem**: fixed dashboards answer only the questions their author
  anticipated; an incident needs answers to questions nobody wrote a
  panel for.
- **How**: separates the query layer (PromQL/LogQL/ad-hoc "Explore" mode)
  from the dashboard layer — Explore lets anyone run a fresh query
  against raw series with no pre-built panel.
  **Learning**: explorability is satisfied only when the design names a
  live ad-hoc query path (not just "we have a dashboard") — a dashboard
  alone does not prove the surface is explorable.

### 3. OpenTelemetry Collector (7,385 stars on the collector repo;
CNCF-graduated May 11, 2026, 27,000+ contributors across 5,200+
organizations per cncf.io — see Sources)
- **Problem**: every vendor/library defines its own span/metric/log
  schema, so an attribute means something different depending on which
  library emitted it.
- **How**: a single semantic-convention registry (`http.status_code`,
  `db.system`, etc.) that all instrumentation is expected to resolve
  against, checked mechanically rather than left to prose description.
- **Learning**: an `attribute_name` is only a real telemetry field if it
  resolves against a named registry (OTel semconv) or a documented
  custom extension — an orphan name that doesn't resolve anywhere is a
  design defect, not a style nit.

### 4. Grafana Loki (28,722 stars)
- **Problem**: full-text log indexing is expensive at scale, and teams
  default to indexing everything "just in case," which is how logs
  become the highest-cardinality, highest-cost telemetry stream.
- **How**: indexes only a small set of structured labels (chosen at
  ingest) and leaves the log line itself unindexed, searched by grep-like
  scan at query time — cardinality is bounded by construction, not by
  discipline after the fact.
- **Learning**: when a design is tempted to add a new indexed
  dimension "for searchability," the Loki move is to ask whether a label
  is truly needed for filtering (keep it structured/low-cardinality) vs.
  whether it only needs to be *findable* inside content (leave it
  unindexed) — collapsing that distinction is exactly how a cardinality
  budget gets blown.

### 5. Jaeger (23,098 stars)
- **Problem**: a single request crossing several services produces
  disconnected per-service logs/metrics with no way to see the request's
  end-to-end path or where time was actually spent.
- **How**: propagates one trace ID through every hop and represents the
  request as a tree of spans with parent/child timing, so latency
  attribution is structural (which span was on the critical path) rather
  than inferred from timestamps across separate systems.
- **Learning**: RED's "duration" signal and Golden Signals' "latency"
  signal are richer when the record names *where* the duration histogram
  sits in a request's span tree, not just that a histogram exists —
  useful for the phase-2 signal-placement statement this role already
  requires.

## Fold-in mapping (which rulebook file, which existing rule)

| Tool | Target file (observability-rulebook repo) | What it upgrades |
|---|---|---|
| Prometheus | `observability-cardinality-budget/README.md` | Names *when* cardinality decisions happen (instrumentation-point naming time) |
| Loki | `observability-cardinality-budget/README.md` | Adds the structured-label-vs-unindexed-content distinction as the handling-policy checklist item |
| Grafana | `observability-explorability/README.md` | Requires the ad-hoc query example to be a live query path, not a dashboard reference |
| OpenTelemetry | `observability/README.md` (role entry, spec-field table) | Ties `attribute_name` requirement to "resolves against OTel semconv or a documented extension" |
| Jaeger | `observability-signal-red/README.md`, `observability-signal-golden/README.md` | Duration/latency signal placement should name span-tree position |

Full fold-in text lands in phase 2 (post-approval), per contract v3 s19 —
this survey and the proposal below are the phase-1 deliverable.
