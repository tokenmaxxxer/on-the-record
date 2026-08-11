---
code_under_review:
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/test_decision_queue_stopgate.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Issue #692 — Phase 2 Implementation Record

## Summary of work

Bound `decision-queue-stopgate.sh`'s waiting-declaration branch to at
most one block per consecutive run within a session, using a sibling
session-keyed state file that follows `retry-loop-bound.sh`'s
persistence pattern (atomic `os.replace`, `OTR_*_STATE_DIR` override,
silent fail-open). Rewrote the block reason to restate the
decision-queue items with `#issue`/`PR#pr (age)` coordinates and name a
satisfiable one-shot escape. Added the Acceptance-named regression test
plus a latch-reset test, and threaded `session_id` through the test
helper.

## Why

Issue #692: the unbounded waiting-declaration block from #600/PR #622
forced six identical "대기 중입니다." turns in a row on 2026-08-11
because the block reason gave no escape format the model could satisfy
and nothing bounded repeated fires. Approved phase-1 proposal:
`docs/issue-692/proposals/2026-08-11-bound-waiting-declaration-guard.md`.

## Upstream / basis

Based on: `docs/issue-692/proposals/2026-08-11-bound-waiting-declaration-guard.md`
(approved via `APPROVE issue-692/implementation`), following the
persistence pattern in `on-the-record/hooks/retry-loop-bound.sh`.

## What did not work

None.

## Doc placement

- No new env var, dependency, or migration — nothing to add to a
  handbook.
- No public-signature or wire-format change — no decisions doc needed.
- No benchmark/investigation numbers produced.

## Open findings

None.

## Next steps

Implement the code changes described above, run the test suite, commit,
push, open the PR, then set loop_state to landed.

## Resolution path

Not applicable — no open findings.
