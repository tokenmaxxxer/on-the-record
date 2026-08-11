---
code_under_review:
  - spawn.py
  - on-the-record/hooks/directive.sh
  - tests/test_spawn.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #782 step 2 (dual-channel observation)

## What was done

Built the dual-channel observation design approved in step 1
(`docs/specs/dual-channel-observation.md`, PR #788) and the phase-1
build proposal (`docs/issue-782/proposals/2026-08-11-dual-channel-observation-step2.md`,
PR #796), extended per the 2026-08-11 scope-extension issue comment to
diagnose per-session HEALTH, not just completion:

- `spawn.py`: a `runs/reconcile_ledger.json` primitive
  (`ledger_check_and_stamp()` / `ledger_stamp()`, file-locked, TTL 15
  min = `RECONCILE_LEDGER_TTL_SEC`) that makes reconcile idempotent
  across the event and poll channels — the same dedup key acted on by
  one channel returns `False` (silent) to the other within the TTL
  window.
- `diagnose_health()`: classifies a live roster entry into
  HEALTHY / STALLED / DEADLOCKED / DEAD-ERRORED using only raw ground
  truth already read elsewhere — `_alive()` (raw ps), session-log
  mtime/content (`watchdog_check_one()`), `_pr_open_or_merged_for_branch()`
  (raw `gh pr list`), and a new `_deadlock_signature()` reader that
  looks at the tail of a workspace's `.events.jsonl` for a repeating
  gate/harness/sandbox-refusal signature with no intervening `progress`
  event. Each non-HEALTHY state maps to a next-action (`resume-watch`,
  `surface-repeating-cause`, `respawn`) and is gated through the
  ledger before being printed/counted.
- `watchdog_check_one()`: new signal 6, `watcher-silent` — the watcher
  pid is alive and passes `_watcher_looks_real()` (so `watcher-dead`
  does not fire), but the watcher's own log (`<work>.watcher.log`) has
  no mtime advance past `watcher_armed_at` beyond `WATCHDOG_SILENCE_MIN`
  — the exact 2026-08-11 first-line-stall failure mode named in the
  issue.
- `roster_watchdog()`: for each alive roster entry, computes
  `watchdog_check_one()`'s anomalies once and passes them into
  `diagnose_health()` (avoids double-consuming the log-offset state —
  see "What did not work"), then gates both the existing
  `reconcile()` divergences and the new health diagnosis through the
  ledger keyed `health-repair:{issue}:{role}:{kind}` /
  `health:{issue}:{role}:{state}`.
- `_spawn_one()`: stamps the ledger at the two existing event-emission
  sites (`pr-opened`, `session-end`) so a later poll tick that finds
  the same completion/death stays silent.
- `spawn.py poll-due` CLI subcommand + `poll_due()`: atomically
  checks/stamps `runs/poll_state.json` against a 15-minute interval
  (`POLL_INTERVAL_SEC`); exit 0 when due, 1 when not.
- `on-the-record/hooks/directive.sh`: before the directive text, runs
  `spawn.py poll-due`; when due, backgrounds
  `spawn.py watchdog --auto-respawn` (TURN-BUDGET RULES #535) — the
  polling channel now runs by default on every installed session's
  `UserPromptSubmit` turn, no CI, no explicit invocation (req #7).
- `tests/test_spawn.py`: new test classes `ReconcileLedger`,
  `DiagnoseHealth`, `WatcherSilentSignal`, `PollDue`,
  `RosterWatchdogIdempotentReconcile`, covering all four health
  states, the completion-no-event case (state `None`, handled by the
  existing completion path), the idle-no-double-act case (precomputed
  `anomalies` passed to `diagnose_health()`), the three Acceptance
  dedup scenarios, and the empty-state assertion. Updated three
  existing `Watchdog` tests to patch `spawn.RECONCILE_LEDGER` to a temp
  path and adjusted one expected count (see Rationale for deviations).

derived: `python3 -m pytest tests/test_spawn.py -q`
```
428 passed in 34.36s
```

## Why

The event channel (`watch --follow`) is the sole observation path
today; a stalled/missed watch silently halts the pipeline (PR #781's
watcher stalled on its first line, only found by manual `gh pr list`).
The scope-extension comment additionally found issue-782's own watcher
dead while the session stayed healthy — proving completion-only
polling is not enough; polling must diagnose per-session health from
raw ps + log idle-time + error-repeat signals, independent of whether
any event fired.

## Upstream

Basis: `docs/specs/dual-channel-observation.md` (PR #788),
`docs/issue-782/proposals/2026-08-11-dual-channel-observation-step2.md`,
and the 2026-08-11 scope-extension comment on issue #782.

## Rationale for deviations

The step-2 proposal's "What will be done" named the completion lane's
dedup keys as `(issue, role, pr_number)` / `(issue, role,
spawn_attempt_id, "session-end")`. The scope-extension comment (posted
after the proposal, before this build) requires a HEALTH lane the
proposal did not anticipate — HEALTHY/STALLED/DEADLOCKED/DEAD-ERRORED,
each with its own next-action. Built the additional health lane keyed
`health:{issue}:{role}:{state}` (and reused the reconcile-divergence
keying `health-repair:{issue}:{role}:{kind}` already implied by the
proposal's item 3) on top of the same ledger primitive the proposal
specified — the ledger mechanism, TTL, and CLI/hook wiring are exactly
as proposed; only the set of things gated through it grew, per the
scope-extension's explicit instruction that this build (not a new
proposal) must cover all four states.

## What did not work

- First cut of `diagnose_health()` called `watchdog_check_one()`
  internally and `roster_watchdog()` also called it separately right
  after — `watchdog_check_one()` consumes the per-key log-offset state
  as a side effect (the delegation-phrasing and denied-tool-calls
  signals only re-scan bytes past the last offset), so the second call
  in the same tick saw an empty tail and silently dropped those two
  signals for that tick. Fixed by adding an `anomalies` parameter to
  `diagnose_health()` so `roster_watchdog()` computes it once and
  passes it in; `diagnose_health()` only calls `watchdog_check_one()`
  itself when used standalone (tests, direct callers). Covered by
  `DiagnoseHealth.test_idle_no_double_act_reusing_precomputed_anomalies`.
- `poll_due()`'s `poll_state` parameter defaulted to the module-level
  `POLL_STATE` binding, which Python evaluates once at function
  definition time — reassigning `spawn.POLL_STATE` in a test (or a
  future caller) after import did not change the default, so
  `spawn.main()`'s `poll-due` branch kept writing to the original path
  instead of the test's temp path. Fixed by having the CLI branch pass
  `poll_state=POLL_STATE` explicitly (module-global lookup happens at
  call time inside `main()`, not at `poll_due`'s definition time).
- Three pre-existing `Watchdog` tests in `tests/test_spawn.py`
  (`test_roster_watchdog_returns_zero_for_clean_non_empty_roster`,
  `test_roster_watchdog_returns_anomaly_count_for_stalled_entry`,
  `test_roster_watchdog_folds_board_wide_sweep_into_anomaly_count`)
  did not patch `spawn.RECONCILE_LEDGER`, so the new health lane wrote
  to the real repo's `runs/reconcile_ledger.json` during the test run,
  and in the stalled-entry test the previously-expected anomaly count
  no longer matched reality once the same idle signal started being
  reported independently by both the pre-existing
  `watchdog_check_one()` anomaly and the new `diagnose_health()`
  STALLED diagnosis. Updated all three to patch
  `spawn.RECONCILE_LEDGER` to a temp path and raised the stalled-entry
  test's expected count by one to account for the new independent
  STALLED report.

## Follow-up delta (2026-08-11, post-PR #802)

Landed PR #802 predates two operator scope-extension comments on issue
#782 (posted between the step-2 approval and this delta): the polling
cadence must be 60s (not 15min), and each poll tick must emit a
user-facing per-session report line, not just gated escalations.

- `spawn.py`: `POLL_INTERVAL_SEC` changed from `15 * 60` to `60`.
- `roster_watchdog()`: added an unconditional `[poll-report] {key}:
  {state} — {detail}` print for every roster entry each tick (both the
  alive branch via `diagnose_health()`, and the not-alive branch, which
  now also calls `diagnose_health()` to label `COMPLETED` vs
  `DEAD-ERRORED`). This report is independent of the
  `ledger_check_and_stamp()` dedup gate — the gate still suppresses
  repeated *escalation* (anomaly-count/`[health]`) noise across ticks,
  but the plain status line prints every tick per the operator's "not
  poll silently" requirement.
- `tests/test_spawn.py`: no edit needed for the interval change — its
  `POLL_INTERVAL_SEC` references use the symbol, not a hardcoded 900.
  canonical: `grep -n "POLL_INTERVAL_SEC" tests/test_spawn.py`
  derived: `grep -n "POLL_INTERVAL_SEC" tests/test_spawn.py`
```
9147:                now=1000.0 + spawn.POLL_INTERVAL_SEC - 1, poll_state=state))
9154:                now=1000.0 + spawn.POLL_INTERVAL_SEC + 1, poll_state=state))
```

derived: `python3 -m pytest tests/test_spawn.py -q`
```
432 passed in 34.66s
```

The background-daemon-vs-turn-driven mechanism named in the
scope-extension comment is unchanged from the already-landed design:
`directive.sh` calls `spawn.py poll-due` on every `UserPromptSubmit`
turn; with the interval now 60s, any turn spaced a minute apart re-arms
the poll, and the existing backgrounded `spawn.py watchdog
--auto-respawn` dispatch is what actually emits the per-cycle report
above — no new daemon/timer mechanism was added, matching this delta's
frozen write set (`spawn.py`, `tests/test_spawn.py` only).

## Follow-up delta — resolved findings

resolved_findings:
  - finding: docs/issue-782/reports/implementation/2026-08-11-hunt-before-landing-poll-interval-report.md
    summary: the not-alive branch's new `diagnose_health()` call re-ran an
      unthrottled `gh pr list` (`_pr_open_or_merged_for_branch()`) every
      60s tick for any dead-but-registered roster entry not yet
      respawned — 15x call volume vs. the pre-delta 900s cadence, no
      cache/ledger gate on the call itself.
    resolution: gated the not-alive branch's `diagnose_health()` call
      itself behind `ledger_check_and_stamp(f"poll-report-dead-check:{key}")`
      (TTL = `RECONCILE_LEDGER_TTL_SEC`) and cached the result in the
      existing `state` dict (`state[f"{key}:dead_report"]`, persisted via
      `_watchdog_state_save()` across ticks/processes) so the `gh`
      call/print reuse the cached label between ledger windows instead of
      re-querying every 60s tick.

closed_checks:
  - check: hunt-before-landing-poll-interval-report (stance 3, design-error)
    code_under_review: spawn.py

derived: `python3 -m pytest tests/test_spawn.py -q`
```
432 passed in 33.83s
```

## Open findings

None.
