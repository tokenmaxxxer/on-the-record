---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
type: feature
breaking: false
canonical: python3 on-the-record/monitors/test_poll_heartbeat.py executed this session in the working tree at code_under_review
acceptance: UNMEASURED-with-reason: no acceptance command on record for this target
verdict: pass
loop_state: landed
---

## What was done

Implemented the monitor attachment board gate per the approved phase-1
proposal (docs/issue-1245/proposals/2026-08-13-monitor-attachment-board-gate.md,
APPROVE issue-1245/implementation posted 2026-08-13T07:53:26Z by
JiwonJung94, single-account mode).

- `on-the-record/monitors/poll-heartbeat.sh`: added a board-presence
  check immediately after the existing `ORCHESTRATE_OFF` kill switch and
  `CHECKOUT`-unresolvable early-exit, and before the
  `.orchestrate-monitor-alive` marker write. If
  `"$(pwd -P)/docs/specs/approvers.md"` is not a regular file, the
  script prints `poll tick: skipped (target repo is not an on-the-record
  board)` and exits 0 — no marker directory, no tick loop entered, no
  `runs/poll_heartbeat_last_state.json` or
  `~/.claude/tokenmaxxxer/poll-watchdog.log` writes. A board target repo
  (carries `docs/specs/approvers.md`) falls through unchanged.
- `on-the-record/monitors/test_poll_heartbeat.py`:
  - `_run_heartbeat` gained a `cwd` parameter (previously always ran in
    the test process's own cwd, which happened not to matter for the
    prior fixtures since none of them asserted board-presence behavior).
  - `t_heartbeat_skips_attachment_on_non_board_repo`: runs in a fresh
    tmp target repo with no `docs/specs/approvers.md`, on a due tick,
    and asserts absence of the registration artifacts named in the
    proposal's constraints (`.orchestrate-monitor-alive/`,
    `runs/poll_heartbeat_last_state.json`,
    `~/.claude/tokenmaxxxer/poll-watchdog.log`) — not merely absence of
    stdout.
  - `t_heartbeat_attaches_on_board_repo`: same shape with
    `docs/specs/approvers.md` created first, asserting the existing
    due-tick behavior (alive marker created, watchdog invoked, captured
    report in stdout) is unchanged from today's baseline.

derived: `python3 on-the-record/monitors/test_poll_heartbeat.py`

```
$ python3 on-the-record/monitors/test_poll_heartbeat.py
ok  t_heartbeat_arms_watchdog_when_due
ok  t_heartbeat_attaches_on_board_repo
ok  t_heartbeat_respects_kill_switch
ok  t_heartbeat_skips_attachment_on_non_board_repo
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller

7/7 passed
```

## Why

requirement: northpole req#7. #1219's landed fix (PR #1240) anchored the
watchdog's *scan* to the target repo but left the operator's separate
widened ask unimplemented: a session on a foreign (non-board) repo
should never get the Monitor *attached* at all, not merely produce
scoped/empty scan output. The gate sits at the top of
`poll-heartbeat.sh` — the only point that sees every tick, including the
first one, before any registration artifact is written — per the
proposal's Rationale (rejected alternative: gating inside `spawn.py`'s
`roster_watchdog()`, which runs too late — the alive marker is already
written by `poll-heartbeat.sh` itself before `spawn.py` is ever invoked).

## Upstream basis

docs/issue-1245/proposals/2026-08-13-monitor-attachment-board-gate.md

## What did not work

None.

## Open findings

None.
