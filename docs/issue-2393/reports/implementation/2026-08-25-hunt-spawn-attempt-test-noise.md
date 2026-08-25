---
proposal: build-now, issue #2393 (no proposal file — two-phase round bypassed per contract)
---

# Hunt record — spawn-attempt-test-noise

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: git diff HEAD -- spawn.py roster.py (new `PYTEST_CURRENT_TEST` early-return
guard in `_record_spawn_attempt()`, spawn.py, plus `_prune_spawn_attempts()`
added to roster.py's `spawn_attempt_sweep()`)
cap_seconds: 120
tier: default
diff_stat_lines: 88 (2 files)
started_at: 2026-08-25T00:00:00Z (approx, not tracked precisely by tool)
ended_at: 2026-08-25T00:20:00Z (approx)
canonical: spawn.py:901-922 (`_record_spawn_attempt()` guard),
spawn.py:1771 (sole caller, `main()`), lifecycle.py:359-469
(`_respawn_or_cap()` calls `_sp._spawn_one()` with no `attempt_id` kwarg,
so it never reaches `_record_spawn_attempt()` regardless of the guard),
spawn.py:2783-2791 and events.py:896-908 (watcher Popen of
`spawn.py watch --follow --self-heal`, never re-invokes `spawn.py spawn`),
spawn.py:2848-2850 (`env={**os.environ, **extra_env}` on the real `claude`
child Popen), grep of tests/test_spawn_pipeline.py:1333-1557,
tests/test_admission_checklist.py:467-525,
tests/test_spawn_board_flows.py:2551-2572 (all mock
`spawn.subprocess.Popen` before the real `claude` child is spawned, so no
unmocked child process exists in this repo's suite to carry a stale env var
forward), grep of gates/*.py for `pytest.main` (13 hits, none dispatch a
real spawn through `_record_spawn_attempt()`).

Traced every path that can reach `_record_spawn_attempt()` using the above
file:line locations. Summary of what each shows:
- `main()` is the only caller (spawn.py:1771), invoked once per top-level
  `spawn.py spawn --issue N --role X` CLI process, before the fork/Popen that
  starts the real `claude` child.
- Auto-respawn (`_respawn_or_cap()`, lifecycle.py:469) calls `_spawn_one()`
  directly in-process and never passes `attempt_id`, so it never touches
  `_record_spawn_attempt()` at all — unrelated to this diff's guard.
- The auto-armed watcher only re-arms itself or continues following; it never
  re-invokes `spawn.py spawn` as a new subprocess, so it can't carry a stale
  `PYTEST_CURRENT_TEST` into a fresh `_record_spawn_attempt()` call.
- The real `claude` child does inherit the orchestrator's full env, so a
  stale `PYTEST_CURRENT_TEST` could in principle propagate to a nested
  `spawn.py spawn` invoked *by* that session later — but every place in this
  repo's own test suite that drives `_spawn_one()`/`main()` mocks
  `spawn.subprocess.Popen` before it reaches the real `claude` Popen call, so
  there is no actual code path in this repo that lets a live, unmocked child
  process inherit the var and run for real afterward. That chain remains
  hypothetical, not reproducible against this checkout.
- `gates/test_*.py` scripts call `pytest.main()` for real board-gate checks,
  a genuine (non-fixture) use of pytest — but none of them dispatch a real
  spawn through `_record_spawn_attempt()` themselves, and `pytest.main()`
  unsets `PYTEST_CURRENT_TEST` in a try/finally around each test.

acceptance: grep -n "_spawn_one(" lifecycle.py — result:
```
469:    _sp._spawn_one(work, role, task, unattended=True, issue=issue, bounded=True)
```
(no `attempt_id=` kwarg passed, confirming the auto-respawn path bypasses
`_record_spawn_attempt()` structurally, independent of the new guard)

No command was found that sets `PYTEST_CURRENT_TEST` in a real, non-test
`spawn.py spawn` process's own `os.environ` at the point
`_record_spawn_attempt()` runs. Per the reproduction requirement, this is
reported as no finding rather than the nested-child-inheritance concern above
(which has no confirmed trigger in this repo).
