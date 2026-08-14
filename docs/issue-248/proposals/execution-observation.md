status: proposed
files:
  - docs/issue-248/reports/execution-observation/fixture-drive.md
  - docs/issue-248/reports/execution-observation.md

## Request

Issue #248's implementation (PR #252, merge commit 3c27dc94) landed on `main` but has no
execution-observation record yet. Independently re-drive the shipped, unmodified
`gates/flows.py:flows_payload()` against a disposable temp-dir fixture reproducing the issue's
own cited example (issue-27: one board-recorded but already-merged role, two open PRs with no
board record) and confirm `flows[].prs` is populated and matches `decision_queue`'s PR set for
the same issue. Also re-run the shipped regression suite PR #252 added
(`tests/test_spawn.py::FlowsPayload`).

## Verdict levels this step checks, and against what evidence

- outcome — does the shipped `gates/flows.py` (as merged in PR #252, present unchanged at HEAD
  bc53410e) satisfy issue #248's acceptance criteria (flows[].prs populated for issue-27-shaped
  subjects; no mismatch with decision_queue for the same PR), checked against a fresh fixture
  drive run this session, not against PR #252's own implementation.md claims.
- trajectory — was #248's phase-1 (survey/proposal, commit c0daeab1) to phase-2
  (implementation, commit 892cfeea) path sound, checked against PR #252's own commit history and
  the `APPROVE issue-248/implementation` issue comment already on record.
- step — which specific artifact, if any, is deficient, checked per-subject against the fixture
  drive's actual payload output.

## Constraints

- Disposable temp-dir fixture only, built via `tempfile.TemporaryDirectory()` — never this
  repo's own board.
- No edits to `gates/flows.py`, `spawn.py`, or `docs/specs/flows-schema.md` — independence per
  this role's directive; a confirmed deficiency goes into this role's own record as a finding,
  not a fix applied here.
- Any acceptance criterion unmet -> the record recommends remediation rather than asserting
  closure was correct.
