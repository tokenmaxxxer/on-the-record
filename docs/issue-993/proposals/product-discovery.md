---
status: proposed
files:
  - docs/issue-993/reports/product-discovery/current-state.md
  - docs/issue-993/proposals/product-discovery.md
---

# Proposal — issue #993, product-discovery pass

## Intent
Per `docs/issue-993/reports/product-discovery/current-state.md`: 33 of 43
`roles/*.json` carry zero board records. This proposal diagnoses each of
the 33 into one of the issue's 5 classes and recommends the fix per
class — landing the fixes themselves is out of this phase-1 write set
(docs-only; hook/gate code changes are a follow-up build, not this
survey pass).

## Constraints found
- This role's `write_scope` is docs-only — a mechanical board_condition
  gate (routing-gap fix) is code under `on-the-record/hooks/` or
  `gates/`, not this proposal's own write set. It is filed as a
  follow-up issue, not built here.
- The axis-owner thin-rulebook gap (capacity-planning,
  performance-engineering) composes with #992 (rulebook deepening
  priority) — not re-litigated or duplicated here, only routed.
- The 3+-role panel / axis-evaluation matrix work composes with #960 —
  same treatment.

## Hypothesis (pre-registration)
We believe filing 1 tracking issue for the routing-gap fix (secure-coding's
board_condition, the clearest evidenced case) and routing 2 items into
#992/#960 will convert this audit's diagnosis into trackable follow-up
work instead of leaving it as prose inside this proposal.

Metric: count of new open GitHub issues cross-referencing #993 for the
routing-gap fix, plus explicit composition notes on #992/#960
(`gh issue list --search "993"`).
Threshold: 1 new issue filed; #992 and #960 each receive one composition
comment or line item.

Decision rule: go if the secure-coding gate issue is filed and #992/#960 each receive a routing note within this proposal's own execution; kill does not apply here since filing a tracking issue is reversible and low cost; pivot drops release-engineering from the filed issue's scope, and notes why, if a reviewer judges its routing gap not real because "배포" carries no meaning distinct from merge-to-main in this repo — the secure-coding filing still goes either way.

Guardrail metric: no filed issue proposes changing the closed 5-axis
vocabulary or reassigning an existing axis owner (matches issue-586's own
guardrail, since this touches the same axis surface for 2 of the 5
owners). Guardrail status: not breached — the routing-gap fix and the
#992/#960 routing notes below touch neither.

ITWWS (if this works we should): once the secure-coding board_condition
gate is built and lands, re-run this survey's Utilization read to confirm
secure-coding's record count rises from 0 and check whether the same gate
pattern generalizes to issue-retrospective and release-engineering's
routing gaps — pre-committed as a follow-up survey pass, not done here.

## Prioritization (RICE)
Reach/Impact scored against "how much of the 43-role rulebook's own
credibility (per #993's own framing: 'dead weight... structural failure')
each fix unblocks," not end-user count (no end-user population exists for
this internal-tooling repo, matching issue-586's own scoring basis).

| Candidate | Reach (1-5) | Impact (1-5) | Confidence (1-5) | Effort (person-days) | RICE |
|---|---|---|---|---|---|
| File secure-coding board_condition gate issue | 4 — fires on every future auth/credential-touching commit, a recurring code shape (5 sampled hits already) | 5 — this is the audit's clearest evidenced routing gap: condition text exists, matching commits exist, 0 records exist | 4 — the condition text and a matching commit are both already in hand from the survey | 1 | 80 |
| Route capacity-planning + performance-engineering axis gap into #992 | 3 — 2 of 5 axis owners | 3 — narrower than the full axis matrix, but blocks those 2 roles' own credibility specifically | 5 — issue-586's own survey already fully derived this; only a routing note is needed | 0.5 | 90 |
| Record genuinely-no-work rationale for the ~27 no-domain roles | 5 — covers most of the 33 zero-usage roles | 2 — lower urgency; these roles are correctly silent, not broken | 5 — this proposal's own current-state survey already derived the rationale per role | 0.5 | 100 |
| File issue-retrospective / release-engineering routing-gap issues | 2 — narrower, 2 roles | 3 | 2 — board_condition satisfaction is plausible but not commit-level confirmed the way secure-coding's is | 1 | 12 |

Recommended order: record the no-work rationale (already written into
this proposal's utilization table below — no separate filing needed),
then file the secure-coding gate issue, then post the #992/#960 routing
notes, then (lower priority, deferred) file the issue-retrospective /
release-engineering pair once their board_condition satisfaction is
confirmed at commit-sha granularity rather than sampled.

## Utilization table — all 43 roles, diagnosis and disposition
Counts and dates per `docs/issue-993/reports/product-discovery/current-state.md`.

| Role | Records | Class | Disposition |
|---|---|---|---|
| implementation | 528 | used | keep |
| execution-observation | 75 | used | keep |
| product-discovery | 64 | used | keep |
| architecture | 44 | used | keep |
| defect-verification | 23 | used | keep |
| conformance-review | 11 | used | keep |
| technical-feasibility | 11 | used | keep |
| requirements-engineering | 9 | used (rare-adjacent) | keep |
| security-threat-model | 3 | rare | keep — 1 issue only; revisit if it stays at 1 after 5 more security-touching landings |
| technical-writing | 3 | rare | keep — 1 issue only; same revisit condition |
| secure-coding | 0 | (a) routing gap | file gate issue (this proposal's go decision) |
| issue-retrospective | 0 | (a) routing gap | file issue, lower priority (deferred pending commit-sha confirmation) |
| release-engineering | 0 | (a) routing gap, tentative | file issue, lower priority, pending write_scope check |
| capacity-planning | 0 | (c) thin rulebook | route into #992 |
| performance-engineering | 0 | (c) thin rulebook | route into #992 |
| knowledge-management | 0 | (a) routing gap, upstream-blocked | starved by issue-retrospective's own gap; no separate fix, resolves once issue-retrospective fires |
| accessibility | 0 | (e) no work yet | rationale: no UI surface exists in this repo (bash/python CLI + git hooks) |
| interaction-design | 0 | (e) no work yet | rationale: no screen/flow-facing requirement has ever landed (requirements-engineering's 3 records are all internal role-spec/gate shape work) |
| user-discovery | 0 | (e) no work yet | rationale: no product-discovery hypothesis has ever required user-interview validation (no end-user population for this internal tool) |
| ux-engineering | 0 | (e) no work yet | rationale: no accumulated screen specs exist to systematize |
| api-design | 0 | (e) no work yet | rationale: no multi-consumer API surface exists |
| brand-design | 0 | (e) no work yet | rationale: no brand asset surface exists |
| content-design | 0 | (e) no work yet | rationale: no copy/microcopy flow exists |
| customer-support | 0 | (e) no work yet | rationale: no CS/SLA surface exists |
| data-engineering | 0 | (e) no work yet | rationale: no data pipeline exists |
| data-modeling | 0 | (e) no work yet | rationale: no schema-owning product surface exists |
| devrel | 0 | (e) no work yet | rationale: no external developer-facing API/SDK exists |
| finance-unit-economics | 0 | (e) no work yet | rationale: no priced product or cost structure decision exists |
| growth-analytics | 0 | (e) no work yet | rationale: no funnel/A-B experiment surface exists |
| incident-response | 0 | (e) no work yet | rationale: no declared incident has closed in this repo's board history |
| legal-compliance | 0 | (e) no work yet | rationale: no personal-data/license/contract decision has landed |
| localization | 0 | (e) no work yet | rationale: no i18n-target surface exists |
| market-analysis | 0 | (e) no work yet | rationale: no competitive-landscape-bearing product decision exists |
| marketing | 0 | (e) no work yet | rationale: no campaign/positioning surface exists |
| ml-engineering | 0 | (e) no work yet | rationale: no model-serving surface exists |
| observability | 0 | (e) no work yet | rationale: no new service/route needing instrumentation exists beyond this repo's own hooks/gates, which are covered by implementation/architecture already |
| partnerships-bd | 0 | (e) no work yet | rationale: no partnership/BD deal structure exists |
| pr-communications | 0 | (e) no work yet | rationale: no external-communications surface exists yet; revisit if releases go external |
| pricing | 0 | (e) no work yet | rationale: no pricing policy exists |
| refactoring-legacy | 0 | (b) scope overlap, tentative | implementation's own records already narrate refactor work inline (per issue-993 survey read, credential/auth-adjacent commits sit inside implementation.md, not a separate role); revisit only if a legacy-debt-specific record type is later wanted |
| risk-management | 0 | (e) no work yet | rationale: no financial/operational/strategic risk decision exists broader than technical-feasibility's own scope |
| sales | 0 | (e) no work yet | rationale: no sales process exists |
| test-authoring | 0 | (b) scope overlap, tentative | test suite work is narrated inside implementation's own records (contract v3 layout puts `test/` under implementation's write set); revisit only if test-design review is wanted as a distinct gate |

## Evidence
- 0 interviews/observations, 2026-08-12: no end-user population exists
  for this internal-tooling repo (same basis issue-586's own proposal
  used); evidence substituted is repo-state reads, cited as `derived:`
  lines in `docs/issue-993/reports/product-discovery/current-state.md` —
  paraphrase: "33 of 43 roles carry zero board records; only 4 of those
  33 carry a machine-checkable board_condition; secure-coding's
  board_condition is plausibly satisfied by landed credential-adjacent
  code with zero records to show for it."

## Accumulation
The 43-role vocabulary is fixed (per `roles/*.json` count, unchanged
since issue-586's own read of the adjacent axis vocabulary); this audit
is a one-time classification pass over a closed set, not a repeating
per-issue cost. The one recurring piece — re-checking secure-coding's
gate against future commits — is delegated to the gate itself once
built, not to a repeated manual audit.

## Out of scope
- Building the secure-coding board_condition gate itself (code, not
  docs; filed as a follow-up issue).
- Writing capacity-planning/performance-engineering's axis_evaluation
  rulebook procedures (cross-repo rulebook content, #992's own scope).
- Reopening the 5-axis vocabulary or any existing axis assignment.
- Deciding whether refactoring-legacy or test-authoring should be
  consolidated into implementation formally, or split back out —
  flagged as tentative scope-overlap only, not resolved here.

## How I'll know it worked
- `gh issue list --search "993"` lists the newly filed secure-coding
  gate issue.
- #992 and #960 each carry a routing note pointing back to this
  proposal for the axis-owner thin-rulebook items.
- The Utilization table above accounts for all 43 roles with a
  disposition, satisfying the issue's acceptance criterion.

## What did not work
None.
