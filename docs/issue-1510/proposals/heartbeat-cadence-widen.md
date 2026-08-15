---
status: approved
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/directive.sh
  - spawn.py
  - tests/test_heartbeat_cadence.py
  - tests/test_spawn.py
---

Skip condition applies (survey-order-directive): this is issue #1510, and
the spec leaves no design decision open — see
docs/issue-1510/reports/implementation/survey.md for the skip record and
the exact constants read this session.

## Request

Operator decision 2026-08-15: widen the poll-heartbeat default tick from
60s to 120s to halve idle machinery cost, scale the derived staleness
tolerance to keep the same 3-tick margin, and lock the no-concurrency-cap
policy for role-session spawning with a regression test (quota safety is
owned elsewhere, by #1498/#1508, not by throttling parallelism here).

## Constraints

- All three constants (heartbeat cadence, staleness tolerance, GC-assert
  cadence doc constant) change together in one commit — they are one
  decision, not three independent edits.
- The staleness-tolerance test must parse the two defaults from the
  shipped shell files, not hardcode copies, so a future cadence edit that
  forgets to scale the tolerance fails the test.
- Respawn-attempt caps (`RESPAWN_MAX_ATTEMPTS` family) are explicitly out
  of scope — they bound retry loops, not spawn parallelism.

## Rationale

Considered leaving the ratio implicit (just bump 60->120 and 180->360 with
no test) and rejected it: issue #1510 requirement 2 explicitly calls for a
tick-cadence coupling test so a future cadence edit cannot silently break
the 3x tolerance margin again — a bare constant bump with no test would
regress silently exactly the way the issue is trying to prevent.

Considered adding a `docs/specs/*.md` file to carry the no-cap policy
sentence and rejected it in favor of a docstring on the new test class
itself: the issue's own consult-log outcome says "the test is the guard,
the sentence is commentary" — commentary co-located with its guard test is
more discoverable than a separate spec file, and adding a new
`docs/specs/*` file would also force a `docs/specs/reconciled-index.md`
regeneration unrelated to this change's actual scope.

## What will be done

- `on-the-record/monitors/poll-heartbeat.sh:166`: `POLL_HEARTBEAT_SLEEP_SECONDS` default 60 -> 120.
- `on-the-record/hooks/directive.sh:180`: `MONITOR_LIVENESS_STALE_SECONDS` default 180 -> 360.
- `spawn.py:5661`: `MONITOR_ALIVE_TOUCH_CADENCE_SECONDS` 60 -> 120 (existing GC assert re-verified against the new value).
- New `tests/test_heartbeat_cadence.py::TestHeartbeatCadenceDefaults::test_defaults_scaled_together` parsing both defaults from the shipped files.
- New `tests/test_spawn.py::NoConcurrencyCap` with `test_no_concurrency_cap` (N=50 stub `spawn_cmd()` calls admitted) and `test_zero_running_sessions_spawns_normally`.

## Out of scope

- `RESPAWN_MAX_ATTEMPTS` / respawn-retry caps.
- Any change to `MONITOR_ALIVE_STALE_THRESHOLD_SECONDS` (7-day GC threshold) — it stays safely above the new 120s cadence with no edit needed.
- #1497 liveness-stamp format and #1508 ordering guarantees — unaffected per issue text.

## Accumulation

This touches three constants across three files that must move together,
but it is not an accumulation-shaped change: there is exactly one such
cadence/tolerance-ratio pair in the codebase (heartbeat tick vs. liveness
staleness), and this proposal adds a test
(`test_defaults_scaled_together`) specifically so a future cadence edit is
caught, not repeated as another manual three-file edit. A future cadence
change edits the same three lines and re-runs the same test; it does not
add a fourth file to this list.

## How you'll know it worked

`python3 -m pytest tests/test_heartbeat_cadence.py tests/test_spawn.py::NoConcurrencyCap -v` passes, and `python3 -c "import spawn; assert spawn.MONITOR_ALIVE_STALE_THRESHOLD_SECONDS > spawn.MONITOR_ALIVE_TOUCH_CADENCE_SECONDS"` exits 0.
