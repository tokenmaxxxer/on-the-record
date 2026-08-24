# Deviation log — issue #2180 (execution-observation role)

- 2026-08-24T10:37:57Z | filed | issue-2180/execution-observation |
  the task instructed filling in the pre-written
  docs/issue-2180/reports/execution-observation.md skeleton directly and
  landing it this session. Attempting that write hit a role-shaped
  judgment call outside the instructed scope.

  canonical: this session's own denied `Bash`/`Write` attempts on
  docs/issue-2180 paths, quoted in `docs/issue-2180/reports/execution-observation/survey.md`'s
  "Write surface" and "Issue #2180's own state" sections — result:
  ```
  approval-gate: neither the PR for issue-2180/execution-observation nor issue #2180 carries an approval from a listed human approver (jiwonjung94, jjongkwann)
  ```
  ```
  approval-gate: issue #2180 is not open (state: CLOSED, reason: COMPLETED) -- a closed issue's board is not live for any role, regardless of any standing PR review or APPROVE comment. (contract v3 s19)
  ```

  Per the deviation loop's "Role sessions" rule, a role session does not
  spawn a peer or file a new issue mid-task on its own initiative — this
  is reported here (not spawned) and in the session's own reply: the
  task landed as a phase-1 survey + proposal round instead
  (`docs/issue-2180/reports/execution-observation/survey.md`,
  `docs/issue-2180/proposals/2026-08-24-execution-observation-issue-2180.md`),
  opened as PR #2183, and the session stopped per the role protocol's
  default two-session mode pending either a spawner-set
  `CORE_BUILD_NOW=1` stamp or a human reopening issue #2180.
