# Deviation log — issue #2166 (execution-observation role)

- 2026-08-24T07:55:50Z | filed | issue-2166/execution-observation |
  the task instructed filling in
  docs/issue-2166/reports/execution-observation.md's skeleton directly
  and landing it this session. Attempting that write hit a role-shaped
  judgment call outside the instructed scope: `approval-gate.sh` denied
  the `Edit` (canonical: acceptance: `Edit` attempt on that record file,
  this session — result:
  ```
  approval-gate: no matching 'APPROVE issue-2166/execution-observation' issue comment (typed or a live in-scope delegation citation) from a docs/specs/approvers.md-listed account was found — this phase-2-shaped write needs phase-2 approval first.
  ```
  ) because no `APPROVE issue-2166/execution-observation` comment exists
  on issue #2166 and `CORE_BUILD_NOW` is unset — the role-handoff
  contract treats a role's own record as phase-2 output requiring human
  approval first, with no carve-out for an observation-only role. Per
  the deviation loop's "Role sessions" rule, a role session does not
  spawn a peer or file a new issue mid-task on its own initiative — this
  is reported here (not spawned) and in the session's own reply: the
  task landed as a phase-1 survey + proposal round instead
  (docs/issue-2166/reports/execution-observation/survey.md,
  docs/issue-2166/proposals/execution-observation-record.md), opened as
  PR #2174, and the session stopped per the role protocol's default
  two-session mode pending an `APPROVE issue-2166/execution-observation`
  comment.
