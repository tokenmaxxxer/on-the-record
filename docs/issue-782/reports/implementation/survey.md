# Current-state survey — issue #782 step 2 (implementation)

Skip condition applies: the spec leaves no design decision open. Step 1
(`docs/specs/dual-channel-observation.md`, merged via PR #788) already
fully resolved every design decision — polling ground-truth set, cadence
+ trigger mechanism, ledger keying, divergence→action table, and the
event-hardening signal. Step 2 is a build against that closed design, not
a design task — scouting/current-state-survey-as-design-input is
skipped per the scout-directive's own skip condition; this file exists
only to name that and to record the concrete write surfaces the build
touches.

## Write surfaces (from reading `spawn.py`, `directive.sh`, existing tests)

- `spawn.py`: `runs/reconcile_ledger.json` primitives (load/save/lock/
  check-and-stamp), dedup-key builders, a new `watcher-silent` signal in
  `watchdog_check_one()`, a completion-detection lane wired into
  `roster_watchdog()` (reuses `_build_observed()`'s existing
  `pr_number`/`session_verdict` reads — no new `gh`/git call types),
  ledger-gating around the existing `reconcile()` divergence print/act
  path, ledger stamps at the two existing event-emission sites
  (`_append_event(..., "pr-opened", ...)` at the PR-detection point in
  `_spawn_one`, and `_append_event(..., "session-end", ...)`), and a new
  `poll-due` CLI subcommand (checks + stamps `runs/poll_state.json`
  atomically, exit code signals staleness) — the mechanism
  `directive.sh` needs to decide whether to fire a poll tick this turn.
- `on-the-record/hooks/directive.sh`: wires the `poll-due` check before
  the directive text, backgrounding `spawn.py watchdog --auto-respawn`
  when due (TURN-BUDGET RULES #535 — this call already exceeds the ~30s
  foreground bar).
- `tests/test_spawn.py`: unit tests for the ledger primitives, the
  completion lane's three dedup scenarios (Acceptance tests 1-3), the
  empty-state assertion, and the new watcher-silent signal.

No new dependency, no new environment variable, no schema/migration —
existing ground-truth readers are reused as-is (spec §1's explicit
constraint).
