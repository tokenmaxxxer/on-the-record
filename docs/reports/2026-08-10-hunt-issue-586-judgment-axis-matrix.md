
## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `check_axis_ownership` (and its siblings `check_role_judgment_axes`, `check_axis_evaluation_entry`) are dead code: nothing calls them, so the "every axis exactly one owner" completeness property the proposal commits to gating is bypassed by simply doing nothing — no role file, no CLI flag, no CI/hook wiring invokes them at all.
Kind: composition
Seed: docs/issue-586/proposals/architecture.md (proposes extending check_axis_ownership in gates/role_spec_shape.py to flag zero-owner axes)
cap_seconds: 180
tier: default
diff_stat_lines: >200 (docs/issue-586/proposals/architecture.md, docs/issue-586/reports/architecture/survey.md, docs/issue-586/reports/architecture/scout-brief.md)
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:06:00Z

### Reproduce
```
grep -rln "check_role_judgment_axes\|check_axis_ownership\|check_axis_evaluation_entry" --include="*.py" --include="*.sh" . | grep -v test_
# -> only gates/role_spec_shape.py itself (the definitions), no caller

python3 gates/role_spec_shape.py roles/architecture.json
# runs main(), which only calls check() (the spec.json-shape checker) —
# never touches check_axis_ownership, regardless of roles/*.json content

find . -iname "*.yml" -o -iname "*.yaml" | xargs grep -l "role_spec_shape" 2>/dev/null
# -> no matches: no CI workflow references role_spec_shape.py either
```

### Observed
`gates/role_spec_shape.py::main()` (the only CLI entrypoint, invoked as
`python3 gates/role_spec_shape.py <spec.json>...`) calls only `check(spec)`.
`check_axis_ownership`, `check_role_judgment_axes`, and
`check_axis_evaluation_entry` are defined but exercised only by
`gates/test_role_spec_shape_batch9.py` unit tests — no production script,
hook, or CI job ever loads all `roles/*.json` into a dict and passes it to
`check_axis_ownership`. Today an axis can be owned by zero roles (or by
two roles) with zero enforcement failures anywhere in the repo's actual
tooling; the proposal's planned "flag zero-owner axes" extension inherits
this same gap because it only describes strengthening the function's logic,
not adding the missing caller/wiring that would make the check run.

### Expected
For the "every axis exactly one owner" completeness property to actually
gate anything, some invoked entrypoint (CLI subcommand, pre-commit hook, or
CI step) must glob `roles/*.json`, build the `roles: dict[str, dict]`, and
call `check_axis_ownership(roles)`, failing the run (non-zero exit) when it
returns non-empty. The proposal should include this wiring as an explicit
deliverable, not just the function-body change, or the "every axis has
exactly one owner" guarantee remains unenforced regardless of how correct
the zero-owner detection logic itself becomes.

## before-landing — stance: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the new `--roles-dir` axis-ownership gate is never invoked outside its own unit test; no hook in `hooks.json` and no CI workflow calls `role_spec_shape.py --roles-dir`, so a zero-owner or double-owned judgment axis passes the whole pipeline undetected.
Kind: composition
Seed: gates/role_spec_shape.py (check_axis_ownership, `_run_roles_dir_check`, `--roles-dir` CLI mode), on-the-record/hooks/hooks.json, on-the-record/hooks/role-spec-reference-guard.sh
cap_seconds: 180
tier: size:200-lines-or->5-files
diff_stat_lines: c35d713..52e7c28 (batch touching gates/role_spec_shape.py + 3 roles/*.json + docs)
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:05:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-586-implementation
# 1. The gate itself works when invoked directly:
python3 gates/role_spec_shape.py --roles-dir roles   # exits 0 currently

# 2. But nothing in the repo's actual enforcement path calls it:
grep -rn -- "--roles-dir" . 2>/dev/null | grep -v "gates/role_spec_shape.py\|gates/test_role_spec_shape_batch9.py\|docs/"
# -> no output: only the gate's own source and its own unit test reference "--roles-dir"

cat on-the-record/hooks/hooks.json | grep -n role_spec_shape
# -> no match

grep -n "role_spec_shape" on-the-record/hooks/role-spec-reference-guard.sh
# -> imports role_spec_shape only to call reference_resolution_check(); never calls
#    check_axis_ownership or main(["--roles-dir", ...])

find . -iname "*.yml" -path "*workflows*"
# -> no workflow files exist in this repo at all; there is no CI step running gates/*.py either
```

### Observed
`--roles-dir` mode exists, is unit-tested in isolation (`gates/test_role_spec_shape_batch9.py`), and correctly detects zero-owner/multi-owner axes when run by hand. But it is wired into no hook (`hooks.json`'s PreToolUse/Stop lists) and no CI workflow. The only hook that even imports `role_spec_shape` (`role-spec-reference-guard.sh`) uses a different function (`reference_resolution_check`) and never touches `check_axis_ownership`. So if a future edit removes `judgment_axes` from a role or duplicates an axis across two roles, nothing in the actual commit/session pipeline fails — the invariant "each of the 5 axes has exactly one owner" is enforced only if someone remembers to run `python3 gates/role_spec_shape.py --roles-dir roles` by hand.

### Expected
Either a hook (e.g. a new entry in `hooks.json`'s Write|Edit|MultiEdit matcher list, alongside `role-spec-reference-guard.sh`) or a CI step should invoke `role_spec_shape.py --roles-dir roles` on every change touching `roles/*.json`, so the gate that was just built to catch zero/multi-owner axes actually runs automatically instead of being reachable only via manual invocation or its own test suite.
