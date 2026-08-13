# issue-1199 capacity-planning deviation log

- 2026-08-13T07:47:30Z | filed | pr-preflight.sh's amendments-reconciled
  check races new issue comments faster than `gh pr create` can finish —
  the same structural pr-preflight comment-race pattern already logged
  by other roles on this issue (e.g. issue-1174's issue-retrospective
  role, `docs/issue-1174/reports/issue-retrospective/deviation-log.md`,
  commits b00156d/005e2c6). Two automated "Judgment opened ... branch
  `issue-1199/capacity-planning`" delegated-judgment comments
  (issuecomment-5277534838, issuecomment-5277538833) arrived across
  consecutive `gh pr create` attempts; the first was reconciled into the
  record in turn (commit 5339bb9). Stopping retries after this turn's
  budget per the identical precedent — commits through 5339bb9 are
  pushed to issue-1199/capacity-planning for on-the-record's outside
  relay to open the PR. reported, not spawned.
