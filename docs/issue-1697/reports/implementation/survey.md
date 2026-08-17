# Survey — issue #1697

Write set: `gates/spawn_on_pr.py`, `tests/test_spawn_on_pr.py`.

## Current state

canonical: gates/spawn_on_pr.py:56-131 (read directly)
`missing_verification()` triggers observer roles (execution-observation,
conformance-review) for a subject when: the subject's
`<subject>/implementation` branch has an open-or-merged PR
(`_pr_number_for_branch`, gates/spawn_on_pr.py:74) AND the subject's
issue is OPEN (`_issue_is_open`, gates/spawn_on_pr.py:63).

- **Merged-PR skip is missing**:
canonical: gates/spawn_on_pr.py:74-87 (read directly), spawn.py:1207-1216 (read directly)
`_pr_number_for_branch` treats OPEN and MERGED identically, backed by
`spawn._pr_open_or_merged_for_branch`. Nothing in `missing_verification`
distinguishes MERGED state, so a subject whose PR already merged still
spawns observers exactly like an open one.

- **Live-base resolution is missing at the spawn-on-pr layer**:
canonical: gates/spawn_on_pr.py:89-131 (read directly, no `git fetch`/`subprocess` call in the function body); spawn.py:7460-7498 (read directly)
`missing_verification`/`spawn_missing_for_pr` never fetch `origin`
themselves — they read `spawn.board(root)` and a PR index straight off
local git/gh state. The actual branch cut for a spawned session happens
later, inside `spawn.checkout_issue_branch()`, which does fetch fresh
via `bootstrap_fetch_and_record_sha` + `_fetch_or_halt`. But that fetch
runs against the workspace clone origin (`issue_workspace()`,
spawn.py:7236) at whatever moment the spawned session actually starts —
there is no explicit "resolve main as of spawn decision time" step
spawn_on_pr.py itself performs, and none that a unit test can exercise
with a moved-main fixture without going through a full session spawn.

- **No defer for an active implementation session**:
canonical: gh issue view 1697 --comments, second comment (2026-08-17, issue-1696 reproduction)
observers spawned while the subject's own implementation session was
still RUNNING. Nothing in gates/spawn_on_pr.py checks roster liveness
for the subject's own implementation session before spawning observers.

## Existing building blocks reused

canonical: gates/closure_sweep.py:162-194 (read directly)
- `closure_sweep._pr_index_all(root)` — bulk branch→{number,state,body}
  index; `state` value set includes `"MERGED"`.

canonical: spawn.py:2219-2296 (read directly)
- `spawn._roster_load()` / `spawn._alive(pid)` — roster pid liveness,
  already used by `spawn._format_roster_row` for the `ps` RUNNING/ENDED
  distinction.

canonical: spawn.py:1687-1697 (read directly)
- `spawn._base(cwd)` — resolves the base branch ref (origin/HEAD or
  origin/main/master fallback) from local git state.

canonical: gates/spawn_on_pr.py:132-151 (read directly)
- `spawn.ledger_write()` — structured event log, already used by
  `_filter_execution_observation` for board notes.

## Alternatives considered

Could add the live-base fetch inside `spawn.checkout_issue_branch()`
only (it already fetches). Rejected: that fetch happens after
`_spawn_one` has already decided to spawn and after `issue_workspace()`
clones — it can't be unit-tested with a bare-git moved-main fixture at
the spawn_on_pr layer, and it does nothing to anchor the trigger
decision itself to live state. This issue's acceptance targets the
*spawn decision*, not just the eventual branch cut.
