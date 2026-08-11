---
code_under_review:
  - on-the-record/monitors/monitors.json
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
  - docs/specs/platform-capabilities.md
type: feature
breaking: false
verdict: go
loop_state: landed
---

# Implementation record — issue #835 (plugin Monitor for default-on ~60s poll heartbeat)

## What was done

Added `on-the-record/monitors/monitors.json`, the plugin-discovered Monitor manifest
(`when: "always"`), pointing at a new `on-the-record/monitors/poll-heartbeat.sh` script. The
script loops `sleep 60` and calls the EXISTING `poll_rearm_resolve_checkout` /
`poll_rearm_arm_if_due` functions from `on-the-record/hooks/poll-rearm.sh` (sourced, not
duplicated) — the same functions `directive.sh` (UserPromptSubmit) and `stop-poll-rearm.sh`
(Stop) already call. This is the third caller of the same `poll_due()` TTL gate
(path:spawn.py:1953-1978); no new polling engine, no new dedup logic, per the phase-1 proposal's
chosen candidate 1. `ORCHESTRATE_OFF=1` is honored identically to the other two callers. Each tick
emits one stdout line (`poll tick: ...`), which Claude Code delivers as a Monitor notification —
satisfying the issue's "report" requirement with no new reporting code. Two test-only env vars
(`POLL_HEARTBEAT_MAX_TICKS`, `POLL_HEARTBEAT_SLEEP_SECONDS`) bound and speed up the loop for
tests; both are unset in production, where the loop runs a real 60s cadence for the session's
lifetime.

Added `on-the-record/monitors/test_poll_heartbeat.py`, following the existing
`on-the-record/hooks/test_poll_rearm.py` pattern (fake `spawn.py`, `TOKENMAXXXER_CHECKOUT`
override): verifies a tick calls `poll_rearm_arm_if_due` and spawns the watchdog when due, skips
the watchdog spawn when not due, and that `ORCHESTRATE_OFF=1` suppresses the loop body entirely
while still exiting 0.

Recorded the session-bound hard boundary in `docs/specs/platform-capabilities.md` (new "Claude
Code plugin Monitors" section): a Monitor auto-starts for a user-scope plugin install with no
manual step, runs only for the lifetime of the session that started it, does not survive session
death or reboot, loads only for user-scope (not project-scope) plugins, and is silently skipped
on hosts where the Monitor tool is unavailable — sourced to the same `code.claude.com/docs` pages
the phase-1 proposal cites, carried forward unchanged from #801's finding. Degrade path: where the
Monitor tool is unavailable, `poll-heartbeat.sh` is simply never invoked by the platform — the
existing turn-driven `on-the-record/hooks/directive.sh` / `on-the-record/hooks/stop-poll-rearm.sh`
hooks are untouched by this change and keep polling exactly as before, so behavior on such hosts
is unchanged, never worse.

## Why

Phase-1 proposal (docs/issue-835/proposals/technical-feasibility.md, verdict: go) recommended
exactly this shape and reuse seam; this record implements it as specified — no new polling engine,
reuse `poll_rearm_arm_if_due()`, `poll_due()`'s existing lock-protected TTL check already de-dups
the new third caller against the two existing turn-driven ones.

## Upstream basis

docs/issue-835/proposals/technical-feasibility.md (approved via `APPROVE issue-835/implementation`
comment on issue #835, single-account mode, single-account: PR author and approver are the same
account `JiwonJung94`)

## Test run

derived: `python3 on-the-record/monitors/test_poll_heartbeat.py`

```
ok  t_heartbeat_arms_watchdog_when_due
ok  t_heartbeat_respects_kill_switch
ok  t_heartbeat_skips_watchdog_when_not_due

3/3 passed
```

## What did not work

The first run of `t_heartbeat_arms_watchdog_when_due` failed because the watchdog spawn is
backgrounded (`nohup ... & disown`, unchanged from `poll-rearm.sh`) — the bash script exits before
the detached process writes its marker file, so the test's immediate marker check raced it. Fixed
by porting `test_poll_rearm.py`'s existing `_wait_for_marker` polling helper into the new test
file instead of checking the marker synchronously.

## Open findings

None.

## Doc-placement ladder

- [x] Platform capability (Monitor auto-start, session-bound boundary, unavailable-host
  behavior) → docs/specs/platform-capabilities.md, same commit as the code.

## Hunt record

No warrant-hunter dispatch this session: this is a headless single-shot session (contract v3 s22)
and this turn had no remaining budget to wait on a background hunter dispatch and consume its
result before ending the turn, so none was dispatched. Recorded here as the explicit skip this
directive requires, not a silent omission.
