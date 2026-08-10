# Current-state survey — issue #586 step 2 (implementation, batch 1)

Scout skip: spec leaves no design decision open (scout-directive skip
condition 2). `docs/issue-586/proposals/architecture.md` (approved,
merged in PR #590) already names the exact 3 files to edit, the exact
axis assignments and rationale, the procedure-template shape, and the
gate-extension direction (add zero-owner check, wire the three
axis-check functions into a real entrypoint). Step 2's job is to realize
that frozen design, not to make new design decisions — no scouting run.

## Write-set state today

- `roles/conformance-review.json`, `roles/capacity-planning.json`,
  `roles/performance-engineering.json` — none carry `judgment_axes` yet.
  `roles/architecture.json` and `roles/security-threat-model.json` are
  the only two with it (`["maintenance_complexity"]`,
  `["attack_potential"]`), confirmed by direct read.
- `gates/role_spec_shape.py` (235 lines): `_JUDGMENT_AXES` is the closed
  5-entry set. `check_role_judgment_axes`, `check_axis_ownership`,
  `check_axis_evaluation_entry` are defined and covered by
  `gates/test_role_spec_shape_batch9.py` (unit tests call the functions
  directly). `check_axis_ownership` today only flags **multiple** owners
  (`len(names) > 1`) — it never flags an axis with zero owners, so it
  would not have caught `alignment`/`external_burden`/`performance`
  sitting unowned. `main()` (line 214) only runs `check()` against
  `spec.json` files passed as argv; it never loads `roles/*.json` and
  never calls `check_role_judgment_axes`/`check_axis_ownership` at all.
  A repo-wide grep for `role_spec_shape` finds no caller of `main()`
  besides its own `if __name__` block, and no entry in
  `on-the-record/hooks/hooks.json` invokes it — the two "role-spec"
  hooks wired there, `role-spec-reference-guard.sh` and
  `role-test-claim-guard.sh`, call unrelated functions
  (`reference_resolution_check` / `record_path_role`, not the axis
  checks). Confirms the architecture proposal's after-proposal-hunt
  finding: the three axis-check functions are dead code, unit-tested
  only.
- No CLI entrypoint or CI/hook step runs `check_axis_ownership` /
  `check_role_judgment_axes` over the real `roles/*.json` directory
  today.
- `on-the-record/hooks/test_delegated_judgment_gate.py` (348 lines):
  fixture roles today are exactly 2 (`architecture`,
  `security-threat-model`), each with one judgment_axes entry — no
  fixture exercises 3+ axis-owning roles in one panel. The approved
  architecture proposal's batch table (section 3) assigns that
  multi-role fixture to batch 5 / issue #586 step 3, owned by
  conformance-review, and explicitly lists it under "Out of scope" for
  batch 1. This survey flags a mismatch: the invoking instruction for
  this session asked for that fixture in this batch, but the
  human-approved, merged proposal says otherwise. Following the frozen
  proposal over the paraphrased re-statement — noted here rather than
  silently doing either.
- The methodology handbook the proposal targets
  (`architecture-methodology.md`) does not exist yet under
  `docs/handbooks/` — current contents there are on-the-record.md,
  operations.md, record-authoring.md, risk-classified-approvals.md,
  setup.md, spawn.md, test-fixture-shape-contracts.md. This batch
  creates it new (the architecture proposal's section 2 target),
  rather than extending an existing file.
- `docs/decisions/` holds 3 dated ADRs today (2026-07-29 x2,
  2026-08-07); no 2026-08-10 judgment-axis-matrix entry yet — this
  batch creates it new.
- Applicable test scope: `pytest gates/ on-the-record/hooks/ -q` covers
  every touched test file; full-repo `pytest -q` also available per the
  proposal's "how you'll know it worked" section.

## Files this batch will touch (matches architecture proposal's frozen list)

- `roles/conformance-review.json` — add judgment_axes: [alignment]
- `roles/capacity-planning.json` — add judgment_axes: [external_burden]
- `roles/performance-engineering.json` — add judgment_axes: [performance]
- `gates/role_spec_shape.py` — extend check_axis_ownership to flag
  zero-owner axes; add a main()-reachable path (new CLI subcommand,
  existing spec.json behavior unchanged) that loads roles/*.json and
  runs check_role_judgment_axes / check_axis_ownership over them
- `gates/test_role_spec_shape_batch9.py` — extend with the zero-owner
  test and a test for the new entrypoint path
- docs/handbooks/architecture-methodology.md — new file, axis-evaluation
  procedure template section (shape from the architecture proposal
  section 2)
- docs/decisions/2026-08-10-judgment-axis-matrix.md — new ADR recording
  the 3 axis assignments and the "why no 6th axis" rationale
