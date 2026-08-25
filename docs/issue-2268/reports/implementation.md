---
issue: 2268
role: implementation
loop_state: landed
upstream:
  - path: gates/merge_gate.py
    sha: 9e2e2382ada5f1da915c015e8288fb1bc0f20cd0
code_under_review:
  - gates/merge_gate.py
  - gates/test_merge_gate.py
type: fix
breaking: none
verdict: pass
---

# issue-2268 — implementation record

## What was done

canonical: gates/merge_gate.py:29-31 (this commit) — `_RESULT_HEADER` now
reads
`r"^## Acceptance check-runner result:\s*(?:(\d+)/(\d+)\s*passed|no checks declared)"`,
matching both the numeric header (unchanged capture groups 1/2) and the
no-checks header `check_runner.NO_CHECKS_MARKER` produces
(`gates/check_runner.py:36`). Before this change the regex only matched the
numeric shape, so `latest_check_runner_comment()` (`gates/merge_gate.py:49`,
the only function that scans PR comments) could never find a no-checks
comment, and `parse_check_runner_result`'s `NO_CHECKS_MARKER`-first branch
(`gates/merge_gate.py:41-42`, added in #2231) was unreachable through that
path.

`parse_check_runner_result()` itself needed no change — it already checks
`NO_CHECKS_MARKER in comment_body` before consulting `_RESULT_HEADER`
(`gates/merge_gate.py:41`), so its existing precedence (no-checks before
numeric) is untouched; only the finder regex was widened.

Added two tests to `gates/test_merge_gate.py` (after
`t_merge_gate_evaluate_refuses_no_checks_as_a_pass`), both driving the real
chain `latest_check_runner_comment` → `parse_check_runner_result` →
`evaluate()` through a mocked `subprocess.run` (the `gh pr view` call), not
by monkeypatching `latest_check_runner_comment` directly — the issue names
that pattern as exactly what let the original gap go undetected:
- `t_finder_reaches_no_checks_branch_through_evaluate` — a PR comment list
  containing a no-checks comment is found by the finder and reaches
  `evaluate()`'s no-checks-not-a-pass branch.
- `t_finder_empty_state_still_reports_comment_missing` — a PR comment list
  with neither header shape still yields `None` from the finder and
  comment-not-found from `evaluate()` (the issue's stated empty-state
  acceptance criterion).

acceptance: python3 -m pytest gates/test_merge_gate.py -q — result:
```
.........................                                                [100%]
25 passed in 1.18s
```

acceptance: python3 gates/merge_gate.py 2228 issue-2211 (before this commit, via `git stash`) — result:
```
거절: PR #2228 (issue-2211)
  - check-runner 코멘트를 찾을 수 없다
```

acceptance: python3 gates/merge_gate.py 2228 issue-2211 (after this commit) — result:
```
거절: PR #2228 (issue-2211)
  - check-runner: 이슈의 Acceptance 절에 실행가능한 검사가 없다(no checks declared) — 통과로 취급하지 않는다
```

The before/after pair shows the finder now reaches the no-checks branch
(reason text changed from comment-not-found to the no-checks refusal) while
PR #2228 remains refused either way — the no-checks branch is not treated as
a pass, matching the issue's acceptance note.

## Why

The issue traces a concrete live failure: PR #2228 carries the no-checks
comment but `merge_gate.py` reported comment-not-found because the finder
regex was never widened alongside the parser in #2231/#2244. The fix is the
minimal one the issue's Ask section names: widen the finder regex only, keep
`parse_check_runner_result`'s existing precedence, and add a
finder-through-evaluate test (not a parser-only test) so this exact gap
class — parser tested, finder not exercised via the real path — cannot
recur silently. Rejected alternative: rewriting `latest_check_runner_comment`
to call `parse_check_runner_result` directly instead of its own regex scan —
larger surface change than the issue asks for, and would still need a
regex/marker check to pick the *latest* matching comment out of the full
list, so it does not remove the widening requirement, only relocates it.

## What did not work

None.

## Upstream basis

canonical: gates/merge_gate.py:29-30@9e2e2382ada5f1da915c015e8288fb1bc0f20cd0
— the commit (issue #2231, PR #2244) that added `NO_CHECKS_MARKER` handling
to `parse_check_runner_result` without widening `_RESULT_HEADER`, which is
the gap issue #2268 reports and this commit closes.

## Open findings

None.

## Next steps

None — record is terminal (`loop_state: landed`).
