# Survey — watchdog `closure_sweep` callers never pass the existing `issue_states` prefetch (issue #743)

The issue body already fixes the design: `find_violations()` already
accepts an `issue_states` map and already skips its own per-subject `gh
issue view` call when the subject's issue is present in that map
(issue #189). The defect is entirely on the caller side — none of the
three deployed callers builds that map and passes it in. This survey
maps the current call sites, the prefetch shape already established for
the sibling PR-list problem, and the test surfaces that need updating.

## The three call sites (issue body's own grep, reconfirmed on current main)

derived: `grep -rn "find_violations(" spawn.py gates/*.py | grep -v "def find_violations"`
```
spawn.py:1946:    violations, skips = closure_sweep.find_violations(root)
spawn.py:3719:        violations, skips = closure_sweep.find_violations(root)
gates/closure_sweep.py:321:    violations, skips = find_violations(root)
```

None of the three passes `issue_states=`. `find_violations`'s signature
and doc (`gates/closure_sweep.py`, lines 134-147) confirm the parameter
exists and, when given, is consumed at lines 159-160 to skip the
per-subject `_issue_view` call at line 162.

- `spawn.py`, line 1946 — inside `_board_wide_sweep()` (`spawn.py`,
  lines 1936-1968), called every tick from `roster_watchdog()` (issue
  #464's board-wide observe-only sweep). This is the "watchdog 경로" the
  issue title and Acceptance item 1 name specifically, and the one
  carrying the measured 101s/tick, 166-subject cost.
- `spawn.py`, line 3719 — inside `spawn.py`'s own `closure-sweep` CLI
  subcommand (`python3 spawn.py closure-sweep [--repo] [--post]`,
  argparse dispatch at `spawn.py`, lines 3713-3737). An explicit single
  human/CI-triggered invocation, not a recurring tick, but it runs the
  exact same `find_violations(root)` call with no prefetch and pays the
  same per-subject `gh issue view` cost on every run.
- `gates/closure_sweep.py`, line 321 — inside that module's own
  `main()` (the standalone `python3 gates/closure_sweep.py [--repo]
  [--post]` verb). Same shape, same missing prefetch.

## The prefetch shape already established for the sibling PR-list problem

`find_violations` already solves an identical problem for PR lookups via
`_pr_index_all` (`gates/closure_sweep.py`, lines 88-131): one `gh pr
list --state all --json number,headRefName,state,body --limit 1000`
call, called once per `find_violations` invocation, returning `(index,
ok)` — `ok=False` means the `gh` call itself failed (caller must not
read that as "no PRs"), and hitting the `_PR_INDEX_LIMIT` exactly
returns `(None, True)` so the caller falls back to the old per-branch
lookup rather than silently truncating (issue #224's lesson, cited in
the docstring).

No equivalent bulk-issue-state fetch exists inside
`gates/closure_sweep.py` today — `issue_states` is a parameter
`find_violations` accepts, but the module itself never builds one.
`gates/flows.py` (a different path, out of scope per the issue body)
does build one via its own `_issue_list_all()` (`gates/flows.py`, lines
69-82: `gh issue list --state all --json number,state,body --limit
1000`, `(list, ok)` shape) and that function's own docstring already
says it's meant to double as "closure_sweep 의 이슈-상태 프리페치(issue
#189)" — a prefetch this issue is the first to actually wire up on the
watchdog/CLI side.

## Why not just import `gates/flows.py`'s helper

`gates/flows.py` builds a `list[dict]` (`number,state,body` — it also
needs `body` for its own plan-parsing) and converts it to
`issue_state_by_n: dict[int, str]` inline (`gates/flows.py`, lines
298-304), not a standalone reusable function. Reaching into `flows.py`
from `closure_sweep.py` for this would create a new inter-module
dependency in the direction the codebase doesn't currently have
(`flows.py` already imports `spawn`; nothing currently imports `flows`),
fetch a `body` field `closure_sweep` never uses, and cross the exact
boundary #674 drew when it removed `flows_payload`'s call into
`closure_sweep` (the two paths are meant to stay independent so a
slowdown in one can't propagate to the other). The natural fix mirrors
`_pr_index_all` instead: a small bulk-fetch helper living in
`gates/closure_sweep.py` itself, next to `_pr_index_all`, with the same
`(index, ok)` / truncation-safe shape, built and called by each of the
three sites above.

## `spawn_coverage._list_open_issues` — not reusable either

`_board_wide_sweep` (`spawn.py`, lines 1936-1968) calls
`spawn_coverage._list_open_issues(root)` a few lines after the
`find_violations` call, for a different purpose (spawn-coverage's
uncovered-issue check). Its `gh issue list` call fetches only `--state
open` (missing closed issues `find_violations` needs to classify
`OPEN_PR_ON_CLOSED_ISSUE`) and only `number,createdAt` (missing `state`
as a distinct field, and it needs `createdAt` which the closure-sweep
prefetch has no use for). Merging the two fetches into one shared call
is a plausible follow-on optimization but changes a second,
independently-tested module (`gates/spawn_coverage.py`) for a marginal
extra `gh`-call saving beyond what this issue asks; not attempted here
(see proposal's Rationale for the explicit alternative-and-rejection).

## Test surfaces that assert today's caller behavior and will break under the fix

- `tests/test_spawn.py`'s `Watchdog` test class
  (`test_board_wide_sweep_reports_and_counts_closure_violations`,
  `test_board_wide_sweep_reports_and_counts_uncovered_issues`,
  `test_board_wide_sweep_clean_returns_zero`,
  `test_board_wide_sweep_reports_gh_failure_not_as_clean`, around
  `tests/test_spawn.py`, lines 3549-3632) all patch
  `sys.modules["closure_sweep"]` with a bare `mock.MagicMock()` and only
  configure `.find_violations.return_value`. Once `_board_wide_sweep`
  calls a new `closure_sweep.issue_state_index_all(root)` before
  `find_violations`, each of these four tests will try to tuple-unpack
  that mock's auto-generated `MagicMock()` return value
  (`unittest.mock.MagicMock`'s default `__iter__` yields nothing),
  raising `ValueError: not enough values to unpack` — all four need
  `fake_cs.issue_state_index_all.return_value` configured alongside the
  existing `find_violations.return_value`.
- `gates/test_closure_sweep.py`'s `MainExitCode` test
  (`test_exit_code_is_2_and_prints_could_not_check`, around
  `gates/test_closure_sweep.py`, lines 94-108) stubs
  `closure_sweep.find_violations` directly (a lambda accepting
  `issue_states=None`) but does not stub any bulk-fetch helper, and does
  not set `--repo`, so `main()`'s new prefetch call would run against
  this session's actual `cwd` — this repo, over a real, authenticated
  `gh` connection (confirmed live: `gh auth status` reports "Logged in
  to github.com account jjongkwann"). That test needs an explicit stub
  for the new prefetch function so it stays fast and network-independent,
  matching every other test in that file.
- No existing test exercises `spawn.py`'s `closure-sweep` CLI subcommand
  (`spawn.py`, lines 3713-3737) at all — a search for the literal string
  "closure-sweep" in `tests/test_spawn.py` only matches an assertion
  string inside a `_board_wide_sweep` test's stdout check, not a CLI
  invocation. Nothing existing breaks there, but nothing existing covers
  the fix there either.

derived: `grep -n "closure-sweep" tests/test_spawn.py`
```
3572:            self.assertIn("closure-sweep: 위반 1건", buf.getvalue())
```

## Acceptance-shape check against the issue body

Acceptance item 1 ("watchdog 경로의 sweep 이 subject 수에 비례한 이슈
조회를 더 이상 하지 않는다... 스텁으로 이슈 조회 호출을 세는 단위
테스트로 N에 비례하지 않고 상수임을 단언") names the watchdog path
specifically (`_board_wide_sweep`/`roster_watchdog`) — this needs a test
that drives the real `find_violations` through the real
`_board_wide_sweep` (not a fully-mocked `closure_sweep` module, which
would test nothing about the wiring) with a stubbed `_issue_view` that
records call count, run at two different subject counts, asserting the
count is identical (not scaling) across them.

Acceptance item 2 ("판정 결과가 변경 전과 같다... 같은 픽스처 보드에
대해 변경 전후 `find_violations` 반환값이 동일한지 비교") is a
regression-safety comparison: since `find_violations`'s own algorithm is
out of scope and unchanged (issue body, "범위 밖"), the comparison is
between calling it the old way (no `issue_states`, per-subject
`_issue_view` stubbed to return specific states) and the new way
(`issue_states` prebuilt from those same states, mirroring what the new
bulk-fetch helper would hand callers) against one fixture PR index,
asserting identical `violations`/`skips`.

## Skip condition check (scout directive)

This is a pure bugfix: the parameter, its consumption logic, and its
established sibling pattern (`_pr_index_all`) already exist and are
already tested (`tests/test_gates.py`'s
`t_find_violations_uses_prefetched_issue_state_skips_issue_view` and
`t_find_violations_without_issue_states_still_calls_issue_view`); the
fix is wiring three call sites to build and pass an already-specified
argument. No product-facing surface, no new user-visible behavior, no
open design question — #674's own survey and proposal (read in full for
this survey) already named this exact gap as a separate, deferred
problem with the shape decided. Scouting was skipped on that basis.
