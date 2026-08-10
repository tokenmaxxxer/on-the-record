---
code_under_review:
  - spawn.py
  - test_spawn.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #645 (implementation role, phase 2)

## What was done
Implemented the approved phase-1 proposal
(`docs/issue-645/proposals/2026-08-10-wall-clock-cap-and-no-wait-spawn.md`)
verbatim, against its frozen write set (`spawn.py`, `test_spawn.py`):

- `_await_bounded(...)` gained an optional `max_wait_s: float | None = None`
  parameter (spawn.py:2802). When set, the poll loop also checks elapsed
  wall-clock since call entry, independent of `last_change` (the
  activity-reset clock), and returns early with a new distinct code
  `WATCH_WALLCLOCK_RC = 3` (spawn.py:2864-2872) without advancing
  `offset_path` — the unread event stays unread for the next call. Default
  `None` leaves every existing call site byte-for-byte unaffected.
- `_watch(...)`'s `--follow` loop (spawn.py:2943) gained an optional
  `max_wait_min: float | None = None` parameter. It tracks a start
  timestamp and a remaining budget, shrinking `max_wait_s` passed to each
  `_await_bounded` call by elapsed wall-clock; once the budget is
  exhausted it returns `WATCH_WALLCLOCK_RC` instead of looping again —
  bounding cumulative `--follow` runtime even under continuous log growth
  (progress-but-never-ending sessions), the gap #451 left open one layer
  up.
- `main()`'s argparse gained two new flags: `--max-wait` (float, minutes,
  threads into `_watch`'s new `max_wait_min`) and `--no-wait` (bool,
  threads into `_spawn_one`'s new `no_wait`).
- `_spawn_one(...)` gained `no_wait: bool = False`. In the fork-parent
  branch (after the watcher is armed), when `no_wait` is set it returns
  `0` immediately — skipping the `_await_bounded` call entirely — after
  printing the same-shaped resume message `_await_bounded` itself already
  prints on a non-session-end event, naming the exact
  `spawn.py watch --issue <n> --role <role>` command to resume observation.
- `test_spawn.py`: added `AwaitBoundedWallClockCap`, `WatchFollowWallClockCap`,
  and `SpawnOneNoWait` test classes — `AwaitBoundedWallClockCap` covers cap
  wins over endless activity, cap-hit not advancing offset, an event still
  winning when it lands before the cap, and unset `max_wait_s` preserving
  existing stall-only behavior; `WatchFollowWallClockCap` covers budget
  exhausted across repeated progress returning `WATCH_WALLCLOCK_RC` and
  unset budget leaving the loop unbounded by wall-clock; `SpawnOneNoWait`
  covers `--no-wait` returning promptly without ever calling
  `_await_bounded`, and the printed resume command round-tripping through
  `_lookup_roster_entry` against the real workspace index the run wrote.
  Also updated two pre-existing `fake_watch` test doubles
  (`WatchFollow.test_main_wires_follow_flag_through_to_watch`,
  `test_main_defaults_follow_to_false`) to accept the new `max_wait_min`
  keyword `_watch`'s real signature now carries.

derived: `sed -n '/class AwaitBoundedWallClockCap/,/^class WatchFollowWallClockCap/p' test_spawn.py | grep -c "def test_"`
```
4
```
derived: `sed -n '/class WatchFollowWallClockCap/,/^class RulebookCheckoutMemo/p' test_spawn.py | grep -c "def test_"`
```
2
```
derived: `sed -n '/class SpawnOneNoWait/,/^class SpawnOneIssueRoleClaim/p' test_spawn.py | grep -c "def test_"`
```
2
```

## Why
Per the proposal's Rationale: the stall clock's reset-on-activity
behavior is relied on by existing callers (`WATCH_CRASH_RC`'s
crash-detection path) and must not change for them, so the wall-clock cap
is additive (a second, independent optional bound) rather than a
replacement of the stall clock. `--no-wait` closes the gap that harness
`run_in_background` alone cannot: `spawn.py` itself still blocked
in-process inside `_await_bounded` before returning, even when the
Claude Code turn calling it was backgrounded.

## Upstream basis
`docs/issue-645/proposals/2026-08-10-wall-clock-cap-and-no-wait-spawn.md`
(status: approved via `APPROVE issue-645/implementation` issue comment,
single-account mode).

## Verification run
derived: `python3 -m pytest test_spawn.py -q`
```
367 passed
```
Confirmed twice for stability; one pre-existing, change-unrelated flake
(`WatcherAutoArm`'s two `/proc/self/cmdline` identity-check tests, which
read the pytest process's own argv and are sensitive to how the suite is
invoked) was observed once and did not reproduce on rerun — not touched
by this change's write set.

## What did not work
- First pass at the `SpawnOneNoWait` tests globally mocked
  `spawn.subprocess.Popen` with a lambda returning a fake watcher process
  object. That also intercepted `_git_head()`'s real `subprocess.run`
  call (which shares the same `Popen` under the hood), breaking the
  `before_head` computation with an unrelated `UnboundLocalError` deep in
  a `finally` block. Fixed by making the fake `Popen` selective — it only
  substitutes when the command list contains `"watch"`, delegating every
  other call (including real git invocations) to the real `Popen`.
- The first draft of `test_resume_command_prints_and_round_trips_through_watch`
  read `spawn.WORKSPACE_INDEX` for the round-trip assertion *after* the
  `finally` block had already restored it to the pre-test path, so the
  lookup always found nothing. Fixed by moving the workspace-index read
  inside the `try`, before the path gets restored.

## Out of scope (per the proposal, untouched by this session)
- `blocking-call-guard.sh` and its tests (architecture role's own
  deliverable) — left exactly as found on disk, uncommitted; not edited
  by this session.
- Documenting `--no-wait`/`--max-wait` in
  `on-the-record/commands/run.md`'s turn-budget rules, and choosing a
  default wall-clock budget value — both explicitly deferred by the
  proposal to a later phase-2 cycle.

## Rationale for deviations
The proposal's frozen write set was `spawn.py` and `test_spawn.py` only.
This session found four other files already modified, uncommitted, on
the branch by a prior stranded session (`docs/specs/enforcement-boundary.md`,
`docs/specs/reconciled-index.md`, `on-the-record/commands/run.md`,
`on-the-record/hooks/hooks.json`), plus three untracked files
(`on-the-record/hooks/blocking-call-guard.sh` and its two test files) —
all belonging to the architecture role's separately-approved
`blocking-call-guard.sh` PreToolUse hook (PR #647, merged), not to this
proposal. Per the survey's own finding and the proposal's Out-of-scope
section, this session does not build, edit, or commit that hook's files —
they are left exactly as found, still uncommitted, for whatever session
is authorized to land them. This session's own commit stages only
`spawn.py` and `test_spawn.py`, matching the proposal's write set exactly.

## Open findings
None raised against this delivery.
