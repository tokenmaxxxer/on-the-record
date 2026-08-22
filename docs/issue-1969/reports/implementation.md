---
code_under_review:
  - tests/test_spawn_judge.py
  - tests/test_consult_trace_root.py
  - tests/test_gates.py
  - gates/test_consult_gate_lib_env.py
  - gates/test_consult_json_parse.py
  - gates/test_consult_siblings.py
  - gates/test_consult_verdict_parsing.py
loop_state: landed
type: fix
breaking: false
verdict: pass
---

# Implementation record: issue-1969

## What was done

Repaired the fast-tier failures caused by #1955's rulebook-retirement
collateral, per the approved proposal
(docs/issue-1969/proposals/repair-fast-tier-red-baseline.md):

1. In tests/test_spawn_judge.py, tests/test_consult_trace_root.py,
   tests/test_gates.py, gates/test_consult_gate_lib_env.py,
   gates/test_consult_json_parse.py, gates/test_consult_siblings.py,
   gates/test_consult_verdict_parsing.py — replaced every
   `spawn.plugin_dirs` monkeypatch/save-restore target with
   `spawn.resolve_role_source`, matching the current production call sites
   (`resolve_role_source(role, repo_root)["skill_dirs"]`), and reshaped the
   lambda return values from bare `[Path(...)]` lists to
   `{"skill_dirs": [...], "skills": [], "skill_sha": None}` dicts.
2. In tests/test_gates.py, deleted these assertions/tests, each because
   its subject no longer exists:
   - `t_unresolved_path_variable_is_not_a_path` — asserted on
     `spawn._path()`, removed by #1955 along with the rulebook
     path-variable resolution it served.
   - `t_rulebook_falls_back_to_github` — asserted on
     `spawn.rulebook_source()` (removed by #1955) and on role files
     carrying a `repo` field (also retired in favor of skill-repo-only
     resolution).
   - `t_new_roles_resolve_without_a_local_checkout` — asserted on
     `spawn.rulebook_source()`'s github-fallback path, which no longer
     exists.
3. Ran `python3 -m pytest -q -m "not slow" --ignore=tests/test_spawn.py`
   live.

## Result

canonical: `python3 -m pytest -q -m "not slow" --ignore=tests/test_spawn.py`,
run live on this branch, 2026-08-22:

```
FAILED tests/test_gh_quota_guard.py::test_sweep_call_budget - AssertionError:...
1 failed, 2003 passed, 16 xfailed, 1 xpassed in 35.24s
```

The remaining failure is the proposal's declared, out-of-scope deviation
(survey cluster 3): a real behavioral gap in `spawn.py`'s
`_board_wide_sweep` GraphQL-call batching that needs a `spawn.py`
production fix outside this issue's `tests/, gates/, on-the-record/hooks/,
docs/` scope line. It is reported here, not silently absorbed — the
issue's literal 0-failed acceptance bar is not hit by this issue's write
set alone, exactly as the proposal's Constraints section stated in
advance.

## Why

#1955 retired `spawn.plugin_dirs(role, spec)`, `spawn.rulebook_source(spec)`,
and `spawn._path(spec)` in favor of skill-repo-only role resolution
(`resolve_role_source(role, repo_root)`), but its own acceptance check ran
only two named test files, so this collateral against the other fast-tier
tests landed silently. This issue makes the fast tier green again by
following the current API, not by reintroducing the retired symbols as
back-compat shims (proposal Rationale).

## Basis

docs/issue-1969/proposals/repair-fast-tier-red-baseline.md (approved via
issue comment `APPROVE issue-1969/implementation`),
docs/issue-1969/reports/implementation/survey.md.

## Rationale for deviations

The proposal's own Constraints section pre-declared this deviation: the
`test_sweep_call_budget` test in tests/test_gh_quota_guard.py fails for a
real `spawn.py` behavioral reason (`_board_wide_sweep` GraphQL-call
batching) outside this issue's `tests/, gates/, on-the-record/hooks/,
docs/` scope — fixing it would require a production `spawn.py` change this
issue's write set excludes. canonical: `python3 -m pytest -q -m "not slow"
--ignore=tests/test_spawn.py` output pasted above under `## Result`. Per
the proposal's "How you'll know it worked", this one failure is expected
to remain and is reported here, not silently absorbed; the issue's literal
"0 failed" acceptance line is therefore not hit by this issue's write set
alone, as the proposal stated in advance.

## What did not work

This session tried a single rewrite approach — the plan spelled out in the
proposal's own item 5 heading (docs/issue-1969/proposals/repair-fast-tier-red-baseline.md),
applied to every file listed in `code_under_review:` above and to the
three deleted assertions listed earlier in this section. canonical:
`python3 -m pytest -q -m "not slow" --ignore=tests/test_spawn.py` output
pasted above under `## Result`. No other approach was tried first.

## Open findings

- The `test_sweep_call_budget` test in tests/test_gh_quota_guard.py
  remains failing (real `spawn.py` behavioral gap, out of this issue's
  scope per the proposal's Constraints — needs a separate issue to fix
  `_board_wide_sweep`'s GraphQL call batching). canonical: `python3 -m
  pytest -q -m "not slow" --ignore=tests/test_spawn.py` output pasted
  above under `## Result`.

## Next steps

File a new issue against `spawn.py`'s `_board_wide_sweep` to address its
GraphQL-call batching, so the `test_sweep_call_budget` test in
tests/test_gh_quota_guard.py can be re-run and checked against the stated
per-tick call budget.

## Resolution path

A follow-up issue scoped to `spawn.py` production code (outside this
issue's `tests/, gates/, on-the-record/hooks/, docs/` write set) changes
`_board_wide_sweep`'s per-subject `gh` call pattern to stay within the
stated per-tick budget, then re-runs
`python3 -m pytest -q -m "not slow" --ignore=tests/test_spawn.py` live to
check the result.

## loop_state

landed
