Subject: issue-1986

# Current-state survey — pytest-xdist hang, spawn-invoking tests

## Reproduction

canonical: executed this turn —
```
$ env -u CORE_BUILD_NOW timeout 120 python3 -m pytest \
    tests/test_spawn_directive_assembly.py tests/test_spawn_board_flows.py -q
(default addopts = "-n auto")
exit 124 (timed out)
```

canonical: executed this turn, results below —
```
test_spawn_directive_assembly.py alone, -n auto: 11 passed in ~1s
test_spawn_directive_assembly.py alone, -n0:     11 passed in ~1s
test_spawn_board_flows.py alone, -n auto:        hang, timeout hit
test_spawn_board_flows.py::ProgressEvents alone, -n auto: hang, timeout hit
test_spawn_board_flows.py::ProgressEvents alone, -n0:     hang, timeout hit
ProgressEvents::test_write_tool_use_fires_progress alone, -n0: hang, timeout hit
```

So the hang is not xdist-specific — it reproduces with zero xdist workers
(`-n0`) once narrowed to the `ProgressEvents` test class in
tests/test_spawn_board_flows.py.

`env -u CORE_BUILD_NOW` was needed for isolation: this shell's own
`CORE_BUILD_NOW=1` (set by the spawning session) leaks into the child
spawn._spawn_one subprocess env and trips a `SinglePhaseSignal` assertion
in tests/test_spawn_directive_assembly.py — an unrelated, pre-existing
environmental pollution issue, out of this issue's scope.

## Root cause

canonical: faulthandler traceback captured this turn —
```
$ env -u CORE_BUILD_NOW timeout -s ABRT 15 python3 -X faulthandler -m pytest \
    "tests/test_spawn_board_flows.py::ProgressEvents::test_write_tool_use_fires_progress" \
    -q -n0 -s
Fatal Python error: Aborted
Current thread ...:
  File ".../selectors.py", line 416 in select
  File ".../subprocess.py", line 2021 in _communicate
  File ".../subprocess.py", line 1154 in communicate
  File ".../subprocess.py", line 505 in run
  File "spawn.py", line 6613 in _workspace_clean_state
  File "spawn.py", line 6861 in auto_sweep
  File "spawn.py", line 8019 in _spawn_one
  File "tests/test_spawn_board_flows.py", line 101 in _run
  File "tests/test_spawn_board_flows.py", line 686 in _run
  File "tests/test_spawn_board_flows.py", line 689 in test_write_tool_use_fires_progress
```

`_run` in tests/test_spawn_board_flows.py calls spawn._spawn_one with
`issue=7` (not None). spawn.py's `_spawn_one` unconditionally runs, before
any mocked collaborator takes over: when `_clean_auto_enabled()` (default
on), it calls `auto_sweep(_workspace_base(), ...)`.

`_workspace_base()` resolves to `$MUSTER_WORK_DIR` or
`~/.tokenmaxxxer/work` — the real, unmocked, machine-global workspace
root, not the test's own `tempfile.mkdtemp()` dir. The test mocks
`spawn.issue_workspace`, `spawn.checkout_issue_branch`, `spawn.spawn_cmd`,
`spawn.ensure_pushed`, `spawn.ledger_write`, `spawn._open_pr_for_branch` —
but never `spawn._workspace_base`, and never disables the sweep.

canonical: executed this turn —
```
$ ls ~/.tokenmaxxxer/work | wc -l
2644
```
2644 real workspace directories currently sit under that path on this
machine (this very session's own tree among them). `auto_sweep` globs
every one with a `.git` dir and calls `_workspace_clean_state` per
directory: `git status --porcelain`, `git log --branches --not --remotes`,
and — for any workspace that is clean-but-ahead of a real configured
remote — `git fetch -q --all` (spawn.py:6613, `timeout=30`). In this
sandboxed session outbound network to those real remotes is unreachable,
so each such fetch burns close to its full 30s budget before the sweep
loop's own timeout/OSError guard catches it and moves to the next
workspace. Enough ahead-and-clean real workspaces among the 2644 pushes a
single `ProgressEvents` test — let alone all 7 in the class — beyond a
120s budget. This also explains why the same test hung 22 minutes under
xdist during issue #1959 while behaving differently outside that run: it
depends on how much real, unrelated state happens to sit in
`~/.tokenmaxxxer/work` at run time, not on `-n auto` itself.

canonical: executed this turn, control measurement —
```
$ tmp=$(mktemp -d) && cd "$tmp" && git init -q && time git fetch -q --all
real 0m0.012s
```
`git fetch --all` in a fresh no-remote repo returns in ~12ms — the delay
is specific to the real, populated `~/.tokenmaxxxer/work` tree the
unmocked `_workspace_base()` points the test at, not to `git fetch` in
general.

## Why "slow" marking alone doesn't cover this

`ProgressEvents` and `EventReporting` (tests/test_spawn_board_flows.py)
already carry `@pytest.mark.slow` with a docstring saying they are "slow
tier, excluded by default." But pytest.ini's `addopts = -n auto` carries
no `-m "not slow"` filter, so slow-marked tests run under the default
addopts regardless of the marker.

## Write surface for the fix

- tests/test_spawn_board_flows.py: the shared `_run` helper (used by both
  `EventReporting` and `ProgressEvents`) is the one seam that must isolate
  spawn._spawn_one's workspace-base lookup from the real machine-global
  directory.
- No spawn.py production-code change is needed — `_workspace_base()`'s
  `MUSTER_WORK_DIR` env override already exists and is exactly the seam
  the test needs; the gap is purely in test isolation.
