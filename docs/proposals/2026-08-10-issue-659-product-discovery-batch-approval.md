---
status: proposed
files:
  - docs/issue-659/reports/product-discovery/current-state.md
  - docs/issue-659/reports/product-discovery/scout-brief.md
  - docs/issue-659/proposals/product-discovery.md
---

# Proposal — issue #659 product-discovery phase 1

Issue #659 asks for two mechanisms: (1) mechanically computed batch-eligibility across pending
delivering PRs from write-set non-overlap, reusing the #573/#587 write_scope overlap primitive; (2)
mechanical gating of concurrent spawn/merge from an issue body's declared `## 실행 계획` step order.
No prior constraint beyond the issue text and this repo's own role-handoff contract (phase 1 is
survey + proposal only, phase 2 requires operator approval).

Constraints so far: reuse existing machinery (`gates/risk_report.py`'s `_glob_matches`,
`gates/flows.py`'s `_plan_from_body`), never invent a parallel mechanism; pre-register
metric/threshold/decision rule per this role's own contract obligation; state explicitly that the
deeper structural fix is #573 reaching real operation, this issue is the throughput-side complement.

What will be done (this phase only): current-state survey
(`docs/issue-659/reports/product-discovery/current-state.md`), scout-brief skip record
(`docs/issue-659/reports/product-discovery/scout-brief.md`, skipped — no external product category
to benchmark for internal repo tooling), and the phase-1 proposal itself
(`docs/issue-659/proposals/product-discovery.md`) with RICE-scored candidates and a pre-registered
hypothesis package (primary metric `approvals_per_landed_pr`, threshold ≤0.7, guardrail
`wrongly_batched_or_spawned_rate` at 0%).

Out of scope: any gate code, hook wiring, or `roles/*.json` schema change (architecture/
implementation's phase); cross-issue dependency gating beyond one issue's own plan body (deferred as
ITWWS follow-up).

How it will be known to have worked: the three files above exist, are internally consistent with
the format `docs/issue-573/proposals/product-discovery.md` established, and the phase-1 PR opens
against `issue-659/product-discovery` for operator review.

## What did not work

- First attempt at `current-state.md` used backtick-quoted references combining a file path with a
  `::function_name` suffix or a `:line-range` suffix (e.g. `` `gates/risk_report.py::_role_write_scopes` ``,
  `` `docs/issue-609/.../current-state.md:5-11` ``); `record-claim-guard.sh` (issue #330 mirror)
  treats the entire backtick span as a literal path and denies the write when that combined string
  does not exist on disk. Fixed by putting the file path alone in backticks and the symbol name in
  parentheses outside the backticks, and dropping line-range suffixes entirely.
