---
status: proposed
files:
  - gates/spawn_on_pr.py
  - spawn.py
  - tests/test_spawn_on_pr.py
---

# spawn-on-pr gate: open-issue scope + per-tick cap + opt-in backfill

## Request

`gates/spawn_on_pr.py::missing_verification()` currently scans the whole
board and mass-spawns verification sessions every 60s tick, including for
closed issues. Scope it to open issues only, add a per-tick spawn cap
(default 4, printing a deferral line when it truncates), and move
closed-issue backfill to a separate opt-in dry-run-default CLI command.

## Constraints

- `missing_verification()` targets only subjects whose issue is still
  OPEN.
- Per-tick spawn cap, constant, default 4; truncation prints one line
  naming how many were deferred — no silent cap.
- Closed-issue backfill stays available as a separate opt-in CLI command,
  dry-run by default.
- Disposition of already-created PRs #1332–#1358 is out of scope.
- `reconcile()` (spawn.py) contract untouched; this stays a sibling sweep
  to closure_sweep/spawn_coverage, not a merge into them.

## Rationale

Considered building a brand-new `gh issue view` call per subject inside
`spawn_on_pr.py` to check open/closed state. Rejected: `gates/closure_sweep.py`
already has `issue_state_index_all(root)`, a single `gh issue list --state
all` call that `spawn._board_wide_sweep()` already runs once per tick for
`closure_sweep.find_violations()`. A second per-subject `gh issue view`
loop would reintroduce the exact O(n) `gh`-call-count regression issue
#743 fixed for closure_sweep; reusing the existing board-wide index keeps
the tick at O(1) `gh` calls for the issue-state dimension and lets
`_board_wide_sweep()` share one fetch across both sweeps by reordering two
existing lines.

## What will be done

- `missing_verification(root, issue_states=None)` gains an `issue_states`
  parameter; when not supplied it fetches `closure_sweep.issue_state_index_all(root)`
  itself. A subject is only included when its issue's state is `"OPEN"`;
  unknown/unfetchable state fails closed (excluded), matching the
  incident's need to stop over-spawning rather than under-spawning.
- `spawn_missing_for_pr(root, cwd, dry_run=False, issue_states=None,
  spawn_cap=SPAWN_CAP)` caps the pair list to `spawn_cap` (module constant,
  default 4) and prints one `[spawn-on-pr] cap=... 초과로 N건 미룸` line
  when truncated.
- New `backfill_closed(root, cwd, dry_run=True)` + a `backfill-closed` CLI
  subcommand (`python3 gates/spawn_on_pr.py backfill-closed [--live]`)
  scan closed-issue subjects with missing verification records; dry-run
  lists pairs without spawning, `--live` spawns them. Never called from
  the automatic tick path.
- `spawn.py::_board_wide_sweep()` moves its existing
  `closure_sweep.issue_state_index_all(root)` call earlier and passes the
  result into `spawn_on_pr.spawn_missing_for_pr(...)`, avoiding a second
  `gh` round-trip per tick.
- `tests/test_spawn_on_pr.py` updated to pass `issue_states` explicitly in
  existing cases, plus new cases for: closed-issue exclusion, open-issue
  pass-through, unknown-state fail-closed, cap+deferral-message, and
  backfill dry-run.

## Out of scope

- Disposition (close/relabel/etc.) of PRs #1332–#1358.
- Any change to `closure_sweep.py`, `spawn_coverage.py`, or `reconcile()`'s
  own contract.
- Making the backfill command runnable from the automatic watchdog tick.

## How you'll know it worked

- `python3 -m pytest tests/test_spawn_on_pr.py` — covers acceptance (a)
  closed-issue subjects yield zero pairs, (b) open-issue subjects still
  yield pairs, (c) cap truncation spawns exactly `spawn_cap` pairs and
  prints one deferral line, (d) `backfill_closed` dry-run lists
  closed-issue pairs without spawning.
- `python3 -m pytest tests/test_merge_gate.py gates/test_closure_sweep.py`
  — no regression.

## Accumulation

This change adds no new inline `subprocess`/`gh` call site: the added `gh`
usage (`closure_sweep.issue_state_index_all`) is an existing shared helper
being reused, not a new ad hoc call. It does not touch any `roles/*.json`-
style repeated-file list. If this pattern (a gate wanting issue-open state)
recurs N more times elsewhere, each caller should keep going through
`closure_sweep.issue_state_index_all` rather than adding its own `gh issue
view`/`gh issue list` call — this proposal does not introduce a second
place that needs that discipline restated.
