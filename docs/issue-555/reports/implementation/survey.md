# Survey — issue-555

Skip condition: pure bugfix. `check_issue_body()` in
`gates/acceptance_gate.py` already returns a `list[str]` and already
accumulates multiple messages in one branch (the `empty state`/`provenance`
pair). The defect is narrowly that two earlier branches (`section is None`,
prose-only / no artifact ref) each `return` immediately instead of
appending to `bad` and continuing — so when an artifact-ref violation and
an empty-state/provenance violation exist simultaneously, only the first is
ever reported. No new design decision: the fix reuses the existing
accumulation pattern already present in the same function.

Write set: `gates/acceptance_gate.py` (restructure `check_issue_body` to
collect all violations before returning) and `gates/test_acceptance_gate.py`
(new test covering the issue's combined-violations acceptance checks;
existing tests serve as the regression check for the no-behavior-change
acceptance check).

The `section is None` case (no `## Acceptance` heading at all) cannot be
combined with anything else — there is no section to check further rules
against — so it stays a fail-fast single-message return, unchanged.
