---
status: proposed
files:
  - tests/test_spawn_judge.py
  - tests/test_consult_trace_root.py
  - tests/test_gates.py
  - gates/test_consult_gate_lib_env.py
  - gates/test_consult_json_parse.py
  - gates/test_consult_siblings.py
  - gates/test_consult_verdict_parsing.py
  - docs/issue-1969/reports/implementation.md
---

## Request

#1955 retired `spawn.plugin_dirs(role, spec)` and `spawn.rulebook_source(spec)`
in favor of skill-repo-only role resolution (`resolve_role_source(role,
repo_root)["skill_dirs"]`). 34 fast-tier tests (measured live today: 29)
still reference the removed symbols and fail. Rewrite the monkeypatch
targets against the surviving API and delete assertions whose subject
(the retired rulebook/repo-field fallback) no longer exists, each
deletion naming the removed symbol. Make `pytest -q -m "not slow"
--ignore=tests/test_spawn.py` pass 0 failed, run live.

## Constraints

- Never touch tests/test_spawn.py (owned by #1959).
- Scope is `tests/, gates/, on-the-record/hooks/, docs/` — no `spawn.py`
  production-code edits.
- Deleted assertions must be listed in the phase-2 record with the
  removed symbol they asserted on (acceptance empty-state clause).
- `tests/test_gh_quota_guard.py::test_sweep_call_budget` fails for an
  unrelated, real behavioral reason ([[implementation-survey|survey]]
  cluster 3) that needs a `spawn.py` production fix outside this
  issue's scope — file it as a deviation, do not fix it here, and say
  so plainly since it means the acceptance's literal 0-failed bar
  cannot be hit by this issue's write set alone.

## Rationale

Considered leaving `spawn.plugin_dirs`/`spawn.rulebook_source` as thin
back-compat shims in spawn.py instead of rewriting the tests, so the
tests would need no change. Rejected: it re-introduces exactly the
symbols #1955 retired for a real reason (freezing skill-repo-only role
resolution, #1758's frozen phase-5 constraint) purely to keep old tests
passing unchanged — that is scope creep into `spawn.py`, which this
issue's own scope line excludes, and defeats the retirement #1955
intentionally shipped.

Considered deleting all 29 failing tests outright rather than rewriting
most of them. Rejected: the `plugin_dirs`-monkeypatch tests exercise
real, still-live behavior (which plugin dirs get passed to `claude -p`)
through a renamed seam — only the `rulebook_source`/`repo`-field
assertions in tests/test_gates.py test a state that no longer exists at
all and warrant deletion.

## What will be done

1. In each of the 7 test files, replace `spawn.plugin_dirs` monkeypatch/
   attribute-save-restore usage with `spawn.resolve_role_source`,
   returning `{"skill_dirs": [...], "skills": [...], "skill_sha": None}`
   (or the subset the call site actually reads) in place of the old
   `[Path("/fake/plugin")]` list return. `core_plugin_dirs` patches are
   left unchanged.
2. In tests/test_gates.py, delete the 4 assertions naming
   `spawn.rulebook_source` (`t_rulebook_falls_back_to_github`,
   `t_rulebook_version_is_recorded_after_consult_failure`, and 2 more),
   recording the removed symbol per assertion.
3. Run `python3 -m pytest -q -m "not slow" --ignore=tests/test_spawn.py`
   live and report the result verbatim in the phase-2 record, including
   the still-open `test_gh_quota_guard.py` deviation.

## Accumulation

The repeated one-line `spawn.plugin_dirs` -> `spawn.resolve_role_source`
monkeypatch-target edit lands in 7 files with no shared test helper. If
`spawn.py`'s role-resolution seam gets renamed again in the future,
these 7 call sites all need the same edit again by hand — this proposal
does not introduce a shared monkeypatch fixture to absorb further
renames, since today's tally is closed at these 7 files and #1955's own
scope declared the retirement final. If a future issue renames the seam
again, that issue should consider a shared `_patch_role_source` test
helper instead of repeating the inline edit an N-th time.

## Out of scope

- `tests/test_spawn.py` (owned by #1959).
- Fixing `spawn.py`'s `_board_wide_sweep` GraphQL-call batching
  (`test_sweep_call_budget` failure) — filed as a deviation, not built
  here.
- Any `spawn.py` production-code change.

## How you'll know it worked

`python3 -m pytest -q -m "not slow" --ignore=tests/test_spawn.py`,
run live, shows 0 failed for every test outside the
`test_gh_quota_guard.py::test_sweep_call_budget` deviation (that one
failure is expected to remain and is reported, not silently absorbed).
