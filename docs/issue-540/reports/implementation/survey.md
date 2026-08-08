# Survey — issue #540

SCOUT SKIP: pure bugfix, no design decision open (scout-directive skip
condition 1). The fix is a pytest config addition plus a test-isolation
patch; no product surface, no alternative architecture to weigh.

## Current state

- `pytest.ini` (repo root) has only `[pytest]\npython_functions = ...` —
  no `testpaths`/`norecursedirs`. Default pytest collection walks the
  whole rootdir, including gitignored `runs/`.
- `.gitignore` has `runs/` at repo root. `runs/rulebooks/**` (per the
  issue text) is where issue orchestration clones subject repos during
  live sessions — those clones can carry copies of this repo's own
  test tree, so files under `runs/rulebooks/**` end up with the same
  basename as files under `test/` (`test/` dir listing:
  check-write-set-conflicts.test.sh, test_latency_report.py,
  test_portability_audit_table.py, test_side_effect_round.py,
  test_silent_failure_repros.py). Two files with the same basename and
  no `__init__.py` under different rootdirs is pytest's classic
  "import file mismatch" collection error.
- Confirmed via `spawn.py:1670`: `ROSTER = ROOT / "runs" / "active.json"`
  is a module-level constant bound once at import, from the real
  repo's `ROOT`, not from any per-test path. `test_spawn.py`'s `Drive`
  class (`test_spawn.py:2054`) calls `spawn.drive("/x", False)` — the
  `"/x"` arg only affects `_build_observed(root, e)`'s root-resolution
  inside `reconcile()`, but `_roster_load()` (`spawn.py:1686`) always
  reads the real `ROSTER` path unconditionally. In a clean worktree
  `runs/active.json` doesn't exist, so `_roster_load` returns `{}` and
  `drive()` finds nothing to reconcile. In a live checkout with a
  populated `runs/active.json` (real in-flight roster entries), `Drive`
  tests inherit that real state instead of an isolated fixture —
  `reconcile()` then walks real roster entries and can hit
  `FileNotFoundError` on stale/moved paths. This is a different root
  cause than the collection-path bug — it's test isolation leaking
  real filesystem state into `spawn.py`'s `Drive` unit tests, not a
  pytest-collection issue. Same contamination family (gitignored
  `runs/` reaching a code path meant to run only against synthetic
  fixtures), different mechanism.
- Existing precedent in the same file: `RequireDoctor._with_root`
  (`test_spawn.py:2014-2018`) monkeypatches `spawn.ROOT` for the
  duration of a test and restores it in `finally`. No equivalent patch
  exists for `spawn.ROSTER` in the `Drive` tests.

## Write set implied

- `pytest.ini` — add `norecursedirs`/`testpaths` (or equivalent) so
  collection skips `runs/`.
- `test_spawn.py` — isolate `Drive` tests from the real `spawn.ROSTER`
  path using the same monkeypatch-and-restore shape already used by
  `RequireDoctor._with_root`.
