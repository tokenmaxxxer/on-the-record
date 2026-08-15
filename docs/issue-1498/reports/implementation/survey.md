# issue-1498 current-state survey

## #1497 write-set overlap check

canonical: `gh issue view 1497` — state OPEN.
derived: `git show cdc2798b --stat` — PR #1499 ("issue-1497: phase-1
survey + proposal for monitor liveness / quiet ticks") merged to main,
touching only `docs/issue-1497/proposals/monitor-liveness-quiet-ticks.md`
and `docs/issue-1497/reports/implementation/survey.md` — docs-only,
phase-1; no code changed.

#1497's stated write set (on-the-record/monitors/poll-heartbeat.sh,
on-the-record/hooks/directive.sh, on-the-record/hooks/stop-poll-rearm.sh)
still does not intersect #1498's frozen write set (spawn.py,
gates/closure_sweep.py, gates/spawn_on_pr.py, gates/spawn_coverage.py,
tests/test_gh_quota_guard.py, docs/handbooks/) — #1497's phase-1 landed as
docs-only (its phase-2 code has not been approved/built yet), so there is
still nothing to sequence against. Its scope (Monitor tick emission +
stamp files) is a different code path from the watchdog gh-call path this
issue targets, so proceeding now does not create a rebase risk either
direction.

## Existing bulk-read machinery (already landed, #1320/#1459/#682/#743)

canonical: gates/closure_sweep.py (read in full this session).

- `_pr_index_all` (function definition near the top third of the file)
  issues one `gh pr list --state all --json number,headRefName,state,body
  --limit 1000` call and builds a branch->state/body map, replacing
  per-branch `gh pr view` calls (its docstring cites issue #682: 179+179
  calls collapsed to 1).
- `issue_state_index_all` issues one `gh issue list --state all --json
  number,state --limit 1000` call and builds an issue->state map (its
  docstring cites issue #743: a 166-subject per-tick `gh issue view` loop
  collapsed to 1 call).
- `rate_limit_remaining` reads GraphQL `remaining` via `gh api rate_limit`
  (REST, does not itself spend GraphQL points) and the file's own CLI
  `main()` already gates on a module constant `_RATE_LIMIT_GUARD_THRESHOLD`
  before running the sweep.

canonical: gates/spawn_on_pr.py, gates/spawn_coverage.py (read in full this
session).

- `spawn_on_pr._issue_is_open` / `spawn_on_pr.spawn_missing_for_pr` both
  accept a pre-fetched `issue_states` map parameter (no per-subject `gh
  issue view` inside them).
- `spawn_coverage._list_open_issues` issues one bulk `gh issue list` call.

## The actual gap: spawn.py `_board_wide_sweep`

canonical: spawn.py (read in full this session), function `_board_wide_sweep`.

This is the function the watchdog tick calls. It already reuses a single
`issue_state_index_all` result across `spawn_on_pr.spawn_missing_for_pr`
and `closure_sweep.find_violations` — so the steady-state call shape is
already O(pages), not O(N-subjects). But `_board_wide_sweep` never calls
`rate_limit_remaining` — only `closure_sweep.py`'s own standalone CLI
`main()` does that guard; the watchdog imports `closure_sweep` as a module
and calls its functions directly, bypassing `main()` entirely. On a
quota-exhausted tick, `_board_wide_sweep` still issues its ~3 bulk gh
calls (issue-list, pr-list, open-issue-list) every tick with no floor
check and no backoff — each fails, and the per-subject "skip" records that
result (one skip per unresolved subject) are what produces the large skip
counts described in the issue text, not literal per-subject `gh` calls.
Per the operator's req 5, an unattended repeated call *attempt* against an
exhausted quota with no backoff is itself the cost to police, since it is
observably identical in effect to a retry storm until a floor+backoff
guard exists.

No backoff/caching exists anywhere in this call chain: a failed bulk call
is retried at full frequency next tick, forever, with no exponential
delay and no negative-result cache.

## Re-check loop backoff (req 4)

No re-check backoff loop exists in the frozen write set today.
`spawn_on_pr.parked_report` (gates/spawn_on_pr.py) is the closest existing
per-tick re-report path and currently re-reports every tick unconditionally
(no backoff state kept). The issue-1163 conformance-review 28-re-check
shape referenced in the issue text is a role-session polling pattern (not
gate code in the frozen write set) and is out of scope for this issue's
write set; req 4's backoff is implemented as a reusable helper in the
quota-guard module so any per-tick re-check caller (including
`parked_report`) can adopt it.

## Local-first design input (issue comment 1) applied to the survey

`_board_wide_sweep` already separates local-only signals from gh-backed
ones: `closure_sweep.accumulation_trend` and `requirement_drift(root)` are
pure-local (no gh call) and already comply with the comment's local-first
ask.

canonical: spawn.py `_board_wide_sweep` body (read in full this session).
The three gh-calling signals (`spawn_on_pr.spawn_missing_for_pr`,
`closure_sweep.find_violations`, `spawn_coverage._list_open_issues`) fetch
issue/PR open/closed/merged state, matching the comment's "PR/issue state
requires gh" carve-out — this proposal gates *when* those calls fire
(quota floor + backoff), never substitutes a local inference for their
result once fetched, preserving the no-local-override invariant.

## Numeric-default survey (constraints require concrete numbers)

- Existing precedent: `_RATE_LIMIT_GUARD_THRESHOLD = 500` in
  gates/closure_sweep.py, already used by that file's own CLI `main()`.
  No other numeric floor/backoff precedent exists in the write set.
