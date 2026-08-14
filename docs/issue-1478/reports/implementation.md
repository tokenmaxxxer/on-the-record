---
code_under_review:
  - on-the-record/hooks/test_pr_base_guard_hook.py
type: fix
breaking: false
# canonical: ran python3 -m pytest --collect-only -q and python3 -m pytest tests/test_pr_base_guard.py on-the-record/hooks/test_pr_base_guard_hook.py -v live this session, both PASS (full output pasted below under "Verification")
verdict: pass
loop_state: landed
---

# issue-1478: dedupe test_pr_base_guard.py basename

Pure bugfix (rename only, no design decision) — scout/proposal skipped per
the mandatory skip condition for pure bugfixes.

## What was done

Renamed the hook-side test file (previously
on-the-record/hooks/test_pr_base_guard.py, now on-the-record/hooks with
suffix _hook.py) via git mv, content unchanged, so its basename no longer
collides with tests/test_pr_base_guard.py during whole-repo pytest
collection.

## Why

PR #1467 (issue #1461) added two test files with the identical basename
(test_pr_base_guard.py) in different directories with no __init__.py
package separation. pytest's rootdir-relative import mechanism refuses
this with "import file mismatch," which was blocking whole-suite
collection on main before any test could run.

## Upstream / basis

docs/issue-1461/proposals/2026-08-14-pr-base-guard.md (the PR that
introduced the duplicate).

## Verification

canonical: ran `python3 -m pytest --collect-only -q` live this session
```
1896 tests collected in 1.89s
```

canonical: ran `python3 -m pytest tests/test_pr_base_guard.py on-the-record/hooks/test_pr_base_guard_hook.py -v` live this session
```
tests/test_pr_base_guard.py::test_rejects_nonmain_base PASSED
tests/test_pr_base_guard.py::test_allows_default_base PASSED
tests/test_pr_base_guard.py::test_allows_no_base_flag PASSED
tests/test_pr_base_guard.py::test_fail_closed_on_unknown_default PASSED
tests/test_pr_base_guard.py::test_allows_alternate_base_named_in_issue_body PASSED
tests/test_pr_base_guard.py::test_rejects_rest_pulls_create_nonmain_base PASSED
tests/test_pr_base_guard.py::test_ignores_non_role_workspace_branch PASSED
on-the-record/hooks/test_pr_base_guard_hook.py::test_rejects_nonmain_base PASSED
on-the-record/hooks/test_pr_base_guard_hook.py::test_allows_default_base PASSED
on-the-record/hooks/test_pr_base_guard_hook.py::test_allows_no_base_flag PASSED
on-the-record/hooks/test_pr_base_guard_hook.py::test_fail_closed_on_unknown_default PASSED
on-the-record/hooks/test_pr_base_guard_hook.py::test_allows_alternate_base_named_in_issue_body PASSED
on-the-record/hooks/test_pr_base_guard_hook.py::test_rejects_rest_pulls_create_nonmain_base PASSED
on-the-record/hooks/test_pr_base_guard_hook.py::test_ignores_non_role_workspace_branch PASSED

14 passed in 1.07s
```

## What did not work

None.

## Open findings

None.
