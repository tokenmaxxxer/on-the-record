# issue-1134 deviation log

- 2026-08-13T03:15Z | filed | consult_cmd()'s new auto-commit call
  (spawn.py `_commit_consult_trace()`, added this issue) breaks the
  `t_both_attempts_exhausted_raises_with_reported_symptom` test in
  gates/test_consult_json_parse.py (call-count assertion: its `fake_run`
  mock intercepts every `subprocess.run`, including the new git
  add/commit calls, so `calls` grows from 2 to 4) — that file is outside
  this proposal's frozen write set (spawn.py, tests/test_gates.py,
  docs/issue-1134/reports/implementation.md); reported, not spawned.
