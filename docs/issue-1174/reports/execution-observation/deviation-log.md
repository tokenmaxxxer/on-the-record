- 2026-08-13T07:46:00Z | filed | pr-preflight.sh's amendments-reconciled
  check raced new automated issue comments faster than `gh pr create`
  could complete (3 new comments — issuecomment-5277517908,
  -5277522553, -5277528340 — arrived across 3 consecutive attempts, the
  first 2 reconciled in turn: commits 3c67322, e3b5bc0). Same
  pr-preflight-race pattern already logged by issue-retrospective and
  others on this issue (commit 005e2c6). Stopping retries after this
  turn's budget per that precedent; commits through e3b5bc0 are pushed
  to issue-1174/execution-observation for on-the-record's outside relay
  to open the PR. reported, not spawned.
