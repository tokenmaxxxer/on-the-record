---
status: proposed
files:
  - docs/issue-659/reports/product-discovery/current-state.md
  - docs/issue-659/reports/product-discovery/scout-brief.md
  - docs/issue-659/proposals/product-discovery.md
---

# Proposal — issue #659: machine-supported batch approval + machine-enforced sequential dependencies

Phase 1 only. Pre-registers hypothesis, metric, threshold, and decision rule per this role's own
contract obligation and the issue's own third acceptance criterion ("pre-registered effectiveness
metric ... deferred-with-reason if the window is unfilled"). No gate code, no hook wiring — that is
architecture/implementation's job. Grounded in
`docs/issue-659/reports/product-discovery/current-state.md`; does not re-derive it.

## Framing carried forward from the issue

This issue is the **throughput-side complement**, not the structural fix. The issue's own text
states it plainly and the current-state survey confirms nothing has changed since: the deepest fix
for "every approval funnels through one human" is #573 reaching real operation as a genuine
delegation mechanism (auto-decide, not just route-and-record) — batching only raises how much a
single approver clears per unit time, it does not remove the single-approver structure. Both axes
below are scoped to raise that ceiling; neither is proposed as a substitute for #573's own
trajectory, and this proposal does not re-argue or duplicate #573's scope.

## Open questions resolved

**1. What "write-set" means for Axis 1.** The issue says "reuse the #573/#587 write_scope
resolution" — the current-state survey confirms the reusable primitive is `_glob_matches` (fnmatch
overlap, `gates/risk_report.py`), not the role-`write_scope` *data* itself. Axis 1 applies that same
primitive to each pending delivering PR's own changed-file set (its actual write-set, e.g. via `gh
pr diff --name-only`), not to role write_scope globs — batch-eligibility is about whether two PRs'
own changes collide, not about which role owns which path. This is reuse of the comparison
mechanism, not a new comparison routine, matching the issue's explicit "extend, never
parallel-invent" instruction.

**2. What a batch-approvable set is, mechanically.** Pairwise non-overlap induces a graph (PRs as
nodes, an edge when write-sets intersect); a batch-approvable set is a maximal independent set
(equivalently, in the common case of few conflicts, a connected component with no internal edges).
A single pending PR is the trivial one-node case (issue's own empty-state requirement).

**3. What Axis 2 gates on.** The issue states the mechanism already exists in the plan syntax: `##
실행 계획` steps are sequential by position, roles joined by `‖` within one step are the only
concurrency the plan itself licenses. The gate is therefore a direct read of `_plan_from_body`'s
parsed `{step, roles, done}` list: refuse spawn/merge of any step > N while any step ≤ N is `done:
false`; within one step, all `‖`-joined roles are eligible together. No new syntax, no new field —
the current-state survey confirms `done` is already tracked and simply not read by any spawn gate
today.

**4. What the two axes' recorded basis must contain**, mirroring #573's own four-field audit-record
shape (derivation source, verdict, and re-derivability, not self-report): for Axis 1, the batch-
approvable set plus, per excluded PR, the specific overlapping path(s) that ruled it out; for Axis
2, the step number refused plus the specific prerequisite step number and its `done` value at
refusal time. Both are produced by the gate mechanism at decision time, never asserted by the
orchestrator after the fact — the same anti-#476 shape as #573's own audit record.

## Candidates scored (RICE)

Reach/Impact scored against "batch/spawn decisions the orchestrator currently makes by eyeball, per
week" — no direct log exists yet for this cadence; scored qualitatively against the same order of
magnitude as #573's own approval-act cadence, since both fire on the same per-decision rhythm.

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Two independent gates: Axis 1 reuses `_glob_matches` on pending PR write-sets to compute a recorded batch-approvable set; Axis 2 reads `_plan_from_body`'s `done`-ordered steps to refuse premature spawn/merge, both producing a re-derivable audit basis | 4 | 5 | 0.6 | 3 | 4.0 | **Keep — primary hypothesis (H1)** |
| 2 | Single combined "readiness score" merging overlap and ordering into one number | 3 | 3 | 0.3 | 3 | 0.9 | Reject — collapses two orthogonal mechanical signals into one; #573's own proposal already rejected exactly this shape ("Rejected: weighted composite / RPN", `docs/specs/impact-classification.md`) for the same reason: a decision that fails on ordering but scores fine on overlap should never round up to eligible |
| 3 | Axis 1 only (batching), defer Axis 2 | 4 | 3 | 0.6 | 2 | 6.0 | Reject on its own but flagged: batching without dependency-gating reproduces exactly the accidental-parallel-conflict failure the issue's own evidence cites (#178/#181 rebase conflict) — a non-overlapping-files batch can still contain a plan-ordering violation if write-set overlap and step order diverge, so shipping Axis 1 alone would look done while leaving the conflict class open |
| 4 | Orchestrator self-report of batch/spawn basis (structured field, no independent gate) | 5 | 1 | 0.8 | 1 | 4.0 | Reject — this is the current-state baseline dressed up with a field; it is exactly the unrecorded-reasoning-as-record failure #476 names, since nothing checks the self-report against the actual write-sets or plan order |
| 5 | No mechanism (status quo) | 5 | 1 | 0.9 | 0 | 4.5 | Reject — does not address the issue's stated goal at all; kept only as the fallback the degradation clause reduces to when a pending-PR write-set or a plan body is unreadable |

Candidate 1 wins on impact and confidence despite candidate 3's higher RICE arithmetic, for the same
reason #573's own table stated: RICE here is a screen, not the verdict, and a lower-effort candidate
that ships only half the mechanism reproduces the exact failure mode (accidental parallel conflict)
the issue's own evidence names.

## Pre-registered hypothesis package

Guardrail metric: `wrongly_batched_or_spawned_rate`, named and non-empty at this same registration
moment, distinct from the primary metric below — a win on throughput while this guardrail breaches
is a reduced-trust result, not a win, mirroring #573's own registration (`auto_decision_reversal_rate`)
for the same reason: throughput gains that hide a correctness regression are worse than no gain.

**H1 (primary).** If batch-approvable sets are computed mechanically from pending-PR write-set
non-overlap (Axis 1) and concurrent spawn/merge is refused whenever the issue's declared plan order
is not yet satisfied (Axis 2), both producing a recorded re-derivable basis instead of orchestrator
eyeballing, then operator approval throughput will rise without an increase in wrongly-batched or
wrongly-parallelized outcomes — because today (per current-state.md) no mechanical batch/spawn gate
exists at all, so the baseline mechanized-batch rate is 0% by construction.

- **Metric**: `approvals_per_landed_pr` = (operator approval actions) / (PRs landed to main),
  measured over a rolling window of the next 20 landed PRs after both gates ship. Secondary
  observation metric: `queue_depth` (count of pending delivering PRs awaiting approval), sampled
  daily over the same window — reported alongside, not substituted for, the primary ratio.
- **Threshold**: baseline is 1 approval per landed PR (current-state.md: every decision is
  individually eyeballed and approved, one at a time). Decision threshold:
  **`approvals_per_landed_pr` ≤ 0.7** over the window — i.e. batching measurably reduces approval
  actions per landed PR by at least 30%, the same 30%-of-ceiling bar #573 registered for its own
  primary metric, kept consistent rather than re-derived.
- **Guardrail status at measurement**: `wrongly_batched_or_spawned_rate` (landed PRs later found to
  have been batched despite an actual write-set collision, or spawned/merged concurrently despite an
  unsatisfied plan-order prerequisite — detectable from the two gates' own audit-record trail
  against what actually landed) must stay **0%** over the same window, stated explicitly next to the
  primary metric's value, never implied. 0%, not a nonzero tolerance, because both failure classes
  this issue exists to close (silent batch collision, accidental parallel conflict reproducing
  #178's rebase conflict) are exactly the classes the issue's own evidence says must not recur, not
  classes with an acceptable background rate.
- **Decision rule**: `approvals_per_landed_pr` ≤ 0.7 AND `wrongly_batched_or_spawned_rate` = 0% →
  **go**. If the primary metric falls short → **pivot**: widen Axis 1's batch-membership computation
  (e.g. from strict independent-set to a looser conflict-tolerant grouping with human review of the
  marginal cases) rather than loosening Axis 2's ordering refusal, since the issue's own cited
  failure mode is exclusively a *loosening* risk (accidental parallel conflict), never a case of the
  gates being too conservative. If the guardrail exceeds 0% regardless of the primary metric →
  **kill-and-redesign**: Axis 1 and Axis 2 each independently re-examined for the specific collision
  or ordering miss, per #573's own precedent of narrowing scope rather than accepting a nonzero
  guardrail breach.
- **Gaming-resistance argument**: each gate's audit-record basis (Axis 1: overlapping path(s) that
  ruled a PR out; Axis 2: the specific prerequisite step and its `done` value) is produced by the
  gate mechanism at decision time from `git`/`gh` state and the parsed plan body, not asserted by
  the orchestrator under review — identical structure to, and directly reused from, #573's own H1
  gaming-resistance argument.
- **Failure signature**: fails quietly if a pending PR's write-set is computed from a stale or
  partial diff (e.g. a PR whose branch has since been force-pushed) — a false non-overlap would
  silently pass Axis 1 while actually colliding. Named here so architecture/implementation is on
  notice that the write-set read must be against current PR state at gate-evaluation time, not
  cached from an earlier read; a periodic audit of batched-PR outcomes against the audit-record
  trail is the follow-up, not built here.

## ITWWS (if this works we should ...)

If H1 proves out at the ≤0.7/0%=guardrail thresholds, extend the same write-set/plan-order gating
to cross-issue dependencies beyond a single issue's own `## 실행 계획` (the issue's own examples —
console #178→#181, audit #14→#12 — span separate issues, which Axis 2 as scoped here does not cover
since `_plan_from_body` reads one issue body at a time). Deferred to whichever role owns the
cross-issue dependency surface next (likely architecture, when a cross-issue plan representation is
designed), not actioned here.

## Deployment-surface constraint carried forward

No mechanism is built in this phase. Architecture/implementation own: where the batch-eligibility
computation and the spawn/merge refusal gate live (new `gates/*.py` module vs. extension of
`gates/risk_report.py` / `gates/flows.py`), the CLI or hook surface that presents the recorded
batch-approvable set to the operator, and the audit-record write path/format for both axes (fields
specified above). No GitHub Actions — matches this repo's own standing 2026-08-08 constraint (#566)
that enforcement lives in deployed hooks.

## Degradation (restated from current-state.md, binding on architecture/implementation)

Right now no mechanical batch/spawn gate exists at all — every batch grouping and every spawn/merge
concurrency decision is orchestrator judgment, unrecorded. Per the issue's own acceptance criteria
("empty state: a single pending PR → trivial singleton batch, asserted"; "plans with no declared
dependencies → everything eligible, asserted"), both gates degrade gracefully to permissive defaults
in the trivial case, not to a refusal — a single PR is always its own batch, and a plan with no
declared steps imposes no ordering constraint. The pre-registered measurement window does not open
until both gates ship and produce at least 20 landed PRs' worth of audit-record trail to measure
against; if that window is unfilled at step 4 (execution-observation), the effect is deferred with
that reason, per the issue's own acceptance criterion.
