Skip condition: pure bugfix / spec leaves no design decision open (issue
#1465's Requirements + Acceptance sections fully prescribe the shape:
which dir to GC, which threshold-derivation rule to satisfy, which
existing machinery to hook into, and the exact four test names). Scouting
skipped per survey-order-directive's mandatory skip record.

## Write set

- spawn.py — new GC functions + `gc-monitor-alive` CLI role.
- on-the-record/monitors/poll-heartbeat.sh — call the new CLI role
  non-fatally, right after the existing alive-marker touch.
- tests/test_monitor_alive_gc.py — new file, the four Acceptance tests.

## Current state (survey)

canonical: on-the-record/monitors/poll-heartbeat.sh (read directly)
`on-the-record/monitors/poll-heartbeat.sh` writes
`~/.claude/tokenmaxxxer/monitor-alive/<sha256(cwd)[:24]>/alive` via
`touch`, once, before the 60s tick loop starts (not re-touched per
tick). The loop's own cadence constant is `POLL_HEARTBEAT_SLEEP_SECONDS`
(default 60), the only cadence constant this script defines — so it is
what "the actual touch cadence in poll-heartbeat.sh" (issue text)
resolves to.

canonical: derived: `grep -rn monitor-alive --include=*.py --include=*.sh . | grep -v poll-heartbeat.sh | grep -v test_monitor_alive_gc`
No prior GC/cron for this dir exists anywhere else in the repo.

canonical: spawn.py (read directly, `roster_clean`/`auto_sweep`/`roster_watchdog` definitions)
`spawn.py` already has an analogous safe-GC precedent: `roster_clean()`
(`spawn.py clean`) and `auto_sweep()` (spawn-time auto-clean) — both
non-destructive-by-default, wired into existing entry points rather than
a new daemon. `roster_watchdog()` is the existing per-tick report path
that already prints tagged lines (`[reconcile]`, `[orphaned]`,
`[resume]`) captured verbatim by poll-heartbeat.sh's stdout capture —
the natural pattern to reuse for the legacy-dir report line.

No `.env`, no new dependency, no schema/migration touched.

## Decision (mechanical, from the issue text)

- Threshold: 7 days, asserted > 60s cadence (test #2 in Acceptance).
- Hook point: heartbeat startup (poll-heartbeat.sh, right after the
  alive-marker touch) via a new `spawn.py gc-monitor-alive` CLI role —
  this was chosen over `spawn.py clean` because GC needs to run every
  session start (heartbeat startup happens far more often than a human
  runs `spawn.py clean`), and the issue explicitly offers "heartbeat
  startup" as an option.
- Legacy dirs: `detect_legacy_monitor_alive_dirs()` only reports (prints
  `[legacy-monitor-alive] <path>`), never deletes — required by
  Acceptance test #4.
- Non-fatal: every entry point (`gc_monitor_alive`, `monitor_alive_gc_cli`)
  swallows exceptions per-item/at the wrapper level; the shell call site
  is also wrapped in `|| true` and its stdout/stderr are redirected to
  `/dev/null` so a Python traceback can never surface into the tick
  loop's captured report text.
