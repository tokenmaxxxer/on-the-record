---
code_under_review:
  - spawn.py
  - tests/test_gates.py
loop_state: coding
type: feature
breaking: false
verdict: pending
---

## What was done

Implementing the approved phase-1 proposal
(canonical: docs/issue-1134/proposals/consult-trace-auto-commit.md,
git log shows PR #1153 merged into main): adding `_commit_consult_trace()`
to spawn.py, wiring it into `consult_cmd()`'s `finally` block, and adding
a scratch-clone gate test to tests/test_gates.py.

## Why

northpole req#2 (docs/specs/northpole.md) — a trace only existing as
uncommitted local state is not a record. Full rationale already recorded
in the phase-1 proposal; not restated here.

## Upstream

Based on: docs/issue-1134/proposals/consult-trace-auto-commit.md

## What did not work

None.

## Open findings

None.

## Next steps

Land the implementation, run the two acceptance-criteria checks
(canonical: docs/issue-1134/proposals/consult-trace-auto-commit.md's
Acceptance section), then update loop_state and verdict based on that
run's actual outcome.

## Resolution path

N/A — no open findings.
