skip: scout-directive skipped — pure bugfix (repair failing tests against
current spawn.py API), no design decision open. Issue itself declares
`design-research-skip: mechanical`, `validity-consult-skip: trivial`.

# Current-state survey: fast-tier failures on issue-1969/implementation

canonical: `python3 -m pytest -q -m "not slow" --ignore=tests/test_spawn.py`
run live on this branch, 2026-08-22 — 29 failed, 1978 passed, 15 xfailed,
2 xpassed.

## Measured count (differs from issue text)

Issue text says 34 failed. canonical: pytest command above, run live
today, shows 29 failed instead. `on-the-record/hooks/test_upstream_defect_scope_guard.py`
— canonical: `python3 on-the-record/hooks/test_upstream_defect_scope_guard.py`,
exit 0 — already passing, not part of the 29.

## Failure clusters (29)

1. **`spawn.plugin_dirs` removed** (tests/test_spawn_judge.py x8,
   gates/test_consult_gate_lib_env.py x2, gates/test_consult_json_parse.py
   x2, gates/test_consult_siblings.py x4, gates/test_consult_verdict_parsing.py
   x1, tests/test_consult_trace_root.py x7, tests/test_gates.py x2 —
   `t_unresolved_path_variable_is_not_a_path`, `t_new_roles_resolve_without_a_local_checkout`).
   canonical: spawn.py:5100-5110 (`resolve_role_source(role, repo_root)`)
   and spawn.py:5886-5894 (`_readonly_plugin_dirs`), read this turn — #1955
   replaced the standalone `plugin_dirs(role, spec)` module function with
   `resolve_role_source(role, repo_root)["skill_dirs"]`. Tests still do
   `spawn.plugin_dirs = lambda role, spec: [...]` / `spawn._patch(spawn,
   "plugin_dirs", ...)`. Fix: monkeypatch `spawn.resolve_role_source`
   (returning a dict with `skill_dirs`, plus `skills`/`skill_sha` where
   the surrounding code reads them) instead of the removed `plugin_dirs`
   name. `core_plugin_dirs` is unchanged and stays as-is.

2. **`spawn.rulebook_source` removed** (tests/test_gates.py x4 —
   `t_rulebook_falls_back_to_github`, `t_rulebook_version_is_recorded_after_consult_failure`,
   plus 2 more asserting `spawn.rulebook_source(spec)`). canonical:
   spawn.py:5100-5110 docstring, read this turn — #1955 retired the
   rulebook/local-checkout/github fallback path and the `repo`-field
   convention entirely; role resolution is unconditionally skill-repo
   now, no "no local checkout, no repo field" state exists to test.
   These assertions have no surviving subject: delete them (recording
   the removed symbol `spawn.rulebook_source` and the retired
   `repo`-field convention as required by acceptance's empty-state
   clause).

3. **Out of scope for this issue, separate root cause — NOT a #1955
   symbol removal**: canonical: pytest output captured live this run —
   `tests/test_gh_quota_guard.py` `test_sweep_call_budget` fails with
   `407 gh calls for 400 subjects` (budget asserts `<= 8`). This asserts
   a real behavioral budget on `spawn._board_wide_sweep()` (added by
   issue #1498, commit 3899d087, unrelated to #1955). Fixing it needs a
   production-code change to `spawn.py`'s per-subject PR-lookup
   batching — outside this issue's declared scope (`tests/, gates/,
   on-the-record/hooks/, docs/` — no `spawn.py`) and a design judgment
   (how to batch), not a rewrite-against-removed-symbol fix. Per
   role-deviation-directive this is FILE-AS-ISSUE, not inline: reported
   in the phase-2 record, not fixed here.

## Write set

tests/test_spawn_judge.py, tests/test_consult_trace_root.py,
tests/test_gates.py, gates/test_consult_gate_lib_env.py,
gates/test_consult_json_parse.py, gates/test_consult_siblings.py,
gates/test_consult_verdict_parsing.py — mechanical monkeypatch-target
rename (`plugin_dirs` -> `resolve_role_source`) plus deletion of the
`rulebook_source`/`repo`-field assertions in tests/test_gates.py.
tests/test_spawn.py is explicitly excluded (owned by #1959).
