---
code_under_review:
  - spawn.py
  - test/test_bootstrap_timing.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Instrumented `spawn.py`'s per-spawn bootstrap path per the approved proposal
(`docs/issue-711/proposals/spawn-bootstrap-timing.md`):

- Added `_BOOTSTRAP_TIMING` (module-level dict) and a `_timed(phase)`
  context manager (spawn.py, near `_rulebook_ttl_min`) that accumulates
  `time.monotonic()` deltas per named phase.
- Wrapped the six named phases: `workspace` (`issue_workspace`), `branch`
  (`checkout_issue_branch`), `rulebook` (`plugin_dirs`), `core`
  (`core_plugin_dirs`), `settings` (`role_settings` + tempfile write), all
  inside `_spawn_one`; and `gh_token`, wrapped at its own memoization point
  inside `_resolve_gh_token()` around the `gh auth token` shell-out (only
  the first, uncached call is timed — matches the proposal's Rationale).
- `_BOOTSTRAP_TIMING.clear()` at the top of `_spawn_one` resets state per
  spawn (the process-wide `_GH_TOKEN_CACHE` is untouched — a second spawn
  in the same process correctly reads `gh_token=0.000`, reflecting the
  real cache hit).
- Added `_bootstrap_timing_line(role)`, which formats a `key=value` line
  with all six phases plus `total=`, defaulting untimed phases to `0.000`
  so the line's shape never depends on which phases ran (e.g. a no-`--issue`
  spawn still shows `workspace=0.000 branch=0.000`).
- Emitted the line as one additional `print(..., file=sys.stderr)` in
  `_spawn_one`, immediately after the existing "플러그인 N개, ..." status
  line — no change to `_spawn_one`'s control flow, branches, or return
  values.
- Added `test/test_bootstrap_timing.py`: asserts all six named phases plus
  `total` appear with numeric values, asserts untimed phases default to
  `0.000` rather than being dropped, and asserts `_timed` accumulates
  across repeated calls to the same phase.

derived: `python3 -m pytest test/test_bootstrap_timing.py -q`
```
....                                                                     [100%]
4 passed in 0.04s
```

## Why

Per issue #711 and the approved phase-1 proposal: bootstrap latency
(rulebook/core fetch, plugin assembly) was previously unmeasured. Step 2
of the issue requires this instrumentation to land before any reduction
technique (a separate future issue) can cite real before/after numbers
instead of a guess.

## Upstream

docs/issue-711/proposals/spawn-bootstrap-timing.md

## Measurement (executed-live, this host, 2026-08-11)

`--dry-run` (the CLI flag) turns out to exit through `main()`'s own short
path (only `role_settings()`, no `plugin_dirs`/`core_plugin_dirs`/
`issue_workspace`) and never reaches `_spawn_one` — a fact the proposal's
step 4 got wrong (it assumed dry-run runs bootstrap phases through
`_spawn_one`). `test/test_bootstrap_timing.py` therefore exercises the
timing primitives directly (the "fixture" branch of the issue's acceptance
wording), not a `--dry-run` CLI invocation. See `## What did not work`.

To satisfy the issue's "provenance: executed-live" requirement, the same
production functions (`plugin_dirs`, `core_plugin_dirs`, `role_settings`,
`_resolve_gh_token`) were called directly on this host, wrapped in the
real `_timed()` context manager, twice in one process:

derived: inline python invoking `spawn.plugin_dirs`/`spawn.core_plugin_dirs`/
`spawn.role_settings`/`spawn._resolve_gh_token` under `spawn._timed(...)`,
twice in one process
```
RUN1: [implementation] bootstrap_timing workspace=0.000 branch=0.000 rulebook=0.881 core=0.911 gh_token=0.040 settings=0.000 total=1.833
RUN2: [implementation] bootstrap_timing workspace=0.000 branch=0.000 rulebook=0.000 core=0.000 gh_token=0.000 settings=0.000 total=0.001
```

RUN1 (TTL cold or first `git pull` since last TTL window) shows
`rulebook=0.881s`, `core=0.911s` — real `git pull` network cost.
RUN2 (same process, TTL warm within `MUSTER_RULEBOOK_TTL`, `gh_token`
process-cached) shows all four measured phases at `0.000`/near-zero total
`0.001s` — confirming the instrumentation visibly distinguishes the
TTL-hit vs TTL-miss cases the issue #285 skip-unchanged mechanism already
provides, exactly the evidence a step-2 reduction proposal would need to
cite. `workspace`/`branch` are `0.000` in both runs because this
measurement did not pass `--issue` (no git workspace/branch operations to
time) — those two phases are wired identically inside `_spawn_one` but
were not separately live-measured here to avoid mutating a real issue
workspace outside a sanctioned spawn.

## Test run

derived: `python3 -m pytest test/ -q`
```
...................                                                      [100%]
19 passed in 0.29s
```

## What did not work

- Expected the `--dry-run` CLI path to run bootstrap phases through
  `_spawn_one` (per the proposal's step 4 claim, made before this
  implementation actually traced the code). Actual: `main()`'s `--dry-run`
  branch (spawn.py, `if a.dry_run:`) returns before ever calling
  `_spawn_one` — it only calls `role_settings()`. Adjusted the test file to
  drive the timing primitives directly (`spawn._timed`,
  `spawn._bootstrap_timing_line`) instead of shelling out `--dry-run`, and
  used direct production-function calls (not `--dry-run`) for the live
  on-host measurement above. This is a factual correction of one proposal
  claim, not a change to the frozen write set, approach, or any
  constraint — the same six phases, the same wrap points, and the same
  emitted line shape all landed exactly as proposed.

## Doc placement

- No new env var, config key, dependency, or migration introduced —
  nothing to add to a handbook.
- No new library-or-format choice or changed public signature/wire
  format beyond what the proposal's `## What will be done` already
  specified.
- Live bootstrap timing numbers recorded above under `## Measurement`,
  which is the benchmark/investigation-numbers rung of the doctrine
  ladder.

## Open findings

None.

## Hunt

Per warrant directive, docs-only fast path does not apply (this diff
touches `spawn.py` + a test file, not only `docs/`). A before-landing
hunter dispatch is owed but is deferred: given contract v3 s22
(headless/single-shot sessions must not end a turn having delegated work
whose result is not consumed within that same turn — this directive takes
priority over the warrant directive's dispatch instruction), and this
being a single-turn headless session with no later turn to consume a
backgrounded hunter's result, no hunter was dispatched this turn. Diff
size (~40 changed lines in `spawn.py`, one new ~65-line test file) falls
in the 21-200 lines tier (120s, one stance) per the warrant directive's
proportional-cadence table, noted here for whoever runs the deferred
hunt. Recorded so the omission is visible, not silent.

closed_checks:
  - check: full existing test suite regression
    code_sha: (working tree at write time; see code_under_review file list above)
    result: 19 passed, 0 failed (`python3 -m pytest test/ -q`)
