---
status: proposed
files:
  - docs/issue-1080/reports/conformance-review.md
---

## Intent

Run a conformance review of the implementation commit landed on
`issue-1080/implementation` (sha `bd407dfb`), against the four
requirements extracted from issue #1080's body in
[survey.md](../reports/conformance-review/survey.md), and record one
verdict per requirement (Present|Surface|Absent|Incorrect|Unverifiable).

## Constraints

- Subject is issue-1080, requirement is northpole req#6. Board condition
  (issue-521): an implementation commit landed and no conformance-review
  record exists yet for it — met.
- `code_under_review` in the record must be a file list, not a commit sha.
- No design decision is open (scout-directive skip, recorded in the
  survey) — this is a straight fidelity check against four enumerated
  acceptance lines, not a proposal round with alternatives to weigh.

## What will be done (phase 2, on Approve)

For each of R1-R4 in the survey, read the diff at
`git diff $(git merge-base origin/main origin/issue-1080/implementation) origin/issue-1080/implementation -- spawn.py gates/requirement_linkage.py gates/test_requirement_drift.py`
and `gates/test_requirement_drift.py`'s test bodies directly (deliberately
without the implementation role's own stated intent in
`docs/issue-1080/reports/implementation.md`), assign a verdict per
requirement, and write
`docs/issue-1080/reports/conformance-review.md` with:
- `code_under_review:` as a `- path` list (spawn.py, gates/requirement_linkage.py, gates/test_requirement_drift.py)
- one verdict per R1-R4, each citing the specific line(s) it is based on
- any finding addressed back to the implementation role, never fixed here

## Out of scope

- No editing of `spawn.py`, `gates/requirement_linkage.py`, or
  `gates/test_requirement_drift.py` — findings are handed off, not fixed.
- No re-judging issue #1080 itself (already closed) or its northpole req#6
  linkage — only whether the landed commit matches the issue's stated
  Fix/Acceptance.

## How you will know it worked

`docs/issue-1080/reports/conformance-review.md` exists with a verdict for
each of R1-R4, `code_under_review` is a file list, and the record carries
the required fields (what was done, why, upstream basis, kind:,
loop_state:, open findings) per the role-handoff contract.
