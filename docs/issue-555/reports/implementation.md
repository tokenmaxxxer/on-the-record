---
code_under_review:
  - gates/acceptance_gate.py
  - gates/test_acceptance_gate.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue-555

## What was done

The `check_issue_body` function in `gates/acceptance_gate.py` used to
`return` immediately on the first violation it found (missing artifact
reference), skipping the empty-state/provenance checks that came after
it. Restructured so the artifact-reference check appends to the same
`bad` list the empty-state/provenance checks already used, and the
function returns `bad` once at the end — collecting every applicable
violation into one refusal. The "no `## Acceptance` heading at all"
branch is unchanged (still fail-fast; there's no section left to check
further rules against). Added `t_all_three_violations_reported_together`
to `gates/test_acceptance_gate.py`, asserting a body missing executable
`check:` forms, `empty state:`, and `provenance:` simultaneously
produces one `check_issue_body` call returning all three violations,
each naming its expected format.

## Why

basis: docs/issue-555/proposals/2026-08-09-acceptance-gate-collect-all-violations.md

Issue #555: repeated spawn-time refusals surfaced one new Acceptance
format requirement per round-trip, costing an orchestrator turn and an
issue-body edit each time. The fix reuses the accumulation pattern the
function already applied to the empty-state/provenance pair, extending
it to the artifact-reference branch that previously short-circuited.

## What did not work

None.

## Doc placement

- No new env var, dependency, migration, or setup step — no handbook
  update needed.
- No library/format choice over a named alternative beyond what's
  already recorded in the proposal's `## Rationale`; no separate
  decision doc needed.
- No benchmark/investigation numbers produced beyond this record and
  the survey.

## Hunt

Docs-only fast path does not apply (code changed). Given headless
single-shot constraints (contract v3 s22: no delegated work may cross a
turn boundary unconsumed), the before-landing hunt was done inline
instead of dispatched as a background agent: stance index checked
against `git diff --stat` (2 files, small diff) — reviewed the diff for
the "guard goes silent on malformed input" and "rule as written cannot
hold" classes. No finding: the restructure only changes control flow
(early-return -> append-then-return-once); it does not change any
regex, add any new input path, or touch the unverifiable/section-presence
short-circuits that other tests already cover.

## Open findings

None.
