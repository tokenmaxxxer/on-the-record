# Deviation log — issue-2286 (execution-observation role)

- 2026-08-25T08:58:17Z | inline | execution-observation(issue-2286): this
  session's review verdict is `result: failed` (`docs/issue-2286/reports/execution-observation.md`
  — tokenmaxxxer-core PR #312 as opened carries none of the 5 new
  `test_board_gate.py` cases the implementation record's own Evidence
  section cites). Initial plan was to reference #2286 without closing
  it, on the reasoning that a failed review should not close its own
  tracking issue. The PR-open gate (`pr-preflight`, CORE_BUILD_NOW=1
  path) refused the PR body without a `Closes #2286` trailer, treating
  this build-now single-phase delivery as phase-2-equivalent regardless
  of the review's own verdict — the deliverable for issue #2286 was
  producing this record, not a passing verdict. Complied: added
  `Closes #2286` to the PR #2391 body, with the failed verdict and the
  concrete open finding (a follow-up test commit needed on PR #312)
  stated plainly in the same body. canonical: PR #2391's body and
  `docs/issue-2286/reports/execution-observation.md`'s own Open
  findings section, both written this session — the failure is stated
  directly in both, not obscured by the closed issue. Stayed inside
  this role's frozen write set — only
  `docs/issue-2286/reports/execution-observation.md` and this log
  touched.
