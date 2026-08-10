---
status: proposed
files:
  - docs/issue-573/reports/product-discovery/current-state.md
  - docs/issue-573/reports/product-discovery/scout-brief.md
  - docs/issue-573/proposals/product-discovery.md
---

# Proposal — issue #573: delegated judgment / tiered auto-approval

Phase 1 only. Pre-registers hypothesis, metric, threshold, and decision rule per this role's own
contract obligation and the issue's fourth acceptance criterion ("Effectiveness is pre-registered
... registered at discovery time"). No hook code, no gate code, no role-file schema change — that
is architecture/implementation's job. Grounded in the merged Step 1 survey
(`docs/issue-573/reports/technical-feasibility/survey.md`) and this repo's own current state
(`docs/issue-573/reports/product-discovery/current-state.md`); does not re-derive either.

## Open questions resolved

**1. How the two axes combine.** AND, never OR, matching the issue's own wording ("only when BOTH
hold"). Depth alone (a decision follows from a recorded operator judgment) does not auto-decide a
high-blast-radius/irreversible change; low mechanical impact alone does not auto-decide a decision
that is a genuinely new value judgment with no recorded precedent. This mirrors #511's own
rejection of a combined/weighted score for the impact axes themselves
(`docs/specs/impact-classification.md`, "Rejected: weighted composite / RPN") — two independent
gates, neither one able to override the other's refusal, is the same shape already chosen in this
repo for combining structural signals, now applied one level up to combine depth with impact.

**2. Where axis-evaluation *authority* sits.** The operator's 2026-08-10 addition is decisive
here: approval authority itself is delegated to the domain-expert role agent that owns each of the
five methodology axes named in the issue (alignment, maintenance complexity, external
burden/crawling, attack potential, performance) — not evaluation-only with the orchestrator still
casting the final vote. This maps directly onto the merged survey's CODEOWNERS/OPA finding: path-
and topic-scoped ownership, not diff-size, is what routes a decision to the party positioned to
judge it. Each axis is owned by one role (the role whose `write_scope`/domain the axis concerns —
e.g. the role that already evaluates external-request behavior owns the crawling-burden axis); the
owning role's own recorded evaluation is the axis's approval, full stop, when the two-axis gate is
satisfied. The operator is not "kept in the loop as a rubber stamp on the expert's finding" — that
would reproduce CAB rubber-stamping (Step 1 finding) by adding a second nominal check with no
independent basis to override the first. The operator owns exactly what the issue says: decisions
above the depth/impact thresholds, i.e. everything the two-axis gate does not clear.

**3. What closes the auto-reject bar.** Explicit contradiction only, per the issue's own stricter
bar for reject (information loss: the operator never sees a discarded deliverable). "Contradiction"
is scoped narrowly and mechanically checkable, matching medicine's enumerated-scope precedent
(Step 1: a written, dated Prescriptive Authority Agreement lists exactly which acts are in scope;
anything outside escalates) rather than open-ended judgment: an axis-owning role's evaluation
auto-rejects only when it cites a specific recorded operator-judgment entry (docs/product,
per #566's capture surface) and states which axis's evaluation the candidate decision directly
contradicts. Absence of a supporting judgment, ambiguity about which entry applies, or a
judgment-entry that merely fails to *support* the decision (rather than actively *contradicting*
it) all escalate — asymmetric with auto-approve by design, same asymmetry the issue states.

**4. What the one-line audit record must contain.** Four fields, each independently checkable
after the fact (per the merged survey's cross-cutting observation: every domain surveyed separates
the auto-tier criterion from a record of why *this instance* qualified) — derivation source (which
docs/product entry the depth axis matched), impact grade (the #511 `classify_axes()` output for
this decision, dominant-axis rule applied), evaluating role + verdict per axis clause invoked (not
every one of the five axes fires on every decision; only the axes the axis-owning role determined
were in scope for this particular decision are cited, but at least one must be, or the decision
was not derivable and should have escalated), and the decision itself (approve/reject) with a
timestamp. This is the mechanized-record countermeasure #476 already established (re-derivable,
not self-report) applied to an approval decision instead of a verification claim.

## Candidates scored (RICE)

Reach/Impact scored against "operator-facing approve/reject decisions per week" (no direct log
exists yet for this cadence; scored qualitatively against the same order of magnitude as #476's
and #566's role-session cadence, since all three fire on the same per-role-session rhythm).

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Two-axis AND gate (depth from docs/product + #511 mechanical impact), axis-owning expert role holds approval authority, contradiction-only auto-reject, four-field audit record | 4 | 5 | 0.6 | 3 | 4.0 | **Keep — primary hypothesis (H1)** |
| 2 | Mechanical impact axis alone (reuse #511, no depth check) | 4 | 2 | 0.7 | 1 | 5.6 | Reject — doesn't address the issue's core ask (judgments the operator already recorded); an unrecorded orchestrator inference of "low impact = fine to auto-decide" reproduces the exact #476 failure mode (approval justified by the orchestrator's own unrecorded reasoning) |
| 3 | Single combined LLM judge (one model call scores alignment+impact holistically, decides) | 3 | 3 | 0.2 | 4 | 0.45 | Reject — non-deterministic gate on a surface every other hook in this repo implements as deterministic checks; violates the issue's explicit "never by the orchestrator's own unrecorded reasoning" line directly, since a single holistic judge is exactly that |
| 4 | OR-combination (either axis alone triggers auto-decide) | 4 | 4 | 0.3 | 2 | 2.4 | Reject — issue states BOTH must hold; OR reproduces catalog drift (Step 1: ITIL standard-change scope widening past its original justification) by letting either axis alone stretch the auto-tier |
| 5 | No delegation (operator reviews every decision, #511/#566 stay unconnected to routing) | 5 | 1 | 0.9 | 0 | 4.5 | Reject — the actual current-state baseline; does not address the issue's stated goal (reduce decision fatigue) at all, kept only as the fallback the degradation clause reduces to when no corpus exists |

Candidate 1 wins on impact and confidence despite candidate 2/5's higher RICE arithmetic, because
RICE here is a screen, not the verdict: 2 and 5 score well only by *not doing the thing the issue
asks for* (cheap because they build nothing new, or build only what already exists). Effort/reach
arithmetic cannot be the deciding factor when the low-effort candidates fail the issue's own stated
requirement outright — consistent with how #566 treated its own RICE table (candidate 3 there
scored higher than the kept candidate and was still rejected on failure-mode grounds).

## Pre-registered hypothesis package

Guardrail metric: `auto_decision_reversal_rate`, named and non-empty at this same registration
moment, distinct from the primary metric (`decision_fatigue_reduction_rate`) below — a win on the
primary while the guardrail breaches is a reduced-trust result, not a win, per the merged survey's
own repeated finding (CAB rubber-stamping, ODA/737 MAX, lazy-consensus misuse: every domain that
failed did so by letting throughput look like a win while a scope/safety guardrail quietly slipped).

**H1 (primary).** If a decision auto-decides only when both the depth axis (derivable from a
recorded docs/product judgment) and the mechanical impact axis (#511's dominant-axis rule, low
grade) hold, evaluated and authored by the axis-owning expert role and never by the orchestrator's
own reasoning, then the operator's decision load will fall without an increase in wrongly-auto-
decided outcomes — because today (per current-state.md) no routing exists at all between the two
already-shipped mechanical pieces (#511, #566) and any approval decision, so the baseline auto-
decision rate is 0% by construction.

- **Metric**: `decision_fatigue_reduction_rate` = (decisions auto-decided under the two-axis gate)
  / (total decisions eligible for approve/reject), measured over a rolling window of the next 20
  qualifying decisions after the mechanism ships in a target repo whose docs/product corpus is
  non-empty (per the degradation clause below, the window cannot start before that).
- **Threshold**: baseline is 0% (current-state.md: no routing mechanism exists today). Decision
  threshold: **`decision_fatigue_reduction_rate` ≥ 30%** — set below half so a first cut that
  correctly escalates most novel/ambiguous decisions (the intended asymmetric-conservative
  design) still counts as working, while still requiring the mechanism to visibly reduce load
  rather than round down to the no-delegation baseline in practice.
- **Guardrail status at measurement**: `auto_decision_reversal_rate` (auto-decisions the operator,
  on review of the audit-record trail, later judges should have escalated — an auto-approval that
  in fact contradicted a recorded judgment, or an auto-reject of something that was not in fact an
  explicit contradiction) must stay **≤ 5%** over the same window, stated explicitly next to the
  primary metric's value, never implied. 5%, not #566's 20% false-flag tolerance, because a
  reversal here is a wrong *decision* (Step 1's stricter reject bar; 737 MAX-class failure shape),
  not a wrong *flag* on a capture hook — the consequence of getting this axis wrong is categorically
  more expensive than the consequence #566's guardrail was bounding.
- **Decision rule**: `decision_fatigue_reduction_rate` ≥ 30% AND `auto_decision_reversal_rate` ≤
  5% → **go**. If `decision_fatigue_reduction_rate` falls short → **pivot**: widen the depth axis's
  match vocabulary against docs/product entries (same "widen before declaring insufficient" rule
  #566 pre-registered for its own detector) rather than loosening the impact axis or the AND
  requirement, since the merged survey's failure modes are all failures of *loosening* the
  auto-tier, never of it being too narrow. If `auto_decision_reversal_rate` exceeds 5% regardless
  of the primary metric → **kill-and-redesign**: narrow axis-role scope (require more than one
  axis clause cited, not just one) or restrict which decision classes are eligible at all — the
  guardrail catching this before operator trust erodes is the entire point of Step 1's repeated
  "detection/correction after the fact is the only mitigation every domain found" observation;
  this repo's version does not get to be the domain that skips the mitigation.
- **Gaming-resistance argument**: the axis-owning role's evaluation is a recorded, re-derivable
  citation (a specific docs/product entry plus a specific #511 grade), not a self-report field —
  identical structure to, and directly reused from, #476's H1 gaming-resistance argument and
  #566's H1 cross-check design. The audit record is produced by the gate mechanism at decision
  time, not asserted by the role under audit after the fact.
- **Failure signature**: fails quietly if the depth-axis match is narrow enough that a genuinely
  applicable recorded judgment goes unmatched (an over-cautious detector that never triggers looks
  identical to "correctly nothing was eligible" in this metric alone, the same blind spot #566
  named for its own detector) — named here so architecture/implementation is on notice that
  `decision_fatigue_reduction_rate` cannot by itself distinguish "mechanism works, few eligible
  decisions occurred" from "mechanism under-matches"; a periodic manual audit of escalated
  decisions (were any of them actually derivable?) is a follow-up, not built here.

## ITWWS (if this works we should ...)

If H1 proves out at the ≥30%/≤5% thresholds, extend axis-owning role review to a periodic
re-review cadence over the docs/product corpus and the axis-role definitions themselves — mirroring
the merged survey's strongest audit-loop precedent (medicine's mandatory annual PAA re-signature,
Python's PEP 13 supermajority amendment) — so the delegation rule does not drift the way ITIL's
standard-change catalog was found to drift without one. Deferred to whichever role owns the
periodic-review surface next (likely architecture, when the axis-role schema is designed), not
actioned here.

## Deployment-surface constraint carried forward

No mechanism is built in this phase. Architecture/implementation own: the axis-role schema
(where in `roles/*.json`/`roles/specs/*.spec.json` an axis-ownership + evaluation-record format
lives), the gate that reads docs/product plus `gates/risk_report.py::classify_axes()` and enforces
the AND rule, and the audit-record write path and format (four fields specified above). No GitHub
Actions — matches this repo's own standing 2026-08-08 constraint (#566) that enforcement lives in
deployed hooks.

## Degradation (restated from current-state.md, binding on architecture/implementation)

Right now docs/product has zero entries in this repo. Per the issue's own acceptance criterion,
this means: **no decision auto-decides today** — every decision escalates until the corpus is
non-empty. The pre-registered measurement window above does not open until that condition changes.
