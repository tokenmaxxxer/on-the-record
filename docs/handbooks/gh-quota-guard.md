# gh quota guard (issue #1498)

GraphQL quota hit 0/5000 on 2026-08-14 even though issue #1459 already cut
REST read cost — the watchdog board-sweep and gate helpers kept attempting
bulk/lookup calls at full frequency with no quota awareness. This guard
adds a floor precondition, sweep/re-check backoff, and a per-tick call
budget on top of #1459's REST/bulk machinery.

## The four numeric defaults

| default | value | where |
| --- | --- | --- |
| quota floor | 500 (GraphQL `remaining`) | `gates/closure_sweep.py::_RATE_LIMIT_GUARD_THRESHOLD`, reused by `spawn.py::_board_wide_sweep` |
| sweep backoff | 1 tick initial, doubling to a max of 8 ticks on rate-limit, reset to 1 on success | `gates/closure_sweep.py::SWEEP_BACKOFF_MAX_TICKS`, `sweep_should_run()`/`record_sweep_result()` |
| re-check backoff | 3 consecutive no-change results before doubling, max 16 ticks, reset to 1 on any observed change | `gates/closure_sweep.py::RECHECK_NO_CHANGE_THRESHOLD` / `RECHECK_BACKOFF_MAX_TICKS`, `recheck_backoff()` |
| per-tick call budget | 8 gh calls per `_board_wide_sweep` tick; an overage is reported as a `[watchdog] board-sweep: 예산 초과` anomaly line, never a silent retry | `spawn.py::_board_wide_sweep` (`call_budget` local) |

## State file

`runs/gh_quota_backoff.json` — a pure local JSON counter file, no gh calls
of its own:

```json
{
  "sweeps": {"board-sweep": {"tick": 12, "interval_ticks": 2, "consecutive_rate_limit_errors": 1}},
  "recheck": {"issue-1163/conformance-review": {"tick": 5, "interval_ticks": 4, "consecutive_no_change": 4}}
}
```

`gates/closure_sweep.py::load_backoff_state()`/`save_backoff_state()` own
the file; `sweeps` and `recheck` are independent namespaces so a sweep's
backoff and a re-check subject's backoff never collide on key names.

## Where the floor applies

`spawn.py::_board_wide_sweep` (the watchdog tick path) calls
`closure_sweep.rate_limit_remaining()` first. Below the floor, all three
gh-calling signals (`spawn_on_pr.spawn_missing_for_pr`,
`closure_sweep.find_violations`, `spawn_coverage._list_open_issues`) are
skipped and exactly one report line is printed
(`[watchdog] board-sweep: 미집계 (rate-limit, remaining=<n>)`). Local-only
signals (`closure_sweep.accumulation_trend`, `requirement_drift`) always
run — they cost no gh quota.

## Bulk resolution, not per-subject lookups

`gates/spawn_on_pr.py::missing_verification()` and `spawn_missing_for_pr()`
resolve each subject's PR via a single `closure_sweep._pr_index_all()`
bulk index + local join, not a `gh pr list --head <branch>` call per
subject — the per-tick budget assumes O(pages), not O(subjects).

## REST-only regression (requirement 2)

Survey found no GraphQL-backed `gh` subcommand left in the watchdog/gate
read paths — every read already goes through `gh api` (REST) or
`gh issue/pr list --json` (REST-backed list endpoints). `verified, not
migrated`; `tests/test_gh_quota_guard.py::test_graphql_free_watchdog_reads`
is the standing regression test.
