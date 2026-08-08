---
code_under_review: HEAD
loop_state: landed
---

# Implementation record — issue #540

## Summary of work

- Added `norecursedirs = runs` to `pytest.ini`'s `[pytest]` section so
  collection skips the gitignored `runs/` tree entirely.
- In `test_spawn.py`'s `Drive` class, added a `_with_roster` helper
  that monkeypatches `spawn.ROSTER` to a path under a
  `tempfile.TemporaryDirectory()`, restored in `finally`, and applied
  it to both `test_stops_when_nothing_to_spawn` and
  `test_never_calls_spawn_one` so they no longer read the live
  `runs/active.json`.

## Why

`norecursedirs` matches the failure mode precisely — pytest walking
into the gitignored `runs/rulebooks/**` clone during collection and
colliding with same-basename test modules — without narrowing what
`test/`/`tests/`/root-level `test_*.py` files get collected (unlike
`testpaths`, which was considered and rejected in the proposal).

`Drive` tests patch `spawn.ROSTER` directly rather than `spawn.ROOT`
because `ROSTER = ROOT / "runs" / "active.json"` is computed once at
import time (spawn.py:1670) — patching `ROOT` post-import doesn't
change the already-bound `ROSTER` value.

## Upstream / basis

docs/issue-540/proposals/2026-08-09-pytest-collection-runs-exclusion.md

## What did not work

None.

## Completed doc-placement items

- N/A — no new env var, dependency, migration, or setup step introduced;
  no library/format decision beyond what the proposal's `## Rationale`
  already recorded.

## Open findings

None.
