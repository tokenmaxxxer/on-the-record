# Current-state survey — issue #573: delegated judgment / tiered auto-approval

## Background / context

Step 1 (`docs/issue-573/reports/technical-feasibility/survey.md`, merged) surveyed four
methodology classes for delegated judgment — ITIL/CAB risk-based change management, code-review
auto-merge/policy-as-code, aviation/medical delegation protocols, RFC/ADR governance — with
primary-source citations. That survey is descriptive only; no mechanism, no verdict. This document
is Step 2's own current-state check: what exists in *this* repo today that the delegation rule
would sit on top of.

Confirmed by directory listing, not assumed:
- The target corpus directory for #566's captured operator judgments (docs/product, no trailing
  file) **does not exist** in this repo. `roles/product-discovery.json`,
  `roles/specs/product-discovery.spec.json`, and `on-the-record/hooks/product-capture-stopgate.sh`
  (+ its test) exist — the *capture mechanism* for #566 shipped — but no operator
  requirement/priority/philosophy/goal statement has yet produced an entry under that directory in
  this repo's own tree. The depth axis this issue adds therefore has **zero recorded corpus** to
  derive from right now.
- `docs/specs/impact-classification.md` (issue #511, merged) already implements the mechanical
  impact axis: `classify_axes()` in `gates/risk_report.py` returns four grades (blast radius,
  reversibility, propagation, existing signals) plus `requires_individual_approval` from the
  dominant-axis rule (reversibility grade 4 alone forces individual approval; the other three
  never override it). This exists, is wired, and is not this issue's to rebuild.
- `docs/specs/approvers.md` lists two human accounts; no "expert-role agent" account or role-level
  approval-authority concept exists there today — approval is currently binary human-or-nothing.
- `roles/*.json` and `roles/specs/*.spec.json` already define role identity and `write_scope`
  per role (the blast-radius/propagation axes read these directly), so a role-scoped
  "expert evaluates its own axis" concept has a structural precedent to attach to, but no role
  file today carries an axis-evaluation record format (alignment / maintenance-complexity /
  external-burden / attack-potential / performance) — that format does not exist yet.
- #476 (merged, `docs/issue-476/`) already established and shipped the anti-theater line this
  issue must inherit rather than re-derive: a gate that checks *field presence* is gameable; the
  countermeasure is mechanized independent re-execution, not a self-report. #566 (merged) already
  applied the same argument to requirement capture. Neither #476 nor #566 built an *approval*
  mechanism — both are capture/verification, not decision-authority delegation.

## Problem, stated without the proposed solution (JTBD)

- **Job performer**: the operator, at the point where a deliverable or decision is ready for
  approve/reject and currently must look at every one of them regardless of how mechanically
  derivable or low-impact the decision is.
- **Job**: get decisions that are *already implied* by judgments the operator has previously and
  explicitly recorded, and whose consequence is small/reversible, resolved without the operator's
  attention — while every decision that is either a genuinely new value judgment or high-impact
  still reaches the operator, and every auto-decision remains checkable after the fact.
- **Circumstance**: no corpus of recorded operator judgments exists yet in this repo (the capture
  directory is empty); a mechanical impact classifier exists and is unused for approval routing;
  no role carries an axis-evaluation record format; the issue's own operator addition
  (2026-08-10) moves approval *authority* itself, not just evaluation, onto the domain-expert role
  agents for in-scope decisions, reserving the operator for above-threshold cases.
- **Desired outcome**: a decision is auto-approved or auto-rejected only when (a) it is derivable
  from an operator judgment already on record (depth) and (b) its mechanical impact grade is low
  (per #511's existing axes) — both required, never either alone — and only via a named expert
  role's own recorded axis evaluation, never the orchestrator's unrecorded reasoning; every
  auto-decision leaves a one-line auditable record; and with no recorded corpus, nothing
  auto-decides at all.

## Where this sits on the opportunity-solution tree

- **Outcome**: the operator's attention is spent only on decisions that are new value judgments or
  carry real blast radius/reversibility risk — not on decisions the operator already, in effect,
  made.
- **Opportunity**: today there is no route from "operator already decided this class of thing" to
  "this instance doesn't need to be asked again" — #511 shipped impact grading but nothing reads
  it for approval routing, and #566 shipped judgment capture but nothing reads *that* for approval
  routing either. The two existing mechanical pieces sit unconnected to any decision-routing use.
- **Candidate solutions**: scored below in the proposal — where the two axes combine (AND vs. OR),
  where axis-evaluation authority sits (per-axis expert role vs. one combined judge), what closes
  the auto-reject bar (contradiction-only vs. broader), and what the audit record must contain.
- **Discriminating assumption test**: whether an auto-decision derived from a two-axis check
  (depth + mechanical impact) and cited expert-role axis records is materially harder to
  rubber-stamp or drift than the single-axis/self-report mechanisms the merged survey found
  failing in every domain surveyed (CAB rubber-stamping, ODA/737 MAX scope creep, lazy-consensus
  misuse) — this is the open question the proposal's pre-registered hypothesis targets.

## Degradation, stated explicitly

The judgment-capture corpus has no entries in this repo right now (confirmed above). Per the
issue's own acceptance criterion, the depth axis has nothing to derive from, so **no decision may
auto-decide today** — every decision escalates until the corpus exists. This is not a future edge
case; it is this repo's actual current state, and the proposal's pre-registered hypothesis
measurement window does not start until #566's capture mechanism has produced at least one entry.
