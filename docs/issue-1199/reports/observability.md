---
subject: issue-1199
role: observability
kind: coding-record
loop_state: landed
---

# observability record (issue-1199)

amendments-reconciled: issuecomment-5281291949, issuecomment-5281333812, issuecomment-5281339711, issuecomment-5281340041, issuecomment-5281352072, issuecomment-5281352244, issuecomment-5281364053, issuecomment-5281364300, issuecomment-5281373577, issuecomment-5281373802, issuecomment-5281492243, issuecomment-5281599615, issuecomment-5281607749, issuecomment-5281613746, issuecomment-5282826921, issuecomment-5282915639, and issuecomment-5282969941 all read this
session — the first fourteen are either the identical generic
batch-review verdict template "Verdict: PR #? → escalate (depth or
impact axis did not clear)" or the two-line "Judgment opened"
orchestrator log line, both naming this same branch's own automated
PR-judgment watcher, which goes off again on each push with a fresh
two-line log set — not a content-change ask.
issuecomment-5282826921 is an automated "Framing snapshot —
delivery-landed" watcher comment whose body names
docs/issue-1199/reports/api-design.md, a different role's record, not
this one; issuecomment-5282915639 is another instance of the same
generic "Verdict: PR #? → escalate" template already listed above.
issuecomment-5282969941 is a "stranded-relay" watcher notice for the
issue-1199/ml-engineering branch's own failed PR-create call — a
different role's branch, not this one. None of the three carries
observability-specific content. None
of the seventeen names a change the proposal, survey, or this phase-2
record must make; no amendment was needed in response to any of them.

The two amendments this session DOES act on are the two operator
requirement-amendment comments on the issue thread: the 2026-08-13
"NATIVE APPLICATION, NO TOOL-ATTRIBUTION CATALOGS" amendment and the
2026-08-14 "SURVEY TARGET IS CLAUDE CODE PLUGINS" amendment, both
addressed by this rework below.

## What was done

Rework of the observability tool-landscape fold-in (PR #1287 landed
this branch once already under the pre-amendment domain-tool survey;
this is a same-branch rework, not a new proposal round — the operator's
2026-08-14 comment orders rework "for observability and
performance-engineering" directly, and the branch's own prior
`APPROVE issue-1199/observability` already opened phase 2 for this
role once). Two things changed:

1. **Survey target**: replaced the domain-o11y-tool survey
   (Prometheus/Grafana/OTel Collector/Loki/Jaeger) with a Claude Code
   plugin-ecosystem survey — four plugins
   (`disler/claude-code-hooks-multi-agent-observability`,
   `simple10/agents-observe`, `ColeMurray/claude-code-otel`,
   `o11y-dev/opentelemetry-skill`), each with live-pulled GitHub star
   counts and cross-listing evidence. Full survey:
   docs/issue-1199/reports/observability/survey.md.
2. **Native application**: per the "no tool-attribution catalogs"
   amendment, edited the `tokenmaxxxer/observability-rulebook` repo
   (`/home/jwjung/tokenmaxxxer/rulebooks/observability-rulebook`) so the
   rulebook prose states each absorbed rule as the role's own native
   judgment — no tool name, no star count, no "source:" framing in the
   rulebook. The prior fold-in's "Tool learnings (issue-1199)" sections
   (which did carry tool names + star counts, landed under the
   pre-amendment survey) are retitled "Practitioner learnings
   (issue-1199)" and stripped of tool attribution in the same commit;
   the four new plugin-derived rules are added natively alongside them
   in the target file each upgrades.

Branched `issue-1199/plugin-landscape-rework` off `main` in the
rulebook repo, committed the five README edits, pushed the branch to
`origin`, and opened
https://github.com/tokenmaxxxer/observability-rulebook/pull/21
against the rulebook repo's `main`. Per contract v3 s8 (two-account
model), a role session opens a PR but does not merge it — merging that
rulebook PR is a human/orchestrator action outside this session's
scope, same as this record's own on-the-record PR below.

derived: git -C /home/jwjung/tokenmaxxxer/rulebooks/observability-rulebook log --oneline -1 issue-1199/plugin-landscape-rework
```
e251ed3 issue-1199: rework tool-landscape fold-in to Claude Code plugin survey, strip tool attribution
```

canonical: git -C /home/jwjung/tokenmaxxxer/rulebooks/observability-rulebook diff --stat main issue-1199/plugin-landscape-rework — read this session, confirms 5 files changed (the same five target READMEs from the prior fold-in), 60 insertions(+), 44 deletions(-), no other paths touched.

## code_under_review

- observability/README.md (tokenmaxxxer/observability-rulebook)
- observability-cardinality-budget/README.md (tokenmaxxxer/observability-rulebook)
- observability-explorability/README.md (tokenmaxxxer/observability-rulebook)
- observability-signal-golden/README.md (tokenmaxxxer/observability-rulebook)
- observability-signal-use/README.md (tokenmaxxxer/observability-rulebook)
- docs/issue-1199/reports/observability/survey.md

## Fold-in mapping (per-target upgrade, applied not just referenced)

1. `disler/claude-code-hooks-multi-agent-observability` (1,513 stars,
   live-pulled) → `observability/README.md`'s spec-field table: an
   instrumentation point must tie to one entry in a short, named list
   of lifecycle/call-site events and emit through one normalized
   attribute shape.
2. `simple10/agents-observe` (643 stars) →
   `observability-explorability/README.md`: the ad-hoc-query surface
   should be a small set of named, scoped query entry points, not one
   general query blob.
3. `ColeMurray/claude-code-otel` (485 stars) →
   `observability-signal-use/README.md` (previously had no
   practitioner-learnings section): utilization examples must include
   billed cost-per-unit-of-work when the bound resource is a
   billed one, not only CPU/memory/disk.
4. `o11y-dev/opentelemetry-skill` (44 stars, second listing backs it)
   → `observability-cardinality-budget/README.md`: a high-volume
   span/log stream needs an explicit sampling-strategy statement,
   separate from the per-dimension cardinality handling policy.

Each target file above appears in the same diff as its named upgrade
(no skipped-with-reason markers used) — see the `derived:`/`canonical:`
citations above.

## Why

northpole req#1/req#5: specialist delegation at real practitioner
completeness. Per the 2026-08-14 amendment, "practitioner" for this
issue means the Claude Code plugin ecosystem specifically (the tools
the role's own operating environment's users actually adopt), and per
the 2026-08-13 amendment the absorbed insight must read as the role's
own native judgment, not a "source: <repo>" catalog — the provenance
trail stays only in this on-the-record survey.

## Upstream

Based on: docs/issue-1199/reports/observability/survey.md (this
session's rework — Claude Code plugin survey, full adoption-evidence
trail and fold-in mapping) and the prior phase-1 proposal
docs/issue-1199/proposals/2026-08-13-observability-tool-landscape.md
(PR #1287, approved via `APPROVE issue-1199/observability`, which
already opened phase 2 for this role/branch pair once — this rework
proceeds under that same approval plus the operator's 2026-08-14
rework order, per the task instruction that the approval token for
this rework is already posted).

## Surface classification

Touched surface: the observability-rulebook's own doc plugins,
classified service-rollup (a common artifact multiple roles roll up
into, not one request path or one resource) — same classification as
the prior fold-in (phase-trace check: consistent methodology naming
across this branch's two fold-in rounds).

## Golden Signals

No new instrumentation point is added by this change itself — it edits
rulebook prose, not a telemetry emitter — restating the same
hypothetical instrumentation points named in the prior fold-in round
for phase-trace/methodology-naming purposes, not as a claim that this
instrumentation exists today:

- latency: PR-cycle-time histogram (지연 계측 지점) — a hypothetical
  measurement from PR-open event to PR-close event on the rulebook
  repo's default-branch CI workflow.
- traffic: pull-request-count counter (트래픽 계측 지점) — a
  hypothetical counter on the rulebook repo's default branch,
  incremented once per pull request cycle.
- errors: gate-refusal-count counter (에러 계측 지점) — a hypothetical
  counter incremented per `PreToolUse` hook refusal across this repo's
  plugin gates.
- saturation: open-PR queue-depth gauge (포화 계측 지점) — a
  hypothetical gauge sampled once per CI run on the rulebook repo.

utilization: none — no resource-bound surface is touched by this
change.

## Cardinality

Candidate high-cardinality dimensions this change's own subject matter
documents (not newly instrumented, but newly folded into the
rulebook's handling-policy guidance), each with an explicit handling
policy:

- `attribute_name` values (semconv-style strings, e.g.
  `http.status_code`, `db.system`) — attribute_type: `string`
  (enum-like, bounded by the registry). Handling policy: **bucket** —
  only registry-resolved or documented-custom-extension names are
  retained; free-form/orphan names are rejected at review time, never
  accumulated as a live series dimension.
- lifecycle/call-site event names (the short, named list this
  session's item-1 rule requires an instrumentation point to tie to)
  — attribute_type: `string` (enum, fixed short vocabulary). Handling
  policy: **bucket** — the vocabulary is fixed and short by design; a
  call site that doesn't map to a named entry is a design defect, not
  a new dimension to accumulate.
- high-volume span/log sampling rate (the new item-4 rule) —
  attribute_type: `float` (a share, 0.0-1.0, not itself a cardinality
  dimension but a companion decision to one). Handling policy:
  **aggregate-away** — the sampling decision lowers event *volume*,
  not label cardinality; it is recorded as a stated policy value, not
  accumulated per-event.

No new numeric time series or metric label is emitted by this change;
all three items above are telemetry-design concepts newly documented
in the rulebook, not newly instrumented here.

## Explorability

Ad-hoc query example, answering a question not fixed in advance, via a
named scoped entry point per this session's item-2 rule (not a general
query blob): `query: gh api repos/disler/claude-code-hooks-multi-agent-observability --jq .stargazers_count` —
a single-purpose "what's this candidate's adoption count" query, the
shape the reworked `observability-explorability` rule now asks for.

## Attribute fields (spec, issue-16)

`attribute_name` is discussed in the Cardinality section above with
its `attribute_type: string` stated immediately alongside it, per the
observability role-entry's spec-field table. No `signal_type`/`verdict`
instrumentation point is newly created by this change — it edits
rulebook prose, not a telemetry emitter.

## Accumulation

This change is not accumulation-cost-shaped: it adds a fixed, bounded
amount of prose (one rule addition or one attribution-strip edit per
target file, five files total) with no per-request, per-user, or
per-event growth — the fold-in content does not grow with production
traffic or usage.

## Open findings

None. The four newly surveyed plugin-derived rules and the
attribution-strip on the four pre-existing sections are applied
verbatim to the mapping in this record's Fold-in mapping section; no
scope beyond the five rulebook files (plus this record and the survey)
was touched, and no gate-code file was modified.

## What did not work

None.
