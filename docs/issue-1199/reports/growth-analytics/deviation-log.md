# Deviation log: issue-1199 (growth-analytics)

- 2026-08-13T16:55:00Z | filed | pr-preflight.sh's amendments-reconciled
  check raced 4 consecutive `gh pr create` attempts (rulebook-repo PR)
  against 4 new issue-1199 comments arriving mid-session, reconciling
  the first 3 in turn — same pr-preflight-race pattern already logged by
  other roles on this issue (see docs/issue-1174/reports/
  issue-retrospective/deviation-log.md). Stopping retries after this
  turn's budget per that precedent; rulebook-repo commit
  5111eb6013397ee42ffa3870e0203abd3f622c5d is pushed to
  origin/issue-1199/growth-analytics for on-the-record's outside relay
  to open the PR. reported, not spawned.
