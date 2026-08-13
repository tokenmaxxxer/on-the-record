# Deviation log — accessibility (issue #1174)

- 2026-08-13T00:00:00Z | filed | pr-preflight.sh requires an
  `amendments-reconciled` line inside docs/issue-1174/reports/accessibility.md
  before opening a PR (new comment issuecomment-5276220535 landed
  mid-session), but approval-gate.sh refuses any write to that exact path
  pre-approval (no `APPROVE issue-1174/accessibility` comment exists on
  #1174) — the two hooks deadlock a phase-1-only PR for this role.
  reported, not spawned.
