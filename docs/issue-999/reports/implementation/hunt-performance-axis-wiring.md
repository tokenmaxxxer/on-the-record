---
proposal: docs/issue-999/proposals/implementation.md
---

# Hunt record — performance-axis-wiring

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: NO FINDING
Seed: git show b6b50ba (docs/issue-999/proposals/implementation.md, docs/issue-999/reports/implementation/survey.md)
cap_seconds: 120
tier: default
diff_stat_lines: 180
started_at: 2026-08-12T15:30:00+09:00
ended_at: 2026-08-12T15:38:00+09:00

Checked the stance's three sub-questions directly:

1. Is check_axis_ownership/check_axis_evaluation_entry invoked outside its
   own unit test? Yes — on-the-record/hooks/role-axis-completeness-guard.sh
   is a real PreToolUse git-commit hook that imports gates/role_spec_shape.py
   and calls check_axis_ownership/check_role_judgment_axes on staged
   roles/*.json (issue #650, hunt #628 finding). This is a landed caller,
   not a gap. `python3 gates/role_spec_shape.py --roles-dir roles` also
   exits 0 today, confirming performance is currently owned by exactly one
   role (performance-engineering.json).

2. Any other role file referencing the performance axis that would
   conflict? `grep -n '"performance"' roles/*.json` returns only
   roles/performance-engineering.json:15. No conflict.

3. Does the handbook's existing performance-axis section match what the
   proposal claims? Read docs/handbooks/architecture-methodology.md lines
   208-245 ("Axis evaluation procedure — performance") directly: it
   READs sli/slo_target/error_budget_remaining/verdict, EXECUTEs a
   3-step recompute of error_budget_remaining then verdict, cites the
   Google SRE Workbook implementing-slos and error-budget-policy chapters.
   This matches the proposal's "What will be done" gate_c_axis_evaluation
   text verbatim (recomputes error_budget_remaining from sli against
   slo_target, then verdict from that recomputed budget, per Google SRE
   Workbook implementing-slos/error-budget-policy).

No state nothing maintains was found: the guard hook is real and wired,
the axis-ownership matrix is currently consistent, and the handbook prose
matches the proposal's restatement. This is a docs-only proposal (no
spec.json edit landed yet in this diff), so there is nothing yet to
reproduce a wiring defect against.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — role-spec-reference-guard.sh's hardcoded 6-role `_VERIFICATION_FAMILY_ROLES` allowlist silently cancels the reference_resolution.rule this diff just added to performance-engineering.spec.json: axis_evaluation entries in a performance-engineering record are never checked (the enforcement hook only fires for execution-observation/conformance-review/defect-verification/security-threat-model/accessibility/secure-coding), so the new rule text is prose-only for this role.
Kind: composition
Seed: git diff roles/specs/performance-engineering.spec.json (8 lines: adds axis_evaluation required_fields entry + extends reference_resolution.rule text + adds gate_c_axis_evaluation key)
cap_seconds: 60
tier: default
diff_stat_lines: 8
started_at: 2026-08-12T06:22:04Z
ended_at: 2026-08-12T06:52:00Z

### Reproduce
```
cd <repo>
# payload A: same orphaned-ref axis_evaluation block, targeting docs/issue-999/reports/conformance-review.md (in family)
bash on-the-record/hooks/role-spec-reference-guard.sh < /tmp/payload_cr.json; echo "exit_cr=$?"
# payload B: identical content/structure, targeting docs/issue-999/reports/performance-engineering.md (NOT in family)
bash on-the-record/hooks/role-spec-reference-guard.sh < /tmp/payload_pe.json; echo "exit_pe=$?"
```
Where both payloads are PreToolUse Write payloads with content:
```
<!-- axis_evaluation
axis: <role's judgment axis>
verdict: contradicts
citation: `docs/issue-999/reports/implementation/nonexistent-citation-xyz.md`
finding:
  target_path: `docs/issue-999/reports/implementation/nonexistent-target-xyz.py`
  required_fix: fix it
-->
```
only the `file_path` role segment differs (`conformance-review.md` vs `performance-engineering.md`).

### Observed
`exit_cr=2` (denied, orphaned-path violations reported: both the citation and finding.target_path backtick refs are flagged as issue #330 orphan references) vs `exit_pe=0` (silently allowed — no output, no denial) for the byte-identical axis_evaluation block, solely because `role-spec-reference-guard.sh`'s `_VERIFICATION_FAMILY_ROLES` set (execution-observation, conformance-review, defect-verification, security-threat-model, accessibility, secure-coding) does not include `performance-engineering` — `record_path_role()` returns `None` for it and the script exits 0 before ever calling `role_spec_shape.reference_resolution_check`.

### Expected
Either the newly-authored reference_resolution.rule text in performance-engineering.spec.json (and the mirrored architecture.spec.json edit) should not claim an enforced invariant it has no enforcing hook for, or role-spec-reference-guard.sh's scope should be extended to cover the roles that now declare this rule — as written, the rule silently does nothing for performance-engineering/architecture records while looking identical (same JSON shape, same "checked_by": "on-the-record/hooks/role-spec-reference-guard.sh" pointer) to the roles where it is actually enforced.
