---
status: proposed
files:
  - docs/issue-1044/reports/conformance-review.md
---

## Intent

Render a per-requirement conformance verdict (Present/Surface/Absent/
Incorrect/Unverifiable) for the panel-CLI-dispatch work landed on `main`
by PR #1056 (merge commit `a269692a0cba919e9ed6bf06c832aa280dec04ae`),
against issue #1044's Direction/Acceptance and requirement R001 (req#5,
orphan-capability standard).

## Constraints

- Two-phase role-handoff contract v3 s19: this proposal must be approved
  (PR review Approve or the exact `APPROVE issue-1044/conformance-review`
  issue comment, per approvers.md) before the verdict record itself is
  written.
- Verdicts are rendered from the artifact (spawn.py, directive.sh,
  test_spawn.py) and the spec (issue text, R001) only — not from the
  building agent's stated intent in docs/issue-1044/reports/implementation.md.

## Requirement list (extracted from issue #1044, phase-1 output)

1. `spawn.py panel <role_a> <role_b> "<question>" [--issue n]` reaches a
   CLI dispatch branch in `main()`.
2. That dispatch mirrors the `consult` dispatch's shape (arg validation,
   error handling, output).
3. The orchestrator directive (`on-the-record/hooks/directive.sh`) mentions
   `panel` next to `consult`.
4. `tests/test_spawn.py` carries a CLI-dispatch test proving the panel argv
   path reaches `panel_cmd` with `run_session` stubbed.
5. (Derived from R001/req#5's orphan-capability framing, per docs/issue-1044/reports/conformance-review/survey.md's gap note) whether "reachable and exercised" is satisfied by a stubbed
   dispatch test alone, or requires evidence of at least one live round-trip.

## What will be done

Phase 2 (after approval): read spawn.py, directive.sh, and test_spawn.py
as currently on `main` at commit `a269692a`, check each of the 5 items
above against that state, and write
`docs/issue-1044/reports/conformance-review.md` with one verdict per item,
each backed by a `canonical:`-cited file:line or command-output quote.

## Out of scope

- No code changes to spawn.py/directive.sh/test_spawn.py — findings are
  handed off (addressed_to the owning role), never fixed here.
- No verdict on issues #973/#985/#1037/#1045 themselves, only on the
  #1044-scoped delivery.

## How it will be known to have worked

The written record passes review-traceability (finding-record) and
review-record-norm checks, and each verdict cites the exact file:line or
command output it was derived from.
