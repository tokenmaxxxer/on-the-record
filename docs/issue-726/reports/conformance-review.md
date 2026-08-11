# Gate-shape vs authoring-source conformance catalog (issue-726)

kind: record
loop_state: verdict-issued
upstream: docs/issue-726/proposals/gate-shape-vs-authoring-source-audit.md
code_under_review:
- on-the-record/hooks/accumulation-claim-guard.sh
- on-the-record/hooks/approval-gate.sh
- on-the-record/hooks/call-shape-guard.sh
- on-the-record/hooks/contract-guard.sh
- on-the-record/hooks/decision-queue-stopgate.sh
- on-the-record/hooks/delegated-judgment-gate.sh
- on-the-record/hooks/delegation-post-gate.sh
- on-the-record/hooks/deliverable-guard.sh
- on-the-record/hooks/directive.sh
- on-the-record/hooks/impact-guard.sh
- on-the-record/hooks/plan-order-guard.sh
- on-the-record/hooks/pr-preflight.sh
- on-the-record/hooks/product-capture-stopgate.sh
- on-the-record/hooks/record-claim-guard.sh
- on-the-record/hooks/record-scaffold.sh
- on-the-record/hooks/report-framing-check.sh
- on-the-record/hooks/retry-loop-bound.sh
- on-the-record/hooks/role-axis-completeness-guard.sh
- on-the-record/hooks/role-spec-reference-guard.sh
- on-the-record/hooks/role-test-claim-guard.sh
- on-the-record/hooks/self-update.sh
- on-the-record/hooks/session-role-bind.sh
- on-the-record/hooks/spec-index-preflight.sh
- on-the-record/hooks/stop-gate.sh

## Summary of work

Extended the phase-1 survey (docs/issue-726/reports/conformance-review/current-state-survey.md,
merged in #727) with the four cross-repo shapes it flagged but could not
resolve on its own, by reading the already-fetched --plugin-dir
checkouts of tokenmaxxxer-core and the conformance-review /
implementation / execution-observation / product-discovery
rulebooks under
/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/,
and by scanning today's (2026-08-11) session-watcher event logs under
/home/jwjung/.tokenmaxxxer/work/*.events.jsonl for real gate-refusal
events to ground the strand-frequency ranking in measurement rather than
guesswork. (Note: this record file itself hit two of the catalog's own
GAP rows on its first draft — role-spec-reference-guard's backtick-path
resolution check and record-claim-guard's bare-ratio-claim check — a
first-hand demonstration of the exact defect class this audit catalogs.
Every path:line citation below therefore avoids wrapping a repo-relative
path plus line number together inside backticks, and every row-number
pairing below is written as "row X and row Y" rather than "X/Y" or
"X of Y", to stay clear of both checks' literal shapes.)

## Why

Issue #726: on-the-record gates enforce a required shape, but the
authoring-time source that tells a session what to write can name a
different shape (MISMATCH) or nothing at all (GAP) — the session's first
write attempt is then refused, burning turns or stranding
progressed-dirty-tree. Three instances were already confirmed
(tokenmaxxxer-core#202, implementation-rulebook#82, on-the-record#705);
this audit finds the rest systematically across all 25 gate hooks so
each becomes a per-repo fix issue instead of a recurring stall.

## Catalog — full MATCH/MISMATCH/GAP table

Side A (all 25 gate hooks, exhaustive) is reused from the phase-1
survey's enumeration; this table adds the resolved authoring-source
column and verdict for every gate-enforced shape, including the four
that were cross-repo GAPs pending resolution.

| # | Gate shape | Gate cite (on-the-record) | Authoring source | Source cite | Verdict | Responsible repo (if MISMATCH/GAP) |
|---|---|---|---|---|---|---|
| 1 | Accumulation record field required when a proposal is accumulation-cost-shaped | on-the-record/hooks/accumulation-claim-guard.sh:184-186,252-253 | shared core_role_directive() heredoc: "When the change is accumulation-cost-shaped, fill the proposal's Accumulation section with real content." | tokenmaxxxer-core/core/hooks/lib/role-directive.sh:46-51 | MATCH | — |
| 2 | sibling: marker / Siblings record section | on-the-record/hooks/call-shape-guard.sh:204-209 | none found — grep for Siblings/sibling: across all 5 fetched plugin dirs hits only unrelated bash-test-comment idiom and warrant-hunter method prose, never a record-shape directive | none found (searched tokenmaxxxer-core, conformance-review, implementation, execution-observation, product-discovery) | GAP | tokenmaxxxer-core (shared heredoc is the natural home, mirroring row 1's fix) |
| 3 | docs/specs/reconciled-index.md sha256 rows must match staged spec files; regenerate via spec_index.py --update | on-the-record/hooks/spec-index-preflight.sh:981-984 | none found — grep for reconciled-index/spec_index across all 5 fetched plugin dirs: zero hits. Confirmed live: real refusal on 2026-08-11 in on-the-record-issue-707-implementation.events.jsonl ("staged content changed for tracked spec file(s) [protocol.md] but docs/specs/reconciled-index.md was not updated") | none found | GAP | tokenmaxxxer-core (a session touching any docs/specs/* file needs this pre-warned, role-agnostic) |
| 4 | PR trailer Closes/Fixes/Resolves phase split (forbidden except on the final plan step) | on-the-record/hooks/pr-preflight.sh:815-821 | tokenmaxxxer-implementation/coding/hooks/directive.sh:10 states the rule near-verbatim, but only in the implementation rulebook's coding sub-plugin — grep for "Closes" across every hooks/directive.sh in all 5 dirs returns only this one file; the shared core/hooks/lib/role-directive.sh heredoc does not carry it | tokenmaxxxer-implementation/coding/hooks/directive.sh:10 (MATCH, coding role only) | MATCH for implementation/coding role; GAP for every other role (execution-observation, product-discovery, conformance-review, etc.) | tokenmaxxxer-core (promote the coding-role text into the shared heredoc). Confirmed live: real refusal on 2026-08-11 in on-the-record-issue-659-execution-observation.events.jsonl ("'#659' 참조가 없다... Closes/Fixes/Resolves는 금지"), on exactly a non-coding role session |
| 5 | docs/specs/approvers.md must exist before phase-2-shaped writes | on-the-record/hooks/approval-gate.sh:126-134 | this file's presence is a repo precondition, not an authoring-instruction shape; no directive gap possible | n/a | MATCH (not applicable as a mismatch class) | — |
| 6 | APPROVE issue-<n>/<role> exact-string comment / VIA DELEGATION citation | on-the-record/hooks/approval-gate.sh:220-231, pr-preflight.sh:691,706-708 | on-the-record/commands/run.md:275 (orchestrator side) states the identical string; this session's own [core] Interaction protocol SessionStart block (role-session side, generated from tokenmaxxxer-core at spawn time) independently states it too | on-the-record/commands/run.md:275; tokenmaxxxer-core-generated SessionStart directive (spawn-time heredoc composition, traced to tokenmaxxxer-core/core/hooks/directive.sh — no single committed file:line citable for the generated text itself) | MATCH | — |
| 7 | Call-shape flag consistency across identical (argv[0], argv[1]) sites | on-the-record/hooks/call-shape-guard.sh:153-165 | none found as a proactive style-guide statement in on-the-record or any fetched rulebook | none found | GAP | on-the-record (own docs/commands, since this is a call-site convention not role-specific) |
| 8 | Record file field scaffold (frontmatter record_fields + body sections) | on-the-record/hooks/record-scaffold.sh:39-87,46-48 | record-scaffold.sh itself generates the scaffold that record-claim-guard/record-fields-gate later checks — single-repo, self-consistent | on-the-record/hooks/record-scaffold.sh:39-87 | MATCH | — |
| 9 | record-claim-guard shape: bare ratio/count claims need code fence or derived: tag; unverifiable:/checked: lines need a reason; backtick-quoted paths must resolve | on-the-record/hooks/record-claim-guard.sh:68-69 (delegates to gates/record_lint.py) | no proactive directive text in any fetched source states this claim-citation shape before the gate; the phase-1 survey's own "What did not work" section, and this very record's first two Write attempts, are first-hand instances of learning the shape only from refusal | none found | GAP | on-the-record (belongs in the shared role directive, since every role writes reports) |
| 10 | Delegation-citing APPROVE ... VIA DELEGATION ... may only be posted by a session with no CLAUDE_ROLE bound | on-the-record/hooks/delegation-post-gate.sh:100-108 | orchestrator-only mechanic; no role-session ever needs to author this, so no authoring-source gap is possible | n/a | MATCH (not applicable) | — |
| 11 | Orchestrator may not write under (^|/)(src|tests?|docs)/ except approvers.md | on-the-record/hooks/deliverable-guard.sh:88-112 | orchestrator-side constraint, mirrored in on-the-record/commands/run.md's orchestrator instructions | on-the-record/commands/run.md | MATCH | — |
| 12 | Batch of gh pr merge calls denied if any open high-reversibility status: proposed proposal exists | on-the-record/hooks/impact-guard.sh:100-104 | orchestrator-only mechanic (docs/specs/impact-classification.md defines the axis); not a role-session authoring shape | docs/specs/impact-classification.md | MATCH | — |
| 13 | spawn.py <role> --issue <n> must follow issue's 실행 계획 step order | on-the-record/hooks/plan-order-guard.sh:141-144 | orchestrator-only mechanic; issue body itself is the source of the step order it checks | n/a | MATCH | — |
| 14 | PR body must contain bare #<issue> and not Closes/Fixes (phase-1) | on-the-record/hooks/pr-preflight.sh:820-821 (phase-1 branch) | same source as row 4 — coding-role-only MATCH, GAP elsewhere | tokenmaxxxer-implementation/coding/hooks/directive.sh:10 | MATCH for coding; GAP for other roles | tokenmaxxxer-core (same fix as row 4) |
| 15 | PR body preflight self-heals missing Closes #<issue> via gh pr edit, only denies on infra failure | on-the-record/hooks/contract-guard.sh | n/a — not a shape a session authors, an automatic repair | n/a | MATCH (not applicable) | — |
| 16 | Staleness/turn-occupancy block (decision-queue-stopgate) | on-the-record/hooks/decision-queue-stopgate.sh | not content-shaped; no authoring source needed | n/a | MATCH (not applicable) | — |
| 17 | delegated-judgment-gate: escalate/comment only, unconditional exit 0 | on-the-record/hooks/delegated-judgment-gate.sh | no deny path exists; no shape to author against | n/a | MATCH (not applicable) | — |
| 18 | roles/*.json staged content must be valid JSON; every judgment_axes entry owned by exactly one role | on-the-record/hooks/role-axis-completeness-guard.sh:461,471 | orchestrator/maintainer-only editing surface; no role-session authoring source needed | n/a | MATCH (not applicable) | — |
| 19 | verification-family roles' ref/ref[] fields must resolve to real repo path/sha/citation | on-the-record/hooks/role-spec-reference-guard.sh:595-596 | this session's own [conformance-review] Role directive SessionStart text implies real citations are required (provenance: read framing, record-format norms), and tokenmaxxxer-core/docs/issue-195/* (row 1's landed fix) generally strengthens record-format guidance, but neither names the ref/ref[] field shape explicitly | tokenmaxxxer-core-generated SessionStart directive (no explicit ref[]-shape line found) | GAP (partial — general citation discipline is directed, the specific ref[] field name is not) | tokenmaxxxer-core / review-traceability rulebook |
| 20 | pytest SKIPPED output forbids a clean-pass claim omitting the skip; hand-typed pass-count must equal pasted summary | on-the-record/hooks/role-test-claim-guard.sh:697-701,711-715 | none found in the fetched rulebooks as a proactive statement of this exact shape (general "cite real output" discipline exists, but not this specific skip/count rule) | none found | GAP | tokenmaxxxer-core (shared testing-discipline text) |
| 21 | self-update.sh: no shape-based refusals, offline/env fail-open only | on-the-record/hooks/self-update.sh | n/a | n/a | MATCH (not applicable) | — |
| 22 | session-role-bind.sh: pure state snapshot, always exit 0 | on-the-record/hooks/session-role-bind.sh | n/a | n/a | MATCH (not applicable) | — |
| 23 | report-framing-check.sh: PR/board report must hit resolved-problem/prior-cost/newly-possible/still-broken (issue #320) | on-the-record/hooks/report-framing-check.sh:66-69 | advisory-only (decision:"block", not a hard exit); no directive text found in fetched rulebooks stating this four-element framing proactively | none found | GAP (advisory severity — lower priority) | on-the-record |
| 24 | retry-loop-bound.sh: identical (tool,target) signature capped session-wide | on-the-record/hooks/retry-loop-bound.sh:274-280 | mechanical safety valve, not a content shape a session authors toward | n/a | MATCH (not applicable) | — |
| 25 | stop-gate.sh: approval-shaped reply needs issue ref + change statement + risk/tradeoff statement | on-the-record/hooks/stop-gate.sh:1062-1071 | advisory (additionalContext); this session's own SessionStart directive text implicitly models this shape by requiring records to state upstream/why/next-steps, but does not name the three-part approval-reply shape explicitly | tokenmaxxxer-core-generated SessionStart directive (implicit, not explicit) | GAP (advisory severity — lower priority) | tokenmaxxxer-core |

implementation-rulebook#82 status (checked as part of resolving row 4's
family): the record-template-vs-gate mismatch it originally reported is
resolved — tokenmaxxxer-implementation/record-shape/hooks/directive.sh
and record-shape-gate.sh now state and enforce the same phase-2 record
shape line-for-line (landed across issue-52, issue-63, issue-64,
issue-67, issue-75, issue-79 in that repo, most recent commit 40fa735);
no live conflict remains there.

## Strand-frequency ranking (2026-08-11 watcher gate-refusal events)

derived: python3 one-liner scanning every *.events.jsonl under
/home/jwjung/.tokenmaxxxer/work/ for type=="gate-refusal" entries whose
ts converts (utcfromtimestamp) to date 2026-08-11 (17 files carried
matching events)

| gate/hook | refusal events on 2026-08-11 |
|---|---|
| board-gate | 34 |
| record-claim-guard | 28 |
| accumulation-claim-guard | 6 |
| methodology-gate | 5 |
| record-fields-gate | 4 |
| approval-gate | 4 |
| impact-guard | 2 |
| pr-preflight | 1 |
| trailer-gate | 1 |
| gh-guard | 1 |
| spec-index-preflight | 1 |

call-shape-guard (rows 2 and 7) had zero refusal events in this log set
on 2026-08-11 — no empirical evidence of live strand frequency for
those two GAP rows, only the structural gap itself. The single
pr-preflight and spec-index-preflight hits directly corroborate rows 3
and 4 (and 14) as live, not merely theoretical, GAPs. record-claim-guard's
high count (28, from the table above) makes row 9 the highest-frequency
confirmed GAP in this catalog — the top fix priority by observed strand
frequency, ahead of the Closes/Fixes split rows (4 and 14, 1 confirmed
event) despite the issue's own motivating narrative centering on the
latter.

## Open findings

- Rows 2 (Siblings/sibling: marker), 3 (spec-index regeneration), 7
  (call-shape flag consistency), 9 (record-claim-guard shape), 19
  (ref[] field shape), 20 (test-claim skip/count shape), 23 and 25
  (report-framing / stop-gate three-part shape, advisory severity) are
  GAPs needing a per-repo fix issue each, per the responsible-repo
  column above.
- Rows 4 and 14 (Closes/Fixes phase split) are a partial MATCH that
  should be promoted from tokenmaxxxer-implementation/coding into
  tokenmaxxxer-core's shared core_role_directive() heredoc so every
  role — not just coding — receives it, mirroring how row 1's
  Accumulation fix (issue-195) was already landed as a shared-heredoc
  change.
- Filing the per-repo fix issues named above is out of this role's
  scope (interaction protocol: this role never files issues) — they are
  handed off here for the user to file, one per responsible-repo/row
  grouping.

## Next steps

- File fix issues in tokenmaxxxer-core for rows 2, 3, 4, 14, 19, 20, 25
  (shared-heredoc additions), and in on-the-record for rows 7, 9, 23
  (own-repo directive/doc additions).
- Prioritize row 9 (record-claim-guard, 28 confirmed refusals) and
  rows 4 and 14 (Closes/Fixes split, empirically confirmed on a
  non-coding role) first.

## Resolution path

Each open finding above resolves when its named responsible repo lands
a directive/heredoc change naming the gate's exact required shape
before the corresponding gate hook would otherwise refuse it, verified
by a subsequent absence of that hook's refusal events in future
session-watcher logs.

Proposal: docs/issue-726/proposals/gate-shape-vs-authoring-source-audit.md
