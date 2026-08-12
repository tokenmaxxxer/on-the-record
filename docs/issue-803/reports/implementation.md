---
code_under_review:
  - on-the-record/hooks/test_deviation_log_guard.py
type: test
breaking: false
canonical: pytest run of on-the-record/hooks/test_deviation_log_guard.py this session, full output in the `## Evidence` section below — 7 passed, 0 skipped, 0 failed.
verdict: pass
loop_state: landed
---

Subject: issue-803

## Summary of work

Core delivery (deviation-log-guard.sh, its hooks.json registration, the
directive.sh paragraph, docs/handbooks/deviation-loop.md) already landed
on main via #958 (commit 273be52). This supplement fills the one gap
left in that delivery: automated test coverage for
`on-the-record/hooks/deviation-log-guard.sh`, mirroring the existing
`test_product_capture_stopgate.py` shape.

Added `on-the-record/hooks/test_deviation_log_guard.py`.
derived: `git ls-files on-the-record/hooks/test_deviation_log_guard.py`
canonical: file listed in git's index, added this session (see
`## Evidence` below for the pytest collection count).

The test file covers: a traceless deviation (recognized-deviation
marker in the transcript, no matching deviation-log append) is
blocked, and a logged deviation (matching append committed) exits
clean with no output.
canonical: pytest run in `## Evidence` below, this session's own live
run — `t_traceless_deviation_is_blocked` and `t_logged_deviation_passes`
both PASSED.

canonical: `git log --oneline -1` output in `## Evidence` below, this
session's own command — HEAD is a merge commit on this branch.
Also merged origin/main into this branch, to build against the
already-landed #958 code instead of this branch's own now-superseded
copy of the same files.

## Evidence

derived: `python3 -m pytest on-the-record/hooks/test_deviation_log_guard.py -v`
```
on-the-record/hooks/test_deviation_log_guard.py::t_no_marker_is_silent PASSED [ 14%]
on-the-record/hooks/test_deviation_log_guard.py::t_traceless_deviation_is_blocked PASSED [ 28%]
on-the-record/hooks/test_deviation_log_guard.py::t_logged_deviation_passes PASSED [ 42%]
on-the-record/hooks/test_deviation_log_guard.py::t_claude_role_set_is_noop PASSED [ 57%]
on-the-record/hooks/test_deviation_log_guard.py::t_orchestrate_off_is_noop PASSED [ 71%]
on-the-record/hooks/test_deviation_log_guard.py::t_missing_transcript_path_fails_closed_silently PASSED [ 85%]
on-the-record/hooks/test_deviation_log_guard.py::t_off_issue_branch_uses_docs_reports_path PASSED [100%]
============================== 7 passed in 0.44s ===============================
```
canonical: pytest run above, executed live against the current working
tree this session — PASS, 7 passed, 0 skipped, 0 failed.

derived: `git log --oneline -1`
```
35e5d07 merge origin/main into issue-803/implementation
```
canonical: git log output above, this session's own command — HEAD is
a merge commit on this branch, not a detached ref.

## Why

The approved proposal's own "How you'll know it worked" section
(docs/issue-803/proposals/2026-08-12-implementation-deviation-loop.md)
only required a manual one-off confirmation run against synthetic
fixtures, which the original delivery did. This session was opened
specifically to supply the missing automated regression coverage so the
no-traceless-deviation invariant stays enforced under future edits to
the guard, matching the test-file convention every other Stop-hook guard
in this directory already follows (e.g. `test_product_capture_stopgate.py`).

## Upstream basis

docs/issue-803/proposals/2026-08-12-implementation-deviation-loop.md
(approved, delivered in #958 / commit 273be52).

## Rationale for deviations

The approved proposal's write set did not list a test file (its
acceptance criterion was a manual confirmation run only). This session
was opened specifically to add automated coverage as a follow-up
supplement to the already-landed #958 delivery, so the write set here
is `on-the-record/hooks/test_deviation_log_guard.py` plus this record —
an intentional, requested extension of the original write set, not an
unplanned mid-build widening.

canonical: the refusal text this session received from the tool
harness, "cannot resolve the current git branch for a board write",
raised during a detached-HEAD interactive rebase step.
Separately, `git rebase origin/main` on this branch was refused by
`board-gate.sh`'s branch-resolution check mid-rebase.
Worked around by using `git merge origin/main` instead, which keeps the
branch ref attached throughout (canonical: `git log --oneline -1`
output in `## Evidence` above shows a merge commit as HEAD, not a
detached state). This is a git-operation swap, not a change to any
file in the write set.

## What did not work

- Ran `git rebase origin/main`; it hit a content conflict on
  `docs/issue-803/proposals/2026-08-12-implementation-deviation-loop.md`
  (the same file, added on both sides with different bodies), and the
  follow-up `git rebase --continue` was refused by `board-gate.sh`
  because interactive rebase leaves `HEAD` detached between steps
  (canonical: refusal text quoted in ## Rationale for deviations
  above). Switched to `git merge origin/main` instead, which does not
  detach `HEAD` mid-operation.

## Open findings

None.
