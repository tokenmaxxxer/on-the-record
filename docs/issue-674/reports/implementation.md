---
code_under_review:
  - gates/flows.py
  - test_flows.py
  - test_spawn.py
  - docs/specs/flows-schema.md
type: fix
breaking: false
verdict: pending
loop_state: coding
---

# Implementation record — issue-674

## Upstream

Basis: docs/issue-674/proposals/2026-08-11-flows-json-closure-sweep-not-run.md
(approved via issue comment `APPROVE issue-674/implementation`), built on
the phase-1 survey docs/issue-674/reports/implementation/survey.md, both
merged to main in PR #717.

## What was done (in progress)

Implementing the proposal's "What will be done" section: stop
`flows_payload` from calling `closure_sweep.find_violations()`, replace
`hygiene.closure_sweep` with a literal empty list, and build
`hygiene.closure_sweep_skips` locally as one `not-run-in-flows` record
per board subject. Updating the two test files and the schema doc to
match. This section will be filled in with the completed summary before
landing.

## Why

repo-status-board has been timing out against this repo's `flows --json`
output since 2026-08-08 because `find_violations()` falls back to a slow
per-branch path; the approved proposal keeps the `hygiene.closure_sweep`
field (avoiding a breaking schema bump repo-status-board's
`SUPPORTED_SCHEMA_VERSION = 1` would reject) while removing the call
that causes the timeout.

## What did not work

None yet.

## Rationale for deviations

None — implementation follows the approved proposal's "What will be
done" section.

## Open findings

None yet.

## Next steps

Land the code/test/doc edits, run the test suite, take the timed live
run, check `rsb --json` availability for acceptance item 3, then commit
and open the PR.

## Resolution path

N/A — no blocking finding is open against this record yet.
