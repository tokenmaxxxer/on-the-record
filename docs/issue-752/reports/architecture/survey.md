---
subject: issue-752
kind: survey
loop_state: phase1-survey
---

# Survey: core judgment capability (Audit C)

what was done: read-only sweep of the repo for the 5 sub-areas in #752 — produce-vs-decide,
consult(#699) as judgment channel, rulebook shaping of judgment vs format, risk-classification/
delegated-judgment gates, and missing core primitives for recorded reasoned judgment.

why: #752 asks for a classified (MET/PARTIAL/GAP) gap map with file:line evidence and rank,
before any change is proposed.

upstream: #752

## Findings

### 1. Produce vs decide — PARTIAL

- `on-the-record/hooks/directive.sh`:56-57 — the only "don't invent" rule found is scoped to
  issue-drafting ("you are the scribe, never the inventor"), not to general design/tradeoff
  judgment.
- `on-the-record/hooks/directive.sh`:70-72 — role routing ("who runs next") is explicitly left
  to the orchestrator's own unstructured judgment, no criteria given.
- `docs/issue-699/reports/implementation/survey.md`:48-53 — that survey's own conclusion: no
  hook fires only when a plain session is about to make a judgment call; `directive.sh` fires
  uniformly regardless of whether the message is a small judgment question or a full delivery.
- `docs/issue-699/reports/implementation/survey.md`:192-200 — grep for `delegat*` found no
  directive/hook that mechanically routes an inline judgment point to consult; the only
  enforcement (`deliverable-guard.sh`) blocks file writes, not in-conversation reasoning.

Missing mechanism: a hook that recognizes a judgment point (design/feasibility/risk/ambiguity)
and mechanically routes it to consult instead of leaving recognition to directive prose.
Belongs in `on-the-record/hooks/`.

### 2. Consult (#699) as judgment channel — PARTIAL (proposed, not enforced)

- `on-the-record/commands/consult.md`:14-20 — consult loads the role's rulebook and returns one
  judgment (`{"answer","confidence","caveats"}`, line 40) — a real verdict, not open Q&A.
- `docs/issue-699/proposals/consult-and-goal-loop.md`:15-20 — R1 judgment-return channel, R2 a
  *norm* (not a gate) to recognize judgment points, R3 session owns decompose→delegate→integrate.
- `docs/issue-699/proposals/consult-and-goal-loop.md`:186-190 — out-of-scope note: mechanical
  enforcement of the R2 delegation norm is explicitly deferred to a follow-up issue.
- `docs/reports/consult-log.md`:1-6 — trace file exists but is header-only; no evidence consult
  has been exercised yet, consistent with proposal (not landed) status.
- `on-the-record/commands/consult.md`:50-56 — consult explicitly is not a delivery act (no
  branch/commit/PR/board write).

Gaps: (1) no mechanical trigger forces a call to consult at a judgment point (norm only);
(2) a consult answer isn't tied back into a durable decision record with alternatives — it's a
Q&A trace line, not a reasoned/alternatives-considered artifact; (3) the "judgment" authority is
another LLM role session, not a designated human, for cases meant for human sign-off.

Related: #699 already targets this gap (phase-1 proposed); #752 should build on it, not
duplicate it.

### 3. Rulebook shaping of judgment vs format — PARTIAL, trending format-heavy

- `roles/specs/architecture.spec.json`:4-40 — `considered_options` (ref[]) is required;
  `decision_drivers` — the actual reasoning-for-weighing field — is `"required": false`.
- `roles/specs/architecture.spec.json`:41-44 — `considered_options` is only existence/
  reference-checked ("must each resolve to a real alternative discussed... no orphan
  references"), not checked for weighing quality.
- `roles/specs/architecture.spec.json`:45-47 — `outcome` is recomputed from the referenced
  ADR's own status field — mechanical consistency, not judgment quality.
- `docs/handbooks/architecture-methodology.md`:1-47 — the one exception: the axis-evaluation
  template requires READ/EXECUTE/CRITERIA/CITATION blanks and explicitly forbids a step that
  "reduces to 'consider whether X' with no checkable output" (see `docs/handbooks/architecture-methodology.md`:41-47).
  This is real judgment-procedure shaping, but scoped only to the fixed set of `judgment_axes`
  named in `docs/decisions/2026-08-10-judgment-axis-matrix.md`, and only to the roles that own
  one of those axes.

Missing mechanism: outside the axis matrix, no rulebook enforces a decision procedure
(weighing considered_options against criteria before committing) — only that alternatives are
named and outcome/status stay internally consistent. Belongs in `roles/specs/*.spec.json` +
`gates/role_spec_shape.py` / `gates/record_lint.py`.
unverifiable: whether the same optional-`decision_drivers` pattern recurs across all
`roles/specs/*.spec.json` files — only `roles/specs/architecture.spec.json` was read in full; a
full sweep of every role spec file was out of this pass's budget.

### 4. Risk-classification / delegated-judgment gates — GAP (judgment-enabling); MET (judgment-policing)

- `docs/handbooks/risk-classified-approvals.md`:1-16,28-37 — `gates/risk_report.py` classifies
  already-open phase-1 proposals `high`/`low`, and is explicitly advisory-only: "never grants
  approval... a `low` classification does not excuse skipping [human APPROVE]."
- `docs/issue-699/reports/implementation/survey.md`:123-132 — `delegated-judgment-gate.sh`
  (#573) operates only as a PreToolUse gate on an already-existing candidate PR at merge time,
  requiring cross-role quorum; not invocable ad hoc mid-conversation. "A merge-approval
  automation, not a consult primitive."
- `docs/issue-688/proposals/2026-08-11-delegated-judgment-corpus-path.md` — confirms the gate's
  mechanism is AND-composition of axis matches to compute an auto-approve/escalate verdict —
  policing, not decision-weighing aid.
- `docs/decisions/2026-08-10-judgment-axis-matrix.md`:31-36 — `check_axis_ownership` flags a
  zero-owner axis (coverage check), not the content of any judgment made on that axis.

No gate found that helps an agent enumerate options or weigh them against criteria before
commitment — every gate found fires against an artifact that already embodies a completed (or
absent) judgment. This is the most consistent pattern across sub-areas 3 and 4.

### 5. Missing core primitives — GAP

- `roles/specs/architecture.spec.json`:16-19,21-24 — `considered_options` (required) exists as
  a partial primitive, but `decision_drivers` (reasoning-for-weighing) is `required: false`, and
  only ref-resolution is checked (§3 above).
- Working informally in prose, not schema-enforced: `docs/issue-699/proposals/consult-and-goal-loop.md`:77-109
  and `docs/issue-688/proposals/2026-08-11-delegated-judgment-corpus-path.md`:33-45 both contain
  genuine "rejected alternative + why" sections — proof the pattern works when a role chooses to
  write it, but nothing requires or checks it.
- `docs/issue-699/reports/implementation/survey.md`:204-215 — the role-handoff contract (v3)
  itself is not stored in this repo (`core/contract/role-handoff-contract.md` lives elsewhere),
  so any claim about a contract-level required reasoning field is unverifiable from this repo.
unverifiable: whether contract v3 (out-of-repo) already requires a reasoning/alternatives field
— the contract text is not present in this repo to check.

Missing primitive: a schema-and-gate-enforced decision-record shape where (1) two or more real
alternatives each carry a stated reason-rejected, (2) a reasoning/tradeoff field is
`required: true` (currently false), (3) a gate checks content presence of that reasoning, not
just ref-resolution. Generalizes the axis-evaluation template's checkable-step discipline
(§3) beyond the fixed axis set to ordinary decision records.

## Rank (northpole-centrality × observed-failure-frequency across the 5 areas)

1. **missing decision-record primitive (§5)** — every other area's gap points at this same root:
   nothing forces or checks weighed reasoning; only naming/presence is enforced.
2. **gates police, don't enable (§4)** — recurred identically in risk_report, delegated-judgment-
   gate, and axis-ownership check; no counter-example found.
3. **produce-vs-decide routing (§1)** — orchestrator's "judgment call" language has no mechanical
   catch, but #699 already proposes a norm-level (not yet mechanical) fix.
4. **consult coverage gap (§2)** — real channel exists, structurally sound, but unenforced and
   not yet wired to a decision record.
5. **rulebook format vs procedure (§3)** — one strong counter-example already exists (axis
   template) showing the pattern is buildable; narrowest scope to fix.

## Related open work (not duplicated)

#699 (consult + goal-loop norm), #573 (delegated-judgment-gate origin), #586 / judgment-axis
matrix ADR, #688 (gate corpus-path bugfix), #319 (risk_report origin). No open issue found
proposing a required-reasoning/alternatives-considered schema field or a pre-commit
decision-support gate — that gap is the open target for this issue's follow-on phase.

## Note on subagent output

The research subagent's raw output for this survey was flagged by the harness as containing an
instruction-shaped pattern ("bypass-permissions") and neutralized before reaching this session.
No directive from that flagged span was followed; findings above were independently checked
against the cited file:line locations before being recorded here.

next steps: on APPROVE issue-752/architecture, write docs/issue-752/reports/architecture.md
(phase-2 record) synthesizing this survey into ranked MET/PARTIAL/GAP findings per the
acceptance criteria, and hand off primitive-design work per the proposal's scope.

open findings: the points above under §1 through §5; none resolved by this pass — read-only per
issue provenance.

resolution path: phase-2, after human APPROVE, either by this architecture role continuing on
this same branch/PR, or by a follow-up issue scoped to whichever HAND-OFF role owns the concrete
primitive (schema field lives in architecture's `roles/specs/*.spec.json` scope; a new gate
script may hand off to whichever role owns `gates/`).
