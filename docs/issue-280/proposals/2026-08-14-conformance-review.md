files:
- docs/issue-280/reports/conformance-review.md

## Requirement list (from issue #280 acceptance criteria)

1. Every GitHub closing-keyword form (close/closes/closed, fix/fixes/fixed,
   resolve/resolves/resolved) is detected case-insensitively in the
   `--closes-only` autodetect path.
2. A phase-1 PR body containing any of these forms with no approval is
   BLOCKED.
3. Regression tests cover all 9 keyword spellings, case variants, and the
   in-code-fence case.

sampling derivation: full — 3 requirements, small diff (gates/pr_reference.py,
gates/test_closes_gate_ci.py, test_gates.py), entire diff read.
