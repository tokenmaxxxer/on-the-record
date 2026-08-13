# Deviation log — observability (issue #1174)

- 2026-08-13T00:00:00Z | filed | pr-preflight.sh requires an
  `amendments-reconciled` line inside this role's phase-2 record path
  before opening a PR (new comment issuecomment-5276431906 landed
  mid-session), but approval-gate.sh refuses any write to that exact
  path pre-approval (no `APPROVE issue-1174/observability` comment
  exists on #1174) — the two hooks deadlock a phase-1-only PR for this
  role, same pattern already filed by the accessibility and
  market-analysis fan-out units (docs/issue-1174/reports/accessibility/deviation-log.md,
  docs/issue-1174/reports/market-analysis/deviation-log.md). reported,
  not spawned.
