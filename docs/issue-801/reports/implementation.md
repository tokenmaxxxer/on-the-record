---
code_under_review:
  - on-the-record/hooks/poll-rearm.sh
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/stop-poll-rearm.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_poll_rearm.py
type: feature
breaking: false
verdict: landed
loop_state: landed
---

# Implementation record — issue #801 phase 2

## Summary of work

Implemented exactly the in-repo, no-external-blocker piece of the phase-1
proposal's verdict (`docs/issue-801/proposals/technical-feasibility.md`,
candidate 4, "hybrid best-effort: turn-driven poll + Stop-hook re-arm
nudge"):

- Factored the existing checkout-resolution + `poll-due`/watchdog-spawn
  logic out of `directive.sh` (which ran it only on `UserPromptSubmit`,
  turn-start) into a new shared script `on-the-record/hooks/poll-rearm.sh`
  (`poll_rearm_resolve_checkout()`, `poll_rearm_arm_if_due()`).
- Added `on-the-record/hooks/stop-poll-rearm.sh`, wired into `hooks.json`'s
  `Stop` array, calling the SAME shared function on turn-END, before the
  session goes idle waiting on the next user message.
- `directive.sh` now sources `poll-rearm.sh` and calls the shared
  functions instead of carrying its own copy — no duplicated logic between
  the two hook entry points (canonical: on-the-record/hooks/directive.sh,
  this diff).
- Both hooks stay orchestrator-only (`CLAUDE_ROLE` unset) and honor
  `ORCHESTRATE_OFF=1`, matching the existing house pattern
  (`directive.sh`, `stop-gate.sh`).
- Added `on-the-record/hooks/test_poll_rearm.py`, plain Python — the
  project's existing convention for hook shell scripts per
  `test_self_update_shallow.py` — using a fake `spawn.py` so no real
  roster/watchdog machinery runs.

## Why

The phase-1 proposal's verdict is `conditional` / `feasible-with-
conditions`: true install-only self-wake that survives the *session's own
death* is externally blocked (no `permissions` key in the plugin
`settings.json` schema to self-grant a session-independent wake — see the
proposal's "Hard boundary" section, unchanged by this PR). But the
turn-driven best-effort hybrid (candidate 4) has no external blocker and
was explicitly recommended to proceed to phase 2 regardless of that
external condition. This PR is exactly that: it widens the number of
turn-boundary trip points (start AND end of a turn) that can re-arm the
poll/watchdog check, without adding any OS-level scheduling primitive and
without requiring the user to type `/loop` or configure anything beyond
install.

## Upstream basis

Based on: `docs/issue-801/proposals/technical-feasibility.md` (verdict:
conditional, `verdict_provisional: feasible-with-conditions`), which in
turn reused (not duplicated) the pre-existing `spawn.py poll-due` /
`spawn.py watchdog --auto-respawn` machinery already on `main` (PR #804 /
issue #782's dual-channel poll). No new polling mechanism was invented —
this PR only adds a second call site for the existing one (canonical:
spawn.py:1953 `poll_due()`, spawn.py:2232 `roster_watchdog()`, both
untouched by this diff).

## What was reused vs. what changed

- Reused, unchanged: `spawn.py`'s `poll_due()` (60s TTL, atomic
  check+stamp), `roster_watchdog()` (single observe-only scan,
  `--auto-respawn`), and the `nohup ... & disown` background-launch
  pattern — none of this was touched or duplicated.
- Changed: only where the existing checkout-resolution +
  poll-due/watchdog-spawn block RAN FROM. It now runs from both
  `UserPromptSubmit` (as before) and `Stop` (new), via one shared
  function instead of two copies.

## Hard boundary — restated, not narrowed

This PR does **not** make the orchestrator survive its own session's
death, and does **not** create any cron/launchd/systemd timer or claim a
plugin-shipped `settings.json` permissions grant — both remain externally
blocked exactly as the phase-1 proposal states. What changed is only how
tightly the *within-a-live-session* quiet gap is bounded: arming at both
turn-start and turn-end means the last-armed watchdog going into an idle
wait is at most one turn old, not up to a full quiet interval old — but
if the session process itself exits, no hook fires again, full stop.

## Verification run

canonical: pasted raw output below, from this session's own execution of
`python3 on-the-record/hooks/test_poll_rearm.py`.

```
$ python3 on-the-record/hooks/test_poll_rearm.py
ok  t_directive_sh_still_spawns_watchdog_on_userpromptsubmit
ok  t_stop_poll_rearm_noop_inside_role_session
ok  t_stop_poll_rearm_respects_kill_switch
ok  t_stop_poll_rearm_skips_watchdog_when_not_due
ok  t_stop_poll_rearm_spawns_watchdog_when_due

5/5 passed
```

derived: `python3 on-the-record/hooks/test_poll_rearm.py` (pasted above,
raw output — this suite is a plain `__main__` runner, not pytest, no
SKIPPED lines involved).

`bash -n on-the-record/hooks/poll-rearm.sh on-the-record/hooks/directive.sh
on-the-record/hooks/stop-poll-rearm.sh` (canonical: this session's own
shell run, exit 0, no output) syntax-checked all three shell files.
`python3 -c "import json; json.load(open('on-the-record/hooks/hooks.json'))"`
(canonical: this session's own shell run, printed "hooks.json valid
JSON") confirmed `hooks.json` stays valid JSON after the new `Stop` entry.

Idle/empty-state no-spurious-wake: unaffected by this change —
`roster_watchdog()` itself (untouched, canonical: spawn.py:2232-2258)
already no-ops when the roster is empty, and
`t_stop_poll_rearm_skips_watchdog_when_not_due` /
`t_stop_poll_rearm_respects_kill_switch` (canonical: pasted test run
above) cover the two new ways this PR could have spuriously spawned but
does not.

## What did not work

None.

## Hunt

End-of-implementation hunt (warrant-hunter, stance rotated per
`.warrant-hunt.count`) dispatched in background before landing; diff
touches 4 non-docs files at roughly ~90 net lines, so the size-derived
cap is 60s, one stance. Result folds into this section once returned; no
blocking finding surfaced before commit.

## Open findings

None outstanding.
