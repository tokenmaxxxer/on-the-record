---
subject: issue-922
kind: survey
role: implementation
---

# Current-state survey — issue #922 implementation (phase 1)

## Scope check (mandatory before any phase-2 write)

canonical: `gh pr list --search 922 --state all` and
`gh issue view 922 --comments` (both run live this session)
`issue-922/product-discovery` (PR #925) is merged and was approved via
the exact comment `APPROVE issue-922/product-discovery`. No PR exists
for `issue-922/implementation`, and no issue-level comment matches
`APPROVE issue-922/implementation` — the only approve-shaped comment
names the `product-discovery` role, not `implementation`. Per contract
v3 s19, phase 2 opens only on a PR-review Approve from a different
approvers.md account, or (single-account mode) the exact issue comment
`APPROVE issue-922/<role>` naming THIS role. Neither exists. This
session therefore writes phase-1 only (this survey + the proposal) and
stops before any code change, regardless of the invoking prompt's
"phase-2" framing.

## Write set the approved design implies

- `on-the-record/monitors/poll-heartbeat.sh` — the capture-hop change:
  replace the detached `nohup ... &>>log &` launch of
  `spawn.py watchdog --auto-respawn` with a synchronous foreground call
  (or an equivalent log-tail-from-offset) whose stdout is echoed
  verbatim as `poll-heartbeat.sh`'s own per-tick stdout.
- `on-the-record/monitors/test_poll_heartbeat.py` — existing test file
  (canonical: `find . -iname "*poll*heartbeat*"`, run live this
  session, → `on-the-record/monitors/poll-heartbeat.sh`,
  `on-the-record/monitors/test_poll_heartbeat.py`) needs new cases for
  the two acceptance scenarios (quiet roster, induced dead-poller/
  stalled watch) asserting the captured stdout carries the rich report.
- `on-the-record/hooks/poll-rearm.sh` — read-only reference; the
  `nohup` launch line lives here (canonical:
  `grep -n poll_rearm_arm_if_due on-the-record/hooks/poll-rearm.sh`,
  run live this session, → line 54, launch lines 66-68) but this
  proposal's design places the capture hop in `poll-heartbeat.sh`'s
  call site, not here — no edit to this file is currently expected;
  listed for visibility only.

## What already exists (reuse, not rebuild)

canonical: `sed -n '2349,2420p' spawn.py` and
`grep -n roster_watchdog spawn.py`, both read live this session.

- `spawn.py` `roster_watchdog()` (function starts at the line the above
  grep reports as `2349:def roster_watchdog`) already prints the full
  report shape to stdout: per-entry `[poll-report]`/`[reconcile]` lines
  with state + detail + `next_action`, `[resume]` lines when
  auto-respawn fires, and the empty-state pair
  `"돌고 있는 역할 세션 없음"` / `"이상 신호 없음"` when the roster is
  empty and the board-wide sweep is clean.
- `spawn.py`'s CLI dispatch carries
  `if a.role == "watchdog": return roster_watchdog(...)` (canonical:
  `grep -n '"watchdog"' spawn.py`, run live this session, → line 4198)
  — this is invoked by `poll-rearm.sh`'s
  `nohup python3 spawn.py watchdog --auto-respawn`. Its stdout today
  goes to `~/.claude/tokenmaxxxer/poll-watchdog.log` via `nohup`'s
  `>>...log 2>&1 &` redirect and is never re-surfaced — this is the
  exact swallow point the proposal names.
- `on-the-record/monitors/poll-heartbeat.sh` (canonical: file read in
  full live this session) — its 60s loop calls
  `poll_rearm_arm_if_due` and currently echoes only
  `"poll tick: due, watchdog armed"` / `"poll tick: skipped (within
  TTL)"`, never the watchdog's own report content. Test hooks already
  exist for bounded-loop testing:
  `POLL_HEARTBEAT_MAX_TICKS`, `POLL_HEARTBEAT_SLEEP_SECONDS`.
- `monitors.json`'s `"when": "always"` declaration (named in the
  proposal, product-discovery survey) is what causes the platform to
  deliver this script's stdout to Claude Code as a notification —
  unchanged, no edit needed here.

## Unknowns the proposal leaves for this phase to resolve

- Whether the capture hop is implemented as a synchronous foreground
  `python3 spawn.py watchdog --auto-respawn` call (blocking
  `poll-heartbeat.sh`'s loop for the watchdog's runtime each tick) or a
  log-tail-from-offset against the still-detached process. The
  foreground call is simpler and matches the proposal's primary
  wording ("capture ... by calling ... in the foreground ... instead of
  the current detached launch"); the offset-tail is named as an
  alternative in the same sentence. No decision was written down by
  product-discovery beyond naming both — this phase's implementation
  proposal below picks one and states why.

## Skip conditions checked

Neither scout-directive skip condition applies on its own (this is not
a pure bugfix, and the write-set choice between foreground-call vs.
log-tail is an open design decision) — however live web scouting adds
nothing here: the "field" for this build is the platform's own
Monitor/stdout-notification contract, already researched and cited by
product-discovery's scout-brief.md (sourced from the platform's own
`plugins-reference.md`), plus this repository's existing polling code,
surveyed above by reading the code directly. This phase's proposal
states its own scoped-skip basis for not repeating an external
competitive sweep, rather than asserting the prior scout's result as
this phase's own finding.
