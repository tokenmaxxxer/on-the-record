# Commit-time gate hooks

`on-the-record/hooks/hooks.json` registers `PreToolUse` (`Bash`) hooks
that inspect a `git commit` attempt before it lands and can deny it
(exit 2) when they positively determine a violation. All of them fail
open (exit 0) on environment gaps — missing `python3`/`git`, a
non-commit command, or nothing relevant staged — and all respect the
`ORCHESTRATE_OFF` kill switch (any value other than empty/`0`/`false`/
`no`/`off` disables the hook for that invocation).

## role-axis-completeness-guard.sh (issue #650)

Denies `git commit` when the staged `roles/*.json` set violates axis
completeness: `gates/role_spec_shape.py`'s `check_axis_ownership` (each
of the five fixed methodology axes — `alignment`,
`maintenance_complexity`, `external_burden`, `attack_potential`,
`performance` — must be owned by exactly one role across the whole set)
and `check_role_judgment_axes` (a role's own `judgment_axes` array, when
present, must only name axes from that closed set).

Evaluates the WHOLE `roles/*.json` set, not just the staged delta: staged
paths are read via `git show :<path>` (what would actually land), every
other `roles/*.json` file is read from the working tree, since ownership
is a property of the assembled set.

Imports `gates/role_spec_shape.py` rather than re-porting the check logic
(same precedent `role-spec-reference-guard.sh` set for this module). The
packaged `on-the-record/gates` copy of that module can lag the top-level
`gates/` copy — this hook tries each candidate gates directory
(`on-the-record/gates`, then the top-level `gates/`) in turn and uses the
first one that actually exposes both `check_axis_ownership` and
`check_role_judgment_axes`, rather than hard-coding a single path that
may be stale.

Wires a real operational caller for the axis-completeness check
(hunt #628 finding on issue #650): the check previously had a
`--roles-dir` CLI entrypoint with zero callers outside its own unit
tests — the same dead-code class already fixed once in #594/#586.

Regression coverage: `on-the-record/hooks/test_role_axis_completeness_guard.py`
drives the hook script itself (subprocess, real git repo fixtures), not
`role_spec_shape.py`'s CLI.
