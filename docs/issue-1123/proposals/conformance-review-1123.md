---
status: proposed
files:
  - docs/issue-1123/reports/conformance-review.md
---

Issue #1123's implementation commit (`14ec8d4f`) landed on `main` with
no conformance-review record yet for that sha; this role was spawned
by `spawn_on_pr.py` to produce one (board condition per the
marketplace conformance-review role spec, issue-521).

Constraints found in phase-1 research (see
`docs/issue-1123/reports/conformance-review/survey.md`): the review
must render a per-requirement verdict, never a holistic quality
judgment or a fix; it must work from the artifact and spec, not the
building session's stated intent; an unlocatable-evidence case is
Unverifiable, never a favorable guess. R001 is the requirement cited
for this review session, though issue #1123's own body states R001 is
not its target — both are recorded as separate verdict rows.

What will be done: write
`docs/issue-1123/reports/conformance-review.md` with one verdict per
issue #1123 requirement (three named requirements + the Acceptance
clause) plus a verdict row for R001, each verdict backed by evidence
reproduced this session (not just re-read from
`docs/issue-1123/reports/implementation.md`'s own claims) — including
one open finding already located in phase-1 research: the regression
guard (`gates/test_consult_json_parse.py`) passes at commit `14ec8d4f`
itself but now fails at current `main` HEAD, root-caused to a later,
unrelated commit (`74e40109`, issue-1313) outside issue #1123's frozen
scope. That finding will be reported, addressed to the owning
issue/role — never fixed here.

Out of scope: fixing the guard regression (belongs to issue-1313's
scope, not this role's write set); re-opening or re-litigating issue
#1123's own implementation, which is already Closed and merged;
touching `spawn.py`, `gates/test_consult_json_parse.py`, or any code
— this role's write set is the record file only.

How it will be verified: the record's verdicts each cite a
canonical/derived source reproduced this session (git worktree checkout
of `14ec8d4f`, direct file reads, and a re-run of the guard both at
that commit and at current HEAD) — not a restatement of the
implementation record's own self-reported pass claim.
