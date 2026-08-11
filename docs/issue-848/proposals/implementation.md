---
status: approved
files:
  - docs/issue-848/reports/implementation/survey.md
  - docs/issue-848/proposals/implementation.md
  - tests/test_spawn.py
  - docs/specs/platform-capabilities.md
  - docs/issue-848/reports/implementation.md
---

# Proposal — issue #848 step 2 (implementation)

## Request

Implement per the merged #849 diagnosis: ensure the #782/#829 poll
backstop deterministically catches a spawned role session's terminal
event that lands after the arming turn ends, add a regression test
demonstrating this, and document that the ephemeral CLI
`run_in_background` watch is best-effort while the poll backstop is
authoritative.

## Constraints

- No re-litigating #849's verdict: `spawn.py`'s own auto-armed watcher is
  immune to parent-turn death; the actual dying mechanism was the CLI's
  `run_in_background` Bash-tool task in a plain top-level session.
- The survey (`docs/issue-848/reports/implementation/survey.md`) found
  the detection mechanism itself (Monitor tick → `poll_rearm_arm_if_due`
  → `roster_watchdog` → `diagnose_health`'s dead-entry completion branch)
  already exists and already reaches a `COMPLETED` verdict for a
  `session-end` written after its roster entry's process died — no new
  production code path is required to satisfy the issue's acceptance
  criterion.
- Approval already covers this step: the issue-level comment
  `APPROVE issue-848/implementation` is posted by a listed approver
  (single-account mode, contract v3 s19); this proposal and its survey
  are written and committed alongside the phase-2 work in the same
  session per contract v3 s22 (headless/single-shot: no later turn to
  split phase-1-then-wait-then-phase-2 across).

## Rationale

Considered adding a NEW warning to `_spawn_one()`'s task-prefix block
(`spawn.py:4783-4841`) so a plain, un-delegated top-level session also
receives the "`run_in_background` dies with its turn" warning text,
extending the #849 survey's Finding 2 gap directly at its source.
Rejected: the #849 proposal's own "Out of scope" explicitly left that
choice (extend the warning vs. attack the poll backstop's session-death
boundary vs. a new session-scoped primitive) to this step to decide, and
the issue's acceptance criterion is about the event being *captured*
("via a surviving/re-armed watch or the poll backstop"), not about
warning text placement — the survey (Finding 1-2) already shows the poll
backstop's Monitor-tick path independently satisfies that criterion for
a spawned role session with no code change, so extending the warning
would be additional defense-in-depth for a *different* failure mode (an
orchestrator that never uses a Monitor at all) rather than what this
issue asks for. Out of scope below.

## What will be done

1. Add a regression test to `tests/test_spawn.py` (the `Watchdog` test
   class, alongside the existing dead-entry/STALLED/DEADLOCKED cases)
   that: registers a roster entry with a dead pid whose workspace
   `.events.jsonl` contains a matched `session-start` → `session-end`
   pair written *after* the entry's process is already dead (simulating
   "the terminal event lands after the arming turn ends"), invokes
   `spawn.roster_watchdog()`, and asserts the `[poll-report]` line
   reports `COMPLETED` rather than the entry being silently dropped from
   the scan.
2. Add a short section to `docs/specs/platform-capabilities.md`
   (adjacent to the existing "Claude Code plugin Monitors" section)
   stating plainly: the CLI's own `run_in_background` Bash-tool task is
   an ephemeral, best-effort channel that dies with its arming turn
   (citing the mechanism #849 pinned); the #782/#829 poll backstop
   (turn-driven hooks + the Monitor's turn-independent tick reaching
   `roster_watchdog`'s completion branch) is the authoritative capture
   path for a spawned role session's post-turn terminal event.
3. Write `docs/issue-848/reports/implementation.md`, the phase-2 record,
   citing the survey's findings, the test added, and the doc line added.

## Out of scope

- Extending `spawn.py:4841`'s warning text to plain top-level sessions,
  or any other change to how a top-level orchestrator chooses between
  `run_in_background` and a Monitor — a design decision the #849
  proposal explicitly deferred, and not required by this issue's
  acceptance criterion (see Rationale).
- Attacking the poll backstop's documented session-death hard boundary
  (the orchestrating session's own process dying) — out of scope per
  `docs/issue-801/proposals/technical-feasibility.md`'s standing finding,
  re-confirmed by #849.
- Re-running the #776 steady-state harness — that is issue #848 step 3
  (execution-observation role).

## Accumulation

The new test follows the existing `Watchdog` test class's established
pattern (tempdir + roster JSON + `_write_events` helper, already reused
across the neighboring `Watchdog`/`Reconcile` test classes) — it adds one
more case to an existing shared harness, not a new inline
subprocess/gh-call pattern. If this scenario needed N more variants (e.g.
one per `session_end_verdict` outcome), each would still be one method
reusing the same helpers; no new per-variant file or duplicated setup
would accumulate.

## How you'll know it worked

The new regression test in `tests/test_spawn.py` fails without the
scenario existing (a dead-but-registered entry with a post-death
`session-end`) being exercised at all, and passes once run, showing
`spawn.roster_watchdog()` reports `COMPLETED` for it rather than the
event going unreported. `docs/specs/platform-capabilities.md` carries a
line a reader of the Monitor/poll-backstop section can find stating
which of the two channels (ephemeral watch vs. poll backstop) is
authoritative.

## Scout

Skip: this is a verification/regression-test task against an already-
diagnosed defect (#849) with no product-facing design decision open —
the mechanism to verify and the documentation gap to close were both
pinned by the survey, not chosen from a field of external alternatives.

## What did not work

None.
