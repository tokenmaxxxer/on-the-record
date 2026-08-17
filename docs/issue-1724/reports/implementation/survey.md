# Current-state survey — issue #1724

## Scouting

Skipped: pure mirror of an existing convention, no design decision left
open. The issue names the exact env var (`OTR_MONITOR_OFF`), the exact
placement ("before its first sleep"), and the exact case-list
("same case-list as ORCHESTRATE_OFF"); it also self-labels
`validity-consult-skip: trivial` and `design-research-skip: mechanical`.
This is an internal operator kill-switch mirroring a pattern
(`case "${VAR:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac`) already
used five times in this repo — no product-category or
external-comparison surface to scout.

## Write set

- `on-the-record/monitors/poll-heartbeat.sh` — new kill-switch check
  near the top, before any state is touched.
- `on-the-record/monitors/monitors.json` — the `description` field.
- `README.md` — a new monitor section naming both operator knobs.
- `on-the-record/monitors/test_poll_heartbeat.py` — a new test asserting
  the kill switch's exit-before-first-sleep/no-stdout/no-runs-write
  contract.

## What exists today

canonical: on-the-record/monitors/poll-heartbeat.sh:33-44 (read directly)
The existing kill switch is a single line, placed before `SCRIPT_DIR` is
even resolved:
```
case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
```
Any value outside that five-item empty-state list exits 0 immediately —
before sourcing `poll-rearm.sh`, resolving `CHECKOUT`, writing the
workspace-keyed alive marker (lines 101-110), running
`spawn.py gc-monitor-alive` (line 117), or entering the tick `while`
loop and its first `sleep` (lines 181-182). This same case-list literal
(`""|0|false|no|off`) recurs identically in four other hooks —
`on-the-record/hooks/spawn-allow-gate.sh:41`,
`issue-retrospective-spawn-check.sh:24`,
`requirement-digest-preflight.sh:24`, and
`role-spec-reference-guard.sh:25` — confirming it is the repo's fixed
convention for an env-var kill switch, not something invented per file.

canonical: on-the-record/monitors/poll-heartbeat.sh:155-163 (read directly)
The only `runs/` state file this script's early-loop path can touch is
`${CHECKOUT}/runs/poll_heartbeat_alive.json`, written by
`_alive_stamp_write` — called for the first time inside the `while` loop
at line 183, i.e. strictly after the first `sleep`. Placing a new
kill-switch check anywhere before line 181 therefore already satisfies
"touches no runs/ state file" for free; the acceptance text's "before
its first sleep" and "touches no runs/ state file" describe the same
cut point, not two separate constraints to satisfy independently.

canonical: on-the-record/monitors/monitors.json:1-8 (read directly)
The single `description` field currently names one knob only:
`"120s poll-due/watchdog heartbeat (env-overridable via
POLL_HEARTBEAT_SLEEP_SECONDS; issue #829 poll_rearm_arm_if_due
machinery, reused)"` — no kill switch is named here at all.

canonical: README.md:1-303 (read directly, full file, and confirmed via
`grep -in "monitor\|poll" README.md` returning no match) — no monitor
section, and no mention of `poll-heartbeat`, `POLL_HEARTBEAT_SLEEP_SECONDS`,
or `ORCHESTRATE_OFF`, exists anywhere in this file. The closest existing
documentation of the Monitor mechanism is
`docs/handbooks/monitor-liveness.md`, which documents `ORCHESTRATE_OFF`
at line 57 but is not linked from README.md's "Learn more" list
(lines 295-303) and is not "the README" the issue names.

## What already tests this file

canonical: on-the-record/monitors/test_poll_heartbeat.py:214-227 (read
directly) `t_heartbeat_respects_kill_switch` is the existing
`ORCHESTRATE_OFF=1` test and is the direct template for the new
`OTR_MONITOR_OFF=1` case: it asserts `returncode == 0` and that the fake
`spawn.py`'s watchdog marker was never written (i.e. the tick loop never
ran). No existing test asserts on stdout being empty for a kill-switch
run or on the `runs/` directory being untouched — both need adding for
this issue's stronger acceptance wording ("writes nothing to stdout, and
touches no runs/ state file").

## Unknowns

None — the issue's acceptance text and case-list convention leave no
open design point; see proposal Rationale for the one placement choice
made explicit (where exactly to insert the new check) and why it is not
really a choice given the "before first sleep" / "no runs/ write"
constraints coincide at the same line, per "What exists today" above.
