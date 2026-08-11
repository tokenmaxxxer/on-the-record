---
status: proposed
files:
  - docs/issue-782/reports/implementation/survey.md
  - docs/issue-782/proposals/2026-08-11-dual-channel-observation-step2.md
  - docs/issue-782/reports/implementation.md
  - spawn.py
  - on-the-record/hooks/directive.sh
  - tests/test_spawn.py
---

# Dual-channel observation — build (issue #782, step 2)

## Request

Build the dual-channel observation design approved and merged in step 1
(`docs/specs/dual-channel-observation.md`, PR #788): a polling channel
that reconciles both the deliverable axis (open/merged PRs) and the
liveness axis (session liveness) on a bounded, hook-driven cadence
regardless of whether any watch event fired; an event channel hardened
against the 2026-08-11 stall failure mode; both merged into one
next-action stream through an idempotent, TTL'd ledger keyed on
issue/role/PR so neither channel double-acts; installed by default via
the plugin's hook surface (no CI, no explicit invocation).

## Constraints

- Reuse `spawn.py`'s existing ground-truth readers
  (`_pr_open_or_merged_for_branch`, `roster_ps`'s liveness join,
  `board()`) — no new `gh`/git call types.
- Reuse `reconcile()`'s existing closed next-action vocabulary for
  health repair unchanged; the only new lane is completion-detection,
  which reports, never repairs.
- Ledger TTL matches the poll cadence (15 min, per the merged spec's
  rationale against `WATCHDOG_SILENCE_MIN`/`WATCHDOG_NO_COMMIT_MIN`).
- Cadence trigger is `directive.sh`'s `UserPromptSubmit` hook (req #7:
  no CI, no explicit skill invocation, reaches every installed session).
- No new dependency, env var, schema, or migration.

## Rationale

Considered wiring the poll cadence as a standalone loop inside
`roster_watchdog()` itself (spawn.py deciding on its own when to re-run)
instead of a hook-driven `poll-due` check in `directive.sh`. Rejected:
`spawn.py` is a one-shot CLI with no persistent process of its own
between orchestrator turns — a self-scheduling loop inside it would
either block the invoking turn (violating TURN-BUDGET RULES #535) or
require a background daemon, which step 1's spec explicitly deferred as
a follow-up (a per-repo long-lived process is materially more surface
than this step asks for). A hook-driven staleness check that the
orchestrator's own turn cadence trips is the only mechanism that reaches
every installed session by construction without adding a process.

## What will be done

1. `spawn.py`: `runs/reconcile_ledger.json` primitives (locked load/
   save/check-and-stamp, TTL 15 min), dedup-key builders for the
   completion lane (`(issue, role, pr_number)` or `(issue, role,
   spawn_attempt_id, "session-end")`) and the health-repair lane
   (`(issue, role, next_action.kind)`).
2. `watchdog_check_one()`: new `watcher-silent` signal — watcher pid
   alive and `_watcher_looks_real()` passes, but the watcher's own log
   (`<work>.watcher.log`, already written by `watch --follow`, path
   derived, no new field) has no mtime advance past `watcher_armed_at`
   beyond `WATCHDOG_SILENCE_MIN` — the 2026-08-11 failure mode
   specifically.
3. `roster_watchdog()`: for each roster entry, run a completion-lane
   check (PR found via `_build_observed()`, or `session_verdict ==
   "normal"`) gated through the ledger before printing/reporting; gate
   the existing `reconcile()` divergence print/act path through the
   ledger the same way.
4. `_spawn_one()`: stamp the ledger at the two existing event-emission
   sites (`pr-opened`, `session-end`) so a later poll tick that finds
   the same completion stays silent (Acceptance test 2/3).
5. New `spawn.py poll-due` CLI subcommand: atomically checks/stamps
   `runs/poll_state.json` against a 15-minute interval; exit 0 (due) or
   1 (not due yet).
6. `directive.sh`: before the directive text, run `spawn.py poll-due`;
   if due, background `spawn.py watchdog --auto-respawn`.
7. `tests/test_spawn.py`: ledger fresh/stale, the three Acceptance
   dedup scenarios, the empty-state assertion, and `watcher-silent`.

## Out of scope

- The background poll daemon (step 1's spec names this as a deferred
  follow-up, not this step).
- Any change to `reconcile()`'s existing health-repair next-action
  vocabulary.
- A new anomaly-signal notification surface beyond the existing
  `[watchdog]`/`[reconcile]` print convention.

## How you'll know it worked

`tests/test_spawn.py` passes: a completion with no watch event is
detected by the polling channel and yields exactly one next-action
(test 1); a watch-detected completion is not missed if polling is
delayed (test 2); event+poll on the same completion produce exactly one
next-action (test 3); with nothing in flight, polling emits no spurious
action (empty state). `watchdog_check_one()` flags `watcher-silent` for
a fixture with an armed-but-silent watcher log.

## Accumulation

Not accumulation-cost-shaped: one-time wiring change to existing hook/
CLI call sites; the ledger is bounded by TTL eviction, not unbounded
append. N/A.

## What did not work

None.
