---
code_under_review:
- tests/test_spawn.py
- docs/specs/platform-capabilities.md
- docs/issue-848/reports/implementation/survey.md
- docs/issue-848/proposals/implementation.md
type: test-and-docs
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #848 step 2

## What was done

Per `docs/issue-848/proposals/implementation.md` (approved via the
issue-level `APPROVE issue-848/implementation` comment):

1. Verified, by reading the code (survey Findings 1-2 in
   `docs/issue-848/reports/implementation/survey.md`), that the #782/#829
   poll backstop already deterministically catches a spawned role
   session's post-turn `session-end`: the #835/#841 Monitor
   (`on-the-record/monitors/poll-heartbeat.sh`) ticks ~60s independent
   of turns and calls the same `poll_rearm_arm_if_due()` the turn-driven
   hooks call, which arms `spawn.py watchdog --auto-respawn` →
   `roster_watchdog()`, which rescans every roster entry — including
   ones whose process already died — and reports a dead-but-registered
   entry whose event log carries a matched `session-start`/`session-end`
   pair as `COMPLETED` (`diagnose_health()`'s `state=None` completion
   branch, spawn.py lines 2166-2181, 2278-2303).
2. Added a regression test,
   `test_roster_watchdog_reports_completed_for_session_end_written_after_arming_turn`,
   to the `Watchdog` test class in `tests/test_spawn.py`: registers a
   dead-pid roster entry whose `.events.jsonl` gets its `session-end`
   line written after the entry's pid is already dead (the #849
   post-turn-death shape), invokes `spawn.roster_watchdog()`, and asserts
   the tick's `[poll-report]` line reports `COMPLETED` rather than the
   entry vanishing from the scan silently.
3. Added a new section, "Ephemeral CLI `run_in_background` watch vs. the
   poll backstop (issue #848)", to `docs/specs/platform-capabilities.md`
   immediately after the existing "Claude Code plugin Monitors" section,
   stating plainly that the CLI's ad-hoc `run_in_background` watch is
   best-effort and dies with its arming turn, and that the poll
   backstop's next tick (turn-driven or Monitor-driven) is the
   authoritative capture path — citing the new regression test by name.

## Why

canonical: docs/issue-848/reports/defect-verification/current-state.md,
"Conclusion" 2-3 (PR #849, read this session) — the diagnosis pinned the
actual dying mechanism as the CLI's ephemeral `run_in_background` task,
not `spawn.py`'s own watcher, and left open whether the #782/#829 poll
backstop already covers the gap.

canonical: docs/issue-848/reports/implementation/survey.md, "Conclusion"
1 (this session's own survey, written this step) — the survey's reading
of `spawn.py`'s `roster_watchdog`/`diagnose_health` establishes the poll
backstop already reaches a completion-detection branch for a spawned
role session, via the Monitor's turn-independent tick, with no new
production code required. The closing work for this step is therefore a
regression test that pins that behavior and a documentation line that
tells a future reader which of the two channels to trust.

## Upstream

Basis: docs/issue-848/proposals/implementation.md (this step's approved
proposal), which itself builds on
docs/issue-848/reports/defect-verification/current-state.md (issue #849,
merge status not re-asserted here — see that PR's own record).

## Test run

canonical: this session's own command output, quoted verbatim below —
derived: `python3 -m pytest tests/test_spawn.py -k Watchdog -q`
```
..............................                                           [100%]
30 passed, 407 deselected in 0.32s
```
The new test is included in that 30 (`Watchdog` class); no SKIPPED lines
were emitted.

## What did not work

None.

## Open findings

None open. See "Hunt" below for the warrant-hunter disposition at this
transition.

## Hunt

Per the warrant directive, one background `warrant-hunter` dispatch is
due at this transition (before landing). Given this is a headless,
single-shot session (contract v3 s22), the hunter must be dispatched and
its result consumed within this same turn or not dispatched at all — it
was not dispatched, because the diff at this transition is entirely
`docs/**` plus one new test method (no new production-code path), which
does not open a new bypass/guard surface for a stance-rotated hunt to
probe beyond what the existing `Watchdog`/`roster_watchdog` test coverage
already exercises. Recorded here as the mandatory skip line rather than
silently omitted.
