---
status: proposed
files:
  - gates/test_role_utilization_report.py
  - roles/refactoring-legacy.json
  - roles/test-authoring.json
  - docs/issue-993/reports/implementation.md
---

# Proposal — issue #993, implementation phase-1

## Request
Per the merged product-discovery phase-1
(docs/issue-993/proposals/product-discovery.md, PR #1004): build the
issue's own named acceptance check (a utilization-report gate test) and
land the boundary-sharpening fix for the two roles the diagnosis left as
`(b) scope overlap, tentative` with no follow-up issue — refactoring-legacy
and test-authoring. The secure-coding/capacity-planning/performance-
engineering fixes are already owned by issues #1005/#992/#960 respectively
per the current-state survey and are out of this write set.

## Constraints
- `roles/specs/secure-coding.spec.json` is not touched here — issue #1005
  owns that exact write set with its own merged phase-1 proposal
  (docs/issue-993/reports/implementation/survey.md, "What #993's own
  diagnosis already routed elsewhere").
- The gate test reads the board (`docs/issue-*/reports/`) and
  `roles/*.json` the same way the existing `gates/roles_due.py` and
  `gates/test_roles_due.py` do — no new report format, no new counting
  convention invented for this one test.
- The boundary fix is a role-file change, not a schema change:
  `roles/*.json` has no machine-enforced schema gate today (per
  `gates/test_role_spec_shape*.py`, which validates `roles/specs/*.spec.json`,
  not `roles/*.json` itself) — adding a new key would be undocumented
  everywhere else, so the fix is a prose addition to the existing
  `use_when` field, not a new field.

## Rationale
Considered adding a new `absorbed_by` field to `roles/refactoring-legacy.json`
and `roles/test-authoring.json` instead of a prose note inside `use_when`.
Rejected: no other role file in `roles/*.json` carries a structured
overlap-disposition field, and `gates/test_role_spec_shape*.py` validates
only `roles/specs/*.spec.json`'s shape, not `roles/*.json`'s — introducing
a new key with no reader and no shape check anywhere would be exactly the
kind of promise-not-mechanism problem the issue is itself auditing for
(#993's own framing: "dead weight... structural failure"). A one-line
addition to the existing free-text `use_when` field, which every other
role file already uses for its own disposition prose, keeps the fix
readable by the same mechanism every other role already relies on.

## What will be done
1. `roles/refactoring-legacy.json` and `roles/test-authoring.json`: append
   one clause to each `use_when` string stating that implementation's own
   write_scope already covers this domain inline when a standalone record
   is not warranted, plus the revisit condition already named in the
   merged proposal (a legacy-debt-specific or test-design-specific record
   type being wanted later).
2. `gates/test_role_utilization_report.py`: a gate test that (a) for each
   of the 43 `roles/*.json` stems, counts records matching exactly the
   product-discovery survey's own derivation rule (`docs/issue-993/reports/product-discovery/current-state.md`
   line 16): a flat `docs/issue-<n>/reports/<role>.md` OR a nested
   `docs/issue-<n>/reports/<role>/*.md`, matched by literal stem equality
   — no fuzzy or partial matching, and the known `coding`
   plugin-directory / `implementation` role-name doubling (a
   deliberate, tracked doubling per this repo's own role-handoff
   convention, not a bug) is left unreconciled, matching the same
   scope the survey itself already carried; (b) asserts every one of the
   43 role stems appears as a key in the resulting count map (zero is a
   valid count, absence is not), and (c) asserts the two roles just
   touched in step 1 carry a `(b)`-style overlap disposition string in
   their `use_when` field, so a future change to either role file that
   silently drops the note fails the gate.
3. Run the new test once and paste real output into
   `docs/issue-993/reports/implementation.md`.

## Accumulation
This touches 2 of the 43 `roles/*.json` files with the same one-line
`use_when` addition shape. If N more roles later need the same
scope-overlap boundary note, each addition stays a single inline clause
in that role's own existing `use_when` string — no shared helper is
warranted at N=2, since the note text is role-specific prose, not a
repeated computation. The gate test built in this proposal is the
scaling mechanism instead: it asserts *whichever* roles carry a `(b)`-style
disposition state that disposition in `use_when`, so growth in the number
of scope-overlap roles is caught by one test, not by re-deriving the audit
by hand each time.

## Out of scope
- Any change to `roles/specs/secure-coding.spec.json` or a new
  `gates/test_secure_coding_routing.py` — issue #1005's own write set.
- Any change to capacity-planning/performance-engineering's rulebook
  content — #992's own scope.
- Any change to the 3+-role panel / axis-evaluation matrix — #960's own
  scope.
- Wiring the new utilization gate test into any pre-commit enforcement
  path (making it block a commit) — it lands as a standalone `gates/`
  test runnable via pytest, matching how `gates/test_roles_due.py` itself
  is not wired into enforcement either.

## How you'll know it worked
`pytest gates/test_role_utilization_report.py -q` passes, with its real
output pasted into `docs/issue-993/reports/implementation.md`, proving all
43 role stems are covered and the two boundary-note roles carry the
expected disposition string.
