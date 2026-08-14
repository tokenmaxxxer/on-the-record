---
kind: proposal
loop_state: proposed
---

# Proposal — issue #335 (execution-observation)

## Verdict levels to be checked, and against what evidence

This is a phase-1 proposal; no verdict is rendered here. Phase 2 will
render all three of the role's mandated verdict levels:

- **outcome** — whether PR #357 (subject issue-335, merged
  `76ea30d3eb07f8fbc68ec950be15e4cbc52b7593`) satisfies the deliverables
  claimed in `docs/issue-335/reports/implementation.md`
  (`shape_contracts.py`'s two shape checks, the golden gh-api sample,
  the wired `tests/test_spawn.py` fixtures, and the handbook doc),
  recomputed as the worst case across cited step-level results, per
  `roles/specs/execution-observation.spec.json`'s recomputation rule.
- **trajectory** — whether the phase-1→phase-2 path for issue #335
  followed contract v3's approval-gate convention: surveyed before
  proposing, obtained real human approval before phase 2 — checked
  against the issue's own comment trail (`gh issue view 335
  --comments`) and PR #357's approval-gate history.
- **step** — whether `shape_contracts.py`'s two checks
  (`assert_gh_paginate_slurp_shape`, `assert_claude_stream_event_shape`)
  still work as documented at their current paths in the tree, given
  that a later, unrelated commit (`c79d034d`, "refactor(issue-729):
  consolidate test/ and root test_* files into tests/") relocated
  `shape_contracts.py`, `test_spawn.py`, and the golden fixture from
  repo root into `tests/` after PR #357 merged — checked by directly
  running the acceptance-criteria-scoped test selection and the
  induced-failure demonstration against the current tree, not by
  re-reading the implementation record's own claims as proof.

## Skip record (scout-directive)

Scouting is skipped. Reason: this is not product-shaped work with a
competitive field to survey, and the acceptance criteria are
prescribed mechanically by the implementation record's own stated
"Executable verification actually run" commands — there is no open
design decision for an external sweep to inform.

## What will be done (phase 2, on approval)

1. Confirm the current on-disk location of the deliverables named in
   `docs/issue-335/reports/implementation.md`
   (`shape_contracts.py`, `test_spawn.py`, the golden gh-api sample,
   `docs/handbooks/test-fixture-shape-contracts.md`), since they may
   have moved after PR #357 merged.
2. Re-run the acceptance-criteria-scoped test selection
   (`-k "gh_paginate_slurp or stream_event_shape or FixtureShapeContracts"`,
   the implementation record's own stated invocation) against the
   current tree and record the fenced pass/fail output.
3. Reproduce the induced-failure demonstration from the implementation
   record (deleting `user.login` from the golden sample, asserting the
   exact `AssertionError` message) directly against current
   `shape_contracts.py` and record the fenced output.
4. Attempt the implementation record's whole-file invocation
   (`pytest test_spawn.py -q`, or its current-path equivalent) against
   the current tree; record whatever result actually occurs (pass
   count, failure, or non-completion), not the implementation record's
   original number restated as current fact.
5. Read `gh issue view 335 --comments` for the approval-gate trail
   backing PR #357.
6. Render the three verdict levels in
   `docs/issue-335/reports/execution-observation.md`, with the
   independence statement preceding any verdict language.

## Out of scope

- Re-implementing, editing, or moving any part of the shipped
  `shape_contracts` module or its tests.
- Re-running the observed role's own full test suite output from the
  implementation record as this role's evidence without independently
  re-executing it this step.
- Any change to `roles/specs/`, `gates/`, or `on-the-record/hooks/`.
- Filing a new GitHub issue — any deficiency found returns as a finding
  in this role's own record; the human files an issue if they judge it
  warranted.
