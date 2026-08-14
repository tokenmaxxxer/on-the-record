# Survey — issue #1490 (test-suite speedup)

## Current state

canonical: pytest.ini (read this turn) — full file: only
`python_functions = test_* t_*` and `norecursedirs = runs`. No
`markers` key, no `addopts` key, no parallel config.

canonical: `ls requirements*.txt pyproject.toml setup.py` (this turn) —
no such file or directory for any of the three; no dependency manifest
exists anywhere in the repo root.

canonical: `python3 -c "import pytest_xdist"` (this turn) —
`ModuleNotFoundError: No module named 'pytest_xdist'`; not installed.

canonical: `wc -l tests/test_spawn.py tests/test_gates.py conftest.py`
(this turn) — 10861, 1674, 51 lines respectively. Test tree per
docs/handbooks/test-layout.md: `tests/*.py` plus colocated tests in
`gates/` and `on-the-record/hooks/`; root `conftest.py` reaches both.

canonical: conftest.py:35-51 (read this turn) — a session-scoped
`autouse` fixture `_no_global_state_leak` snapshots `subprocess.run`
and three `spawn` module attributes at session start, asserts them
unchanged at session end (issue #360, catches teardown-less
monkeypatches). Under `pytest-xdist` each worker runs its own pytest
session, so this fixture's scope becomes per-worker rather than
whole-suite: a leak from a test in worker A's process stays invisible
to worker B's copy of the fixture. This is a detection-strength change
worth naming in the delivery record; the fixture keeps catching
same-worker leaks either way.

canonical: git show 71173111 (this turn) — full diff. #1486
(commit 71173111) already fixed the coupling class Requirement 1 names
("the #1456 watchdog lock — the exact class of coupling #1486 just
fixed"): two `RosterOwnershipScoping` tests in tests/test_spawn.py
(~lines 10644-10695) called `spawn.main()`'s watchdog dispatch
unmocked, racing the real `WATCHDOG_LOCK_PATH` flock; fixed by patching
`spawn.watchdog_lock_acquire.__defaults__` to a per-test tmp path,
mirroring `tests/test_watchdog_freshness.py`'s existing
`lock_path=tmp_path / "watchdog.lock"` pattern
(tests/test_watchdog_freshness.py:27-52, read this turn).

canonical: `grep -rln 'Path("runs")\|Path("workspace")\|"/tmp/\|WATCHDOG_LOCK_PATH\|shape_contracts\|os.chdir' tests/*.py conftest.py`
(this turn) — matched only tests/test_ps_state_rows.py,
tests/test_gates.py, tests/test_spawn.py.

canonical: tests/test_ps_state_rows.py:22-90, tests/test_gates.py:184-186
(read this turn) — the matched lines carry literal strings such as
`"/tmp/s.json"` and `"/tmp/rb"` as function arguments into
`spawn.spawn_cmd(...)`/`spawn._path(...)` under test; the test process
does not open, write, or read those literal paths from disk itself.

This grep sweep is a static lower bound only. No `-n auto` run has been
executed in this session (pytest-xdist is not installed yet, per the
canonical above), so whether the sweep is exhaustive for real
concurrent-execution collisions is unknown; running the suite under
xdist and observing its outcome is build-phase work, gated on
installing the dependency first.

canonical: `grep -rn "os.environ\[" tests/test_gates.py
tests/test_watchdog_freshness.py tests/test_spawn.py | wc -l` (this
turn) — 91 assignments combined. `os.environ` is process-global, so
under xdist (separate worker processes) cross-worker collision on it is
structurally impossible; a same-process, same-worker ordering leak
across tests within one file (a pre-existing hazard, not new under
xdist) is out of this survey's scope to fully audit — Requirement 1
frames the "enumerate and fix" step as build-phase work.

canonical: `grep -rln "subprocess\." tests/*.py | wc -l` (this turn) —
12 files use `subprocess.`; these are the real-subprocess-lifecycle
test files Requirement 2 targets for the `slow` marker
(tests/test_spawn.py is the issue body's named example).

canonical: pytest.ini (read this turn) — no `markers` key exists, so
no `slow` marker is registered anywhere; a bare `-m "not slow"` today
would match nothing (no test carries the marker) rather than excluding
the intended lifecycle tests.

canonical: `grep -rln "pip install\|pytest" docs/handbooks/*.md` (this
turn) — docs/handbooks/northpole-harness.md, test-layout.md,
operations.md already reference `pytest`/`pip install`; one of these is
the natural handbook-touch site for documenting the new
`pytest-xdist` dependency and the `-m "not slow"` default-run
convention, satisfying contract v3's operational-surface-commit rule.

## Gaps for the proposal to resolve

- Where the `pytest-xdist` dependency gets declared, given no manifest
  file exists at all — this repo has never had one. Introducing the
  first one is itself a decision (which format, whether it also pins
  `pytest`'s already-installed 8.3.3).
- Whether `slow` is marker-registered via `pytest.ini`'s `markers =` key
  (avoids `PytestUnknownMarkWarning`) alongside `addopts = -n auto` for
  the default parallel run, or left unregistered.
- Which tests collide under an actual `-n auto` run — the grep sweep
  above is a static lower bound only; running the suite under xdist and
  observing its outcome is build-phase work, gated on installing the
  dependency first.
