---
status: proposed
files:
  - docs/issue-1510/reports/conformance-review.md
---

## Intent
Check whether PR #1513 (issue-1510/implementation) actually matches
issue #1510's stated Requirements and Acceptance items — the
poll-heartbeat cadence widen from 60s to 120s, its two scaled
derived constants, and the two new regression tests — rather than
holistically judging the code's quality.

## Constraints
- Per-requirement verdict only: Present, Surface, Absent, Incorrect, or
  Unverifiable for each of issue #1510's 4 Requirements and 3
  Acceptance items — never a bundled pass/fail.
- No fix: any gap found is reported, addressed_to the implementation
  role, never patched by this session.
- PR #1513 is still OPEN (not yet merged to main); this review targets
  the PR's diff directly, per the spawn-on-PR trigger that opened this
  session, rather than waiting for a merge that has not happened.

## What will be done
Phase 2 (after approval) will write
docs/issue-1510/reports/conformance-review.md: one `### Requirement:`
section per item in the requirement list already extracted in
docs/issue-1510/reports/conformance-review/survey.md, each citing a
live re-run of the two named test files
(tests/test_heartbeat_cadence.py, tests/test_spawn.py::NoConcurrencyCap)
and a live re-check of the three constants' file:line values and the
GC assert, checked out transiently from issue-1510/implementation and
reverted afterward — not trusted from the implementation record's own
prose.

## Out of scope
- Reviewing docs/issue-1510/reports/implementation.md or
  docs/issue-1510/reports/implementation/survey.md's own prose quality
  — only the code and tests they describe are checked against the
  issue's Requirements/Acceptance items.
- Any edit to on-the-record/monitors/poll-heartbeat.sh,
  on-the-record/hooks/directive.sh, spawn.py, or either test file —
  this role never patches the target artifact.

## How you'll know it worked
docs/issue-1510/reports/conformance-review.md exists with one verdict
per Requirement/Acceptance item, each backed by a live command
citation (pytest run or direct constant/assert re-check) rather than a
restated claim from the implementation record.
