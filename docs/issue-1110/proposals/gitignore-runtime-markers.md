---
status: proposed
files:
  - .gitignore
---

scout-skip: pure bugfix — no design decision open.

## Request

Runtime marker files hooks write into the target repo root
(`.orchestrate-greeted`, `.pull-check`, `.orchestrate-monitor-alive/`) are not
gitignored, so any workspace where the plugin ran shows as dirty, which fails
`tests/test_gates.py::t_rulebook_version_is_recorded`. Add them to
`.gitignore`, matching the treatment PR #1109 already gave
`.landing-obligations/`, and audit for any other such markers.

## Constraints

- Empty state (markers never written) must behave as today — a pure
  `.gitignore` addition, no code path changes, satisfies this trivially.
- No scope beyond `.gitignore` — this is not a hook behavior change.

## Rationale

Considered fixing this at the hook level (write markers under a subdirectory
already gitignored, e.g. `.landing-obligations/`) instead of listing each
marker individually. Rejected: that would change each hook's write path and
touch three separate shell scripts for a problem `.gitignore` already solves
for `.landing-obligations/` — more surface changed for the same outcome, and
inconsistent with the precedent PR #1109 already set (gitignore the path, not
relocate the writer).

## What will be done

Add `.orchestrate-greeted`, `.pull-check`, and `.orchestrate-monitor-alive/`
to `.gitignore`.

## Out of scope

Changing where/how hooks write these markers; any other runtime state files
not found by the audit (see docs/issue-1110/reports/implementation/survey.md).

## How you'll know it worked

`python3 -m pytest tests/test_gates.py::t_rulebook_version_is_recorded -q`
passes on a checkout where `.orchestrate-greeted` and `.pull-check` exist
(simulating hooks having run).
