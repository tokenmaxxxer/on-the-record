
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
