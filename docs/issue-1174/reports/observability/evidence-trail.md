# observability operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file (docs/issue-1174/reports/observability.md)
is gated behind an "APPROVE issue-1174/observability" comment per contract
v3 s19. This file carries the evidence trail as allowed phase-1 material
instead, matching the technical-writing/api-design precedent for this
issue (docs/issue-1174/reports/technical-writing/evidence-trail.md,
docs/issue-1174/reports/api-design.md).

## What was done (delivered to the rulebook repo, outside this repo's gate)

Authored the observability role's operational playbook and opened it as
a pull request against tokenmaxxxer/observability-rulebook, branch
issue-1174/operational-playbook.
canonical: `gh pr create` output this turn, returning
https://github.com/tokenmaxxxer/observability-rulebook/pull/19, commit
d0337c945e2fc03d1eeae0b119f217ba0ab20815 on that branch.

Per the approved proposal (docs/issue-1174/proposals/operational-playbook-program.md
sections (a) axis-derived N floor, (b-revised) fan-out unit, (c) depth-gate
shape, amendment 4 removal-category requirement), the PR adds 7 axis files
under playbook/, one per this role's decision axis (its 7 sibling
methodology plugins per docs/issue-7/proposals/2026-07-31-produces-methodology-hook-machine.md's
"phase norms as plugin combinations"):

- playbook/methodology-selection.md (3 rules)
- playbook/signal-red.md (4 rules)
- playbook/signal-use.md (4 rules)
- playbook/signal-golden.md (4 rules)
- playbook/cardinality-budget.md (4 rules)
- playbook/explorability.md (3 rules)
- playbook/phase-trace.md (3 rules)

25 rule blocks total, each condition -> choice -> source, each axis file
carrying at least one rule marked **REMOVAL** (amendment 4).

canonical: `python3 gates/playbook_depth_gate.py /tmp/rb/observability-rulebook/playbook --role observability --floor 21 --axes methodology-selection,signal-red,signal-use,signal-golden,cardinality-budget,explorability,phase-trace` run this turn, output:
```
ACCEPT x22, REJECT x3 (blocks #4, #15, #17 — "no choice/action verb":
these three lead with a bolded field name, e.g. "For **rate**, place a
monotonic..." rather than a bare imperative verb)
role=observability accepted=22 floor=21 count_ok=True
PASS
```
The accepted count (22) sits above the floor (21) per that same run;
the 3 rejected blocks are a known heuristic gap (bolded-noun lead
instead of a bare verb), not a retroactive edit to shipped rule text.

N derivation: rich tier (batch 3 per the proposal's (b) tiering,
observability alongside test-authoring/requirements-engineering/
conformance-review/defect-verification), 7 axes, N_min = max(12, 7*3) =
21. 25 >= 21.

## Research protocol (amendment 1, three layers)

Layer 1 (practitioner decision knowledge — operator's demonstrated
depth: condition -> choice -> source, not definitions):
- query: "Google SRE Golden Signals RED USE method when to use each
  monitoring" -> speedscale.com/blog/golden-signals,
  groundcover.com/blog/4-golden-signals (RED-vs-USE-vs-Golden-Signals
  selection criteria).
- query: "high cardinality metrics label explosion tag policy drop hash
  bucket Prometheus" -> last9.io/blog/how-to-manage-high-cardinality-metrics-in-prometheus
  (drop/hash/bucket remediation patterns).
- query: "Charity Majors observability engineering high cardinality high
  dimensionality explorability unknown-unknowns ad-hoc query" ->
  8thlight.com podcast summary (explorability's practitioner definition
  and ad-hoc-query value claim).

Layer 2 (named methodology/standard, verified at source):
- query: "OpenTelemetry semantic conventions attribute naming best
  practices cardinality" -> last9.io/blog/otel-naming-best-practices
  (OTel semconv naming discipline, opt-in cardinality attributes).
- query: "histogram percentile p99 latency vs average pitfalls SRE
  book" -> clickhouse.com/resources/engineering/percentiles-vs-averages,
  one2n.io/blog/sre-math-percentiles-in-sre-why-averages-lie-about-latency
  (Google SRE/Workbook percentile-over-average guidance, the
  never-average-percentiles rule).

Layer 3 (distinct academic-theory layer): canonical: this session's own
WebSearch tool-call transcript, this turn — the six queries above are
every query issued this session, and none targeted a distinct
peer-reviewed source independent of the named methodologies. This gap
is restated under Open findings below.

Per-rule mapping: each of the 25 rule blocks carries its own `source:`
line resolving to one of the URLs above — see the playbook files in the
open PR for the full per-rule citations (not reproduced here to avoid
duplicating primary content across two repos).

## Open findings

- Layer-3 gap (canonical: this session's own WebSearch tool-call
  transcript, this turn, same citation as above): technical-writing's
  playbook cites a distinct academic source under amendment 4
  (Adams/Converse/Hales/Klotz, *Nature* 594, 2021); this session ran no
  query aimed at an equivalent independent academic source for
  observability. A later session should search queueing-theory /
  distributed-systems-monitoring literature (e.g. saturation/
  utilization measurement, percentile-estimation error) for this role's
  layer-3.
- Layer-2 source pages were read via WebSearch result summaries, not
  individually WebFetched. A later session should fetch each cited page
  directly to check for summarization drift against the live text.
  no canonical citation for this item — it is a stated risk, not a
  claim about current state.
- The role's spec file has not gained a playbook-pointer field yet
  (out of scope for this unit) — Acceptance check 2 (a live session
  citing a playbook rule) is not yet satisfiable.
  canonical: `grep -c playbook_refs roles/specs/observability.spec.json`
  in this working tree this turn, returning 0.

## PR not opened (main repo)

The rulebook-repo PR (tokenmaxxxer/observability-rulebook#19) is open.
This repo's own PR for branch issue-1174/observability could not be
opened: pr-preflight.sh detected a post-spawn issue comment
(issuecomment-5276431906, reconciled above) and requires
docs/issue-1174/reports/observability.md to carry an
`amendments-reconciled` line citing it before `gh pr create` will run;
approval-gate.sh unconditionally refuses any Write/Edit/MultiEdit to
that exact path pre-approval (it is this role's phase-2 record path),
with no phase-1-legal way to satisfy pr-preflight's requirement. This
is the same deadlock market-analysis hit and stopped retrying against
(docs/issue-1174/reports/market-analysis/evidence-trail.md, commit
cf21418). Per that precedent: the branch is committed and pushed
(origin/issue-1174/observability); PR creation is left for external
relay or a later approval-gate-exempt session, rather than retried
further here.

## Next steps

- On receiving "APPROVE issue-1174/observability", promote this file's
  content into the phase-2 record with the full required-field set.
- Get a human review/merge decision on
  https://github.com/tokenmaxxxer/observability-rulebook/pull/19.
- Parent-repo units this work depends on for full Acceptance: the
  spec's playbook-pointer field (out of scope for this fan-out unit) and
  a live-session citation check (Acceptance check 2).

## basis

- docs/issue-1174/proposals/operational-playbook-program.md
- tokenmaxxxer/observability-rulebook PR #19

## kind

report

## loop_state

awaiting_approval

## why

Records this session's research-and-delivery work for issue #1174's
operational-playbook program (observability fan-out unit) while the
phase-2 record file stays gated pending human approval.
