# issue-1134 deviation log

- 2026-08-13T00:00:00Z | filed | `on-the-record/hooks/upstream-defect-scope-guard.sh`
  denies every `gh pr create` call universally (no repo-target scoping),
  including this role's normal phase-1 PR against
  `tokenmaxxxer/on-the-record` itself — blocks PR submission for
  issue-1134 (same defect logged for issue-1141, commit 7aedc79);
  reported, not spawned.
- 2026-08-13T03:15Z | filed | consult_cmd()'s new auto-commit call
  (spawn.py `_commit_consult_trace()`, added this issue) breaks the
  `t_both_attempts_exhausted_raises_with_reported_symptom` test in
  gates/test_consult_json_parse.py (call-count assertion: its `fake_run`
  mock intercepts every `subprocess.run`, including the new git
  add/commit calls, so `calls` grows from 2 to 4) — that file is outside
  this proposal's frozen write set (spawn.py, tests/test_gates.py,
  docs/issue-1134/reports/implementation.md); reported, not spawned.
- 2026-08-13T03:30Z | filed | same `gh pr create` universal block recurs
  at phase-2 delivery time — `on-the-record/hooks/upstream-defect-scope-guard.sh`
  still denies it with no repo-target scoping; commit + push to
  `issue-1134/implementation` on `origin` completed (commit 18bf981),
  but `gh pr create` for the phase-2 delivery PR could not run from this
  session; reported, not spawned.
