# Survey — issue #650

## What exists

- `gates/role_spec_shape.py` (issue #521/#586) implements the axis-completeness
  check as `check_axis_ownership(roles: dict[str, dict]) -> list[str]`
  (each of the 5 `_JUDGMENT_AXES` must be owned by exactly one role) plus
  a per-role `check_role_judgment_axes`, both driven by CLI mode
  `--roles-dir <dir>` via `_run_roles_dir_check` (gates/role_spec_shape.py:242-260).
- `roles/*.json` is the real, populated write surface: 41 role config files,
  each optionally carrying a `judgment_axes` array (opt-in, issue-573).
- Zero callers of `--roles-dir` outside the module's own tests
  (`gates/test_role_spec_shape_batch9.py`) — confirmed via repo-wide grep
  for `check_axis_ownership`, `_run_roles_dir_check`, `--roles-dir`. No
  hook, gate script, or CI workflow invokes it. This is the exact dead-code
  class already fixed once in PR #594 (issue #586) and now recurring
  (hunt #628 finding, issue #650).
- `on-the-record/hooks/hooks.json` registers a `PreToolUse` (`Bash`)
  group that already gates `git commit`: `spec-index-preflight.sh` (drift
  check on `docs/specs/reconciled-index.md`, using staged content via
  `git show :<path>`, zero-install/no-import inline Python) and
  `pr-preflight.sh`. Both fail-open on missing `python3`/`git` and fail
  fast on non-commit commands. `role-spec-reference-guard.sh` (a
  `Write|Edit|MultiEdit` hook) is the one existing hook that DOES import
  `gates/role_spec_shape.py` directly (via `sys.path.insert` resolved from
  the hook's own script dir, `RSRG_GATES_DIR`), for a different function
  (`reference_resolution_check`) — this establishes the plugin's precedent
  for importing this module from a hook rather than re-porting its logic
  inline.
- `docs/specs/role-spec-template.schema.json` documents the schema shape;
  its description already states `role_spec_shape.py` is the checker.

## Gap

The axis-completeness check (`check_axis_ownership` +
`check_role_judgment_axes`) is real, tested-at-the-unit-level logic with
no wire into any path a human or CI actually exercises. `roles/*.json`
can drift to zero-owner or double-owner axes and nothing catches it
before or at commit time.

## Candidate operational paths (per issue's own menu: spawn / gate / reconcile)

- **Gate at commit time** (chosen — see proposal `## Rationale`): a new
  `PreToolUse` `Bash` hook, same shape as `spec-index-preflight.sh`, that
  denies `git commit` when the staged `roles/*.json` set fails
  `check_axis_ownership`/`check_role_judgment_axes`. Matches existing
  precedent (two hooks already gate `git commit` this way) and the
  existing import precedent (`role-spec-reference-guard.sh` already
  imports this exact module from a hook).
- Reconcile verb: no existing "reconcile" CLI/verb in this repo takes
  `roles/` as input; would need inventing new command-surface, out of
  proportion to a completeness check.
- Spawn path: no role-spawn code path in this repo reads `judgment_axes`
  at spawn time today; wiring it there would require touching the spawn
  mechanism itself, a materially larger surface than this fix warrants.

## Skip conditions

Neither scout skip condition applies cleanly (an operational-path choice
is a real design decision), but scouting here means codebase precedent,
not external product research — the field for this fix is the plugin's
own hook conventions (`docs/decisions/`, `on-the-record/hooks/*.sh`
patterns), which this survey walks above.
