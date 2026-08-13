---
status: approved
files:
  - spawn.py
  - tests/test_spawn.py
---

## Request

`reconcile --unreported` silently drops workspace-index entries whose
directory no longer exists on disk, instead of still checking whether the
session ended normally and unreported. Two pre-existing tests in
`RosterReconcileUnreported` fail on unmodified main because of this.
Judge whether the tests or the code are wrong, then fix the chosen side.

## Constraints

- `tests/test_spawn.py::RosterReconcileUnreported` must all pass.
- `pytest -k roster` must show no new failures.
- The empty-workspace-index case (reconcile reports nothing, exits clean)
  must be covered.
- If judged a regression, a named regression test for the
  cleaned-before-report case is required.

## Rationale

Two candidate fixes were considered, per docs/issue-1283/reports/implementation/survey.md:

1. **Test defect** — update the two failing tests' stubs to create real
   directories at their `work` paths, leaving `_roster_reconcile_unreported`'s
   existence-skip in place. Rejected: the survey's git-history read shows
   the existence check (`b62e57dc`, issue #1124) was added *after* these
   tests (`c4bb24b0`, issue #534) already existed and passed, and that
   commit's own adjacent comment states its purpose as tolerating an
   already-cleaned workspace, not dropping the entry — the `continue`
   contradicts its own comment. Rewriting the tests to match the
   contradicted behavior would also reopen the exact silent-loss window
   the issue names: a session that ends and is cleaned before its
   `[watch]` comment posts would never be listed again, forever.
2. **Observation-loss regression (chosen)** — drop the
   `Path(work).exists()` skip so `_roster_reconcile_unreported()` always
   proceeds to `session_end_verdict()` and the comment-marker check, keep
   the pre-existing tests unmodified, and add a named regression test.

Reproduced failure on main this session:
```
$ python3 -m pytest tests/test_spawn.py::RosterReconcileUnreported -q
..FF.
=================================== FAILURES ===================================
...
FAILED tests/test_spawn.py::RosterReconcileUnreported::test_lists_ended_session_with_open_pr_before_ack_and_empties_after
FAILED tests/test_spawn.py::RosterReconcileUnreported::test_filters_by_issue
2 failed, 3 passed in 0.42s
```

## What will be done

- In `spawn.py::_roster_reconcile_unreported()`, remove the
  `Path(work).exists()` early-skip branch (spawn.py:2911-2916) so the
  function always calls `session_end_verdict()` and checks the comment
  marker regardless of whether the workspace directory still exists.
  `session_end_verdict()` and `_issue_comments()` already tolerate a
  missing `work` path (per survey), so no further guarding is needed.
- In `tests/test_spawn.py`, leave the two pre-existing
  `RosterReconcileUnreported` tests unchanged, add one named regression
  test asserting a `session_end_verdict == "normal"` entry with a
  nonexistent `work` path and no `[watch]` comment is still reported, and
  add one test covering the empty workspace-index case (`{}` -> return 0,
  no exception).

## Accumulation

Not accumulation-shaped: this removes one conditional branch from a
single existing function and adds two isolated test methods to an
existing test class — no shared helper, no repeated-file pattern, and no
per-N-occurrences growth. Neither `_roster_reconcile_unreported()` nor
the new tests introduce a new `subprocess`/`gh` call site; the existing
`_issue_comments()` call already there is unchanged.

## Out of scope

- Any change to `session_end_verdict()` or `_issue_comments()` themselves.
- Any change to `roster_reconcile()`'s dispatch logic or other reconcile
  modes (`--issue` filtering already covered by existing tests).
- Archival/cleanup behavior in `clean` (issue #1124's own scope).

## How you'll know it worked

```
python3 -m pytest tests/test_spawn.py::RosterReconcileUnreported -q
python3 -m pytest tests/test_spawn.py -k "roster" -q
```
Both green, no new failures.
