---
status: proposed
files:
  - docs/issue-848/reports/defect-verification.md
---

# Proposal — issue #848 defect-verification, step 1

## Intent

Reproduce and pin the exact lifecycle bug behind the #845 §step-6 finding
(the observing session's own background `watch --follow` task died with
its parent turn before it could report a post-turn event), determine
whether it lives in `spawn.py`'s own watch/watchdog machinery, and
determine whether the #782/#829 poll backstop deterministically catches
the post-turn event. No fix — that is issue #848 step 2 (implementation),
gated on this record.

## Constraints

- Cite the #845 merged execution-observation record (PR #845,
  `docs/issue-776/reports/execution-observation.md`) as canonical
  evidence for the transcript-side facts; do not re-litigate its FAIL
  verdict.
- Actually reproduce the OS-level lifecycle claim (does a watcher armed
  the way `spawn.py`'s own auto-arm does survive its forking process's
  exit?) rather than asserting it from reading code alone.
- No fix, no test additions — those belong to step 2.

## What will be done

Write `docs/issue-848/reports/defect-verification/current-state.md`
(already committed alongside this proposal, phase-1 survey home) pinning:

1. `spawn.py`'s own watch/watchdog machinery (`_spawn_one()`'s
   `fork()+setsid()+Popen(start_new_session=True)` auto-arm,
   `spawn.py:4914-4942`, issue #488) is, by a live reproduction of the
   same process shape, immune to the parent-turn-death failure — it is
   not the mechanism behind #845's finding.
2. The mechanism that actually died in #845 is the Claude Code CLI's
   `run_in_background` Bash-tool task, armed by a plain (`CLAUDE_ROLE`
   unset) top-level session — a session type that never receives
   `spawn.py:4841`'s existing "`run_in_background` 로 넘긴 작업은 부모
   턴이 끝나는 순간 함께 죽는다" warning, because that warning is
   injected only into role-spawned sessions' task text
   (`spawn.py:4783-4841`, gated on `issue is not None`).
3. The #782/#829 poll backstop (`on-the-record/hooks/directive.sh`,
   `on-the-record/hooks/stop-poll-rearm.sh`, the #835/#841
   `on-the-record/monitors/poll-heartbeat.sh` Monitor) is documented, in
   its own source comments and in `docs/specs/platform-capabilities.md`,
   as turn-driven / session-bound — it narrows the turn-boundary quiet
   gap but does not, and by its own documented design cannot, cover a
   dead orchestrating session, which is exactly what #845 hit. This
   matches the standing hard boundary already recorded in
   `docs/issue-801/proposals/technical-feasibility.md`.

On phase-2 approval, `docs/issue-848/reports/defect-verification.md` (the
role's own contract-mandated record — findings, severity, loop_state) is
written per `verify:finding-record` / `verify:severity-classification`,
restating this survey's confirmed mechanism as a formal finding addressed
to `implementation`, with severity assigned by the deterministic band
lookup.

## Out of scope

- Any change to `spawn.py`, the poll-rearm hooks, or the Monitor (step 2,
  implementation role).
- Re-running the #776 harness (step 3, execution-observation role).
- Designing the actual fix (whether the `spawn.py:4841`-style warning
  should extend to plain top-level sessions, whether the CLI should offer
  a session-scoped—not task-scoped—background primitive, or whether the
  poll backstop's session-death boundary should be attacked directly) —
  a design decision out of this role's scope, for step 2 to decide.

## How you'll know it worked

`docs/issue-848/reports/defect-verification/current-state.md` pins one
confirmed mechanism (file:line, plus a live process-lifecycle
reproduction distinguishing it from `spawn.py`'s own immune watcher) and
answers the issue's explicit question about the #782/#829 poll backstop
with a citation to that backstop's own documented hard boundary, not
assumption.

## Scout

Skip: investigative reproduction/diagnosis task with no product-facing
design decision open — the issue asks for the lifecycle bug to be pinned
and the poll backstop's coverage determined, not for a design direction
to be chosen; there is no external field to scout.

## What did not work

None.
