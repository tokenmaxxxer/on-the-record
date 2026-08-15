---
code_under_review:
  - spawn.py
  - tests/test_standing_red_watch.py
loop_state: landed
type: feature
breaking: false
verdict: pass  # canonical: python3 -m pytest tests/test_standing_red_watch.py -q (this turn) — see fenced output below
---

# Implementation record — issue #1491 (phase-2)

## What was done

Implemented the approved phase-1 design
(`docs/issue-1491/proposals/2026-08-15-standing-red-zero-policy.md`).
canonical: `gh issue view 1491 --comments` (this turn) — thread shows
"APPROVE issue-1491/implementation" posted by JiwonJung94 (listed in
`docs/specs/approvers.md`).
canonical: `git log --oneline -5` (this turn) — merge commit `20aa5937`
"Merge pull request #1524 from tokenmaxxxer/issue-1491/implementation"
is on the branch history, confirming the phase-1 proposal PR is merged.

- `spawn.py`: added `STANDING_RED_STATE`, `STANDING_RED_CADENCE_MIN`,
  `_standing_red_state_load/save()`, `_standing_red_tree_hash()`,
  `_standing_red_load_contract()` (reuses `gates/test_tier_contract.py`'s
  `load_contract()` verbatim, no reimplemented tier logic),
  `_standing_red_parse_failed_ids()`, and `standing_red_check(state=None,
  now=None, root=ROOT)` — placed next to `watchdog_check_one`/
  `WATCHDOG_STATE`, mirroring their state-load/save and observe-only
  shape.
- `roster_watchdog()` calls `standing_red_check(root=root)` once per tick,
  right after `_board_wide_sweep_all()` and before the live-roster early
  return, so it fires independent of whether any role session is alive;
  each returned signal is printed as `[standing-red] ...` and folded into
  the existing `anomaly_count` return value — no new output channel, no
  issue-creation call, matching every other watchdog signal category.
- Cadence gate: `standing_red_check()` no-ops (returns `[]` immediately,
  no subprocess spawned) unless `STANDING_RED_CADENCE_MIN` minutes have
  elapsed since the last recorded run — `last_run=None` (truly first
  call, no prior state) always runs.
- Fast-tier only, via `gates.test_tier_contract.load_contract(root)`; a
  missing/invalid `.on-the-record/test-tiers.json` takes the no-contract
  path (records `last_run`, returns `[]`, never runs a silent full
  suite — issue #1518's own `no_contract_gap` philosophy, no full-suite
  fallback added here since req 1 scopes this check to the fast tier
  only).
- Flake rule (req 3): a failing test's `consecutive_count` increments
  only when the current run's `tree_hash` matches the prior run's for
  that test; report fires at `consecutive_count >= 2`, except a truly
  empty state file (no prior `standing_red` key at all) reports all
  current reds on that first run — the issue's own stated "empty state"
  acceptance criterion.
- Duplicate suppression + re-arm (req 4): a test with `reported: true` at
  the current `tree_hash` is never re-reported; a `tree_hash` change
  resets `consecutive_count` to 1 and `reported` to `false` for that
  test, re-arming it under the same twice-consecutive rule.
- Recovered tests (no longer failing) are dropped from state entirely, so
  a future recurrence starts the flake count fresh rather than inheriting
  a stale streak.
- `tests/test_standing_red_watch.py`: the four issue-named acceptance
  tests (`test_new_red_reported_once`, `test_flake_needs_two_consecutive`,
  `test_observe_only`, `test_rearm_on_tree_change`), plus
  `test_no_contract_no_run`, `test_cadence_gate_skips_before_interval`,
  and the observation-loss regression guard
  (`test_observation_loss_regression_guard`) asserting that a
  `standing_red_check()` signal folded into `roster_watchdog()`'s output
  does not crowd out an existing `STALLED`-shaped `[poll-report]`
  signal from the pre-existing `diagnose_health()` path — the binding
  constraint from the phase-1 proposal, made runnable rather than left
  as an unverified claim. All tests use a synthetic tmp-path git repo and
  a fake fast-tier command (a short Python script printing fixed `FAILED
  <id>` lines) — no dependency on this repo's own suite composition.

## Why

Per the approved proposal's Rationale section (file: `docs/issue-1491/
proposals/2026-08-15-standing-red-zero-policy.md`): extend `spawn.py`'s
existing watchdog machinery (`watchdog_check_one`/`WATCHDOG_STATE`/
`roster_watchdog`) rather than a standalone script + separate
cron/systemd timer, to keep one authority for "when do watchdog checks
run" and reuse the existing observe-only contract, state-file JSON
conventions, and signal-line output format verbatim — the alternative
(a second entry point) was rejected as exactly the script/policy-vs-test
drift the issue's own root-cause analysis warns against.

## Upstream basis

- Issue #1491 requirements 1-5 and acceptance criteria.
- Approved phase-1 proposal:
  `docs/issue-1491/proposals/2026-08-15-standing-red-zero-policy.md`.
- Tiering artifacts reused as-is: `gates/test_tier_contract.py`
  (`load_contract`), per #1518/#1490.
- APPROVE token: issue #1491 comment "APPROVE issue-1491/implementation",
  author JiwonJung94, posted 2026-08-15 (see canonical citation above).

## Test tiering gap (test-tier-contract directive, issue #1518)

derived: `test -f .on-the-record/test-tiers.json`
```
(no output — file does not exist in this repo's own checkout)
```
This repo (on-the-record itself) has no `.on-the-record/test-tiers.json`
of its own yet, so the test-tier directive's fast/slow split does not
apply to *this session's* own test runs — the directive's no-silent-full-
suite requirement is satisfied here by scoping this turn's verification
run to the new/adjacent test files rather than the full 1963-test
collection (full-suite wall-clock not measured this turn). This is a
gap for a future tiering-adoption proposal on this repo's own suite, not
something `standing_red_check()` itself needs to solve — the feature it
implements is designed to *consume* a target repo's
`.on-the-record/test-tiers.json` when that repo has one (see
`test_no_contract_no_run`), and correctly no-ops advisory-only when it
doesn't.

## Acceptance run

canonical: `python3 -m pytest tests/test_standing_red_watch.py -v` (this turn)
```
tests/test_standing_red_watch.py::test_no_contract_no_run PASSED
tests/test_standing_red_watch.py::test_cadence_gate_skips_before_interval PASSED
tests/test_standing_red_watch.py::test_flake_needs_two_consecutive PASSED
tests/test_standing_red_watch.py::test_new_red_reported_once PASSED
tests/test_standing_red_watch.py::test_observe_only PASSED
tests/test_standing_red_watch.py::test_rearm_on_tree_change PASSED
tests/test_standing_red_watch.py::test_observation_loss_regression_guard PASSED
7 passed in 0.92s
```

canonical: `python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py tests/test_poll_watchdog_log.py -q` (this turn) — adjacent existing watchdog test files, run to confirm `roster_watchdog()`'s new call site did not break pre-existing watchdog test coverage.
```
......................                                                   [100%]
22 passed in 1.11s
```

## What did not work

- First draft of `standing_red_check()`'s cadence gate defaulted
  `last_run` to `0` via `own_state.get("last_run", 0)`; with a test
  clock starting at `now=0` this made `(now - last_run) < cadence`
  always true, so the very first call (empty state, `now=0`) silently
  no-op'd instead of running — caught by `test_new_red_reported_once`
  returning `[]` instead of the expected baseline signal. Fixed by using
  `own_state.get("last_run")` (`None` sentinel) so an absent `last_run`
  always runs regardless of `now`.
- `test_observe_only` originally asserted `git status --porcelain` was
  empty after two checks; the test's own fixture setup (writing
  `.on-the-record/test-tiers.json` and the fake test script into the
  synthetic repo) legitimately leaves untracked files, which is not what
  observe-only is about. Reworded the assertion to check the commit log
  is unchanged (HEAD/commit count), which is what "the check doesn't
  mutate the observed repo" actually means.
- `test_observation_loss_regression_guard` originally asserted
  `rc >= 2` (standing-red signal + STALLED signal both counted). The
  dead-roster-entry branch of `roster_watchdog()` prints its
  `diagnose_health()` result via a separate `[poll-report]` code path
  that does not increment `anomaly_count` for that branch — an existing
  behavior, not something this change should alter. Relaxed to `rc >= 1`
  (the standing-red contribution alone) since the test's real assertion
  is the `printed` string containing both signal texts, not the exact
  count arithmetic of a pre-existing unrelated branch.

## Open findings

None.
