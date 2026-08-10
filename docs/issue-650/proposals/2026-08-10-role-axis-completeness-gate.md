---
status: proposed
files:
  - on-the-record/hooks/role-axis-completeness-guard.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_role_axis_completeness_guard.py
  - docs/handbooks/hooks.md
---

## Request

Issue #650 (hunt #628 finding): `gates/role_spec_shape.py`'s `--roles-dir`
axis-completeness check (`check_axis_ownership` / `check_role_judgment_axes`)
has zero callers on any operational path — same dead-code class already
fixed once in #594/#586. Wire a real caller so the check actually runs
somewhere operational, plus a regression test driving the caller, not the
entrypoint.

## Constraints

- The caller must be a real, already-triggered path — not a new
  standalone script nobody invokes (that would just be dead code one
  layer removed).
- The regression test must drive the CALLER (the hook), not
  `role_spec_shape.py`'s CLI directly — issue #650's explicit acceptance
  criterion, aimed at preventing a repeat where the test only proves the
  entrypoint works in isolation.
- Zero-install: this repo's `on-the-record/hooks/*.sh` scripts must not
  require a `pip install` in the consumer repo (existing convention,
  documented in `spec-index-preflight.sh` and `role-spec-reference-guard.sh`).
- Fail-open on missing `python3`/`git`, fail-closed (deny) on a
  positively-determined violation — the pattern both existing
  commit-time hooks (`spec-index-preflight.sh`,
  `role-spec-reference-guard.sh`) already use.

## Rationale

Chosen: a new `PreToolUse` (`Bash`) hook,
`role-axis-completeness-guard.sh`, that denies `git commit` when the
staged `roles/*.json` set violates axis completeness (an axis owned by
zero or by more than one role, or a role's own `judgment_axes` shape
invalid). It imports `gates/role_spec_shape.py`'s existing
`check_axis_ownership`/`check_role_judgment_axes` functions rather than
re-implementing the logic, following the import precedent
`role-spec-reference-guard.sh` already set for this exact module.

Rejected alternative 1 — a "reconcile" verb: the issue's own menu offers
spawn path / gate / reconcile verb. This repo has no existing reconcile
CLI that takes `roles/` as input (surveyed: no such command-surface
exists today). Building one from scratch to host a single completeness
check is a materially larger surface than the fix warrants, and would
itself need its own operational caller — reintroducing the same
dead-code risk one layer up.

Rejected alternative 2 — wiring the check into the role-spawn path: no
code path in this repo currently reads `judgment_axes` at spawn time
(surveyed: grep for spawn-time role-config consumers found none that
touch `judgment_axes`). Wiring the check there would mean inventing that
read path too, well outside this issue's frozen write set and outside
what a completeness-shape fix should touch.

The commit-time gate is rejected-alternative-free by comparison: two
hooks (`spec-index-preflight.sh`, `pr-preflight.sh`) already gate
`git commit` this way for a structurally identical problem (schema/index
drift undetected until commit), so this fix follows an established,
already-battle-tested wiring pattern rather than inventing a new one.

## What will be done

- Add `on-the-record/hooks/role-axis-completeness-guard.sh`: a
  `PreToolUse` `Bash` hook matching the `git commit` command shape
  (same regex-gate style as `spec-index-preflight.sh`), that on a commit
  attempt reads the staged `roles/*.json` set via `git show :<path>` for
  every staged path matching `roles/*.json` (falling back to the working
  tree for any `roles/*.json` file not itself staged, since axis
  ownership is evaluated across the WHOLE set, not just the staged
  delta), imports `gates/role_spec_shape.py` (same
  `sys.path.insert`-from-script-dir resolution `role-spec-reference-guard.sh`
  uses), runs `check_role_judgment_axes` per role and
  `check_axis_ownership` across the assembled set, and denies (exit 2,
  reasons to stderr) on any violation. Fail-open (exit 0) when
  `python3`/`git` is missing, the command isn't `git commit`, or no
  `roles/*.json` path is staged. Respects the existing `ORCHESTRATE_OFF`
  kill switch.
- Register the hook in `on-the-record/hooks/hooks.json` under the
  existing `PreToolUse`/`Bash` group (alongside `spec-index-preflight.sh`,
  `pr-preflight.sh`, etc.).
- Add `on-the-record/hooks/test_role_axis_completeness_guard.py`: a
  regression test that invokes the hook script itself (subprocess, same
  harness style as the repo's other `test_*_guard.py` files under
  `on-the-record/hooks/`), constructing a real git repo fixture with
  `roles/*.json` files whose `judgment_axes` violate axis ownership
  (double-owned and zero-owned axis cases), staging them, and asserting
  the hook denies the commit (exit 2) — plus a passing case (exit 0) with
  a valid axis-ownership set. This drives the CALLER (the hook process),
  not `role_spec_shape.py`'s CLI, per the issue's acceptance criterion.
- Document the new hook and its `ORCHESTRATE_OFF` behavior in
  `docs/handbooks/hooks.md` (new-hook-entry convention already used for
  the existing commit-time gates), since it's a new operational gate a
  future contributor needs to know about.

## Out of scope

- Re-touching `gates/role_spec_shape.py`'s own logic or its existing
  unit tests (`gates/test_role_spec_shape*.py`) — the functions already
  work; only their wiring is missing.
- The "reconcile verb" and "spawn path" alternatives (see Rationale).
- Any change to `roles/*.json` content itself — this fix only adds
  enforcement, it doesn't touch what's being enforced.

## Accumulation

`test_role_axis_completeness_guard.py` drives the hook via repeated
`subprocess.run(["bash", str(GUARD)], ...)` calls (>= 3 sites) and writes
`roles/*.json`-shaped fixture files inside a throwaway `tmp_path` git repo
per test — both match the two accumulation shapes
`accumulation-claim-guard.sh` watches for. Neither grows unbounded: the
subprocess call sites are a small, fixed set of test cases (one per
axis-completeness scenario: valid, zero-owner, double-owner, invalid axis
name, no-staged-roles, non-commit command, `ORCHESTRATE_OFF`), not a
pattern that accretes a new inline call per future change; a shared
`_run()` helper already collapses the repeated shape to one call site per
test. The `roles/*.json` fixture files are ephemeral pytest `tmp_path`
fixtures, never real `roles/` entries — they don't add to the repo's real
41-file `roles/` set and aren't touched by future unrelated commits the
way a real accumulating file would be.

## How you'll know it worked

- `on-the-record/hooks/test_role_axis_completeness_guard.py` passes,
  demonstrating the hook (not the entrypoint) denies a commit that
  breaks axis completeness and allows one that doesn't.
- Full existing suite (`gates/`, `on-the-record/hooks/`) still passes —
  no regression to the module's own unit tests or other hooks.
- Manual/fenced run: staging a `roles/*.json` edit that double-owns an
  axis and attempting `git commit` is denied by the new hook with a
  clear stderr reason.
