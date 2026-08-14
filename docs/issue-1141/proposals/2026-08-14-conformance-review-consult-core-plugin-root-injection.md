---
status: proposed
files:
  - docs/issue-1141/reports/conformance-review.md
---

## Intent

Issue #1141 is a marketplace conformance-review spawn: PR #1152
(`issue-1141/implementation`) landed on `main` and no conformance
record exists yet for its 3 requirements / 2 acceptance checks. This
phase renders a per-requirement verdict against the implementation
already delivered.

## Constraints

- Verdict scale: Present | Surface | Absent | Incorrect | Unverifiable
  per requirement — never a holistic quality judgment, never a fix.
- Work deliberately without the building agent's stated intent
  (`docs/issue-1141/reports/implementation.md`'s own claims) — verify
  each citation independently against the working tree and command
  output.

## What will be done

Render one verdict per requirement (3) and per acceptance check (2)
in `docs/issue-1141/reports/conformance-review.md`, each backed by a
re-run or re-read citation, and file any open findings this review
surfaces (routed to the owning role, not fixed here).

## Out of scope

Editing spawn.py, gates/test_consult_gate_lib_env.py, or
docs/issue-1141/reports/implementation.md — those belong to the
implementation role.

## How you will know it worked

docs/issue-1141/reports/conformance-review.md exists with a verdict
for each of the 3 requirements and 2 acceptance checks, each citing
reproducible evidence.
