# Deviation log — issue-2298 (conformance-review role)

2026-08-25T13:35:00Z inline conformance-review(issue-2298): first two
Write attempts at docs/issue-2298/reports/conformance-review.md were
refused by `on-the-record/hooks/pretooluse-dispatcher.sh`'s
record-claim-guard (issues #333/#793/#870/#330/#791) — count/outcome/
defect claims lacked an adjacent `derived:`/`canonical:` execution tag,
and bare mentions of `pr-2329-review:docs/issue-2298/reports/performance-engineering.md`
/ `pr-2329-review:.../deviation-log.md` were flagged as reach-broken
references (untracked on this branch until PR #2329 merges). Restructured
every claim in the record to carry an inline `derived: <command>` +
code-fence of the actual output, or a
`canonical: pr-2329-review:<path>:<line>` sha-qualified citation, before
the write was accepted — the substance of the review (10 requirement
verdicts, one Surface finding on R7) was unchanged, only the citation
shape.

2026-08-25T13:45:00Z inline conformance-review(issue-2298): initial
judgment was to omit a `Closes #2298` trailer from this PR's body, since
this delivery is a review record, not the feature fix (issue #2298's
actual closing PR is #2329) and merging a review PR auto-closing the
issue seemed like the wrong side-effect. `gh pr create` was refused twice
by `pr-preflight` (`on-the-record/hooks/pretooluse-dispatcher.sh`) citing
`CORE_BUILD_NOW=1` treating this session as phase-2-equivalent, which
mechanically requires `Closes #2298` (or Fixes/Resolves) in the PR body
for any build-now single-phase delivery PR, and separately required the
body's first paragraph to be prose rather than trailer-only. Complied:
added a lead prose paragraph and a `Closes #2298` trailer at the end of
the body — deferring to the gate's uniform build-now convention over this
session's own semantic read of what "closes" should mean for a review-
only artifact. canonical: `gh pr create` refusal output, this session
(both attempts), and the succeeding `gh pr create --body-file
/tmp/pr2298-body.md` call that produced
https://github.com/tokenmaxxxer/on-the-record/pull/2341.
