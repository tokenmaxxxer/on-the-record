---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/monitors.json
  - README.md
  - on-the-record/monitors/test_poll_heartbeat.py
---

## Request

Scouting skip: mechanical, no design decision open — issue #1724 names
the exact env var, exact placement, and exact case-list
(`docs/issue-1724/reports/implementation/survey.md` "Scouting").

The plugin Monitor (`on-the-record/monitors/poll-heartbeat.sh`,
`when: always`) arms in every interactive session of any repo with the
plugin enabled, and Claude Code has no per-monitor on/off setting. The
existing `ORCHESTRATE_OFF=1` kill switch stops every hook in the plugin,
which is more than an operator who only wants a quiet session needs.
`POLL_HEARTBEAT_SLEEP_SECONDS` can stretch the tick cadence but cannot
stop the process from producing due-tick output at all. #1724 asks for a
second, narrower kill switch — `OTR_MONITOR_OFF=1` — that stops only
this one Monitor script, and for both operator knobs
(`OTR_MONITOR_OFF`, `POLL_HEARTBEAT_SLEEP_SECONDS`) to be named together
in `monitors.json`'s description and in a README monitor section, with
`.claude/settings.local.json`'s `env` block named as the recommended
place to set them.

## Constraints

- With `OTR_MONITOR_OFF=1` set, `poll-heartbeat.sh` must exit 0 before
  its first `sleep`, write nothing to stdout, and touch no `runs/` state
  file (issue Acceptance check 1).
- Every other hook (`directive.sh`, `stop-poll-rearm.sh`,
  `poll-rearm.sh`, the commit-time gate hooks) must behave exactly as
  before — the new switch is monitor-only, never routed through the
  shared `poll_rearm_arm_if_due()` machinery or any other hook file
  (issue Acceptance check 1 parenthetical).
- Unset or `0`/`false`/`no`/`off` must be identical to today's behavior,
  including `ORCHESTRATE_OFF=1` still stopping the monitor (issue
  empty-state clause) — the new switch's case-list must match
  `ORCHESTRATE_OFF`'s existing five-item list exactly (task instruction:
  "same case-list as ORCHESTRATE_OFF").
- `monitors.json`'s `description` and the README's monitor section must
  each name both `OTR_MONITOR_OFF=1` and `POLL_HEARTBEAT_SLEEP_SECONDS`
  as the two operator knobs, and name `.claude/settings.local.json`'s
  `env` as the recommended place to set them (issue Acceptance check 2).
- Minimal diff (task instruction): no new files beyond the two doc/test
  additions already implied, no new state.

## Rationale

**Separate case statement vs. folding into the existing one.** Two ways
to add the check were on the table:

1. **Fold `OTR_MONITOR_OFF` into the existing `ORCHESTRATE_OFF` case
   statement** (rejected), e.g. matching on a combined
   `"${ORCHESTRATE_OFF:-}:${OTR_MONITOR_OFF:-}"` string, or adding a
   second pattern to the same `case`. This reads as fewer lines, but it
   conflates two independently-toggleable switches into one harder-to-
   read match expression, makes it easy to accidentally change one
   switch's semantics while editing the other's pattern, and blurs the
   issue's explicit "the switch is monitor-only" framing — the two
   switches are conceptually unrelated (one is plugin-wide, one is
   monitor-only) and the existing four other `ORCHESTRATE_OFF` call
   sites (survey's "What exists today") never combine two switches this
   way either, so it would also be a new convention, not a mirror of the
   existing one.
2. **A second, adjacent `case` statement, same literal five-item
   empty-state list, same `exit 0` action** (chosen): mirrors the
   existing line exactly, is trivially greppable as its own kill switch,
   and needs no new logic to reason about — two independent one-line
   checks, either of which exits early. This is the literal reading of
   "same case-list as ORCHESTRATE_OFF" (a second instance of the same
   pattern, not a merged one).

**Placement.** The survey's "What exists today" section already
established that "before its first sleep" and "touches no runs/ state
file" describe the same cut point (the only `runs/` write on this path,
`_alive_stamp_write`, happens inside the loop, after the first `sleep`)
— so placing the new check immediately after the existing
`ORCHESTRATE_OFF` line (before `SCRIPT_DIR` is even resolved) satisfies
both constraints, plus "writes nothing to stdout" (nothing prints before
that line today), for free. No alternative placement was seriously
considered: any later placement would only add risk of touching state
the acceptance forbids, for no benefit.

**Failure signal.** If this proposal is wrong, the signal is the new
`on-the-record/monitors/test_poll_heartbeat.py` assertion failing
against the actual `poll-heartbeat.sh` output (non-empty stdout, a
written `runs/` file, or a nonzero exit code), or a live session still
seeing Monitor output after `OTR_MONITOR_OFF=1` is set.

## What will be done

- In `poll-heartbeat.sh`: add
  `case "${OTR_MONITOR_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac`
  immediately after the existing `ORCHESTRATE_OFF` line (line 44), and
  extend the header comment's existing "Kill switch: ORCHESTRATE_OFF=1"
  line (lines 33-35) to also name `OTR_MONITOR_OFF=1` as the
  monitor-only counterpart.
- In `monitors.json`: extend the `description` string to name
  `OTR_MONITOR_OFF=1` (monitor-only kill switch) alongside the existing
  `POLL_HEARTBEAT_SLEEP_SECONDS` mention.
- In `README.md`: add a short monitor section (placed in the
  "Interaction flow" area, alongside the existing spawn/rulebook
  subsection) naming both `OTR_MONITOR_OFF=1` and
  `POLL_HEARTBEAT_SLEEP_SECONDS` as the two operator knobs, and naming
  `.claude/settings.local.json`'s `env` block as the recommended place
  to set them, with a minimal JSON snippet showing that block's shape.
- In `on-the-record/monitors/test_poll_heartbeat.py`: first, extend
  `_run_heartbeat`'s env-dict construction to unconditionally normalize
  `OTR_MONITOR_OFF` (`env["OTR_MONITOR_OFF"] = env_extra.get("OTR_MONITOR_OFF", "")`),
  mirroring how it already unconditionally sets
  `POLL_HEARTBEAT_SLEEP_SECONDS`/`POLL_HEARTBEAT_MAX_TICKS` and pops
  `CLAUDE_ROLE` — a pre-phase-2 hunt
  (`docs/issue-1724/reports/implementation/2026-08-17-hunt-otr-monitor-off-kill-switch.md`)
  found that without this, an ambient `OTR_MONITOR_OFF=1` in the
  invoking shell (exactly what this proposal tells operators to set via
  `.claude/settings.local.json`) silently masks any test that claims
  `OTR_MONITOR_OFF` is unset, including a regression that deletes the
  `ORCHESTRATE_OFF` check entirely. Then add one new test,
  `t_heartbeat_respects_monitor_only_kill_switch`, mirroring the
  existing `t_heartbeat_respects_kill_switch` (`ORCHESTRATE_OFF`) test
  but for `OTR_MONITOR_OFF=1` — asserting `returncode == 0`, empty
  stdout, the watchdog marker never written, and
  `${CHECKOUT}/runs/` never created; plus a second test asserting
  `ORCHESTRATE_OFF=1` alone (with `OTR_MONITOR_OFF` explicitly normalized
  to unset by the fixed helper above) still stops the monitor exactly as
  it does today, pinning the empty-state clause's "identical behavior to
  today" requirement.

## Out of scope

- Any change to `ORCHESTRATE_OFF`'s own behavior, case-list, or the four
  other hook files that check it — untouched, per "the switch is
  monitor-only."
- Any change to `POLL_HEARTBEAT_SLEEP_SECONDS`'s existing semantics —
  only its documentation is touched, not its behavior.
- `docs/handbooks/monitor-liveness.md` or `docs/handbooks/hooks.md` —
  the issue names `monitors.json`'s description and "the README's
  monitor section" specifically; extending either handbook is a
  follow-up, not this issue's write set.
- `README.ko.md` — the issue names "the README" (singular); the Korean
  translation is not in this issue's write set.

## Accumulation

`on-the-record/monitors/test_poll_heartbeat.py`'s existing kill-switch
test (`t_heartbeat_respects_kill_switch`) and both new ones this
proposal adds all call the same existing `_run_heartbeat` helper
(survey's "What already tests this file") — no new raw `subprocess.run`
call site is added, and no new fixture/marker plumbing is needed since
the existing `_wait_for_marker`/env-dict shape already covers a
kill-switch run. If a third monitor-only kill switch is ever added
later, the two `ORCHESTRATE_OFF`/`OTR_MONITOR_OFF` cases here should
become one table-driven test parametrized over the switch's env-var name
rather than a third copy-pasted test function; that refactor is not
needed yet at two cases and is out of scope for this proposal.

## How you'll know it worked

- `python3 on-the-record/monitors/test_poll_heartbeat.py` — all tests
  pass, including the two new kill-switch cases.
