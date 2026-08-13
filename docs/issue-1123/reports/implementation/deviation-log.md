# Deviation log — issue #1123

- 2026-08-13T02:00:00Z | inline | pre-existing test
  `t_both_attempts_exhausted_raises_with_reported_symptom` in
  `gates/test_consult_json_parse.py` started writing real files into
  docs/reports/consult-raw-failures once `_persist_consult_raw_output()`
  landed in `consult_cmd()`'s parse-failure path; stubbed the helper with
  the same `_persist_raw_under(root)` fixture its sibling tests already
  use — stays inside the frozen `gates/test_consult_json_parse.py` write
  set, mechanical, no design judgment, one-off.
