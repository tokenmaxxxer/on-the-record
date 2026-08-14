---
status: proposed
files:
  - docs/issue-1102/reports/execution-observation.md
---

# Proposal — execution-observation for issue-1102

## Intent

Judge whether the implementation role's phase-1→phase-2 execution on
issue #1102 (wiring a `roles/specs/*.spec.json` obligation trigger, per
northpole req#5) was sound, by reading its landed artifacts only — PR
#1107, PR #1109, and its own record — never by re-running its code.

## Constraints

Per the execution-observation role directive: never edit the observed
role's `src/`/`test/`/`docs/issue-1102/` paths outside this role's own
report path; never re-execute the observed task's code as evidence
(re-running the cited test suite is permitted only as corroborating
evidence of the artifact's current state, not as a substitute for
reading the diff/commits/record); phase-2 record
(`docs/issue-1102/reports/execution-observation.md`) waits for a human
Approve.

## What will be done

Phase 2 (after Approve) will render a three-level verdict in
`docs/issue-1102/reports/execution-observation.md`:
- **outcome** — did PR #1109 land the issue's three acceptance checks
  (failing→due test case, resolved→not-due test case, empty-state test
  case), recomputed as the worst case among the step-level results it
  cites.
- **trajectory** — three named pass/fail/n-a checks: scouted-when-required,
  surveyed-before-proposing, approved-by-human, evaluated against PR
  #1107's phase-1 commit history and the issue #1102 approval comment.
- **step** — per-artifact findings on `gates/roles_due.py`'s
  `_matching_obligation`/`_trigger_matches` diff hunk,
  `roles/specs/defect-verification.spec.json`'s `trigger` block diff
  hunk, and the open composition finding disclosed in the observed
  role's own before-landing warrant-hunt record
  (`docs/issue-1102/reports/implementation/hunt-roles-due-obligation-trigger.md`).

## Out of scope

Fixing or re-litigating the composition finding the observed role
already disclosed and filed as a follow-up (uncommitted stand-in report
file suppressing a real failing obligation) — this role only cites it,
per the never-edit-the-observed-artifact constraint. No new issue filing.

## How it will be known to work

`docs/issue-1102/reports/execution-observation.md` exists, committed on
this branch, with the independence statement preceding all
verdict-bearing language, all three verdict levels addressed (each
naming "not applicable, because X" if skipped), and every verdict
sentence carrying an adjacent citation (commit SHA, file:line, or PR
comment URL) with an explicit evidence mode (read/command/asserted).
