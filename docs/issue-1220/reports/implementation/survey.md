# Current-state survey — issue #1220

Scout skip: issue text carries `validity-consult-skip: trivial — presentation-layer
change with an explicit observation-regression guard; no open design decision.`
This is a pure internal-tooling presentation change with no product-facing
surface, no external exemplar category to scout against — the scout-directive's
skip condition ("spec leaves no design decision open") applies. No scout brief
written.

## Write surfaces

- `on-the-record/monitors/poll-heartbeat.sh` (canonical: on-the-record/monitors/poll-heartbeat.sh) —
  the 60s Monitor loop. Currently:
  - the `poll_due()` non-zero branch (TTL not yet elapsed) unconditionally
    `echo`s `"poll tick: skipped (within TTL)"` every tick.
  - the due branch (issue #1117) does *whole-text* SHA-256 hash
    suppression: it hashes the captured `spawn.py watchdog --auto-respawn`
    stdout+rc-derived text and only prints if the hash differs from
    `runs/poll_heartbeat_last_hash`. This is coarse — a single-byte diff
    anywhere in the multi-session report re-emits the full dump, not a
    delta. There is no periodic bounded heartbeat.
- `spawn.py:roster_watchdog()` (canonical: spawn.py:2644-2769) — the
  underlying scan that produces the report text. Per session per tick it
  unconditionally prints `[poll-report] {key}: {state} — {detail}` (line
  2751) and `[watchdog] {key}: 정상` or an anomaly list (lines 2757-2765),
  regardless of whether the state changed since the previous tick. Dedup
  via `ledger_check_and_stamp()` only gates the escalation side-effect
  (`[health]`/`[watchdog] 이상 신호` lines), not the always-printed
  `[poll-report]`/`정상` lines.
  - Crash/dead-entry path (canonical: spawn.py:2706-2741) prints a
    `[poll-report]` line carrying the dead-session label (session-end
    verdict or STALLED), and a `[resume]` line when a PR is ready.
- `gates/test_poll_heartbeat_delta.py` (canonical: gates/test_poll_heartbeat_delta.py) —
  existing hermetic test harness (issue #1117) for the shell-level
  hash-suppression tests: fake `spawn.py` writing canned
  `FAKE_WATCHDOG_REPORT` text, run via `POLL_HEARTBEAT_MAX_TICKS=1` per
  invocation, hash state carried in `runs/poll_heartbeat_last_hash` inside
  a tmp checkout. New tests for #1220 fit the same harness.
- `on-the-record/monitors/test_poll_heartbeat.py` (canonical: on-the-record/monitors/test_poll_heartbeat.py) —
  base heartbeat test (pre-#1117), covers the loop's tick-bounding/sleep-override
  mechanics that any new test must not break.

## Gaps this proposal must close

1. Whole-text hash (current #1117 mechanism) cannot express "emit only the
   delta" — it is binary (identical / not identical) over the whole
   report, not per-session or per-drift-item. #1220 wants entry-level
   diffing: "a snapshot with a new drift item emits exactly the delta."
2. No periodic bounded heartbeat exists — once the hash stabilizes, output
   goes silent forever with no aliveness signal. #1220 req #3 allows (does
   not require) a ~30min "monitoring active, N sessions healthy" line.
3. `"poll tick: skipped (within TTL)"` is unconditional on every non-due
   tick. #1220 req #1 says this line must never print.
4. Regression guard: req #2 requires a test asserting a crashed-session
   tick always emits even under delta suppression — distinct from the
   existing #1117 identical-text-suppressed test.
