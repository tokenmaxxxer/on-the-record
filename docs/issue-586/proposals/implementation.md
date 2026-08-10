---
status: proposed
files:
  - roles/conformance-review.json
  - roles/capacity-planning.json
  - roles/performance-engineering.json
  - gates/role_spec_shape.py
  - gates/test_role_spec_shape_batch9.py
  - docs/handbooks/architecture-methodology.md
  - docs/decisions/2026-08-10-judgment-axis-matrix.md
---

# Proposal — issue #586 step 2: realize the axis matrix (implementation, batch 1)

## Request
Realize batch 1 of the approved, merged architecture proposal
(`docs/issue-586/proposals/architecture.md`, PR #590): set
`judgment_axes` on the three unowned-axis roles
(conformance-review/alignment, capacity-planning/external_burden,
performance-engineering/performance), extend
`gates/role_spec_shape.py`'s `check_axis_ownership` to fail on an
unowned axis (today it only catches double-ownership) and give the
three axis-check functions a real, callable entrypoint (per the
proposal's after-proposal-hunt finding that they are dead code), and
ship the rulebook axis-evaluation procedure template as a new handbook
section plus a dated ADR.

## Constraints
- The axis assignments, rationale, and template text are already
  decided and human-approved in the merged architecture proposal — this
  batch does not reopen any of that; it only implements it.
- `_JUDGMENT_AXES` stays a closed 5-entry set; no new axis is added.
- The multi-role panel fixture in
  `on-the-record/hooks/test_delegated_judgment_gate.py` is explicitly
  out-of-scope for batch 1 per the architecture proposal's batch table
  (assigned to batch 5 / step 3, owned by conformance-review) — this
  proposal's write set does not include that file, even though the
  session's invoking instruction asked for it in this batch (see
  survey.md's flagged mismatch).
- Writing rulebook procedure prose inside the four rulebook repos
  (conformance-review-rulebook, capacity-planning-rulebook,
  performance-engineering-rulebook, architecture-rulebook) is out of
  reach from this checkout, same constraint the architecture proposal
  already stated for itself — batches 2-4 stay follow-up issues.
- The new `main()` path must not change `role_spec_shape.py`'s existing
  `spec.json`-argv behavior — that entrypoint is already relied on
  wherever it is invoked today.

## Accumulation
This batch edits 3 of 43 `roles/*.json` files with the same one-line
shape (`"judgment_axes": [...]` added). `_JUDGMENT_AXES` is closed at 5
entries (unchanged here), so at most 5 roles will ever carry this field
— 2 already do, this batch brings the total to 5, and no further
`roles/*.json` edit of this shape is expected after batch 1 lands. If a
future issue reopens the axis vocabulary, `check_axis_ownership`'s
zero-owner extension (this proposal) is exactly the mechanical brake
that fails the gate until the matrix is complete again — same
accumulation argument the architecture proposal already made for the
same 3 files.

## Rationale
Two options for wiring the axis checks into a real entrypoint:
1. **Extend `role_spec_shape.py`'s existing `main()` with a new
   subcommand/flag** (chosen) that, when passed, loads `roles/*.json`
   from a given directory and runs `check_role_judgment_axes` +
   `check_axis_ownership` over the set, alongside the existing
   per-spec-file mode.
2. **A brand-new script** (e.g. `gates/role_axis_check.py`) that only
   does the axis-ownership check, left uncalled by anything just like
   today.

Rejected (2): it would repeat the exact defect the after-proposal hunt
found — a checker that exists, is unit-tested, and is never invoked by
any hook, CI job, or other entrypoint. Extending the existing `main()`
(1) makes the axis check reachable the same way the shape check already
is (`python3 gates/role_spec_shape.py ...`), one file, one script,
no new dead surface. It costs a slightly busier `main()`, accepted
because the alternative reproduces the bug this batch exists to fix.

## What will be done
1. `roles/conformance-review.json` — add `"judgment_axes": ["alignment"]`.
2. `roles/capacity-planning.json` — add `"judgment_axes": ["external_burden"]`.
3. `roles/performance-engineering.json` — add `"judgment_axes": ["performance"]`.
4. `gates/role_spec_shape.py`:
   - `check_axis_ownership`: also flag axes with zero owners (today only
     flags `len(names) > 1`), same reasons-list shape.
   - `main()`: add a `--roles-dir <dir>` mode. When passed, load every
     `<dir>/*.json`, run `check_role_judgment_axes` per role and
     `check_axis_ownership` across the set, print reasons to stderr,
     exit 1 on any failure. The existing `<spec.json>...` positional
     mode is untouched when `--roles-dir` is absent.
5. `gates/test_role_spec_shape_batch9.py`: add a test asserting
   `check_axis_ownership` flags a zero-owner axis, and a test exercising
   the new `--roles-dir` CLI path against a tmp fixture directory
   (3 roles owning 3 axes = pass, one role missing = fail).
6. `docs/handbooks/architecture-methodology.md` (new file): the
   axis-evaluation procedure template section, verbatim shape from the
   architecture proposal section 2 (READ/EXECUTE/CRITERIA/CITATION
   blanks), plus one paragraph of context linking it to
   `check_axis_evaluation_entry`'s shape check.
7. `docs/decisions/2026-08-10-judgment-axis-matrix.md` (new ADR):
   records the 3 axis -> role assignments, cites the architecture
   proposal as source, and restates the "why no 6th axis" rejection
   (cost/unit-economics, legal/compliance) already decided there.
8. Run `pytest gates/ on-the-record/hooks/ -q` and full-repo `pytest -q`;
   fix anything the edits break before landing.

## Out of scope
- The multi-role panel fixture (batch 5 / step 3, conformance-review's
  own work per the architecture proposal).
- Rulebook procedure prose in the four rulebook repos (batches 2-4,
  follow-up issues, not this checkout).
- Reopening the 5-axis vocabulary, the 2 already-owned axes, or any
  axis-assignment rationale — all already decided and merged.
- Closing issue #586 — rulebook procedure batches (2-4) and the panel
  fixture (batch 5) remain; this PR references #586 plainly, no
  `Closes`.

## How you'll know it worked
- `python3 gates/role_spec_shape.py --roles-dir roles` exits 0 after the
  3 role edits (all 5 axes single-owned) and would have exited 1 before
  them (demonstrable by running it against the pre-edit files via git
  stash, or by the new unit test's zero-owner fixture).
- `gates/test_role_spec_shape_batch9.py`'s new tests pass.
- `pytest gates/ on-the-record/hooks/ -q` and full-repo `pytest -q` both
  pass, with actual command output captured in the implementation
  record.
- `python3 gates/role_spec_shape.py roles/specs/<name>.spec.json` still
  exits 0 for all 43 roles (regression check — batch 1 does not touch
  `roles/specs/*.spec.json`).

## What did not work
None yet — appended during build if anything breaks.
