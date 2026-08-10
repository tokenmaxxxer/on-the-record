---
code_under_review:
  - spawn.py
  - test_spawn.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal
(`docs/issue-678/proposals/2026-08-10-progress-aware-respawn-counter.md`)
in `spawn.py`:

- Added `_respawn_fingerprint(work)`: git HEAD sha (`_git_head`) + a stable
  sha256 hash of `board_snapshot()` serialized with sorted keys.
- `RESPAWN_STATE`'s per-key entry now carries `attempts` (the no-progress
  streak), `total_attempts` (increments every respawn regardless of
  progress), and `fingerprint` (the state recorded after the previous
  respawn).
- `_respawn_or_cap()`: before the existing cap check, compares the current
  fingerprint against the stored one; a difference resets `attempts` to 0
  before this attempt increments it to 1. Absence of a prior fingerprint
  (first respawn) starts the streak at 1 as before — no reset either way.
- Added `RESPAWN_ABSOLUTE_MAX = RESPAWN_MAX_ATTEMPTS * 4`, checked
  independently of the streak against `total_attempts`; either cap firing
  reaches `_post_crash_comment()`.
- `_post_crash_comment()` takes a new `absolute: bool` flag: the marker's
  `cap` value differs per cap kind (2 vs `RESPAWN_ABSOLUTE_MAX`), so the
  two caps carry distinguishable idempotency markers and comment bodies
  ("no-progress respawn cap" vs "absolute total-respawn ceiling").
- `test_spawn.py`: new `ProgressAwareRespawnCounter` class — new-commit
  streak reset, board-delta streak reset, consecutive no-progress still
  hits the streak cap, `RESPAWN_ABSOLUTE_MAX` fires independently of a
  resetting streak, and a regression guard that `refused`/
  `waiting-on-human` never reach `_respawn_or_cap()`.

## Why

Per the issue: a session advancing every respawn (new commit or board
delta) should not exhaust the same fixed cap as a session spinning in
place. Basis: `docs/issue-678/proposals/2026-08-10-progress-aware-respawn-counter.md`.

## Verification run

```
$ python3 -m pytest test_spawn.py -k "RespawnOrCap or SelfTriggeredRespawn or ProgressAware" -q
18 passed, 355 deselected
$ python3 -m pytest test_spawn.py -q
373 passed
```

## What did not work

None.

## Open findings

None.
