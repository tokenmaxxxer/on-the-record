---
status: proposed
files:
  - docs/specs/enforcement-boundary.md
  - docs/issue-573/reports/implementation.md
---

# Proposal — issue #573: add missing boundary-spec verdict rows

Skip condition (survey-order-directive): pure bugfix, no design decision
open. `gates/test_boundary.py::t_all_gates_modules_recorded` fails
because two already-shipped hook scripts have no verdict row in
`docs/specs/enforcement-boundary.md`. The fix is to add rows following
the exact template every other `on-the-record/hooks/*.sh` row in that
file already uses — no new mechanism, no alternative design.

## Request

The prior delivery (PR #583, merged) shipped
`on-the-record/hooks/delegated-judgment-gate.sh` without adding its
required verdict row to `docs/specs/enforcement-boundary.md`, because
that spec file was outside the approved phase-2 write set (recorded as
an Open finding in `docs/issue-573/reports/implementation.md`). Running
the boundary test now (`python3 gates/test_boundary.py`) also shows a
second, unrelated pre-existing gap: `product-capture-stopgate.sh`
(issue #566) has no row either. Both must be filled for the repo-wide
boundary test (issue #441) to pass again.

## Constraints

- Narrow write set: the spec file and this follow-up's own implementation
  record only — no hook behavior changes.
- Each new row must follow the same column shape (mechanism / verdict /
  reason) and verdict vocabulary already defined in the file's header
  (`contract`, `contract, CI-supplement`, `repo-local`, etc.).
- The boundary test must be run and shown green before the record is
  written, per this follow-up's own instruction.

## Rationale

Alternative considered and rejected: fold this into the next unrelated
proposal that happens to touch `docs/specs/enforcement-boundary.md`,
instead of a dedicated follow-up. Rejected because the boundary test is
currently red on `main` for anyone running the full suite, and leaving a
known, already-diagnosed gap unfixed while waiting for an unrelated
change to carry it is worse than a small dedicated fix — the prior
record's own "Resolution path" section already names this exact
follow-up as the intended next unit of work.

## What will be done

- Add a `delegated-judgment-gate.sh` row to the
  `on-the-record/hooks/*.sh (plugin-shipped)` table: verdict `contract`
  (new, issue #573: `PreToolUse`+`Bash` on `gh pr create`, zero-install,
  ships with the plugin, per the hook's own header comment).
- Add a `product-capture-stopgate.sh` row to the same table: verdict
  `contract` (issue #566, `Stop` hook, zero-install, ships with the
  plugin, per the hook's own header comment) — pre-existing gap,
  unrelated to issue #573, fixed here because it blocks the same test.
- Run `python3 gates/test_boundary.py` and confirm all pass.
- Write this follow-up's own record at
  `docs/issue-573/reports/implementation.md` documenting the change (its
  loop_state transitions per phase-2 rules once approved).

## Out of scope

- Any change to hook behavior, `hooks.json`, or other spec files.
- Step 5 (execution-observation / conformance-review measurement) —
  tracked separately per the issue's reopen note.

## How you'll know it worked

`python3 gates/test_boundary.py` exits 0 with no assertion failure,
specifically `t_all_gates_modules_recorded` passing for both hooks.
