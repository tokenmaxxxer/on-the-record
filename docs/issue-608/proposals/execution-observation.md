---
status: proposed
files:
  - docs/issue-608/reports/execution-observation/fixture-measurement.md
  - docs/issue-608/proposals/execution-observation.md
---

## Request

Step 1 of #608: fixture-measure approval-gate efficacy in a plugin-installed
target repo, driving the shipped `on-the-record/hooks/` surface directly
(never this repo's own dev-time `gates` tooling), across `approvers.md`
present/absent and approved/unapproved phase-2 acts, and confirm or refute
the three candidate causes named in the issue body. Findings only — step 2
implements a fix.

## Verdict levels this step checks, and against what evidence

- outcome — not applicable at step 1: no fix is delivered yet, so there is
  nothing to recompute an outcome verdict against. Step 2's PR is where an
  outcome verdict belongs.
- trajectory — not applicable at step 1: this step is itself the first
  action on this issue; there is no prior phase-1-to-phase-2 path on #608 to
  judge yet.
- step — which candidate cause(s) the fixture run confirms or refutes,
  checked against the unmodified `on-the-record/hooks/deliverable-guard.sh`
  script's actual exit codes and stderr when driven with a real JSON
  stdin payload across the matrix, captured as fenced output in
  `docs/issue-608/reports/execution-observation/fixture-measurement.md`.

## Constraints

- Fixture repo only — a disposable `git init` under this session's scratch
  directory, never this repo's own board.
- No edits to `on-the-record/hooks/*`, `gates/*`, or any src/test path — this
  step reads and drives the shipped scripts unmodified; a fix is step 2's
  responsibility, not this role's.
- Docs-only unit: nothing outside `docs/issue-608/` is written.

## Out of scope

- Implementing the missing enforcement (step 2).
- Verifying candidate cause (b) against the tailor repo's actual installed
  plugin version — no access to that repo from this session; recorded as
  not confirmed rather than guessed at.

## How this will be known to have worked

`docs/issue-608/reports/execution-observation/fixture-measurement.md`
contains fenced, reproducible fixture output for all matrix cells, and an
explicit CONFIRMED/NOT CONFIRMED verdict against each of the issue's three
candidate causes.
