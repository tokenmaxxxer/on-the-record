---
status: proposed
files:
  - docs/issue-659/reports/execution-observation/survey.md
  - docs/issue-659/proposals/execution-observation.md
  - docs/issue-659/reports/execution-observation.md
---

# Proposal — issue #659 step 4: execution-observation

Phase 1 only, per role-handoff contract v3 s19. No verdict language below —
verdict levels (outcome/trajectory/step) are named here as what phase 2 will
check, not decided.

## Intent

Observe PR #712's landed batch-eligibility (`batch_eligible_groups`) and
plan-order (`plan_order_blocked`) gates, and attempt the pre-registered
effectiveness measurement from `docs/issue-659/proposals/product-discovery.md`
("Pre-registered hypothesis package").

## Constraints

- Never re-execute the observed role's code; only PR #712's diff, its commits,
  and its own record (`docs/issue-659/reports/implementation.md`) are admissible
  evidence.
- Never edit `gates/`, `on-the-record/hooks/`, or implementation's own docs paths.
- Every verdict-bearing sentence in phase 2 must cite a commit SHA, file:line, or
  PR comment URL adjacent to the verdict.

## What will be done (phase 2, once approved)

Write `docs/issue-659/reports/execution-observation.md` as the first act of phase
2, addressing all three verdict levels:

- **outcome**: recompute the pre-registered `approvals_per_landed_pr` /
  `wrongly_batched_or_spawned_rate` metric against real post-ship traffic, per
  `docs/issue-659/reports/execution-observation/survey.md`'s derived counts. If
  the 20-PR window and gate-fired audit-record precondition are still unfilled at
  phase-2 time, record effect-not-demonstrated / deferred-with-reason rather than
  fabricating a ratio — exactly per the issue's own Acceptance clause.
- **trajectory**: whether implementation's phase-1→phase-2 path was sound
  (scouted/surveyed before proposing, got real human approval), evidenced from
  `docs/issue-659/reports/implementation.md` and PR #712's commit messages.
- **step**: which artifact, if any, is deficient — evidenced from PR #712's diff
  and implementation's own record, never from re-running `gates/risk_report.py`
  or `gates/flows.py`.

## Out of scope

- Re-executing or re-testing `batch_eligible_groups`/`plan_order_blocked`.
- Editing any file under `gates/`, `on-the-record/hooks/`, or another role's
  `docs/issue-659/` subtree.
- Filing an issue for any deficiency found — findings go into this role's own
  record only; the human files the issue.

## How this will be verified

Phase 2 is complete when `docs/issue-659/reports/execution-observation.md` is
committed on this branch with the independence statement preceding all verdict
language, all three verdict levels addressed (or explicitly marked not
applicable with reason), and every count claim backed by a `derived:` command
output.
