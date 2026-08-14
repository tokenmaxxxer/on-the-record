---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - tests/test_spawn.py
---

Skip condition: pure bugfix (per docs/issue-1292/reports/implementation/survey.md)
— the shape of the fix is fixed by the already-landed #1282 non-board
sweep-exclusion pattern in the same file; no design decision is open.

## Request

#1275's hard `exit 1` on a non-git arm-root kills the whole Monitor
process for a session's lifetime and never writes the alive marker,
reproducing the #947 false "monitor unavailable" notice. Demote it to
the same sweep-exclusion/dormancy path #1282 already built for a
non-board git root: tick loop always runs, arm-root excluded from the
sweep when non-git, roster-derived board targets still swept every
tick, silent when there is nothing to watch, alive marker always
written.

## Constraints

- No `[monitor-arm-refused]` error and no exit-1 "script failed"
  notification for a non-git arm-root.
- Roster-derived board targets (#1276) must still be swept every tick
  even when the arm-root itself is non-git.
- Board-root and non-board-git-root behavior from #1282 stays unchanged.
- `spawn.py`'s sweep helpers must not crash on a non-git root (cf. the
  `_repo_slug` `FileNotFoundError` class fixed in #1283).

## Rationale

Considered adding a parallel non-git branch inside `spawn.py`'s
`_board_wide_sweep_all` (an explicit `git rev-parse` check before
deciding whether to sweep the arm-root) and rejected it: the survey
found `_board_wide_sweep_all` already excludes any arm-root lacking
`docs/specs/approvers.md`, and a non-git directory never has that file
either — duplicating the check in `spawn.py` would be a second gate
enforcing the same fact the existing one already enforces, with no
behavioral difference, just extra surface to keep in sync. The chosen
approach instead only touches the shell script's own gate (mirroring
the `is_board` computation #1280 already introduced), which is the one
place that currently still hard-exits.

## What will be done

- In `on-the-record/monitors/poll-heartbeat.sh`, replace the
  `if ! git ... ; then ... exit 1; fi` block with a non-crashing
  `is_git` check, and fold it into the existing `is_board` computation
  so a non-git root is forced to `is_board=0` (defensive: even if a
  stray `docs/specs/approvers.md` happened to exist under a non-git
  directory, it still can never be a board).
- Add named tests to `tests/test_spawn.py`: non-git root arms with rc=0
  and an alive marker and no error text; non-git root + roster board
  entry still sweeps that board target with prefixed lines; non-git
  root + empty roster is the named empty-state case (alive, silent, no
  files under the arm-root).

## Out of scope

- Any change to `spawn.py`'s sweep helpers themselves — the survey found
  they already tolerate a non-git root without modification.
- Any change to the #1245/#1280 non-board-git-root behavior.

## Accumulation

This touches one inline `git rev-parse`/`gh`-adjacent check inside a
single script (`poll-heartbeat.sh`), not a repeated-file list or a
growing set of ad-hoc subprocess calls — there is exactly one arm-root
gate in this script, already consolidated with the `is_board` gate it
now feeds. A future Nth root-classification rule (e.g. a third kind of
excluded root) would extend this same single `is_git`/`is_board`
computation in place, not add a new parallel inline check elsewhere —
no accumulation risk beyond what already exists in this one gate.

## How you'll know it worked

`python3 -m pytest tests/test_spawn.py -k 'monitor or heartbeat or
roster' -q` passes, including the new non-git-root cases, with no
skipped tests.
