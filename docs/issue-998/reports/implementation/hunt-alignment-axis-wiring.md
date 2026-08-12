---
proposal: docs/issue-998/proposals/implementation.md
---

# Hunt record — alignment-axis-wiring

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `check_axis_evaluation_entry` (and `role_spec_shape.py` generally) is never invoked from any hook/CI/runner, so the planned `axis_evaluation` shape enforcement the proposal describes is dead code in practice.
Kind: silent-failure
Seed: docs/issue-998/proposals/implementation.md, docs/issue-998/reports/implementation/survey.md (git diff --stat HEAD~1 HEAD)
cap_seconds: 120
tier: default
diff_stat_lines: 169
started_at: 2026-08-12T06:08:26Z
ended_at: 2026-08-12T06:12:00Z

### Reproduce
```
grep -rln "role_spec_shape" --include=*.py --include=*.sh --include=*.yml . \
  | grep -v on-the-record/ | grep -v test_role_spec_shape_batch9.py
```

### Observed
Only `gates/role_spec_shape.py` itself matches (its own `__main__`/imports).
No `.sh` hook, no CI workflow, no other gate runner imports or shells out to
`gates/role_spec_shape.py`. Its `main()` (the only entry point actually
executable from the CLI) calls `check(spec)` per spec.json argument but never
calls `check_axis_evaluation_entry` at all — that function is exercised only
by `gates/test_role_spec_shape_batch9.py`, its own unit test. So even if the
proposed `conformance-review.spec.json` edits (new `axis_evaluation`
required_fields entry, `gate_c_axis_evaluation` field) land exactly as
planned, nothing in CI or pre-commit ever calls
`check_axis_evaluation_entry` against a real role record's actual
`axis_evaluation` array — a role can emit a malformed `axis_evaluation`
entry (wrong `axis`, bad `verdict`, missing `finding.target_path` on a
`contradicts` verdict) and no gate rejects it.

### Expected
Either a hook/CI step shells out `role_spec_shape.py <role-record-or-spec>`
in a mode that reaches `check_axis_evaluation_entry` on real record content,
or the proposal should flag that wiring the check into an actual caller is
a prerequisite, not just adding the schema entry that only unit tests read.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: NO FINDING
Seed: git diff --stat roles/specs/conformance-review.spec.json (4 insertions, 2 deletions: axis_evaluation added to required_fields, reference_resolution.rule extended with axis_evaluation clause, gate_c_axis_evaluation added pointing at docs/handbooks/architecture-methodology.md)
cap_seconds: 60
tier: size:small
diff_stat_lines: 6
started_at: 2026-08-12T15:11:24+09:00
ended_at: 2026-08-12T15:12:21+09:00

Investigated: role-axis-completeness-guard.sh (issue #650) only globs `roles/*.json` (top-level role definitions), never `roles/specs/*.spec.json` — so it cannot see or react to this diff at all; no cancellation there. role-spec-reference-guard.sh (checked_by for reference_resolution) delegates to record_lint.orphaned_path_reference_check, a generic backtick-path resolver that does not special-case axis_evaluation shape (that's a separate, unwired gap — gates/role_spec_shape.check_axis_evaluation_entry exists and is unit-tested in gates/test_role_spec_shape_batch9.py but nothing calls it from a hook), not a case of one rule permitting what another forbids. delegated-judgment-gate.sh's parse_axis_evaluations expects `<!-- axis_evaluation ... -->` HTML-comment blocks with axis/verdict/citation/finding.target_path/finding.required_fix key:value lines in the role's own record markdown — this shape matches (not contradicts) the new reference_resolution.rule text and check_axis_evaluation_entry's expectations. Did not find two rules/hooks that are each locally correct but jointly cancel (one's permission voiding another's refusal) for this diff.
