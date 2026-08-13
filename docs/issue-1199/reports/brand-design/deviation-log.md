# Deviation log — brand-design (issue #1199)

- 2026-08-13T00:00:00Z | filed | pr-preflight.sh requires an
  `amendments-reconciled` line inside this role's phase-2 record path
  before opening a PR (new comment issuecomment-5276660902 landed
  mid-session, unrelated to brand-design's scope), but approval-gate.sh
  refuses any write to that exact path pre-approval (no `APPROVE
  issue-1199/brand-design` comment exists on #1199) — the two hooks
  deadlock a phase-1-only PR for this role, same pattern already filed
  for issue-1174's observability/accessibility/market-analysis fan-out
  units (docs/issue-1174/reports/observability/deviation-log.md).
  reported, not spawned.
