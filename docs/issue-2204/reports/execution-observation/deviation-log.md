# Deviation log — issue #2204 (execution-observation role)

- 2026-08-24T14:29:00Z | filed | issue-2204/execution-observation | the
  task instructed filling in
  docs/issue-2204/reports/execution-observation.md's skeleton directly
  and landing it this session. Attempting a read of the implementation
  role's own record at that path (via `git show
  origin/issue-2204/implementation:docs/issue-2204/reports/implementation.md`)
  hit a role-shaped judgment call outside the instructed scope: this
  workspace's `approval-gate.sh` PreToolUse hook denied the command
  (canonical: acceptance: that `Bash` attempt, this session — result:
  "approval-gate: neither the PR for issue-2204/execution-observation
  nor issue #2204 carries an approval from a listed human approver...")
  because no `APPROVE issue-2204/execution-observation` comment exists
  on issue #2204 and `CORE_BUILD_NOW` is unset in this session's
  environment — the role-handoff contract treats a role's own record as
  phase-2 output requiring human approval first, with no carve-out for
  an observation-only role (full reasoning in the proposal's Rationale).
  Per the deviation loop's "Role sessions" rule, a role session does not
  spawn a peer or file a new issue mid-task on its own initiative — this
  is reported here (not spawned) and in the session's own reply: the
  task landed as a phase-1 survey + proposal round instead
  (docs/issue-2204/reports/execution-observation/survey.md,
  docs/issue-2204/proposals/execution-observation-record.md), to be
  opened as a PR, and the session stops per the role protocol's default
  two-session mode pending an `APPROVE issue-2204/execution-observation`
  comment.
