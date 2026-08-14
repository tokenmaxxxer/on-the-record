---
status: proposed
files:
  - docs/issue-1013/reports/conformance-review.md
---

Subject: issue-1013

## Request

Run a conformance review of the merged issue-1013 implementation
(mergeCommit `9afe1712974a82351c0b0b3f183370578de10765`, PR #1028)
against its target spec
(`docs/issue-1013/proposals/session-ownership-scoping.md`), producing a
per-requirement verdict record. The board condition for this role fired
because that commit landed with no prior conformance-review record for
it — see
`docs/issue-1013/reports/conformance-review/2026-08-14-survey.md` for the
board-condition citation and the requirement list this proposal builds
on (items 1-9).

## Constraints

- Verdicts are Present|Surface|Absent|Incorrect|Unverifiable per
  requirement, never a holistic code-quality judgment, never a fix.
- Evidence for each verdict comes from reading the merged diff and, where
  a requirement claims a behavior, running the relevant test(s) live —
  not from the implementation record's own narration of what it did.
- Findings, if any, are handed off to the owning role (implementation);
  this role never edits spawn.py or tests/test_spawn.py to fix a gap.

## What will be done

For each of the 9 requirements in the survey's requirement list, read the
corresponding code in
`git show 9afe1712974a82351c0b0b3f183370578de10765 -- spawn.py
tests/test_spawn.py` and, for the two acceptance-test requirements (7,
9), run `python3 -m pytest tests/test_spawn.py -k
RosterOwnershipScoping -q` live. Record one verdict line per requirement
in `docs/issue-1013/reports/conformance-review.md`, plus any open finding
(e.g. the design's own noted gap that `ORCHESTRATOR_SESSION_ID` is never
set anywhere in the repository, making the scoping degenerate to
self-matching on every real invocation today — carried as a known,
explicitly out-of-scope limitation in the target spec itself, not a
build defect).

## Out of scope

- Building or fixing anything in spawn.py/tests/test_spawn.py.
- Re-litigating the target spec's own design choices (e.g. whether
  `_roster_own`'s empty-state `None == None` matching is the right
  design) — conformance review checks built-vs-specified, not
  specified-vs-ideal.

## How this will be known to work

`docs/issue-1013/reports/conformance-review.md` carries one verdict per
requirement (1-9), each citing the exact file:line or command output it
is based on, plus the standard record fields (what was done, why,
upstream basis, kind/loop_state, open findings).

## Accumulation

Not accumulation-cost-shaped: a single-pass review of one merged commit
against one spec, no repeated/growing state.

## What did not work

None.
