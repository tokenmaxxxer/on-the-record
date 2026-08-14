# issue-1199 observability tool-landscape survey (REWORK, 2026-08-14)

## Rework scope

Operator amendment (issue comment, 2026-08-14, "SURVEY TARGET IS CLAUDE CODE
PLUGINS"): the survey target for every role's tool-landscape fold-in is the
Claude Code plugin/skill ecosystem, not general domain practitioner tools.
This supersedes the 2026-08-13 survey below only for the fold-in target —
the domain-tool learnings already landed under the prior survey may stay in
the rulebook, but per the follow-on 2026-08-14 native-application amendment
they must not carry tool-attribution framing (tool name + star count) in the
rulebook prose itself; that attribution stays only in this on-the-record
survey file. This rework (a) surveys Claude Code plugins with adoption
evidence, (b) strips tool-attribution framing from the rulebook's existing
"Tool learnings (issue-1199)" sections while keeping the absorbed rules as
native prose, and (c) adds the newly surveyed plugin-derived learnings
natively into the same sections.

## Method

Adoption-evidence method (tech-feasibility), applied to the Claude Code
plugin ecosystem per the amendment: GitHub star counts pulled live via
`gh api repos/<org>/<repo> --jq .stargazers_count` (no pretrained recall),
cross-checked against multiple independent listings (WebSearch across
awesome-claude-code lists, mcpmarket.com, claudedirectory.org) so each
candidate rests on more than one source.

```
$ gh api repos/disler/claude-code-hooks-multi-agent-observability --jq .stargazers_count
1513
$ gh api repos/simple10/agents-observe --jq .stargazers_count
643
$ gh api repos/ColeMurray/claude-code-otel --jq .stargazers_count
485
$ gh api repos/o11y-dev/opentelemetry-skill --jq .stargazers_count
44
$ gh api repos/langfuse/Claude-Observability-Plugin --jq .stargazers_count
19
$ gh api repos/TechNickAI/claude_telemetry --jq .stargazers_count
28
```

Sources:
- https://api.github.com/repos/disler/claude-code-hooks-multi-agent-observability (gh api, this session)
- https://api.github.com/repos/simple10/agents-observe (gh api, this session)
- https://api.github.com/repos/ColeMurray/claude-code-otel (gh api, this session)
- https://api.github.com/repos/o11y-dev/opentelemetry-skill (gh api, this session)
- https://github.com/hesreallyhim/awesome-claude-code (WebSearch, this session — independent listing)
- https://github.com/rohitg00/awesome-claude-code-toolkit (WebSearch, this session — independent listing)
- https://tessl.io/registry/o11y-dev/opentelemetry-skill/0.2.2/files/README.md (WebSearch, this session — second listing for o11y-dev/opentelemetry-skill)

Langfuse (19 stars) and TechNickAI/claude_telemetry (28 stars) were
web-searched but dropped from the fold-in candidate set below: their star
counts sit an order of magnitude below the other four candidates and their
independent-listing count was thinner, so they don't clear "most-adopted"
— kept in the evidence trail above only to show they were checked, not
silently omitted.

## Surveyed plugins

### 1. disler/claude-code-hooks-multi-agent-observability (1,513 stars)
- **Problem**: raw Claude Code hook payloads (PreToolUse/PostToolUse/
  session-start/session-end) arrive in whatever ad-hoc shape each event
  type happens to produce, so a dashboard or downstream consumer has to
  special-case every event type instead of reading one schema.
- **How**: every hook handler normalizes its raw payload into one fixed
  structured-event schema before it ever reaches storage or the dashboard
  — the lifecycle event vocabulary is a short, named, enumerable list
  (tool-call start/end, session start/end, subagent spawn), and
  normalization happens right at the hook boundary, not downstream.
- **Learning**: an instrumentation point only counts as real when it ties
  to one entry in a short, named list of lifecycle events *and* emits
  through one normalized attribute shape — an ad-hoc emission at an
  arbitrary call site with its own one-off shape is exactly what this
  design avoids.

### 2. simple10/agents-observe (643 stars)
- **Problem**: a single general-purpose "query the observability data"
  entry point forces every question through one wide, ambiguous surface,
  which tends to produce vague or incomplete ad-hoc answers.
- **How**: exposes several narrow, named `/observe` commands (a status
  check, a debug drill-down, a server-management command) instead of one
  monolithic query tool — each command states one job and one scope.
- **Learning**: an ad-hoc-query surface reads stronger when it's a small
  set of named, scoped entry points (each answering one class of
  question) rather than one general query blob — gives explorability a
  concrete shape requirement beyond "a live query path exists."

### 3. ColeMurray/claude-code-otel (485 stars)
- **Problem**: usage volume, latency/performance, and cost typically live
  in three separate places (a usage log, an APM trace, a billing
  dashboard), so nobody can correlate "this session ran slow" with "this
  session ran expensive" from one signal set.
- **How**: a single OpenTelemetry pipeline emits usage, performance, and
  cost as sibling attributes in the same trace/metric stream, so cost
  becomes a first-class emitted signal alongside latency and traffic
  rather than a separate accounting artifact.
- **Learning**: for an agent/session-shaped resource-bound surface, cost-
  or resource-consumption-per-unit-of-work belongs as a legitimate
  utilization metric — USE's utilization axis should not read as
  CPU/memory-only when the resource being bounded is a metered/billed
  one.

### 4. o11y-dev/opentelemetry-skill (44 stars; a second listing via the
Tessl registry and the o11y-dev GitHub org backs the count, not a single
source)
- **Problem**: one large "how to do observability" reference document
  mixes unrelated decisions (how to design a collector pipeline, how to
  bound cardinality, how to pick a sampling rate, how to secure telemetry
  in transit), so a reader has to pull the one decision they need out of
  an undifferentiated wall of guidance.
- **How**: splits guidance into separate reference files gated by task —
  a cardinality-management reference sits in its own file, distinct from
  a sampling reference, distinct from a collector-security reference —
  so each decision carries its own bounded checklist.
- **Learning**: cardinality-bucketing and sampling-rate decisions are
  separable and get blended together when a design only asks "what's the
  handling policy for this dimension" — a high-volume span/log stream
  needs both a cardinality handling policy (which labels/dimensions to
  keep) *and* an independent sampling-strategy statement (what share of
  events to keep), and a design that states only the former leaves the
  high-volume case half-specified.

## Fold-in mapping (native application, no tool-attribution in the rulebook)

| Plugin (evidence, kept only in this survey) | Target rulebook file | Native rule added (no tool name/stars in rulebook prose) |
|---|---|---|
| disler/claude-code-hooks-multi-agent-observability (1,513★) | `observability/README.md` (role-entry, instrumentation-point spec fields) | An instrumentation point must tie to one entry in a short, named list of lifecycle/call-site events and emit through one normalized attribute shape — not an arbitrary one-off emission. |
| simple10/agents-observe (643★) | `observability-explorability/README.md` | The ad-hoc query surface should be exposed as a small set of named, scoped query entry points (one per question class), not one general query blob. |
| ColeMurray/claude-code-otel (485★) | `observability-signal-use/README.md` | Utilization examples must include metered/billed resource consumption (cost-per-unit-of-work), not only CPU/memory/disk, when the bound resource is a metered one. |
| o11y-dev/opentelemetry-skill (44★, second listing backs it) | `observability-cardinality-budget/README.md` | A high-volume span/log stream needs an explicit sampling-strategy statement, stated separately from the per-dimension cardinality handling policy — the two are not the same decision. |

Full fold-in text lands directly in phase 2 (this rework proceeds under the
already-posted approval for issue-1199/observability plus the operator's
2026-08-14 rework order) — see docs/issue-1199/reports/observability.md.
