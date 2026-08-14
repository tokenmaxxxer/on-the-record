---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/directive.sh
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
verdict: pass  # canonical: pytest -k "monitor or heartbeat or roster" — result: PASS (see Verification below)
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal, per issue #1280's own task
description naming it as approved:
docs/issue-1280/proposals/monitor-heartbeat-sweep-exclusion.md.

canonical: docs/issue-1280/proposals/monitor-heartbeat-sweep-exclusion.md (read this session)
The proposal was implemented as written:

- `on-the-record/monitors/poll-heartbeat.sh`: the #1245 non-board `exit 0`
  gate is demoted to an `is_board` flag; the tick loop now always runs
  regardless of arm-root board status. #1275's non-git-root check keeps
  its `exit 1`. The alive marker write moved from
  `$(pwd -P)/.orchestrate-monitor-alive/alive` to
  `~/.claude/tokenmaxxxer/monitor-alive/<sha256(pwd -P)[:24]>/alive`
  (computed via inline `python3 -c`), so no registration artifact lands
  inside a non-board target repo.
- `on-the-record/hooks/directive.sh`: `OTR_MN_DIR` replaced by
  `OTR_MN_ROOT="$(pwd -P)"`, and the inline python now derives the same
  `~/.claude/tokenmaxxxer/monitor-alive/<hash>/` path from that root with
  the identical sha256 formula, so the #947 notice logic reads the
  relocated marker.
- `spawn.py` `_board_wide_sweep_all()`: arm-root is now only included in
  the sweep when `(root / MARKER).exists()`; a non-board arm-root is
  silently excluded (no line printed, matching the "non-board root +
  empty roster -> no output" acceptance criterion) while roster-derived
  board targets are still swept every tick. Docstring updated to drop
  the stale "arm-root is never skipped" claim.
- `tests/test_spawn.py`: fixed
  `test_board_wide_sweep_all_empty_roster_sweeps_arm_root_only` to use a
  real board root (added `docs/specs/approvers.md`). Added
  `test_board_wide_sweep_all_non_board_root_with_roster_board_sweeps_roster_only`,
  `test_board_wide_sweep_all_non_board_root_empty_roster_alive_and_silent`,
  and a new `PollHeartbeatMarkerRelocationTest` class that runs the real
  `poll-heartbeat.sh` and `directive.sh` scripts via `subprocess` to
  verify no files are created inside a non-board target repo and that
  `directive.sh` computes the identical relocated-marker hash
  `poll-heartbeat.sh` writes to.

## Why

Plugin Monitors are armed once at session start and cannot be re-armed;
the prior `exit 0` on a non-board arm-root permanently killed idle watch
for the whole session, defeating roster-derived board watch (#1276) for
any session that spawns into a board repo from a non-board root, and
caused a false #947 "idle self-wake unavailable" notice because the
alive marker was never written. Demoting the gate to a sweep-exclusion
keeps the loop alive and dormant when there is nothing to watch, while
still catching roster targets that appear mid-session.

## Upstream basis

docs/issue-1280/proposals/monitor-heartbeat-sweep-exclusion.md

## Verification

canonical: pytest run this session (see fenced output below)

```
$ python3 -m pytest tests/test_spawn.py -k "monitor or heartbeat or roster"
40 passed, 2 failed, 455 deselected
```
derived: `python3 -m pytest tests/test_spawn.py -k "monitor or heartbeat or roster"`

The 2 failures
(`RosterReconcileUnreported::test_filters_by_issue`,
`RosterReconcileUnreported::test_lists_ended_session_with_open_pr_before_ack_and_empties_after`)
are outside this change's write set.

canonical: pytest run this session against unmodified main HEAD via git stash (see below)

```
$ git stash && python3 -m pytest tests/test_spawn.py::RosterReconcileUnreported -q; git stash pop
2 failed, 2 passed
```
derived: `git stash && python3 -m pytest tests/test_spawn.py::RosterReconcileUnreported -q; git stash pop`

The same 2 failures reproduce with 0 changes staged.

## What did not work

None.

## Open findings

None.
