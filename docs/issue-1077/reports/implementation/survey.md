# issue-1077 survey: cross-suite `pytest tests/ gates/` pollution

Scout: skipped — pure bugfix. The failure is a single misordered
`unittest.addCleanup` pair in one test class; no design decision is
open (skip condition: "the change is a pure bugfix").

## Reproduction

canonical: `python3 -m pytest tests/ gates/ -q 2>&1 | tail -5`, run this session
derived: `python3 -m pytest tests/ gates/ -q 2>&1 | tail -5`
```
234 failed, 805 passed, 1 xfailed, 2 warnings in 48.38s
```

## Bisection

canonical: `python3 -m pytest gates/ -q`, run this session
- `gates/` alone: 385 passed, 1 xfailed — clean.

canonical: `python3 -m pytest tests/test_gates.py -q`, run this session
- `tests/test_gates.py` alone: 109 passed, 1 known failure
  (`t_rulebook_version_is_recorded`) — the one acceptance already
  excludes.

canonical: `python3 -m pytest tests/ gates/test_gates_refusal.py -q`, run this session
- still 151 failed — proves the pollution originates inside `tests/`,
  before `gates/` even starts collecting.

canonical: `python3 -m pytest tests/test_approve_scope.py tests/test_bootstrap_timing.py tests/test_gates.py -q` (test_flows.py omitted), run this session
- removing `tests/test_flows.py` from the combined run drops the
  failure count to the single known pre-existing one. `test_flows.py`
  is the sole polluter.

## Root cause

canonical: `tests/test_flows.py` lines 187-189, read this session

Class `DecisionQueueSessionScope.setUp` in `tests/test_flows.py`:

```python
old_env = dict(spawn.os.environ)
self.addCleanup(spawn.os.environ.clear)
self.addCleanup(spawn.os.environ.update, old_env)
```

`unittest.addCleanup` runs its registered callbacks in LIFO order
(reverse of registration). Registered order here is `[clear, update]`,
so execution order is `[update(old_env), clear()]` — the environment
is restored first, then wiped completely by the trailing `clear()`.

canonical: `tests/test_flows.py` lines 187-189, read this session
Every process-global env var, including `PATH` and `HOME`, is gone for
the rest of the pytest process once this test class's teardown runs.

Because `os.environ` is process-global, this leak crosses module and
suite boundaries: any test collected after `DecisionQueueSessionScope`
tears down — in `tests/` or `gates/` — inherits an empty environment
and fails wherever it shells out (`gh`, `git`) expecting a normal
`PATH`.

canonical: subprocess.run traceback captured this session, test
t_find_violations_uses_prefetched_issue_state_skips_issue_view in
`tests/test_gates.py`
```
FileNotFoundError: [Errno 2] No such file or directory: 'gh'
```
raised from `/usr/lib/python3.10/subprocess.py:1863` — direct evidence
of the wiped `PATH`.

## Fix tried locally (not committed — phase-1 forbids code edits)

Swapping the registration order to `[update, clear]` (so LIFO executes
`[clear, update(old_env)]` — clear first, then restore exactly
`old_env`).

canonical: `python3 -m pytest tests/ gates/ -q 2>&1 | tail -5`, run this session with the two lines swapped (reverted before commit)
derived: `python3 -m pytest tests/ gates/ -q 2>&1 | tail -5`
```
1 failed, 1038 passed, 1 xfailed in 68.48s (0:01:08)
```

Only the pre-existing `t_rulebook_version_is_recorded` failure
remains — matches the acceptance's "known-marked failure" exception.

## Write set

- `tests/test_flows.py` — the two-line cleanup-order swap.

canonical: bisection above, run this session — no other pollution
source found; the single swap resolves the entire combined-run
failure count (234 → 1, the known failure).
