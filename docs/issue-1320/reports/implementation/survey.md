Subject: issue-1320

## Scout skip record

Skip condition: spec leaves no design decision open (scout-directive skip
condition 2). Issue #1320 fixes exact thresholds (rate-limit remaining <
500), an exact output line format (`[watchdog] board-sweep: 미집계
(rate-limit, remaining=<n>)`), and names the exact call sites to remove
(line numbers in `gates/closure_sweep.py` cited in the issue body).
Nothing here is a "which approach" choice — scouting other watchdog
designs would not change what gets built. Scouting skipped.

## Current-state survey

`gates/closure_sweep.py` (391 lines) already has bulk-list helpers:
- `_pr_index_all(root)` — one `gh pr list --state all --json
  number,headRefName,state,body --limit 1000` call, returns `(index, ok)`.
  Truncation (`len(data) >= 1000`) returns `(None, True)`.
- `issue_state_index_all(root)` — one `gh issue list --state all --json
  number,state --limit 1000` call, same truncation contract.

`find_violations()` in `gates/closure_sweep.py` currently **falls back to
per-item calls** when these bulk indices are unavailable or truncated:
- `_issue_view(root, issue)` (function defined in `gates/closure_sweep.py`)
  — `gh issue view <n> --json state` — called per-subject when
  `issue_states` doesn't already contain the issue.
- `spawn._pr_for_branch` + `_pr_view_state_body(root, pr)` (function
  defined in `gates/closure_sweep.py`) — `gh pr view <n> --json
  state,body` — called per-branch when `_pr_index_all` returned `(None,
  True)` (truncated).

canonical: gates/closure_sweep.py (Read tool, this session, full file) — this fallback is the O(board-size) gh-call path; the issue body's own log excerpt ("확인 불가 (gh 실패) 365건") names the same failure shape.

Requirement 1 prohibits per-item `gh issue view`/`gh pr view` in the
sweep path outright — so the fix is to delete the fallback branches, not
tune them: on truncation or missing-from-index, the subject/role becomes
a `skip` with a reason, same as an outright `gh` failure.
`_issue_view`/`_pr_view_state_body` stay defined (still unit-tested
directly) but `find_violations` stops calling them.

`find_violations` also currently requires the caller to pre-fetch
`issue_states` (`main()` does this before calling it); when called
without it (e.g. bare in tests), it falls back to per-subject
`_issue_view`. To keep `find_violations` itself O(1) regardless of
caller, it now computes the bulk issue-state index internally when
`issue_states is None`, instead of falling back to per-item lookups.

No `gh api rate_limit` call exists anywhere in `gates/closure_sweep.py`
today — requirement 3 (pre-sweep guard) is new code, not a modification.

Dedup of sweep invocations (requirement 2) and the `POLL_INTERVAL_SEC`
call-site wiring live in `spawn.py` — out of scope for this proposal per
the issue's own Ordering note (lands after #1313).

canonical: `gh pr view 1313` (this session, 2026-08-14) — GraphQL could not resolve PR #1313, so #1313 has not merged into main.
