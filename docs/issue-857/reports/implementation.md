---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
  - docs/handbooks/setup.md
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Added `STATE_ROOT` (spawn.py, right after `ROOT`): `MUSTER_STATE_ROOT`
env var override, defaulting to the existing `ROOT / "runs"` when unset
(no behavior change for any session that doesn't set it). `ROSTER`
(spawn.py:1757 pre-change) and `WORKSPACE_INDEX` (spawn.py:2487
pre-change) — the two files the phase-1 survey pinned as the shared
namespace behind PR #855 finding 5 — are now derived from `STATE_ROOT`
instead of the fixed `ROOT / "runs"`. This is the isolation seam the
phase-1 proposal named without implementing: give a harness-launched
fixture session its own state dir via env var, so its `spawn.py watch
--issue N` reads/writes physically different roster/workspace-index
files than the observing session's, independent of whether `-C`/cwd was
threaded correctly (closing the survey's Finding 2 gap — `-C`-dependence
— and, as a side effect of both files moving together, Finding 3's
bare-key `ROSTER` fallback in `_watch()` too, since observer and fixture
now never share the underlying file at all).

Hardened `_roster_locked()`'s and `_roster_save()`'s
`ROSTER.parent.mkdir()` calls to `parents=True` (previously bare
`exist_ok=True`, which only created the immediate parent) — needed once
`STATE_ROOT` can be an arbitrary, not-yet-existing per-run directory
rather than the always-present plugin-install `runs/` dir.

canonical: docs/issue-857/reports/defect-verification/current-state.md
("Finding 4"), read this session
Also closed the survey's Finding 4 (independently reproduced by the
phase-1 survey's dispatched warrant-hunter):
`_workspace_index_put()`'s load-mutate-save was unlocked, so two
concurrent writers (e.g. an observer and a fixture, one now on a
different `STATE_ROOT`, but each also potentially racing with itself
across roles) could silently drop one write. Added
`_workspace_index_locked()` (fcntl flock on a sibling `.lock` file, same
pattern as `_roster_locked()`) and wrapped `_workspace_index_put()`'s
body in it.

Added `StateRootIsolation` to `tests/test_spawn.py`: two real
`python3 -c` subprocesses (matching production, where an observer and a
harness-launched fixture are separate interpreter processes) —
`test_fixture_state_root_never_resolves_observers_roster` registers a
workspace-index + roster entry for issue 776/execution-observation under
one `MUSTER_STATE_ROOT`, then asserts a second process with a *different*
`MUSTER_STATE_ROOT` — even reusing the same issue number and even with
`-C` pointed at the observer's own repo, exactly PR #855 finding 5's
reproduction shape — resolves neither the workspace-index entry nor the
bare roster key, and that the observer's own index file is left with
its one entry untouched (empty-state acceptance criterion); and
`test_state_root_env_var_overrides_default_runs_dir` pins that
`MUSTER_STATE_ROOT` actually redirects `spawn.STATE_ROOT`/`ROSTER`/
`WORKSPACE_INDEX`.

Documented `MUSTER_STATE_ROOT` in `docs/handbooks/setup.md` (KR + EN),
alongside the existing `MUSTER_ROLE_MODEL`/`MUSTER_AGENT_GH_TOKEN` env
var entries, per the doctrine ladder (new env var -> handbook, same
commit).

## Why

canonical: docs/issue-857/reports/defect-verification/current-state.md
The phase-1 survey (defect-verification role, merged PR #861) pinned the
collision to `ROSTER` being a single file per plugin installation keyed
bare `issue-<n>/<role>` with no repo/run scoping and a blind-overwrite
register (Finding 1), and showed the repo-scoped `WORKSPACE_INDEX` layer
(issue #533) only isolates correctly when `-C` is threaded correctly —
which PR #855's own evidence shows did not hold for the fixture session
(Finding 2) — and that even a correctly-scoped `WORKSPACE_INDEX` lookup
still falls through to the repo-unscoped `ROSTER` for pid data (Finding
3). The survey recommended, without implementing, "an env var or
`-C`-derived per-run state root `spawn.py` writes to instead of the
fixed `ROOT / "runs"`" as the seam for this (implementation) step.

## Upstream / basis

Based on: docs/issue-857/reports/defect-verification/current-state.md
(phase-1 survey, PR #861) and docs/issue-857/proposals/defect-verification.md
(phase-1 proposal naming the per-run state root seam for this step).
Finding 4's fix follows docs/issue-857/reports/defect-verification/hunt-defect-verification.md's
reproduction and `ROSTER`'s own `_roster_locked()` pattern
(spawn.py:1760-1770 pre-change).

## Rationale for deviations

The phase-1 proposal explicitly deferred the isolation seam's exact
shape ("per-run env var vs. `-C`-derived state root vs. issue-number
namespacing") to this step as an open design decision, and named
`WORKSPACE_INDEX`'s missing lock (Finding 4, an open finding routed to
this step by the survey) as work this step should also cover. Neither is
a deviation from `## What will be done` in a frozen proposal — no
implementation-role phase-1 proposal exists for this issue (the
defect-verification role's phase-1 proposal covers step 1 only and
explicitly named this step's design choice as open); this section is
included because the choice among the proposal's named alternatives
(env var, chosen over `-C`-derived scoping or issue-number namespacing)
is exactly the kind of judgment call this section exists to record: an
env var was picked because it needs no change to how the fixture's `-C`
is invoked (which is exactly the input Finding 2 showed is unreliable)
and it isolates `ROSTER` and `WORKSPACE_INDEX` together with one seam
rather than two.

## Test run

derived: `python3 -m pytest tests/test_spawn.py -q`
```
........................................................................ [ 16%]
........................................................................ [ 32%]
........................................................................ [ 49%]
........................................................................ [ 65%]
........................................................................ [ 82%]
........................................................................ [ 98%]
.......                                                                  [100%]
439 passed in 35.25s
```

## What did not work

None.

## Open findings

None outstanding at landing. Findings 1-4 from the phase-1 survey are
all addressed by this change (Findings 1-3 by `STATE_ROOT`, Finding 4 by
`_workspace_index_locked()`).
