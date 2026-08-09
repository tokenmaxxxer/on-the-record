---
status: proposed
files:
  - gates/acceptance_gate.py
  - gates/test_acceptance_gate.py
  - docs/issue-555/reports/implementation/survey.md
---

## Request

Make the spawn-time Acceptance gate (`gates/acceptance_gate.py`) report
every format violation in one refusal instead of failing fast on the
first, so a round-trip fixes all violations at once instead of one per
attempt. Skip condition (scout directive): pure bugfix — the fix is
fully determined by the issue's Acceptance checks, no design decision
open.

## Constraints

- Behavior for a compliant Acceptance section must be unchanged (empty
  list returned).
- The "no `## Acceptance` heading at all" case cannot be combined with
  other checks — there is no section to check further rules against —
  and stays a fail-fast single-message return.
- The `unverifiable:` escape hatch must still exempt artifact-ref,
  empty-state, and provenance checks entirely, unchanged.

## Rationale

Two ways to collect all violations were considered:

- **Restructure `check_issue_body` to append to one `bad` list across
  all applicable branches, returning it once at the end (chosen).** The
  function already does this for the empty-state/provenance pair; the
  fix only extends the same pattern to the artifact-ref branch, which
  currently returns early instead of appending.
- **Run all sub-checks independently as isolated functions returning
  their own violation-or-None, then concatenate.** Rejected: this
  reshapes the function into a new dispatch structure for the same
  outcome the direct fix already reaches, and would touch every branch
  (including the section-presence and unverifiable checks) versus only
  the one that currently short-circuits — larger diff for no behavior
  difference.

## What will be done

In `check_issue_body`, change the "Acceptance 절이 프로즈뿐이다" branch
from `return [...]` to appending its message to `bad` and continuing
into the empty-state/provenance checks (currently skipped whenever the
artifact-ref check fails), then return `bad` once at the end covering
all three violation classes. Add a test asserting that a body lacking
executable `check:` forms, the `empty state:` line, and the
`provenance:` line simultaneously produces a single `check_issue_body`
call whose returned list names all three, each naming its expected
format.

## Accumulation

This is a one-time restructure of one function's control flow, not an
append to a repeated list or an inline call-count that grows per
invocation — there is nothing here that scales with N future changes.

## Out of scope

- The `section is None` (missing `## Acceptance` heading) case — stays
  a single-message fail-fast return per Constraints.
- Any change to what counts as a valid artifact reference, empty-state
  line, or provenance value.

## How you'll know it worked

`python3 gates/test_acceptance_gate.py` passes, including the new test
asserting all three violations appear in one refusal (issue Acceptance
check 1/2), and the existing compliant-issue test
(`t_artifact_reference_passes` et al.) still passes unchanged (issue
Acceptance check 3).
