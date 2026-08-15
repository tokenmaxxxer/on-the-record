---
status: proposed
files:
  - docs/issue-1491/proposals/2026-08-15-standing-red-zero-policy.md
  - docs/issue-1491/reports/implementation/survey.md
---

# Standing-red zero policy — phase-1 design (#1491)

## Request

Design (not yet build) a watchdog-integrated, observe-only check that
runs the fast test tier on main on a bounded cadence, diffs the failing
test set against a recorded baseline, and produces a signal for a new
defect issue whenever a test goes standing-red — so that reds like the
#441/#1477/#1486 instances are caught by the watchdog instead of by
accident during unrelated PR verification.

## Constraints

- Watchdog checks are observe-only/advisory: this check must never
  block, gate, auto-fix, or spawn — watch-coverage staying inviolable is
  a binding constraint of every existing watchdog check (spawn.py's
  `watchdog_check_one`/`roster_watchdog`), and #1491 does not get an
  exception.
- Must include an observation-loss regression guard: adding this check
  must not reduce roster_watchdog's existing per-session anomaly
  coverage, and the new check's own "is it actually watching" state
  must be independently assertable by a test, not just implied by the
  absence of errors.
- Must reuse #1490/#1518 tiering artifacts (`gates/test_tier_contract.py`,
  `.on-the-record/test-tiers.json`) rather than re-implement tier
  selection or budget logic.
- Ordering: implementation (phase-2) is blocked on #1490 having landed,
  per the issue's own requirement 5 — the fast tier has to be affordable
  on a cadence before a recurring check is worth running. #1490 has
  landed (`docs/issue-1490/reports/implementation.md` exists with
  `execution-observation.md`/`parallel-test-suite.md` proposals), so
  #1491 phase-2 is unblocked once this design is approved.
- Flake handling: a failure reports only after two consecutive failures
  on the same tree (req 3); no hardcoded flake list.
- Duplicate suppression: a red already reported (state carries the
  issue reference) re-arms only when the tree hash changes (req 4).
- This PR is phase-1 only: a design record, no `spawn.py`/`gates/`/`tests/`
  changes.

## Rationale

Chosen approach: a new function pair, `standing_red_check()` +
`standing_red_state_load/save()`, added to `spawn.py` next to
`watchdog_check_one`/`WATCHDOG_STATE`, invoked from `roster_watchdog()`'s
existing tick loop on its own cadence gate (a `last_run` timestamp in
its state file, not a new cron/timer mechanism).

Alternative considered and rejected: a standalone script (e.g.
`checks/standing_red_watch.py`) invoked by a separate cron/systemd timer
outside `roster_watchdog()`. Rejected because it would duplicate the
observe-only contract, the state-file JSON conventions, and the signal-line
output format that already exist in `spawn.py`, and because it would
create a second, differently-triggered watchdog cadence outside the one
place (`roster_watchdog`) that currently owns "when do watchdog checks
run" — splitting that authority is exactly the kind of drift the issue's
own root-cause analysis (script/policy changes landing without their
tests being updated) warns against: two watchdog entry points are two
places to forget to update together. `spawn.py`'s size (6000+ lines) is
a real cost of the chosen approach, but it is outweighed by keeping one
authority for "watchdog cadence" and reusing the existing
`WATCHDOG_STATE` file/constants pattern verbatim.

A second alternative — running the standing-red check as a git pre-push
or CI gate instead of a watchdog tick — was rejected outright because it
would violate the binding observe-only/advisory constraint: this issue
is explicitly building an *advisory* check (watchdog philosophy: report,
never auto-fix or block), not a merge gate.

## What will be done (phase-2 scope, not built in this PR)

- Add `standing_red_check(state, now=None)` to `spawn.py`: loads the
  local `.on-the-record/test-tiers.json` contract via
  `gates.test_tier_contract.load_contract()`, runs the fast-tier command
  when the bounded cadence has elapsed since the recorded `last_run`,
  parses the failing test IDs from its output, and diffs them against
  `state["standing_red"]` (a dict keyed by test_id, each entry carrying
  `tree_hash`, `consecutive_count`, and `reported_issue` once filed).
- Cadence and consecutive-failure bookkeeping mirror
  `WATCHDOG_SILENCE_MIN`-style named constants: a
  `STANDING_RED_CADENCE_MIN` constant for the bounded interval, and the
  two-consecutive-failure rule (req 3) implemented as: a test_id's
  `consecutive_count` increments only when both the current run's tree
  hash and the failure match the prior run's; a tree-hash change resets
  the counter and clears `reported_issue` (req 4's re-arm).
- `roster_watchdog()` calls `standing_red_check()` once per tick
  (respecting its own cadence gate so it does not run the suite every
  tick) and appends any newly-reportable test IDs as a signal line in
  its existing print-only output format — never as an issue-creation
  call. Filing the defect issue (citing the failing test, the landed
  change that stranded it, current-contract grounding — req 2's shape)
  stays the orchestrator's job reading that signal line, matching how
  every other watchdog anomaly is currently handled.
- New `tests/test_standing_red_watch.py` with the four acceptance tests
  the issue names: `test_new_red_reported_once`,
  `test_flake_needs_two_consecutive`, `test_observe_only`,
  `test_rearm_on_tree_change` — plus one observation-loss regression
  test asserting `roster_watchdog()`'s existing per-session anomaly
  signals are unchanged by the new check's presence (the binding
  constraint from this proposal's Constraints section, made concrete as
  a runnable check rather than left as an unverified claim).
- State persists in a new `runs/standing_red_state.json` (same
  directory convention as `WATCHDOG_STATE`), not inside the existing
  session-roster state file, so a standing-red-check bug cannot corrupt
  session-liveness state and vice versa.

## Out of scope

- Any actual code change to `spawn.py`, `gates/`, or `tests/` — this PR
  is the phase-1 design only.
- Auto-fixing, auto-closing, or blocking anything on a standing red —
  forbidden by the observe-only constraint.
- Changing #1490's tiering logic or #1518's contract schema — this
  design only consumes `gates/test_tier_contract.py`, it does not modify
  it.
- Slow-tier standing-red watch (only the fast tier, per the issue's own
  requirement 1); a slow-tier variant is a follow-up if ever needed.
- Deciding the exact `STANDING_RED_CADENCE_MIN` value — that is a
  phase-2 implementation detail to tune against the fast tier's actual
  measured budget_seconds, not a phase-1 design commitment.

## How you'll know it worked

This PR: reviewable design record only — approval is the human
reviewer merging it, per role-handoff contract v3 s19's two-phase gate;
no test run applies to a docs-only phase-1 PR.

Phase-2 (future, once approved): the four acceptance tests named in the
issue plus the added observation-loss regression test all pass; a
synthetic run demonstrates a first-run empty-state baseline reporting
all current reds once (the issue's stated "empty state" acceptance
criterion), and a second run with an unchanged tree does not re-report
them.
