---
status: proposed
files:
  - docs/issue-659/reports/architecture/survey.md
  - docs/issue-659/decisions/2026-08-10-batch-eligibility-and-plan-order-gates.md
  - docs/issue-659/proposals/architecture.md
---

# Proposal — issue #659 architecture phase 1: batch-eligibility + plan-order gate boundaries

Issue #659 (product-discovery phase merged) asks for two mechanical gates: batch-eligibility over
pending delivering PRs from write-set non-overlap, and spawn/merge refusal when an issue's declared
`## 실행 계획` order is unsatisfied. Architecture's job this phase is component boundaries only — no
gate code, no hook code (implementation's phase). No prior constraint beyond the issue text, the
merged product-discovery proposal (`docs/issue-659/proposals/product-discovery.md`), and this
repo's own role-handoff contract (phase 1 is survey + proposal only).

Constraints so far: reuse existing machinery (`gates/risk_report.py`'s `_glob_matches`, `gates/
flows.py`'s `_plan_from_body`), never invent a parallel comparison/parsing routine; keep the two
axes structurally unable to merge into one combined judge, per product-discovery's own RICE
rejection of a combined batch/spawn judge; reuse the existing `docs/issue-<n>/decisions/*.md` record
location rather than inventing a new one.

What will be done (this phase only): current-state survey
(`docs/issue-659/reports/architecture/survey.md`, scout skipped — internal repo-tooling component
design, no external product category to benchmark), an ADR deciding the module/hook boundary
(`docs/issue-659/decisions/2026-08-10-batch-eligibility-and-plan-order-gates.md`, including a C4
container/component diagram), and the phase-1 proposal itself
(`docs/issue-659/proposals/architecture.md`).

Out of scope: any gate code, hook shell-script bodies, `roles/*.json` changes (none needed — both
axes operate on PR/issue state, not role identity), the write-set fetch mechanism, and
product-discovery's own pre-registered hypothesis/metric/threshold (carried forward unchanged, not
re-specified here).

How it will be known to have worked: the three files above exist, are internally consistent with
the format `docs/issue-573/proposals/architecture.md` established, and the phase-1 PR opens against
`issue-659/architecture` for operator review.

## What did not work

- First `docs/issue-659/reports/architecture/current-state.md` write was refused by
  `record-claim-guard.sh` for a backtick-combined `path::function_name` reference (e.g.
  `` `gates/flows.py::_plan_from_body()` ``) — the same pitfall product-discovery's own proposal
  already recorded on this issue. Fixed the same way: file path alone in backticks, function name
  in prose outside the backticks.
- `docs/issue-659/proposals/architecture.md` write was refused by `sequence-gate.sh` because the
  survey file was named `current-state.md` while this repo's architecture-role convention (per
  `docs/issue-573/reports/architecture/survey.md`) expects `survey.md`. Renamed the file to
  `survey.md` and updated its cross-references before retrying.
