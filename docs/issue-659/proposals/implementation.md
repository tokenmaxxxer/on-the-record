---
status: proposed
files:
  - gates/risk_report.py
  - gates/flows.py
  - on-the-record/hooks/impact-guard.sh
  - on-the-record/hooks/plan-order-guard.sh
  - on-the-record/hooks/hooks.json
  - gates/test_batch_eligible_groups.py
  - gates/test_plan_order_blocked.py
  - docs/issue-659/reports/implementation/survey.md
  - docs/issue-659/proposals/implementation.md
---

# Proposal — issue #659: batch-eligibility + plan-order gates (implementation, phase 1)

## Request

Implement the two mechanical gates the merged architecture ADR
(`docs/issue-659/decisions/2026-08-10-batch-eligibility-and-plan-order-gates.md`) already decided
the shape of: Axis 1, `batch_eligible_groups` grouping pending PRs by write-set non-overlap;
Axis 2, `plan_order_blocked` refusing premature spawn/merge against an issue's declared execution
order. Both write an audit-record basis to `docs/issue-<n>/decisions/`. Tests per the issue's
Acceptance section.

## Constraints

- No new `gates/*.py` module — each function lives next to the primitive it extends
  (`batch_eligible_groups` beside `batch_blocked` in `risk_report.py`; `plan_order_blocked` beside
  `_plan_from_body` in `flows.py`), per the ADR's decided module boundary.
- Both functions stay pure (no I/O, no GitHub calls, no file writes) — the audit-record write
  happens in the calling hook script, not inside the function.
- Axis 1 runs in `impact-guard.sh` strictly after the existing `batch_blocked` call, never
  before or merged into it.
- Axis 2 ships as a new hook file (`plan-order-guard.sh`), not an extension of `impact-guard.sh`.
- No `roles/*.json` schema change (ADR: neither axis touches role identity).

## Rationale

The alternative of writing the audit record inside `batch_eligible_groups`/`plan_order_blocked`
themselves was considered and rejected: the ADR requires both functions to stay pure and
independently unit-testable against fixtures with no I/O, and `impact-guard.sh` already
demonstrates the pattern of the hook script owning its own report/deny output while the gate
module stays a pure classifier — matching that existing split keeps the two functions testable the
same way `batch_blocked` already is (fixture in, decision list out, no filesystem mocking needed
in the unit tests). The alternative of extending `impact-guard.sh` to also call
`plan_order_blocked` was also considered and rejected, matching the ADR's own stated reason: Axis 2
gates a different command surface (spawn/merge, not batch-approval framing), and this repo's
`on-the-record/hooks/*.sh` files are already one-hook-one-concern.

## What will be done

- `gates/risk_report.py`: add a private `(list[str], list[str]) -> bool` overlap-check wrapper
  around `_glob_matches` (path-vs-path, not path-vs-glob), then `batch_eligible_groups(prs, root)`
  taking `[{"path"|"number": ..., "files": [...]}, ...]`, building a conflict graph from pairwise
  write-set overlap, and returning connected components with no internal edge as
  batch-approvable groups (singleton list -> single-element group; no PRs -> empty list).
- `gates/flows.py`: add `plan_order_blocked(plan)` taking `_plan_from_body`'s
  `[{step, roles, done}, ...]` output, returning `[{step, prerequisite_step,
  prerequisite_done}, ...]` for every step > N blocked by some undone step <= N; steps sharing one
  `‖`-joined entry are never blocked against each other; empty/no-dependency plans return `[]`.
- `on-the-record/hooks/impact-guard.sh`: after the existing `batch_blocked` call clears, call
  `batch_eligible_groups` on the same target-repo's pending delivering PRs (file lists resolved by
  the hook via `gh pr diff --name-only`, matching the ADR's caller-resolves-freshness note), write
  the grouping's basis to `docs/issue-<n>/decisions/batch-<UTC timestamp>.md`.
- `on-the-record/hooks/plan-order-guard.sh` (new): mirrors `impact-guard.sh`'s checkout-resolution
  and Python-heredoc shape, matches spawn/merge-shaped `gh` commands, calls `plan_order_blocked`
  against the target issue's parsed plan, denies with the refusal basis, writes it to
  `docs/issue-<n>/decisions/spawn-refusal-<UTC timestamp>.md`.
- `on-the-record/hooks/hooks.json`: register `plan-order-guard.sh` under `PreToolUse`/`Bash`,
  alongside the existing `impact-guard.sh` entry.
- Tests: `gates/test_batch_eligible_groups.py` (overlapping + non-overlapping fixture -> correct
  grouping with audit record; singleton PR -> trivial singleton group); `gates/test_plan_order_blocked.py`
  (fixture plan with a `‖` parallel step and a sequential dependency -> sequential refused,
  parallel allowed; no-dependency plan -> everything eligible).

## Out of scope

Product-discovery's pre-registered effectiveness metric (queue depth / operator approvals per
landed PR), deferred to the issue's step-4 execution-observation phase. Any change to
`batch_blocked`'s existing risk-permission logic. Any `roles/*.json` schema change.

## How you'll know it worked

`gates/test_batch_eligible_groups.py` and `gates/test_plan_order_blocked.py` pass, covering the
issue's Acceptance fixtures (overlap grouping with audit record, singleton empty state; premature
sequential refusal with parallel allowed, no-dependency empty state). `plan-order-guard.sh` is
registered in `hooks.json`. Both hook scripts write their decision basis under
`docs/issue-<n>/decisions/`.
