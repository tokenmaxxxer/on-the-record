---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# issue #922 implementation phase 2 — poll-heartbeat.sh capture-hop

## What was done

basis: docs/issue-922/proposals/poll-heartbeat-capture-hop.md (approved via issue #922 comment `APPROVE issue-922/implementation`)

- `on-the-record/monitors/poll-heartbeat.sh`'s due branch no longer calls
  the shared `poll_rearm_arm_if_due()` (which launches the watchdog
  detached via `nohup ... &` and returns only a boolean). It now inlines
  the same atomic `python3 spawn.py poll-due` TTL-check-and-stamp call
  (read unchanged out of `poll-rearm.sh` as reference, not duplicated
  logic), and on a due tick runs `python3 spawn.py watchdog
  --auto-respawn` in the FOREGROUND, capturing combined stdout+stderr
  into a shell variable.
- That captured report is echoed verbatim as the tick's own stdout
  (replacing the old static `"poll tick: due, watchdog armed"` line) and
  also appended to `poll-watchdog.log`, so crash-recovery visibility via
  the log is unchanged.
- The skipped-tick branch (`"poll tick: skipped (within TTL)"`) is
  unchanged, and gained the same crash-logging behavior
  `poll_rearm_arm_if_due` already had for a `poll-due` crash (previously
  only reachable via the shared function; now inlined identically since
  this branch no longer calls that function).
- `poll-rearm.sh`, `directive.sh`, and `stop-poll-rearm.sh` source text is
  unchanged.
  canonical: `git diff --stat -- on-the-record/hooks/poll-rearm.sh on-the-record/hooks/directive.sh on-the-record/hooks/stop-poll-rearm.sh`, executed this session, empty output.
- `test_poll_heartbeat.py`: updated the existing due-tick assertion (it
  asserted the now-removed static line) to assert against a fake
  watchdog report instead, and added the two proposal-mandated cases:
  `t_heartbeat_surfaces_empty_roster_report` (empty-roster report
  surfaces verbatim in stdout and the log, and the old static line is
  gone) and `t_heartbeat_surfaces_induced_dead_poller` (an induced
  dead-poller fixture's `STALLED (watcher-dead)`, `[poll-report]`, and
  `[resume]` lines all surface in stdout).

derived: `cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-922-implementation && python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -v`
```
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_arms_watchdog_when_due PASSED [ 20%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_skips_watchdog_when_not_due PASSED [ 40%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_respects_kill_switch PASSED [ 60%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_surfaces_empty_roster_report PASSED [ 80%]
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_surfaces_induced_dead_poller PASSED [100%]
5 passed in 0.18s
```
canonical: pytest output pasted directly above, executed this session.
acceptance: python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -v — result: 5 passed, 0 skipped.

## Why

The bare `"poll tick: due, watchdog armed"` line was the silent gap named
in issue #922: the Monitor notification channel ticked but never
surfaced anything readable. Foreground capture is the same-shape change
the proposal's Rationale picked over log-tailing (see that file) — no
new async coordination primitive, no persisted byte offset.

## Rationale for deviations

The approved proposal's build-plan section was implemented as written
(itself already rewritten once during phase 1, per the warrant-hunt
finding recorded in that same document): inline the due-check, run the
watchdog in the foreground, echo its captured output. No further
divergence occurred during phase-2 execution.

## What did not work

None.

## Open findings

canonical: docs/issue-922/reports/implementation/2026-08-12-hunt-poll-heartbeat-capture-hop.md, section "before-landing — stance 0", read this session.

A before-landing warrant-hunt (stance 0) recorded there identified this
gap: the rich report only reaches `poll-heartbeat.sh`'s own stdout when
this script's tick wins the shared atomic `poll-due` TTL race against
`directive.sh`/`stop-poll-rearm.sh`. When either turn-driven hook wins
instead (likely the common case, since they fire every user turn vs.
this script's 60s cadence), the watchdog still runs via the unchanged
`nohup`-background path in `poll-rearm.sh`; its report lands only in
`poll-watchdog.log`, and this tick prints the unchanged
`"poll tick: skipped (within TTL)"` with no report content.

This is not a regression introduced by this change — the same
three-caller shared-TTL-gate race existed identically before this
proposal (whichever caller won the race launched the watchdog; the
other two calls returned 1 and produced no watchdog output regardless).
The approved proposal's Rationale explicitly names the two turn-driven
hooks as already running the watchdog on the same cadence and treats
that shared cost as accepted, not newly introduced; wiring full
every-tick coverage across all three callers sits under the proposal's
out-of-scope item naming step 3, the #776 harness scenario wiring, as
separate work.

resolution path: a follow-up product-discovery round, or the issue #922
execution-plan step 3 itself, needs to settle whether the turn-driven
hooks should also surface their own captured report (per the operator's
scoping-note point 2 on the issue thread, "Monitor 자동무장 stdout +
훅 systemMessage") so a Monitor-tick win stops being the only path to a
user-visible report. Making that change would require editing
`on-the-record/hooks/poll-rearm.sh`, `directive.sh`, and/or
`stop-poll-rearm.sh` — outside this proposal's frozen write set
(`on-the-record/monitors/poll-heartbeat.sh`,
`on-the-record/monitors/test_poll_heartbeat.py` only) — so it is
reported here per the SCOPE-EXCEEDED rule rather than widened mid-build.

## Doc placement ladder

- [x] No new env var, config key, dependency, or migration introduced —
  no handbook update required.
- [x] No changed public signature or wire format beyond the mechanism
  already recorded in the phase-1 proposal's own Rationale — no separate
  decisions-doc entry needed this phase.
- [x] No benchmark/investigation numbers produced.

## Hunt cadence

- after-proposal hunt (phase 1): recorded at
  docs/issue-922/reports/implementation/2026-08-12-hunt-poll-heartbeat-capture-hop.md
  — FINDING (write-set gap), resolved by rewording the proposal's
  mechanism paragraph before phase-2 approval.
- before-landing hunt (phase 2, this session): same file, section
  "before-landing — stance 0" — FINDING (TTL-race coverage gap), logged
  above under Open findings, not resolved within this proposal's scope.

closed_checks:
- check: poll-rearm.sh/directive.sh/stop-poll-rearm.sh unchanged
  code_sha: uncommitted-worktree (see code_under_review file list above; git diff --stat citation above)
- check: skipped-tick stdout line unchanged (`"poll tick: skipped (within TTL)"`), asserted by `t_heartbeat_skips_watchdog_when_not_due`
  code_sha: uncommitted-worktree (see code_under_review file list above)
