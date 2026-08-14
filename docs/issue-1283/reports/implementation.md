---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: bugfix
breaking: false
canonical: pytest tests/test_spawn.py::RosterReconcileUnreported -q (executed this session, see Acceptance verification)
verdict: pass
loop_state: landed
---

## What was done

Per docs/issue-1283/proposals/reconcile-unreported-regression.md, judged
the defect an observation-loss regression (not a test defect) and
implemented the code-side fix: removed the `Path(work).exists()`
early-skip branch in `spawn.py::_roster_reconcile_unreported()`
(spawn.py:2911-2916 before this change) so the function always proceeds
to `session_end_verdict()` and the `[watch]`-comment-marker check
regardless of whether the workspace directory still exists on disk. Left
the two pre-existing `RosterReconcileUnreported` tests
(`test_lists_ended_session_with_open_pr_before_ack_and_empties_after`,
`test_filters_by_issue`) unmodified, and added
`test_lists_normal_session_after_workspace_cleaned` (named regression
test for the cleaned-before-report case) and
`test_empty_workspace_index_reports_nothing` (empty-index acceptance
case) to `tests/test_spawn.py`.

canonical: warrant-hunter transcript this session (agent id
a6a1499ca6e3df0cf, see Hunt below)

A warrant-hunter pass found that this fix, by removing the early skip,
newly exposed an uncaught `FileNotFoundError`: `_repo_slug()` runs
`subprocess.run(..., cwd=root, ...)`, and `cwd` being a nonexistent path
crashes the whole reconcile sweep instead of just that one stale entry.

canonical: spawn.py:1101-1122 (edited this session, see diff)

Fixed `_repo_slug()` to catch `FileNotFoundError` around that
`subprocess.run` call and treat it the same as a failed slug lookup
(`None`, cached).

canonical: spawn.py:2929-2932 (read this session)

That routes a missing `work` directory through the existing
"확인 못 함은 통과가 아니다" (#287) fail-closed branch instead of
crashing.

canonical: `python3 -m pytest tests/test_spawn.py::RosterReconcileUnreported::test_lists_normal_session_after_workspace_cleaned_no_stub -q` (executed this session)

Added `test_lists_normal_session_after_workspace_cleaned_no_stub`, which
exercises the real `_repo_slug` -> `subprocess.run(cwd=work)` path (no
`_issue_comments` stub) against a nonexistent `work`, to guard this — see
Acceptance verification below for the passing run.

## Why

canonical: docs/issue-1283/reports/implementation/survey.md (written this
session)

The survey's git-history read shows the existence check was added in
`b62e57dc` (issue #1124) *after* the `RosterReconcileUnreported` tests
already existed (`c4bb24b0`, issue #534), and that commit's own adjacent
comment states its intended purpose as tolerating an already-`clean`ed
workspace, not silently dropping the entry — contradicting the `continue`
it introduced. `session_end_verdict()` and `_issue_comments()` already
tolerate a nonexistent `work` path (except for the `_repo_slug()`
subprocess-cwd crash fixed above), so the skip added no real safety and
only reopened the no-silent-observation-loss window the issue names.

## Upstream

Basis: docs/issue-1283/proposals/reconcile-unreported-regression.md

## What did not work

Expected the removal of the existence-skip alone to be sufficient (per
the proposal's "no further guarding is needed" claim, based on reading
`session_end_verdict`/`_issue_comments` at survey time).

canonical: warrant-hunter transcript this session (agent id
a6a1499ca6e3df0cf, see Hunt below)

Actual: the warrant-hunter found `_repo_slug()`'s
`subprocess.run(cwd=root, ...)` raises `FileNotFoundError` uncaught when
`root` doesn't exist, crashing the sweep — the survey's read of
`_issue_comments` missed that it transitively calls `_repo_slug()`, which
is where the actual crash site is. Fixed at spawn.py:1101-1122 (see
above).

## Acceptance verification

canonical: `python3 -m pytest tests/test_spawn.py::RosterReconcileUnreported -q` (executed this session)

acceptance: python3 -m pytest tests/test_spawn.py::RosterReconcileUnreported -q — result: pass
```
.......                                                                  [100%]
7 passed in 0.15s
```

canonical: `python3 -m pytest tests/test_spawn.py -k roster -q` (executed this session)

acceptance: python3 -m pytest tests/test_spawn.py -k roster -q — result: pass
```
........................................                                 [100%]
40 passed, 460 deselected in 75.30s (0:01:15)
```

## Open findings

canonical: warrant-hunter transcript this session (agent id
a6a1499ca6e3df0cf, see closed_checks below)

None open — the one finding the warrant-hunter returned was fixed and
verified in this same session (see closed_checks below).

## Hunt

Dispatched warrant:warrant-hunter against the diff (existence-skip
removal in `_roster_reconcile_unreported`) before phase-2 completion.

closed_checks:
- warrant-hunt: `_roster_reconcile_unreported` crash-on-missing-workspace
  via `_repo_slug`'s `subprocess.run(cwd=root)` FileNotFoundError —
  code_under_review: spawn.py, tests/test_spawn.py — resolved by
  wrapping that `subprocess.run` call in `_repo_slug()` with
  `try/except FileNotFoundError`, verified by
  `test_lists_normal_session_after_workspace_cleaned_no_stub` and the
  full acceptance runs above.
