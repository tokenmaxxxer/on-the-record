# Deviation log — issue #2574 (execution-observation role)

- 2026-08-27 | filed | issue-2574/execution-observation |
  the task instructed filling in the pre-written
  docs/issue-2574/reports/execution-observation.md skeleton directly and
  landing it this session. Attempting that write hit a live approval-gate
  denial, not a judgment call within this role's own authority to
  resolve.

  canonical: this session's own denied `Write`/`Bash` attempts on
  docs/issue-2574 paths, quoted in
  `docs/issue-2574/reports/execution-observation/survey.md` (committed
  this session, `ee64e7af`) — result:
  ```
  approval-gate: neither the PR for issue-2574/execution-observation nor issue #2574 carries an approval from a listed human approver (jiwonjung94, jjongkwann): no Approve review on an open PR, and no issue comment that is exactly 'APPROVE issue-2574/execution-observation'. Free-text comments are feedback, a bot's or agent's Approve is not a human's, and phase 2 waits for the human. (contract v3 s19)
  ```
  Root cause: canonical: `gh issue view 2574 --json state,stateReason`
  (this session) — result:
  ```
  state: CLOSED
  stateReason: COMPLETED
  ```
  even though the fix's own PR #2578 (carrying `Closes #2574`) is still
  open and unmerged (canonical: `gh pr view 2578 --json state,mergedAt`,
  this session — result: `state: OPEN`, `mergedAt: null`). The
  approval-gate's closed-issue precondition denies unconditionally,
  before any `CORE_BUILD_NOW`/APPROVE-comment path is evaluated, and
  `CORE_BUILD_NOW` was confirmed absent from this session's own
  environment (derived: `printenv | grep -i CORE_BUILD_NOW`, this
  session — no output).

  Per the deviation loop's "Role sessions" rule, a role session does not
  spawn a peer or file a new issue mid-task on its own initiative — this
  is reported here (not spawned) and in the session's own reply: the
  task landed as a phase-1 survey + proposal round instead
  (`docs/issue-2574/reports/execution-observation/survey.md` and
  `docs/issue-2574/proposals/2026-08-27-execution-observation-issue-2574.md`,
  both committed this session at `ee64e7af`), and the session stops per
  the role protocol's default two-session mode pending either a
  spawner-set `CORE_BUILD_NOW=1` stamp on a future respawn of this role,
  or a human reopening issue #2574.
