# Deviation log — issue #388

- 2026-08-14T00:00:00Z, `filed`, `gates/gates.py`'s `record_enums`
  (called from `gates/ci.py`) treats a role's nested 4-bucket
  `record_fields.loop_state` dict (introduced for `execution-observation`
  by commit `782a81db`) as a flat allow-list, so every literal
  `loop_state` value this role's own spec requires — including
  `handed-off`, used by this issue's own execution-observation record —
  fails the check; reported, not spawned (role session, SCOPE-EXCEEDED
  RULE — fixing `gates/gates.py` is outside this role's
  docs/issue-<n>/reports/execution-observation.md write scope). See this
  issue's own execution-observation record's Open findings section for
  the full evidence.
