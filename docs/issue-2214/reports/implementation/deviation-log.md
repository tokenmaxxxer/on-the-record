# Deviation log — issue #2214

- 2026-08-24T00:00:00Z | inline | a before-landing warrant-hunt (stance 0,
  "is the guarantee just touched bypassable") identified that the first
  cut of `analyze()` gated all thrash-signal reporting behind
  `if not blocked:`.
  canonical: `docs/issue-2214/reports/implementation/2026-08-24-hunt-trajectory-analyzer.md`
  A crashed/silently-dead backgrounded subagent (async-launch ack seen,
  its `task_notification` never arrives) held `blocked_on_subagent` true
  for the rest of the log, permanently discarding real, unrelated thrash
  signal.
  Fixed by reporting `stalled`/`reasons` unconditionally, independent of
  `blocked_on_subagent` — a purely-waiting session already produces zero
  repeat signal on its own (an in-flight dispatch has no settled
  `tool_result` to count), so the gate was defending against a case that
  cannot occur while suppressing one that does.
  canonical: `docs/issue-2214/reports/implementation.md` — `## What did
  not work`
  Stays inside this session's write set (no phase-1 proposal froze one —
  build-now bypass); a role-shaped judgment call (how `blocked_on_subagent`
  and `stalled` should compose) rather than a mechanical fix, but does
  not change what the deliverable claims to do and is a one-off scoped to
  this one function. Regression test
  (`test_dead_subagent_does_not_permanently_suppress_unrelated_thrash`)
  and the fix landed together in the same commit (3f7d93ff), carried by
  PR #2221.
