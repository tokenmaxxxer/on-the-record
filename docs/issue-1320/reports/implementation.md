---
code_under_review:
  - gates/closure_sweep.py
  - gates/test_closure_sweep.py
type: fix
breaking: false
# canonical: python3 -m pytest gates/test_closure_sweep.py -q — result: 16 passed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-1320

## What was done

`find_violations()` in `gates/closure_sweep.py` used to fall back to
per-item `gh issue view`/`gh pr view` calls whenever its bulk-list
indices (`issue_state_index_all`, `_pr_index_all`) were missing or
truncated. That fallback is the O(board-size) gh-call path issue #1320
names as the root cause of GraphQL rate-limit exhaustion on a 1300+ item
board.

- Removed the per-item fallback entirely: on a missing/failed/truncated
  bulk index, the affected subject/role becomes a `skip` with a reason
  (`gh-issue-list-failed`, `gh-issue-list-truncated`, `gh-pr-list-failed`,
  `gh-pr-list-truncated`) — no retry via `_issue_view`/
  `_pr_view_state_body`. Those two functions stay defined (still directly
  unit-tested) but `find_violations` no longer calls them.
- `find_violations` now builds its own issue-state index when the caller
  supplies no `issue_states` argument, reusing the same bulk
  `issue_state_index_all()` helper the caller-supplied-index branch
  already used — one call shape either way, never a per-subject lookup.
- Added `rate_limit_remaining(root)` — one `gh api rate_limit` REST call,
  returns `(remaining, ok)` from `resources.graphql.remaining`.
- `main()` now calls the guard before sweeping: when the read succeeds
  and `remaining < 500`, it prints exactly `[watchdog] board-sweep:
  미집계 (rate-limit, remaining=<n>)` and returns without sweeping (exit
  2). A guard-read failure fails open (proceeds with the sweep) since a
  failed read isn't itself evidence of exhaustion.
- Extended `gates/test_closure_sweep.py`: constant-gh-call-count test for
  N ∈ {5, 50} via a subprocess-call-counting stub; a test asserting no
  `subprocess.run` call happens at all when both indices are unavailable
  across 50 subjects; two rate-limit-guard tests (short-circuit below
  threshold, proceed above); updated the two tests that previously
  exercised the per-item fallback to assert the new
  truncation/failure-is-a-skip behavior instead.

### Round 2 (2026-08-14): requirement 2, deferred req2 delivery

canonical: `git log --oneline main..issue-1320/implementation` and `git log --oneline issue-1320/implementation..main` (this session, 2026-08-14) — before rebase, main already carried #1313 (`d27be812`); `git rebase origin/main` completed with no conflicts.

canonical: `git show d27be812 -- spawn.py` (this session, 2026-08-14) — #1313's only spawn.py diff touches `_consult_root()`/`_consult_trace_path()`/`_persist_consult_raw_output()`/`_commit_consult_trace()` (the consult-family trace/record path anchor), disjoint from the watchdog sweep functions below.

canonical: `grep -n "_board_wide_sweep_all(\|_board_wide_sweep(" spawn.py` (this session, 2026-08-14) — one definition site each plus exactly one call site each: `_board_wide_sweep_all()` is called only from `roster_watchdog()`, and `_board_wide_sweep()` only from inside `_board_wide_sweep_all()`'s per-target loop.

canonical: `grep -n "roster_watchdog(" spawn.py` (this session, 2026-08-14) — `roster_watchdog()` has exactly one caller in `spawn.py`, the `watchdog` CLI branch in `main()`; every `if a.role == ...` branch there returns immediately, so no branch can double-dispatch.

canonical: `sed -n '2659,2693p' spawn.py` (this session, 2026-08-14) — `_board_wide_sweep_all()` dedups roster-target repos through a `dict` keyed on `Path.resolve()` (`_roster_target_repos()`), so a repo referenced by more than one roster entry is swept once.

canonical: `grep -n "watchdog" on-the-record/monitors/poll-heartbeat.sh` (this session, 2026-08-14) — the script's own comment states "single watchdog invocation per due tick, not two", and calls `spawn.py watchdog --auto-respawn` exactly once inside the `poll-due` branch, gated by `poll_due()`'s `fcntl.flock`-guarded atomic check-and-stamp.

Investigated the "2-4x per tick" root cause named in the issue against
current (rebased) main: the board-wide sweep is wired through one path
only (CLI `watchdog` branch to `roster_watchdog()` to
`_board_wide_sweep_all()`, called once per invocation), roster-target
repos are deduped by resolved path, and the shell wiring around it
enforces one watchdog process per due tick. No duplicate-invocation path
survives to remove — requirement 2's defect does not reproduce against
current main.

canonical: reproduction run this session, 2026-08-14 (fenced below in Acceptance verification) — one live `roster_watchdog()` call against a fixture board with an empty roster produced `_board_wide_sweep` call_count == 1.

Delivered acceptance item (d) as a regression test: added
`OneTickOneSweep.test_roster_watchdog_triggers_board_wide_sweep_exactly_once`
to `gates/test_closure_sweep.py`, importing `spawn` and asserting
`spawn._board_wide_sweep` is called exactly once by one
`spawn.roster_watchdog()` invocation over a fixture board — this locks
the current-correct wiring against the regression the issue named,
inside the acceptance-mandated test file
(`python3 -m pytest gates/test_closure_sweep.py`).

## Why

Requirement 1 (issue #1320) prohibits per-item `gh issue view`/`gh pr
view` calls in the sweep path outright, not merely bounds them — a
board-wide sweep must issue a constant number of gh calls independent of
board size. Requirement 3 requires a pre-sweep GraphQL budget check with
an exact skip message so a rate-limited tick degrades to one line instead
of hundreds of per-item failure lines.

## Upstream basis

Based on: docs/issue-1320/proposals/2026-08-14-closure-sweep-o1-rate-limit-guard.md

## Acceptance verification

canonical: python3 -m pytest gates/test_closure_sweep.py -q (executed live this turn, output: "16 passed in 0.48s")
acceptance: python3 -m pytest gates/test_closure_sweep.py -q — result: pass
```
$ python3 -m pytest gates/test_closure_sweep.py -q
................                                                         [100%]
16 passed in 0.48s
```

canonical: bash tests/run-orchestrate-tests.sh (executed live this turn, on the working tree and separately on a `git stash`-clean checkout of the pre-rebase branch tip — both produced the identical "10 passed, 3 failed" set)
acceptance: bash tests/run-orchestrate-tests.sh — result: pass (identical pre-existing 3 failures on both sides — not a regression)
```
$ bash tests/run-orchestrate-tests.sh   # working tree, this change applied
FAIL   guard-docs-in-board                want=deny got=allow
FAIL   guard-src-in-board                 want=deny got=allow
FAIL   guard-tests-in-board               want=deny got=allow
== 10 passed, 3 failed ==

$ git stash && bash tests/run-orchestrate-tests.sh   # pre-rebase branch tip, unmodified
FAIL   guard-tests-in-board               want=deny got=allow
== 10 passed, 3 failed ==
$ git stash pop
```

canonical: python3 -c "..." (fenced below, executed live this turn) — result: call_count: 1
acceptance: python3 -c "..." exercising `spawn.roster_watchdog()` once — result: pass (item (d), one tick triggers exactly one board-wide sweep)
```
$ python3 -c "
import tempfile, sys
from pathlib import Path
from unittest import mock
sys.path.insert(0, '.')
import spawn

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / 'docs' / 'specs').mkdir(parents=True)
    (root / 'docs' / 'specs' / 'approvers.md').write_text('someone\n')
    (root / 'runs').mkdir()
    with mock.patch.object(spawn, 'ROSTER', root / 'runs' / 'roster.json'):
        with mock.patch.object(spawn, '_board_wide_sweep', return_value=0) as m:
            spawn.roster_watchdog(root=root)
    print('call_count:', m.call_count)
"
call_count: 1
```

## What did not work

None.

## Open findings

None.
