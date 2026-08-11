# ADR — batch-eligibility and plan-order gates as two independent modules

## Context

Issue #659 asks for two mechanical gates: Axis 1, batch-eligibility over pending delivering PRs
from write-set non-overlap; Axis 2, spawn/merge refusal when an issue's declared execution-plan
order is unsatisfied. `docs/issue-659/reports/architecture/survey.md` found the reusable
primitives already deployed (`_glob_matches` in `gates/risk_report.py` for overlap; `_plan_from_body`
in `gates/flows.py` for plan parsing) and, separately, an existing but orthogonal batch mechanism
(`batch_blocked` in `gates/risk_report.py`, wired into `on-the-record/hooks/impact-guard.sh`) that
grades individual-proposal risk, not cross-PR write-set collision. Product-discovery's proposal
(`docs/issue-659/proposals/product-discovery.md`) already rejected a single combined gate for the
two axes at the decision layer (RICE candidate #2); this ADR extends that same rejection to the
module-boundary layer, and additionally decides where each axis's computation and audit-record
write live.

## Decision

Two new functions, each in the file that already owns its primitive, no new `gates/*.py` module:

- **Axis 1** — `batch_eligible_groups(prs: list[dict], root: Path) -> list[list[dict]]`, added to
  `gates/risk_report.py`, next to `batch_blocked`. Each PR dict carries `{path/number, files}` (its
  own changed-file list, e.g. via `gh pr diff --name-only`, resolved by the caller — this function
  takes file lists, not GitHub API calls, keeping it testable without network access, mirroring
  `scan_open_proposals` vs. `report`'s own split). Computes pairwise non-overlap with a
  `(list[str], list[str]) -> bool` wrapper around the existing `_glob_matches` (path-vs-glob
  becomes path-vs-path exact/glob comparison, same function, new call shape — not a new algorithm),
  builds the conflict graph, returns connected components with no internal edge as batch-approvable
  groups. Placed in `risk_report.py`, not a new file, because it is the second stage of the same
  batch-eligibility pipeline `batch_blocked` already starts (risk-permission, then write-set
  grouping) — colocating keeps that pipeline's two stages next to each other and reuses the same
  import in `impact-guard.sh` without adding a second `gates/*.py` import site.
- **Axis 2** — `plan_order_blocked(plan: list[dict]) -> list[dict]`, added to `gates/flows.py`, next
  to `_plan_from_body`. Takes the already-parsed `[{step, roles, done}, ...]` list (no new parsing),
  returns the subset of steps whose refusal basis is `{step, prerequisite_step,
  prerequisite_done}` for any step > N where some step <= N has `done: false`; `‖`-joined roles
  within one eligible step are never blocked against each other. Placed in `flows.py`, not a new
  file, because it is a pure function of `_plan_from_body`'s own output type and belongs with the
  parser that produces it, the same locality argument as Axis 1's placement.

Both functions are pure — inputs in, a decision list out, no I/O, no GitHub calls, no file writes —
so both are independently unit-testable against fixtures per the issue's own acceptance criteria,
and neither imports the other. This mirrors issue #573's own component-boundary decision (one
direction of dependency, gate depends on primitive, nothing depends on the gate).

**Rejected: a single new `gates/batch_and_order.py` module hosting both.** Would create one file
depending on two others (`risk_report.py`'s overlap primitive and `flows.py`'s plan parser) for two
signals the product-discovery proposal already established must never be allowed to round up to
eligible through shared code — a single shared module invites exactly that coupling by making it
easy to compute one combined verdict. Colocating each axis with its own primitive instead keeps the
two axes physically unable to merge without an explicit new function.

**Rejected: extending `batch_blocked` in place to also do write-set grouping.** Conflates a
risk-permission gate (is this proposal ever batchable) with a grouping computation (which
already-permissible PRs collide) — current-state.md's finding #1, restated as the binding
constraint here.

## Deployment surface (hook wiring, decided; hook code itself is implementation's job)

- Axis 1's audit record and Axis 2's refusal record both land at
  `docs/issue-<n>/decisions/batch-<timestamp>.md` and
  `docs/issue-<n>/decisions/spawn-refusal-<timestamp>.md` respectively — reusing the existing
  `docs/issue-<n>/decisions/*.md` convention (current-state.md finding, degradation clause item 3),
  never a new top-level record directory. Both record shapes carry the four fields product-
  discovery's proposal already specified (excluded/refused item, the specific overlapping path(s)
  or prerequisite step, derivation source, re-derivability basis) — architecture does not re-specify
  those fields, only their file location.
- Axis 1 is surfaced at the same hook point `batch_blocked` already occupies
  (`on-the-record/hooks/impact-guard.sh`), called after `batch_blocked` clears a proposal set, never
  before — preserves the existing risk-gate-first ordering current-state.md's background section
  confirms is already deployed.
- Axis 2 is surfaced as a new hook, `on-the-record/hooks/plan-order-guard.sh`, at the spawn/merge
  command point (mirrors `impact-guard.sh`'s own shape: import `gates/flows.py`, deny the command on
  a non-empty `plan_order_blocked` result) — a new hook file, not an extension of `impact-guard.sh`,
  because it gates a different command surface (spawn/merge, not batch-approval framing) and the
  existing hook already has one job per this repo's own `on-the-record/hooks/*.sh` one-hook-one-gate
  pattern (confirmed by the hook directory listing: each `*-guard.sh`/`*-gate.sh` file gates one
  concern).

## Consequences

- Two independently testable, independently failing functions — a bug in Axis 1 cannot silently
  suppress Axis 2's refusal or vice versa, satisfying the issue's own two separate acceptance
  checks.
- `impact-guard.sh` grows one more call in its existing pipeline (Axis 1) rather than a new hook
  file, keeping the batch-approval-framing surface at one entry point; `plan-order-guard.sh` is a
  new file because it is a genuinely new gate at a different command surface, not scope creep on an
  existing one.
- Both new functions depend on `root: Path`-style filesystem/state access already used elsewhere in
  `risk_report.py`/`flows.py` (no new dependency introduced), keeping implementation's phase free of
  any new library or environment requirement.
- Follow-up risk named in product-discovery's proposal (stale/force-pushed PR diff producing a false
  non-overlap) is a caller-side concern — `batch_eligible_groups` takes file lists the caller must
  fetch fresh at evaluation time; this ADR does not specify the fetch mechanism (implementation's
  job) but the function signature makes staleness the caller's responsibility to avoid, not
  something the function itself can detect.

## Alternatives considered

Recorded inline above (single combined module; extending `batch_blocked` in place; folding Axis 2
into `impact-guard.sh`) — each rejected for a stated, distinct reason rather than omitted silently.

## C4 (container/component boundary)

```
                         docs/issue-<n> (issue body, ## 실행 계획)
                                    |
                                    v  read-only
                    +-----------------------------+
                    |  gates/flows.py              |
                    |  _plan_from_body (existing)  |
                    |  plan_order_blocked (new)     |
                    +-----------------------------+
                                    |
                                    v  denies on non-empty result
                    +-----------------------------------+
                    | on-the-record/hooks/               |
                    | plan-order-guard.sh (new hook)      |
                    +-----------------------------------+
                                    |
                                    v  writes
                    docs/issue-<n>/decisions/spawn-refusal-*.md


                    pending delivering PRs (file lists via caller)
                                    |
                                    v  read-only
                    +-----------------------------------+
                    |  gates/risk_report.py               |
                    |  _glob_matches (existing)            |
                    |  batch_blocked (existing, unchanged) |
                    |  batch_eligible_groups (new)         |
                    +-----------------------------------+
                                    |
                                    v  denies / groups
                    +-----------------------------------+
                    | on-the-record/hooks/                |
                    | impact-guard.sh (existing, +1 call)  |
                    +-----------------------------------+
                                    |
                                    v  writes
                    docs/issue-<n>/decisions/batch-*.md
```

Both towers share no edge between `flows.py` and `risk_report.py` — the independence the decision
above is built to preserve.
