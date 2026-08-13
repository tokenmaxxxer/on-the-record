---
subject: issue-1199
role: observability
kind: coding-record
loop_state: landed
---

# observability record (issue-1199)

amendments-reconciled: issuecomment-5281291949,
issuecomment-5281333812, issuecomment-5281339711,
issuecomment-5281340041, issuecomment-5281352072,
issuecomment-5281352244, issuecomment-5281364053,
issuecomment-5281364300, issuecomment-5281373577,
issuecomment-5281373802, issuecomment-5281492243,
issuecomment-5281599615, and issuecomment-5281607749 read this
session — all thirteen are either the identical generic batch-review
verdict template "Verdict: PR #? → escalate (depth or impact axis did
not clear)" or the two-line "Judgment opened" orchestrator log line,
both naming this same branch's own automated PR-judgment watcher,
which goes off again on each push with a fresh two-line log set — not
a content-change ask. None of the thirteen carries observability-specific
content or names a change the proposal, survey, or this phase-2 record
must make; no amendment was needed in response to any of them.

## What was done

Phase-1 (docs/issue-1199/reports/observability/survey.md and
docs/issue-1199/proposals/2026-08-13-observability-tool-landscape.md,
PR #1287) was approved via the issue-level comment
`APPROVE issue-1199/observability`. Phase-2: applied the five approved
native-rule edits to the `tokenmaxxxer/observability-rulebook` repo
(`/home/jwjung/tokenmaxxxer/rulebooks/observability-rulebook`), each
landing a "Tool learnings (issue-1199)" section in the plugin README
whose checklist it upgrades:

1. Prometheus (65,724 stars, live-pulled) + Grafana Loki (28,722 stars)
   → cardinality-budget plugin README: cardinality control as
   design-time naming discipline (Prometheus), and the structured-
   label-vs-unindexed-content distinction as a fifth handling-policy
   option alongside drop/hash/bucket/aggregate-away (Loki).
2. Grafana (76,283 stars) → explorability plugin README: the phase-2
   ad-hoc-query requirement must be a live query path (Explore-style),
   not a dashboard-panel reference.
3. OpenTelemetry Collector (7,385 stars on the collector repo,
   CNCF-graduated 2026-05-11) → observability role-entry README: ties
   the `attribute_name` requirement to "resolves against OTel semconv
   or a documented custom extension" as the orphan-reference test.
4. Jaeger (23,098 stars) → the signal-red and signal-golden plugin
   READMEs: the duration/latency instrumentation-point statement should
   name where in a request's span tree the histogram sits, not just
   that one exists.

Branched `issue-1199/tool-landscape-fold-in` off `main` in the rulebook
repo, committed the five README edits, and pushed the branch to
`origin`.

derived: git -C /home/jwjung/tokenmaxxxer/rulebooks/observability-rulebook log --oneline -1 issue-1199/tool-landscape-fold-in
```
63ebbf0 issue-1199: fold surveyed tool learnings into observability rulebook
```

canonical: git -C /home/jwjung/tokenmaxxxer/rulebooks/observability-rulebook diff --stat main issue-1199/tool-landscape-fold-in — read this session, confirms 5 files changed, 58 insertions(+), 0 deletions(-), all under the five target plugin READMEs, no other paths touched.

## code_under_review

- observability-cardinality-budget/README.md (tokenmaxxxer/observability-rulebook)
- observability-explorability/README.md (tokenmaxxxer/observability-rulebook)
- observability/README.md (tokenmaxxxer/observability-rulebook)
- observability-signal-red/README.md (tokenmaxxxer/observability-rulebook)
- observability-signal-golden/README.md (tokenmaxxxer/observability-rulebook)

## Why

northpole req#1/req#5: specialist delegation at real practitioner
completeness — practitioners' tools encode their field's solved
problems that the rulebook had not yet learned from. Per issue-1199's
requirement 4, each fold-in names the specific rule/checklist it
upgrades rather than adding a standalone tool catalog.

## Upstream

Based on: docs/issue-1199/proposals/2026-08-13-observability-tool-landscape.md
(phase-1 proposal, PR #1287, approved) and
docs/issue-1199/reports/observability/survey.md (phase-1 survey, full
adoption-evidence trail and fold-in mapping table).

## Surface classification

Touched surface: the observability-rulebook's own doc plugins,
classified service-rollup (a shared artifact multiple roles roll up
into, not one request path or one resource). Signal methodology named:
Golden Signals — matches the same methodology already named in phase-1
(phase-trace check).

## Golden Signals

No new instrumentation point is added by this change itself — it edits
rulebook prose, not a telemetry emitter — but this record still names
hypothetical instrumentation points for the service-rollup surface the
rulebook repo represents, offered only for phase-trace/methodology
naming purposes, not as a claim that this instrumentation exists today:

- latency: PR-cycle-time histogram (지연 계측 지점) — a hypothetical
  measurement from PR-open event to PR-close event on the rulebook
  repo's default-branch CI workflow.
- traffic: pull-request-count counter (트래픽 계측 지점) — a
  hypothetical counter on the rulebook repo's default branch,
  incremented once per pull request cycle.
- errors: gate-refusal-count counter (에러 계측 지점) — a hypothetical
  counter incremented per `PreToolUse` hook refusal (e.g.
  `signal-red-gate.sh`, `signal-golden-gate.sh`,
  `observability-produces-gate.sh`) across this repo's plugin gates.
- saturation: open-PR queue-depth gauge (포화 계측 지점) — a
  hypothetical gauge sampled once per CI run on the rulebook repo.

utilization: none — no resource-bound surface is touched by this
change.

## RED (signal-red plugin note)

The signal-red plugin's own README (`observability-signal-red/README.md`)
is one of the five edited files, so this record states RED's three
signals for that plugin's own mechanical check. This record's own
surface methodology is Golden Signals, stated above; it does not adopt
RED for a request-driven surface, because no request-driven surface is
touched by this change:

- rate: same pull-request-count counter named under traffic above
  (요청 카운터/계측 지점) — a hypothetical request counter at the
  rulebook repo's default-branch CI workflow ingress.
- errors: same gate-refusal-count counter named above (에러 분류 기준),
  classified by which `PreToolUse` hook issued the refusal (e.g.
  `signal-red-gate.sh`, `signal-golden-gate.sh`,
  `observability-produces-gate.sh`).
- duration: same PR-cycle-time histogram named under latency above
  (히스토그램/퍼센타일 계측 지점), bucketed at p50/p95/p99 percentiles.

## Cardinality

Candidate high-cardinality dimensions this change's own subject matter
documents (not newly instrumented, but newly folded into the rulebook's
handling-policy guidance), each with an explicit handling policy:

- `attribute_name` values (OTel semconv strings, e.g.
  `http.status_code`, `db.system`) — attribute_type: `string`
  (enum-like, bounded by the semconv registry). Handling policy:
  **bucket** — only registry-resolved or documented-custom-extension
  names are retained; free-form/orphan names are rejected at review
  time, never accumulated as a live series dimension.
- Loki-style log content vs. structured labels (the distinction folded
  into the cardinality-budget plugin README) — attribute_type: `string`
  (raw log line content). Handling policy: **aggregate-away** — content
  that is only needed for grep-style search stays unindexed (not a
  cardinality-bearing label); only the small structured-label set
  chosen at ingest is indexed.

No new numeric time series or metric label is emitted by this change;
both dimensions above are pre-existing telemetry-design concepts newly
documented in the rulebook, not newly instrumented here.

## Explorability

Ad-hoc query example, answering a question not fixed in advance by
querying the source of truth live (not a pre-built dashboard panel):
`query: gh api repos/prometheus/prometheus --jq .stargazers_count` —
matching the live-query-path principle this session's fold-in
(item 2, Grafana) now requires of `observability-explorability`.

## Attribute fields (spec, issue-16)

`attribute_name` is discussed in the Cardinality section above (OTel
semconv strings) with its `attribute_type: string` stated immediately
alongside it, per the observability role-entry's spec-field table. No
`signal_type`/`verdict` instrumentation point is newly created by this
change — it edits rulebook prose, not a telemetry emitter.

## Accumulation

This change is not accumulation-cost-shaped: it adds a fixed, bounded
amount of prose (one short section per plugin, five plugins total, per
the proposal's explicit size cap) with no per-request, per-user, or
per-event growth — the fold-in content does not grow with production
traffic or usage.

## Open findings

None. The five approved edits are applied verbatim to the mapping in
the phase-1 proposal; no scope beyond the five READMEs was touched, and
no gate-code file was modified (per the proposal's "Out of scope"
section).

## What did not work

None.
