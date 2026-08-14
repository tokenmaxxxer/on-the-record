---
code_under_review:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
type: fix
breaking: false
canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -v (this turn) — 15 passed
verdict: pass
loop_state: landed
---

# Implementation record — issue #1310

## What was done

canonical: on-the-record/hooks/pr-preflight.sh (this session's edit)

Added `_MACHINE_LOGIN_RE`/`_MACHINE_BODY_RE`/`_is_machine_comment()` to
`hooks/pr-preflight.sh`'s embedded Python (issue #1177 amendments-reconciled
block) and changed the newest-comment scan to skip machine comments, so the
block only considers the newest operator comment newer than session spawn.

canonical: on-the-record/hooks/test_pr_preflight.py (this session's edit)

Added three unit tests covering the three Acceptance cases named in the
issue: a machine-comment stream, an operator comment mixed in, and the
empty-comment state.

## Why

canonical: docs/issue-1310/proposals/machine-comment-cursor.md (this
session's Read of that file)

requirement: northpole req#1 (specialist delegation must be able to
finish deliveries) — pr-preflight was starving role sessions on busy
issues (watchdog/consult-trace comments landing every 30-60s), stranding
verified commits on pushed branches.

## Upstream

canonical: docs/issue-1310/proposals/machine-comment-cursor.md (phase-1,
merged PR #1311, this session's Read of that file)

basis: docs/issue-1310/proposals/machine-comment-cursor.md

## What will be done vs done

- [x] `_is_machine_comment()` author-pattern OR text-pattern detection
- [x] machine comments excluded from the amendments-reconciled block
- [x] operator comments keep current blocking + mandatory re-read/amendments-reconciled cursor
- [x] the three named unit-test cases from the issue's Acceptance section

canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -v (this turn) — 15 passed

Ran the test suite this turn; transcript below.

```
hooks/test_pr_preflight.py::test_hook_allows_pr_when_only_machine_comments_post_spawn PASSED
hooks/test_pr_preflight.py::test_hook_denies_pr_when_operator_comment_among_machine_comments PASSED
hooks/test_pr_preflight.py::test_hook_allows_pr_when_no_comments_at_all_1310 PASSED
hooks/test_pr_preflight.py::test_hook_denies_pr_when_post_spawn_comment_unreconciled PASSED
hooks/test_pr_preflight.py::test_hook_allows_pr_when_post_spawn_comment_reconciled PASSED
hooks/test_pr_preflight.py::test_hook_allows_pr_when_no_post_spawn_comments PASSED
hooks/test_pr_preflight.py::test_hook_allows_pr_when_no_comments_at_all PASSED
hooks/test_pr_preflight.py::test_hook_allows_pr_when_no_events_file PASSED
============================== 15 passed in 1.38s ==============================
```

## What did not work

None.

## Open findings

None.
