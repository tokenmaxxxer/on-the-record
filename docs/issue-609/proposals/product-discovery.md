---
status: proposed
files:
  - docs/issue-609/reports/product-discovery/current-state.md
  - docs/issue-609/reports/product-discovery/scout-brief.md
  - docs/issue-609/proposals/product-discovery.md
---

# Proposal — issue #609: spec-stage open-decision triage

Phase 1 only. Pre-registers hypothesis, metric, threshold, and decision rule per the issue's third
acceptance criterion ("Pre-registered effectiveness metric ... iterative decision rule registered
at discovery time") and this role's own contract obligation. Grounded in and extending #573's
merged product-discovery proposal and #586's completed axis matrix, not re-deriving either; does
not re-run #573's Step 1 sweep (see scout-brief.md skip record).

## Open questions resolved

**1. What record shape an open-decision item gets.** Reuse the existing `axis_evaluation` shape
(`gates/role_spec_shape.py::check_axis_evaluation_entry`) for the *owning role's evaluation of the
item*, but the item itself needs one new, thinner shape one layer upstream: `{item, source_role,
source_path, candidate_axes}` — the ambiguity as recorded by the role that declined to settle it,
before any axis-owning role has evaluated it. This mirrors #573's own layering (a candidate decision
exists as an object before any axis role evaluates it) rather than inventing a second, parallel
evaluation vocabulary; the evaluation itself, once triage runs, is a `axis_evaluation` entry
verbatim — same `supports`/`contradicts`/`no-opinion` verdicts, same citation requirement — so
`check_axis_evaluation_entry` needs no change, only a new caller.

**2. How an open decision maps to the axis matrix.** Mechanically, from `candidate_axes` matched
against the same five-axis table #586 completed (`docs/decisions/2026-08-10-judgment-axis-matrix.md`)
— never orchestrator ad-hoc routing, per the issue's explicit requirement. A role recording an open
decision states which axis(es) it believes the ambiguity concerns (e.g. token-storage-format ->
`attack_potential`; rate-limit-policy -> `external_burden`; schema -> whichever axis the schema
question's blast radius/reversibility maps to under #511's classifier) at the moment it declines to
settle the item — the same self-tagging discipline #573 already requires of a role recording a
judgment-derived candidate decision. This keeps triage a mechanical table lookup (item's stated
axis -> #586's owning role) rather than a second inference step the orchestrator would otherwise
have to perform, which is exactly the ad-hoc-routing failure mode the issue rules out.

**3. What closes the escalation bar.** Both conditions the issue names, either one sufficient (an
OR at the escalation gate — not to be confused with #573's AND gate for auto-approve, which this
does not touch): (a) the item exceeds the registered depth/impact thresholds (reuses #573's
existing two-axis AND check verbatim — an item that does NOT clear #573's own auto-decide gate is,
by definition, above threshold), or (b) the panel's verdicts conflict (more than one owning role
evaluates the same item and their verdicts disagree — one `supports`, another `contradicts`, on the
same axis-mapped item). Either condition alone escalates; only an item that clears BOTH the
depth/impact gate AND unanimous/single-role non-conflicting verdicts resolves without the operator.
This is the same asymmetric-conservative shape #573 chose for auto-approve (AND to auto-decide, any
single disqualifier escalates), applied here to the escalation direction instead of the approval
direction — deliberately not a new design, since the issue asks for extension, not reinvention.

**4. What "routed to the owning expert role(s) for a recorded evaluation" produces before
escalation.** The same four-field audit record #573 registered (derivation source, impact grade,
evaluating role + verdict per axis clause invoked, decision/outcome + timestamp), with "decision"
here meaning "resolved without escalation" or "escalated" rather than approve/reject — and when it
escalates, the evaluations attached are exactly those four-field records, not a fresh operator-facing
summary. This is what makes "arriving WITH the expert evaluations attached" (issue text) auditable
rather than asserted.

## Candidates scored (RICE)

Reach/Impact scored against "spec-stage open-decision items reaching the operator per proposal
document" (no direct log exists yet; scored qualitatively against #573's own approval-act cadence,
since open decisions and approval acts both fire on the same per-role-proposal rhythm).

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Thin upstream item shape + reuse of #573's `axis_evaluation`/two-axis gate verbatim + OR-escalation (threshold-exceeded OR panel-conflict) + four-field record | 4 | 5 | 0.6 | 2 | 6.0 | **Keep — primary hypothesis (H1)** |
| 2 | New, independent open-decision evaluation vocabulary (own verdict set, own audit shape, not reusing #573's `axis_evaluation`) | 3 | 3 | 0.3 | 4 | 0.68 | Reject — duplicates machinery #573 already validated for the identical judgment shape (an expert role stating supports/contradicts/no-opinion with citation); the issue explicitly asks for "same ... discipline ... as #573/#587," not a parallel one |
| 3 | Orchestrator classifies each open decision's axis itself at triage time (no self-tagging by the source role) | 3 | 4 | 0.2 | 3 | 0.8 | Reject — this is exactly "orchestrator ad-hoc routing," which the issue explicitly rules out; relevance must come from the axis matrix mechanically, and mechanical requires a stated tag to look up, not an orchestrator inference |
| 4 | AND-only escalation bar (both threshold-exceeded and panel-conflict required to escalate) | 4 | 2 | 0.5 | 2 | 2.0 | Reject — inverts the issue's own asymmetry; an item that clears the depth/impact gate but has genuinely conflicting expert verdicts must still escalate (per #573's own "conflicting verdicts never auto-resolve" logic), so AND would let a conflicted-but-low-impact item auto-resolve, which the issue does not authorize |
| 5 | No triage (status quo — every open decision reaches the operator wholesale) | 5 | 1 | 0.9 | 0 | 4.5 | Reject — the issue's own stated live-evidence baseline; addresses nothing, kept only as the degradation-clause fallback when no corpus exists |

Candidate 1 wins on impact and confidence despite candidate 5's higher raw RICE arithmetic, for the
same reason #573's own table rejected its low-effort candidates: RICE is a screen here, not the
verdict, and candidate 5 scores well only by not doing what the issue asks.

## Pre-registered hypothesis package

Guardrail metric: `open_decision_misroute_rate`, named and non-empty at this same registration
moment, distinct from the primary metric below — a win on the primary while the guardrail breaches
is a reduced-trust result, not a win, mirroring #573's own guardrail design for the same reason
(throughput gains that hide a misdirected or wrongly-resolved decision are worse than no gain).

**H1 (primary).** If a spec-stage open decision is triaged through the same axis-matrix routing and
two-axis (depth + impact) gate #573 already validated for approval acts — self-tagged by axis at
authoring time, evaluated by the owning role(s), and escalated only on threshold-exceeded OR
panel-conflict — then the fraction of open decisions reaching the operator with no expert evaluation
attached will fall, without an increase in decisions that were resolved below the operator but
should have escalated — because today (per current-state.md) zero routing exists between an open
decision and any axis-owning role, so the baseline is 0% triaged by construction.

- **Metric**: `open_decision_triage_rate` = (open-decision items that receive an owning-role
  evaluation before reaching the operator) / (total open-decision items recorded across all
  proposals/specs in the measurement window), measured over the next 20 qualifying open-decision
  items recorded after the mechanism ships in a target repo whose judgment-capture corpus (the
  depth axis's source) is non-empty — per the degradation clause below, the window cannot start
  before that.
- **Threshold**: baseline is 0% (current-state.md: no routing mechanism exists today). Decision
  threshold: `open_decision_triage_rate` ≥ 30% — the same threshold #573 registered for its own
  analogous metric, kept identical rather than re-derived, since both metrics measure the same
  underlying question (does axis-matrix routing meaningfully reduce what reaches the operator
  undifferentiated) on the same per-role-session cadence and #573's own registered value already
  accounts for the intended asymmetric-conservative design escalating most novel items.
- **Guardrail status at measurement**: `open_decision_misroute_rate` (items later found, on review
  of the audit-record trail, to have been resolved below the operator when they should have
  escalated — e.g. a panel-conflict that was missed because a role failed to self-tag an axis the
  item actually concerned) must stay ≤ 5% over the same window, stated explicitly next to the
  primary metric's value, never implied. 5%, matching #573's own guardrail bound, for the identical
  reason: a misroute here is a wrong decision reaching the wrong resolution, not a wrong flag.
- **Decision rule**: `open_decision_triage_rate` ≥ 30% AND `open_decision_misroute_rate` ≤ 5% ->
  **go**. If triage rate falls short -> **pivot**: widen the self-tagging vocabulary/examples roles
  use to map an ambiguity to a `candidate_axes` entry (same "widen the match, don't loosen the gate"
  rule #573 pre-registered), not the escalation OR-condition. If misroute rate exceeds 5% regardless
  of triage rate -> **kill-and-redesign**: require multi-axis citation confirmation before an item
  is allowed to resolve without escalation, or narrow which decision classes are eligible for
  self-tagged triage at all.
- **Gaming-resistance argument**: identical to #573's — the owning role's evaluation is a recorded,
  re-derivable `axis_evaluation` citation, not a self-report field; the audit record is produced by
  the triage mechanism at routing time, not asserted by the role under audit after the fact.
- **Failure signature**: fails quietly if the self-tagging step under-matches (a role too
  conservative about which axis an ambiguity concerns escalates everything, which looks identical
  in `open_decision_triage_rate` alone to "correctly nothing was eligible") — named here so
  architecture/implementation is on notice, mirroring #573's identical named blind spot for its own
  metric.

## ITWWS (if this works we should ...)

If H1 proves out at the ≥30%/≤5% thresholds, fold spec-stage open-decision triage into the same
periodic re-review cadence #573's ITWWS already deferred for approval-act routing (axis-role
definitions and the axis matrix itself), rather than running two separate re-review loops for two
artifact types that now share one routing table. Deferred to whichever role owns the periodic-review
surface next, not actioned here — same deferral #573 registered.

## Deployment-surface constraint carried forward

No mechanism is built in this phase. Architecture/implementation own: the thin upstream
open-decision-item shape (schema, likely in `roles/specs/*.spec.json` or a new record-shape gate
alongside `check_axis_evaluation_entry`), the triage gate that maps `candidate_axes` -> #586's
owning-role table and applies #573's two-axis AND check plus the OR-escalation rule, and the
audit-record write path. No GitHub Actions — matches this repo's standing constraint (#566) that
enforcement lives in deployed hooks.

## Degradation (restated from current-state.md, binding on architecture/implementation)

The judgment-capture corpus has zero entries in this repo right now. Per the issue's explicit
requirement, this means: no open decision resolves below the operator today — every open decision
escalates until the corpus is non-empty, consistent with #573's own degradation rule. The
pre-registered measurement window above does not open until that condition changes.
