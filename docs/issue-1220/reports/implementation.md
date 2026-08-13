---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - gates/test_poll_heartbeat_delta.py
  - on-the-record/monitors/test_poll_heartbeat.py
type: feature
breaking: false
# canonical: python3 gates/test_poll_heartbeat_delta.py and python3 on-the-record/monitors/test_poll_heartbeat.py — output pasted under Acceptance verification below.
verdict: pass
loop_state: landed
---

## What was done

canonical: python3 gates/test_poll_heartbeat_delta.py — result: see Acceptance verification below
Changed `on-the-record/monitors/poll-heartbeat.sh`: replaced the prior whole-text SHA-256 suppression (issue #1117) with a line-keyed diff. The due branch splits the captured watchdog report into lines, keys each by its `[tag] key:` prefix (`poll-report`/`watchdog`/`health`/`reconcile`/`orphaned`/`resume`/`watchdog-crash`) or `session/role: status` entry prefix, keys unprefixed bullet lines (`  - ...`) under the nearest preceding tagged key with a per-tick ordinal suffix (`{parent_key}#0`, `{parent_key}#1`, ...) so variable-count anomaly bullets never collapse onto one key, and keys any remaining unprefixed singleton line to a fixed constant.

canonical: python3 gates/test_poll_heartbeat_delta.py — result: see Acceptance verification below
The keyed map is diffed against the previous tick's map, persisted as JSON at `runs/poll_heartbeat_last_state.json` (superseding the prior `runs/poll_heartbeat_last_hash` sibling file). Unchanged keys emit nothing; new/changed keys emit their line; keys matching an always-emit category (STALLED/CRASHED/COMPLETED/watcher-dead/`[resume]`/`[orphaned]`/`[watchdog-crash]`) emit every tick regardless of diff. A non-zero watchdog exit now appends a `[watchdog-crash]` marker line so a crash is always in the always-emit category, not just a hash-differing string.

canonical: python3 gates/test_poll_heartbeat_delta.py — result: see Acceptance verification below
The non-due branch's unconditional `echo "poll tick: skipped (within TTL)"` was removed — a normal within-TTL tick now produces zero stdout. Added a bounded aliveness heartbeat: when a due tick's diff produces no output and the elapsed time since the last emission of any kind crosses the bound, one bounded `[heartbeat] monitoring active, N session(s) tracked, no changes` line is printed and the emission clock resets. First-ever tick (no `runs/poll_heartbeat_last_state.json`) emits every key once, satisfying the "empty state" acceptance case.

canonical: python3 gates/test_poll_heartbeat_delta.py — result:
```
8/8 passed
```
Changed `gates/test_poll_heartbeat_delta.py`: kept the prior suppression-era cases (updating the first-tick assertion to check the new state file instead of the retired hash file) and added the proposal's listed cases — only-changed-line-emits, dead-line-always-emits, non-due-silent, first-tick-emits-initial-state (folded into the updated existing case), and the watchdog-bullet round-trip regression guard.

canonical: python3 on-the-record/monitors/test_poll_heartbeat.py — result:
```
5/5 passed
```
Changed `on-the-record/monitors/test_poll_heartbeat.py`: one pre-existing test (`t_heartbeat_skips_watchdog_when_not_due`) asserted the now-removed "skipped (within TTL)" line — updated to assert empty stdout, logged as an inline deviation (docs/issue-1220/reports/implementation/deviation-log.md) since this file sits outside the proposal's frozen write set but the change is a direct, mechanical consequence of the approved non-due-branch behavior change.

## Why

Issue #1220 (citing northpole req#4) asks for true delta-only Monitor emission: no output on a non-due or no-change tick, only the delta when something changed, always-surfacing crash/dead/orphaned/resume transitions, and a bounded aliveness signal so the channel never goes fully silent. The prior whole-text hash compare re-emitted the full report on any single-byte diff, which does not satisfy "emits exactly the delta."

## Acceptance verification

canonical: python3 gates/test_poll_heartbeat_delta.py — result:
```
ok  t_change_after_suppression_emits
ok  t_changed_tick_emits
ok  t_dead_session_line_always_emits_even_unchanged
ok  t_fresh_state_first_tick_always_emits
ok  t_identical_second_tick_suppressed
ok  t_non_due_tick_produces_no_output
ok  t_only_changed_line_emitted_not_full_report
ok  t_watchdog_anomaly_bullets_survive_round_trip

8/8 passed
```

canonical: python3 on-the-record/monitors/test_poll_heartbeat.py — result:
```
ok  t_heartbeat_arms_watchdog_when_due
ok  t_heartbeat_respects_kill_switch
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller

5/5 passed
```

- identical-snapshots second tick emits nothing: covered by `t_identical_second_tick_suppressed` and `t_watchdog_anomaly_bullets_survive_round_trip`.
- new-delta emits exactly the delta: covered by `t_only_changed_line_emitted_not_full_report`.
- crashed-session always emits: covered by `t_dead_session_line_always_emits_even_unchanged`.
- first-ever tick emits initial state: covered by `t_fresh_state_first_tick_always_emits`.

Live proof plan (not executed this session — requires a running Monitor-hosting session, out of reach in this headless single-shot turn): after this lands, an idle window of 10+ minutes in a session with the Monitor running should produce no visible monitor messages beyond at most one bounded heartbeat, and an induced state change (e.g. a new PR appearing) should surface within one tick, per the proposal's "How you'll know it worked — Live" section.

## Hunt

canonical: docs/issue-1220/reports/implementation/hunt-delta-only-monitor-emission.md, read this session.
docs/issue-1220/reports/implementation/hunt-delta-only-monitor-emission.md (pre-existing, phase-1 after-proposal stance) found: the proposal's originally-described "single fixed key" fallback for unprefixed lines would collapse multiple `  - {a}` anomaly-detail bullet lines into one dict entry, silently dropping all but the last.

canonical: python3 gates/test_poll_heartbeat_delta.py — result: see Acceptance verification above
This build resolves that finding directly: bullet lines are keyed `{parent_key}#{ordinal}` (per-tick position under their preceding tagged header), not a shared fixed key, so each anomaly bullet gets its own diff key. `t_watchdog_anomaly_bullets_survive_round_trip` is the closed-check regression guard for this.

closed_checks:
- check: warrant-hunt finding (bullet-collapse under fixed key) — resolved by per-parent ordinal keying, guarded by t_watchdog_anomaly_bullets_survive_round_trip
  code_sha: 257f4ea0bd7a800dfea019b3f064345cfbdabe67

## What did not work

None.

## Rationale for deviations

canonical: python3 on-the-record/monitors/test_poll_heartbeat.py — result: see Acceptance verification above
`on-the-record/monitors/test_poll_heartbeat.py` was edited even though it is not in the proposal's frozen `files:` list (`on-the-record/monitors/poll-heartbeat.sh`, `gates/test_poll_heartbeat_delta.py`). The proposal's own "What will be done" mandates removing the non-due branch's unconditional echo line; that pre-existing test asserted exactly that line's presence and would fail against the approved change. The fix is a single mechanical assertion swap (echo-line check -> empty-stdout check), makes no design choice, and does not change what the deliverable does — classified INLINE-FIX per the deviation loop and logged at docs/issue-1220/reports/implementation/deviation-log.md.

## Open findings

canonical: docs/issue-1220/reports/implementation/hunt-delta-only-monitor-emission.md, read this session.
None open — the one warrant-hunt finding against the phase-1 proposal (bullet-line collapse) is resolved by the closed_checks entry above; verify retains authority to re-derive or cite-and-skip it.

## Basis

canonical: docs/issue-1220/proposals/delta-only-monitor-emission.md, read this session.
Based on: docs/issue-1220/proposals/delta-only-monitor-emission.md (proposal PR #1229, merged), approved via `APPROVE issue-1220/implementation` posted on the issue per contract v3 s19 single-account mode.
