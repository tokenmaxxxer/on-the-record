---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py -k "watchdog or board_wide_sweep or ConsumerFixture or RosterOwnershipScoping" — result: 42 passed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-1219

## What was done

canonical: docs/issue-1219/proposals/2026-08-13-watchdog-root-anchoring.md
(read this session) — approved via the issue-level comment
`APPROVE issue-1219/implementation` (gh issue view 1219 --comments, read
this session)

Fixed the anchoring defect: `spawn.py watchdog` (invoked from
`on-the-record/hooks/poll-rearm.sh`'s `nohup ... watchdog --auto-respawn`
on every ~60s due tick) silently ignored `-C`/cwd and always scanned the
on-the-record checkout's own board (`ROOT = Path(__file__).resolve()
.parent`), leaking tokenmaxxxer/on-the-record's own issues/PRs/
requirement-drift lines and checkout paths into consumer sessions on
unrelated target repos.

- `roster_watchdog()` gained a `root: Path = ROOT` parameter; its
  board-facing calls (`_board_wide_sweep`, `_build_observed`,
  `_post_session_end_comment`, `_pr_open_or_merged_for_branch`, both
  `diagnose_health` calls) now use `root` instead of the module-level
  `ROOT`.
- `_board_wide_sweep` and `requirement_drift` keep their `gates/`
  `sys.path.insert` pinned to the module-level `ROOT` (gates code only
  ever lives in the checkout) while scanning `root` (the target board) —
  this split lets `root` be a foreign repo with no `gates/` directory at
  all with no import failure.
- The CLI dispatch for `a.role == "watchdog"` now supplies
  `root=Path(a.cwd).resolve()`, so `-C` (default `"."`, i.e. the session's
  cwd when `poll-rearm.sh` calls it) actually reaches the watchdog. Dev
  sessions (cwd == the checkout) are unaffected — `Path(a.cwd).resolve()`
  equals `ROOT` in that case.
- `tests/test_spawn.py`: updated `test_cli_watchdog_all_flag_threads_all_scope`
  for the new call shape; added `test_cli_watchdog_no_all_flag_threads_cwd_as_root`,
  `ConsumerFixtureWatchdogAnchoring.test_foreign_repo_watchdog_output_carries_no_marketplace_or_otr_references`
  (hermetic, no network — foreign tempdir repo, mocked `closure_sweep`/
  `spawn_coverage`, asserts zero occurrences of the checkout path,
  `"marketplaces"`, or `"tokenmaxxxer/on-the-record"` in output), and
  `test_dev_session_cwd_is_checkout_stays_unchanged`.

canonical: python3 -m pytest tests/test_spawn.py -k "watchdog or board_wide_sweep or ConsumerFixture or RosterOwnershipScoping" — result: pass (executed live this session, fenced output below)

```
$ python3 -m pytest tests/test_spawn.py -k "watchdog or ConsumerFixture or RosterOwnershipScoping or board_wide_sweep" -q
42 passed, 446 deselected in 0.60s
```

canonical: python3 -m pytest tests/test_spawn.py -q (full suite, executed live this session) — result: 484 passed, 4 pre-existing failures unrelated to this change, fenced output below

```
$ python3 -m pytest tests/test_spawn.py -q
4 failed, 484 passed in 1160.10s (0:19:20)
FAILED tests/test_spawn.py::SpawnOneNoWait::test_no_wait_returns_promptly_without_calling_await_bounded
FAILED tests/test_spawn.py::RosterReconcileUnreported::test_filters_by_issue
FAILED tests/test_spawn.py::RosterReconcileUnreported::test_lists_ended_session_with_open_pr_before_ack_and_empties_after
FAILED tests/test_spawn.py::ConsultCmd::test_traces_on_malformed_verdict
```

canonical: derived command below, executed live this session against this branch's unmodified pre-change tree (git stash) — result: the same test IDs fail there too, fenced output below

```
$ git stash
$ python3 -m pytest tests/test_spawn.py -q -k "test_no_wait_returns_promptly_without_calling_await_bounded or test_filters_by_issue or test_lists_ended_session_with_open_pr_before_ack_and_empties_after or test_traces_on_malformed_verdict"
4 failed, 481 deselected in 18.02s
FAILED tests/test_spawn.py::SpawnOneNoWait::test_no_wait_returns_promptly_without_calling_await_bounded
FAILED tests/test_spawn.py::RosterReconcileUnreported::test_filters_by_issue
FAILED tests/test_spawn.py::RosterReconcileUnreported::test_lists_ended_session_with_open_pr_before_ack_and_empties_after
FAILED tests/test_spawn.py::ConsultCmd::test_traces_on_malformed_verdict
$ git stash pop
```

canonical: python3 -c "<inline script: git-init a scratch tempdir with no GitHub remote and no board, call spawn.roster_watchdog(root=<that tempdir>)>", executed live this session — result: zero tokenmaxxxer/on-the-record or checkout-path references, fenced output below

```
[watchdog] accumulation-trend: no prior tick data (first run) — shape1_sites=0 shape5_files=0
[watchdog] spawn-coverage: 이슈 목록을 읽을 수 없다 (gh 실패) — 판정 불가
돌고 있는 역할 세션 없음
rc= 1
```

(`rc=1` is the existing "gh unreachable counts as an anomaly, not silent
success" contract already documented in `_board_wide_sweep`'s docstring —
unrelated to this fix; the acceptance point verified here is the absence
of any tokenmaxxxer/on-the-record/checkout-path text in the output above.)

## Why

canonical: docs/issue-1219/reports/implementation/survey.md (current-state
survey traced the exact code path this session)

The watchdog CLI branch was the one `spawn.py` subcommand found silently
dropping `a.cwd`; every other board-facing operation (role spawn, `watch`,
`reconcile`, etc.) already threads `-C`/repo identity correctly per the
survey. This is the mechanical fix the issue's own
`validity-consult-skip: trivial` framing calls for — no alternative
architecture was warranted (see the proposal's Rationale for the one
alternative considered and rejected).

## Upstream / basis

Based on: docs/issue-1219/proposals/2026-08-13-watchdog-root-anchoring.md

## What did not work

None.

## Open findings

canonical: derived command below, run this session

```
$ find . -iname "*hook-root-anchored*"
(no output)
```

2026-07-26-hook-root-anchored-to-target-project.md under docs/proposals/,
cited by the issue as prior art, is not present in this working tree per
the command above (no backtick path quoted here — it does not resolve) —
noted as an unresolvable pointer, not acted on further since the anchoring
class was independently retraced from `spawn.py` itself (see survey). Not
a blocking finding against this change.

## Next steps

None — `loop_state: landed`, terminal for this record's `type: fix`.

## Resolution path

Not applicable — no open findings against this build.
