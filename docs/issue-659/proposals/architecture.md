---
status: proposed
files:
  - docs/issue-659/reports/architecture/survey.md
  - docs/issue-659/decisions/2026-08-10-batch-eligibility-and-plan-order-gates.md
  - docs/issue-659/proposals/architecture.md
---

# Proposal — issue #659: batch-eligibility + plan-order gate component boundaries (architecture, phase 1)

Phase 1 only: component boundaries and write surfaces, no gate code, no hook code. Grounded in
`docs/issue-659/reports/architecture/survey.md` and product-discovery's merged proposal
(`docs/issue-659/proposals/product-discovery.md`); does not re-derive product-discovery's RICE
scoring or its pre-registered hypothesis package (both carried forward unchanged). Full decision
detail — component boundary, deployment surface, C4, rejected alternatives — lives in the ADR
(`docs/issue-659/decisions/2026-08-10-batch-eligibility-and-plan-order-gates.md`); this proposal
states the decision and its basis, not a second copy of it.

## Decision, summarized

Two independent, pure functions, each colocated with the primitive it extends, no new `gates/*.py`
module:

- `batch_eligible_groups` in `gates/risk_report.py` (Axis 1) — wraps the existing `_glob_matches`
  overlap primitive to compare pending-PR write-sets pairwise, returns connected-component
  batch-approvable groups. Runs as a new stage in `on-the-record/hooks/impact-guard.sh`, after the
  existing `batch_blocked` risk-permission gate.
- `plan_order_blocked` in `gates/flows.py` (Axis 2) — consumes `_plan_from_body`'s existing parsed
  `{step, roles, done}` output, returns steps refused for premature spawn/merge. Runs from a new
  hook, `on-the-record/hooks/plan-order-guard.sh`, at the spawn/merge command surface.

Both write their audit-record basis to `docs/issue-<n>/decisions/*.md`, reusing this repo's existing
record convention rather than a new location.

## Why two functions, not one module or one gate

Survey.md's central finding: this repo already has a *different*, deployed batch mechanism
(`batch_blocked`, risk-axis permission) that issue #659's Axis 1 must extend past, not merge into —
conflating "is this proposal ever batchable" with "which already-batchable PRs collide" would hide
a correctness distinction behind one function. Separately, product-discovery's own proposal already
rejected a single combined batch/spawn judge at the decision layer (RICE candidate #2, "collapses
two orthogonal mechanical signals into one"); the ADR extends that same rejection one layer down, to
the module boundary, for the identical reason — a PR that fails plan-order but passes write-set
overlap must never round up to eligible by sharing a code path with the axis that would have passed
it.

## Deployment surface (decided; hook shell script content is implementation's)

`impact-guard.sh` gains one more call (Axis 1) inside its existing pipeline, since it already gates
the batch-approval-framing surface. `plan-order-guard.sh` is a new file, not an extension of
`impact-guard.sh`, because it gates a different command surface (spawn/merge) and this repo's
`on-the-record/hooks/*.sh` files are already one-hook-one-concern (confirmed by directory listing in
survey.md). No `roles/*.json` schema change — both axes operate on PR/issue state, not role
identity, unlike issue #573's `judgment_axes` addition.

## Out of scope (unchanged from product-discovery's constraint, restated for this phase)

Gate code, hook shell-script bodies, and the write-set fetch mechanism (e.g. `gh pr diff
--name-only` call site) are implementation's job, not architecture's. The pre-registered hypothesis,
metric, threshold, and guardrail are product-discovery's and are not re-specified here.

## How it will be known to have worked

The three files above exist, the ADR names a rejected alternative for each of its two structural
choices (module boundary, hook placement) rather than presenting the decision as the only option
considered, and the phase-1 PR opens against `issue-659/architecture` for operator review — mirrors
the format `docs/issue-573/proposals/architecture.md` and `docs/issue-659/proposals/product-discovery.md`
already established for this issue's own phase-1 PRs.

## Degradation (restated from survey.md, binding on implementation)

Left undecided, implementation would face an unconstrained choice between three plausible-looking
wrong shapes already visible in this repo's own history (extending `batch_blocked` in place, a
single combined gate for both axes, inventing a new audit-record location) — each named and rejected
in the ADR rather than left for implementation to rediscover by trial.
