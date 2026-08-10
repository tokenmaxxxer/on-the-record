# Current-state survey — issue #609: spec-stage open-decision triage

## Background / context

#573 (merged) shipped delegated-judgment machinery for APPROVAL ACTS only: a two-axis AND gate
(depth from a docs/product judgment + #511's mechanical impact grade), axis-owning expert roles
holding approval authority via `judgment_axes`/`axis_evaluation` (`gates/role_spec_shape.py`), and
a four-field audit record. #586 (merged) completed axis ownership — all five methodology axes
(`alignment`, `maintenance_complexity`, `external_burden`, `attack_potential`, `performance`) now
have exactly one owning role each (`docs/decisions/2026-08-10-judgment-axis-matrix.md`). #587
(merged) built execution-observation/remediation around that same routing machinery. None of the
three touches SPEC-STAGE OPEN DECISIONS — ambiguities a role records in its own proposal/spec
because it correctly declines to arbitrarily settle them (this issue's own trigger: a
requirements-engineering role correctly declined to settle token-storage/schema/sync/rate-limit
ambiguities, then queued the whole list for the operator regardless).

Confirmed by directory/code inspection, not assumed:
- `gates/role_spec_shape.py` defines `_JUDGMENT_AXES` (5, closed per the #586 ADR),
  `check_role_judgment_axes`, `check_axis_ownership`, and `check_axis_evaluation_entry` (verdict in
  `{supports, contradicts, no-opinion}`, citation required, `finding` required only when
  `contradicts`). This shape is defined for **approval acts** — it validates one role's evaluation
  of a candidate *decision already proposed for approve/reject*, not an *open, unresolved* item a
  proposal author is explicitly flagging as unsettled.
- The judgment-capture corpus directory (docs/product, no trailing file) still has zero entries in
  this repo (confirmed: the directory does not exist). #573's degradation clause ("no decision
  auto-decides today; every decision escalates until the corpus is non-empty") is still the live
  state — nothing has changed this since #573/#587 merged.
- No `open_decision`, `open-decision`, or `spec-stage` record shape exists anywhere in this repo
  (grepped docs/, roles/, gates/, on-the-record/) — the only hits are unrelated issues (#68, #172,
  #457, #54, #246, #271) using "open" in prose, not as a record kind.
- Role proposal files in this repo (e.g. `docs/issue-573/proposals/product-discovery.md`, section
  "Open questions resolved") already contain a de facto "open decision" pattern in free prose — the
  author states the open question, the resolution, and the citation basis, inline, with no
  structured shape and no routing to another role for evaluation. This is exactly the pattern the
  issue's live evidence describes at a larger scale: individually-reasonable prose entries, still
  queued wholesale for the operator with no axis-mapping step in between.
- `roles/*.json` / `roles/specs/*.spec.json` carry `judgment_axes` (opt-in, 2 roles currently:
  `architecture`, `security-threat-model` per grep) — the axis-ownership routing table this issue's
  triage step must reuse, not re-derive. No role file has any field describing how it should surface
  an *open decision it cannot itself resolve* toward that table.

## Problem, stated without the proposed solution (JTBD)

- **Job performer**: the operator, at spec-review time, receiving a role's proposal/spec document.
- **Job**: see only the open decisions that are genuinely novel value judgments or exceed the
  registered depth/impact thresholds — each already carrying the relevant expert role(s)' recorded
  evaluation — rather than every ambiguity a role's proposal happened to leave open, undifferentiated
  by how mechanically resolvable or how consequential each one is.
- **Circumstance**: #573/#586 already route *approval acts* to axis-owning roles by axis match and
  the two-axis (depth + impact) AND gate; nothing today applies that same routing to an *open item
  inside a proposal/spec* before it reaches the operator — a role that correctly declines to
  arbitrarily settle an ambiguity has no mechanism to hand that ambiguity to the roles positioned to
  judge it first. The judgment-capture corpus remains empty in this repo, so the depth axis (an
  operator judgment already on record) has nothing to derive from for either the existing
  approval-act gate or any extension of it.
- **Desired outcome**: an open decision recorded in a proposal/spec is mapped to the judgment-axis
  matrix, routed to the owning expert role(s) for a recorded evaluation, and only escalates to the
  operator (with those evaluations attached) when it exceeds registered depth/impact thresholds or
  the panel's verdicts conflict — mechanically, from the axis matrix, never by orchestrator ad-hoc
  routing. With zero recorded corpus, every open decision still escalates (degradation consistent
  with #573).

## Where this sits on the opportunity-solution tree

- **Outcome**: the operator's spec-review attention is spent only on open decisions that are new
  value judgments or exceed impact/depth thresholds — not on every ambiguity a role declined to
  settle, regardless of how mechanically routable that ambiguity already is.
- **Opportunity**: #573/#586 built the axis-ownership routing table and the approval-act gate shape,
  but scoped it to decisions already proposed for approve/reject. Spec-stage open decisions — a
  distinct, earlier artifact (an *unresolved* item inside a proposal, not a *candidate* decision
  awaiting approval) — bypass that routing entirely and reach the operator wholesale, reproducing
  the decision-fatigue channel #573 closed, one stage earlier in the pipeline.
- **Candidate solutions**: scored in the proposal — whether an open-decision item reuses the
  existing `axis_evaluation` shape as-is vs. needs its own record shape one layer upstream of it;
  whether triage runs as a new gate step vs. is folded into an existing one; what closes the
  escalation bar (threshold-exceeded vs. panel-conflict, both from the issue text) vs. any softer
  bar.
- **Discriminating assumption test**: whether an open-decision item can be mapped onto the *same*
  five-axis matrix and depth/impact threshold logic #573 already validated for approval acts,
  without inventing a second, parallel routing table — this is the open question the proposal's
  pre-registered hypothesis targets.

## Degradation, stated explicitly

The judgment-capture corpus has zero entries in this repo right now (confirmed above, unchanged
since #573). Per #573's own degradation rule, carried forward here per the issue's explicit
requirement ("degradation consistent with #573... empty corpus -> full escalation"): with no
recorded operator judgment to derive a depth match from, **no open decision can be resolved below
the operator today** — every open decision escalates to the operator until the corpus is
non-empty. This is this repo's actual current state, not a hypothetical edge case, and the
proposal's measurement window does not open until that condition changes.
