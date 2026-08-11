---
status: proposed
files:
  - docs/issue-707/reports/product-discovery/current-state.md
  - docs/issue-707/reports/product-discovery/scout-brief.md
  - docs/issue-707/proposals/product-discovery.md
---

# Proposal — issue #707: standing-delegation mechanism for APPROVE

Phase 1 only, per this role's own contract obligation and the issue's step-1 assignment
("product-discovery"). No hook code, no gate code, no delegation-record schema implementation —
that is step 2 (implementation)'s job. Grounded in `docs/issue-707/reports/product-discovery/
current-state.md` and `scout-brief.md`; does not re-derive either.

## Open questions resolved

**1. Does this repeat the withdrawn 2026-07-26 precedent?** No — the precedent's objection, read
off `protocol.md` §5's own framing, is "an agent now holds the approval seat." This proposal's kept
candidate never moves the seat: the human still authors the delegation record (a GitHub act — an
issue comment, per the current-state survey's segment-fit finding that this repo's topology is
one-grantor/many-actors), and every downstream APPROVE cites that human utterance as provenance.
What changes is that one human utterance now covers many future matching instances instead of one.
This is the axis the scout brief's "separation of grantor identity from actor identity" must-be
names directly — the grantor is still human; only the *instance count* per utterance changes.

**2. Who may cite the delegation record as APPROVE provenance?** The orchestrator session relaying
the operator's request — never the bound acting role session for the issue×role under approval.
This is the issue's own stated invariant, and it is now mechanically checkable: `approval-gate.sh`
already reads #698's `session-role-bind.sh` snapshot (unforgeable, keyed by `session_id`, written
before any session-controlled code runs) to determine "is this session the branch's own bound
role." The same snapshot answers "is this session NOT that role" for a delegation citation: a
delegation-citing session whose snapshot's `role` matches the branch's `<role>` is refused
regardless of what the delegation record says, exactly mirroring the existing self-approval refusal
shape the gate already implements for the human-typed string. No new identity mechanism is needed —
#698 already built the one piece this decision depends on.

**3. What does the delegation record contain?** Four fields the issue itself names as required, in
the same audit-record spirit `docs/issue-573/proposals/product-discovery.md`'s H1 already
established for this repo (a re-derivable citation, never a self-report field):
- **scope** — which issues or issue-classes (e.g., "issue-707", "docs-only proposals", "class:
  typo-fix") the grant covers, stated narrowly per the scout brief's scope-precision axis;
- **grant** — who granted it (must be an `approvers.md` login), when, and in what GitHub artifact
  (an issue comment is the natural home, matching protocol.md §5's existing canonical-location
  rule for the APPROVE signal itself — delegation should not introduce a second signal location,
  the exact drift protocol.md §5 already warns against for issue-126);
- **revocation** — how the grant is withdrawn (a second GitHub act, e.g. a comment naming the grant
  as revoked), checked live at every citation, per the scout brief's "revocation must be enforceable
  in real time" must-be;
- **expiry** — a bound after which the grant no longer covers new instances even absent explicit
  revocation, per the scout brief's "always time-boxed" must-be.

**4. What provenance shape does the gate accept as APPROVE?** Not a second human-shaped string.
`approval-gate.sh`'s existing check (`APPROVE issue-<n>/<role>` exact-match, from an approvers.md
login) stays byte-identical for the human-utterance path. A delegated APPROVE is a *different*
citation shape entirely — the orchestrator session references the delegation record's identifier
(not retyping the human's original words) — so the two paths can never be confused by a near-match
comment, the same string-equality discipline protocol.md's contract already applies to the
human-typed line.

## Candidates scored (RICE)

Reach/Impact scored against "phase-transition approvals per week across active issue×role
branches" (no direct log exists yet for this cadence in this repo; scored qualitatively at the same
order of magnitude as #573's and #566's per-role-session cadence, since all fire on the same
per-phase rhythm the issue's own load figure — 20+ issues/day × 2 phase decisions — describes).

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Scoped/dated/revocable delegation record (GitHub-act grant + revocation), orchestrator-only citation, checked against #698's session-role-bind snapshot, distinct provenance shape from human APPROVE, empty-state byte-identical | 5 | 5 | 0.6 | 3 | 5.0 | **Keep — primary hypothesis (H1)** |
| 2 | Let the bound acting role session itself post APPROVE when a delegation record covers its own branch | 5 | 2 | 0.3 | 1 | 3.0 | Reject — directly violates the issue's own invariant ("the ACTOR can never approve its own change") and reopens the 2026-07-26 precedent's actual objection, since the seat would now sit with the acting agent |
| 3 | Blanket standing delegation with no scope/expiry field (operator delegates "everything, indefinitely") | 5 | 3 | 0.4 | 1 | 6.0 | Reject — scores well on RICE only by skipping the scout brief's must-bes (scoped, dated, revocable); reproduces the ITIL standard-change catalog-drift failure Step 1's #573 survey already found and this repo's own precedents (#511's dominant-axis rule, #573's AND-not-OR) exist specifically to avoid |
| 4 | Per-instance human pre-approval batched into one comment listing N issue numbers, re-typed each time | 3 | 2 | 0.8 | 1 | 4.8 | Reject — does not reduce operator utterances per matching instance at all (still one utterance per batch, and every new instance needs a new batch line); does not address #699 R3's actual load problem |
| 5 | No delegation mechanism (status quo — human types APPROVE per phase per issue, always) | 5 | 1 | 0.9 | 0 | 4.5 | Reject — the current-state baseline; kept only as the empty-state fallback candidate 1 must degrade to |

Candidate 1 wins despite candidate 3's higher RICE arithmetic for the same reason `docs/issue-573/
proposals/product-discovery.md` rejected its own candidates 2/5 on the identical shape: RICE here
screens, it does not verdict — candidate 3 scores well only by omitting the must-bes that make a
standing grant safe rather than a blank check.

## Pre-registered hypothesis package

Guardrail metric: `self_approval_violation_count`, named and non-empty at this same registration
moment, distinct from the primary metric below — a win on the primary while this guardrail is
nonzero is not a reduced-trust result, it is a **contract violation** (invariant 4), so this
guardrail's bar is stricter than the usual "small nonzero tolerance" shape other issues in this repo
use.

**H1 (primary).** If a scoped/dated/revocable delegation record, citable only by a session whose
#698 session-role-bind snapshot does not match the branch's own role, is honored by `approval-gate.
sh`/`pr-preflight.sh`/`contract-guard.sh` as APPROVE provenance distinct from the human-typed
string, then the operator's per-transition typed-approval load falls for delegation-covered
issues/classes without the bound acting role session ever successfully self-approving — because
today (per current-state.md) no delegation mechanism exists at all, so the baseline delegated-
approval rate is 0% by construction and every transition, covered or not, currently requires one
fresh human utterance.

- **Metric**: `operator_approvals_per_landed_pr` = (count of issue comments matching `APPROVE
  issue-<n>/<role>` typed fresh by a human, i.e. NOT a delegation citation) / (count of PRs landed
  to main), measured over a rolling window of the next 20 landed PRs on issues/classes an active
  delegation record covers, after the mechanism ships.
- **Threshold**: baseline is 1.0 (today, every landed PR requires exactly one matching human-typed
  APPROVE per phase transition it went through; current-state.md confirms no routing exists to
  reduce this). Decision threshold: **`operator_approvals_per_landed_pr` ≤ 0.5** for the covered
  window — set at half rather than near-zero because the invariant (candidate-1 design) requires
  the delegation record's own grant to itself be a human GitHub act, so some human authorship
  persists per delegation scope; the metric should show fewer *repeated* per-instance utterances,
  not a fully mechanized zero.
- **Guardrail status at measurement**: `self_approval_violation_count` (instances where the bound
  acting role session's own citation of any delegation record passed `approval-gate.sh`) must be
  **exactly 0** over the same window, stated explicitly next to the primary metric's value, never
  implied. Not a percentage tolerance — invariant 4 has no acceptable nonzero rate, unlike this
  repo's other guardrails (#573's 5% reversal tolerance, #566's 20% false-flag tolerance), because
  a self-approval here is not a quality regression, it is the contract's central invariant failing.
- **Decision rule**: `operator_approvals_per_landed_pr` ≤ 0.5 AND `self_approval_violation_count` =
  0 → **persist**. If the primary metric falls short (delegated approvals aren't actually reducing
  utterances) → **pivot**: widen delegation scope-matching (e.g., issue-class patterns, not just
  per-issue-number grants) rather than loosen the citation-identity check, mirroring #573's own
  "widen the depth axis before loosening the guardrail" rule. If `self_approval_violation_count` is
  nonzero, regardless of the primary metric → **kill immediately**: the mechanism is refused and
  reverts to the empty-state (human-only) path until redesigned — no pivot is acceptable on this
  guardrail, because a single self-approval is itself the failure this whole issue exists to
  prevent, not a signal to tune a threshold.
- **Gaming-resistance argument**: the delegation citation is checked against #698's unforgeable
  session-role-bind snapshot, not against the live `CLAUDE_ROLE` env var or any string the citing
  session controls — identical structural argument to `approval-gate.sh`'s existing self-approval
  refusal for the human-typed path, now extended to the delegation path rather than re-derived.
- **Failure signature**: fails quietly if delegation scope is written too narrowly to ever match
  (an over-cautious grant that never fires looks identical to "correctly nothing was in scope" in
  `operator_approvals_per_landed_pr` alone) — named here so implementation is on notice, mirroring
  #573's own named blind spot for its depth axis.

## ITWWS (if this works we should ...)

If H1 persists at the ≤0.5 / =0 thresholds, extend the delegation-record grammar to cover
implementation-side batch approvals for #659's measured multi-issue load directly, and add a
periodic operator re-review cadence over active (non-expired) delegation records — mirroring the
scout brief's "revocation must be enforceable in real time" must-be with a proactive expiry nudge
rather than only reactive revocation. Deferred to whichever role owns the periodic-review surface
next (likely architecture, alongside the delegation-record schema itself), not actioned here.

## Spec-or-kill verdict

**SPEC.** The delegation record is viable and should be specified for step 2 (implementation),
scoped exactly as follows — this is the frozen contract step 2 inherits, not an open question:

- **Storage**: a GitHub issue comment on the covered issue (or a designated cross-issue "standing
  delegation" issue for class-scoped grants), matching protocol.md §5's existing canonical-location
  rule for APPROVE itself — no second signal location.
- **Grammar** (exact-match, same string-equality discipline as `APPROVE issue-<n>/<role>`): a
  delegation grant is a comment whose entire body is `DELEGATE <scope> UNTIL <expiry-date>` from an
  `approvers.md` login; scope is either `issue-<n>/<role>` or a named class token implementation
  defines (e.g. `class:docs-only`); revocation is a comment whose entire body is `REVOKE <scope>`
  from an `approvers.md` login, checked live (most-recent grant/revocation pair wins) at every
  citation, never cached.
- **Citation**: an orchestrator session (never the bound acting role session, and never any other
  role session either) posts `APPROVE issue-<n>/<role> VIA DELEGATION <scope>`, distinct in shape
  from the human-typed `APPROVE issue-<n>/<role>` so the two provenance paths are never confused by
  near-match text. The identity check this citation requires must **positively verify orchestrator
  identity** (absent `CLAUDE_ROLE` / no #698 session-role-bind snapshot, this repo's own existing
  convention for "this is an orchestrator, not a role session") — a same-issue after-proposal hunt
  dispatch (`docs/issue-707/reports/product-discovery/hunt-after-proposal.md`) found that checking
  only "the citing session's snapshot role differs from the branch's own role" is insufficient: a
  session bound to an unrelated role on an unrelated issue would also pass that narrower check
  without being the orchestrator at all. Step 2 must wire the stricter, positive check, not the
  merely-different-role check this open question first sketched.
- **Empty state**: with no `DELEGATE` comment present and in scope, unexpired, and unrevoked, for
  the citing issue×role, behavior is byte-identical to today — `approval-gate.sh` finds no matching
  delegation and falls through to requiring the human-typed string, exactly as it does now.
- **Kill condition, pre-committed**: if the pre-registered guardrail
  (`self_approval_violation_count`) is ever nonzero during rollout, the mechanism is killed
  immediately per the decision rule above, not iterated on.

## Deployment-surface constraint carried forward

No mechanism is built in this phase. Architecture/implementation own: the exact parser for the
`DELEGATE`/`REVOKE` grammar, wiring the check into `approval-gate.sh`/`pr-preflight.sh`/
`contract-guard.sh` (three call sites today, per the current-state survey — a shared check module
vs. three inline duplicates is an architecture call, not this role's), the audit-trail format
linking a delegated APPROVE back to its specific grant comment, and updating `protocol.md` §8's
prose per the issue's own requirement. No GitHub Actions — matches this repo's own standing
enforcement-lives-in-deployed-hooks constraint (#566, #573).
