# Current-state survey — execution-observation of issue #1111

## Scope statement

Observed role: implementation (phase-1 proposal + phase-2 delivery),
issue #1111, on branch `issue-1111/implementation`.

canonical: gh pr view 1113 --json number,state,mergedAt,commits,url (executed this session)
Observed artifacts:
- Phase-1 PR https://github.com/tokenmaxxxer/on-the-record/pull/1113
  (MERGED 2026-08-12T17:44:19Z) — commits `d030539`, `eaa59d5`,
  `e0ccf56`.

canonical: gh pr view 1114 --json number,state,mergedAt,commits,files,reviews (executed this session)
- Phase-2 delivery PR https://github.com/tokenmaxxxer/on-the-record/pull/1114
  (MERGED 2026-08-12T17:53:54Z, closes #1111) — carries the phase-1
  commits plus `73475d0` (build), `12398ac` (implementation record +
  deviation), `8a609f6` (before-landing hunt fold-in). `reviews` came
  back empty — no PR-review Approve, so any approval must be the
  single-account issue-comment path (checked below).
- Its own record: `docs/issue-1111/reports/implementation.md` (as
  landed in PR #1114's diff, read via `gh pr diff 1114`).

canonical: gh issue view 1111 --comments; gh pr diff 1114 (both executed this session)
What was read this session, in order: `gh issue view 1111` (issue body
+ acceptance criteria) and its comments (found the `APPROVE
issue-1111/implementation` comment and the judgment-loop escalation
comments); `gh pr view 1113 --json ...` and `gh pr view 1114 --json
...` (body, commits, files, reviews); the full unified diff of PR
#1114 (`gh pr diff 1114`, 811 lines) covering every changed/added
file: the proposal
(`docs/issue-1111/proposals/2026-08-13-product-capture-ownership.md`),
`docs/issue-1111/reports/consult-log.md`,
`docs/issue-1111/reports/implementation.md`, the two hunt records
(`hunt-product-capture-ownership.md`,
`2026-08-13-hunt-before-landing.md`), `deviation-log.md`, `survey.md`,
`docs/reports/product/priorities.md`, and the four hook/test file
diffs (`on-the-record/hooks/deliverable-guard.sh`,
`on-the-record/hooks/product-capture-stopgate.sh`,
`on-the-record/hooks/test_deliverable_guard.py`,
`on-the-record/hooks/test_product_capture_stopgate.py`). The diff was
read before the record narrative was treated as authoritative — the
scope above is built from the diff's own hunks, not from
`implementation.md`'s framing of itself.

canonical: gh issue view 1111 --json comments; git show origin/main:docs/specs/approvers.md; gh pr view 1114 --json commits (all executed this session)
Approval check (read this session, not asserted): a comment whose
entire body is the exact string `APPROVE issue-1111/implementation` is
authored by `JiwonJung94`. `docs/specs/approvers.md` on `origin/main`
lists `JiwonJung94` and `jjongkwann`. PR #1114's author is also
`JiwonJung94` — single-account mode applies, and the string matches
exactly, so this is a valid human approval.

## Scout skip record

Skipped. Reason: this session's deliverable is fixed by the
`execution-observation` role directive itself — a three-level verdict
(outcome/trajectory/step) against a spec-defined recomputation rule
(`roles/specs/execution-observation.spec.json`) — leaving no open
design/product decision to scout a comparable field for. This is not a
product-shaped build; it is the "spec literally leaves no design
decision open" skip condition.

## Diff-hunk inventory (for step-level citation admissibility)

canonical: gh pr diff 1114 (811-line unified diff, read in full this session)
Hunks actually touched by PR #1114's diff:
- `on-the-record/hooks/deliverable-guard.sh`: header comment block
  (lines ~13-22) and the exemption logic (`EXEMPT_SUFFIXES` tuple,
  `PRODUCT_CAPTURE_ISSUE_RE`, the `if` gate) replacing the single
  `n.endswith("docs/specs/approvers.md")` line.
- `on-the-record/hooks/product-capture-stopgate.sh`: header comments
  documenting the retarget, and the `rel = os.path.join(...)` /
  `product_dir = ...` lines inside the Python heredoc.
- `on-the-record/hooks/test_deliverable_guard.py`: three new test
  functions (`test_product_capture_priorities_write_allowed`,
  `test_product_capture_issue_scoped_write_allowed`,
  `test_product_capture_unrelated_file_denied`).
- `on-the-record/hooks/test_product_capture_stopgate.py`: path-string
  updates inside four existing test functions, plus the added
  `if __name__ == "__main__"` runner block.
- New files (every line is an added hunk): the proposal, consult-log
  entry, `implementation.md`, the two hunt records, `deviation-log.md`,
  `survey.md`, `docs/reports/product/priorities.md`.

Anything outside these hunks (e.g. `harness/fixture-target/scenario.py`,
which the implementation record discusses but which PR #1114's diff
does not touch) is context only, not admissible as step-level evidence
against this PR's own change.
