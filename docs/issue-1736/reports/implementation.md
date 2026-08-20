---
code_under_review:
  - spawn.py
  - test/test_spawn_model_override.py
  - tests/test_spawn.py
  - harness/fixture-concurrent-judgment/test_panel.py
type: feature
breaking: false
verdict: ok
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal
(`docs/issue-1736/proposals/model-override.md`), basis: issue #1736
comment `APPROVE issue-1736/implementation`.

canonical: spawn.py:5367-5378 (read this turn)
`resolved_role_model(cli_model: str | None = None)` — a non-empty
(after `.strip()`) `cli_model` wins first; otherwise falls through to
the existing `MUSTER_ROLE_MODEL` env > `role_model.txt` > `"sonnet"`
chain unchanged.

canonical: spawn.py:5378-5412, 5546-5551, 6206-6209 (read this turn)
`spawn_cmd()`, `_consult_cmd_and_env()`, and `_run_panel_session()` each
carry a new `model: str | None = None` parameter, forwarded to
`resolved_role_model(model)` in place of the no-arg call.

canonical: spawn.py:5586, 6321, 7703 (read this turn)
`model` threads through `_spawn_one()`, `consult_cmd()`, and
`panel_cmd()` down to the functions above; `panel_cmd()` forwards
`model` to both `ThreadPoolExecutor` `launcher` submissions.

canonical: spawn.py:6800-6803, 6964-6965, 7005-7006, 7089, 7101-7106 (read this turn)
A new `ap.add_argument("--model", ...)` feeds `a.model` at the three
dispatch sites (`consult`, `panel`, `spawn`'s `_spawn_one(...)` call)
plus the `--dry-run` preview's `resolved_role_model(a.model)` call.

canonical: spawn.py:5879-5896, 5999, 6034 (read this turn)
`_judge_cmd_and_env()` and its two hardcoded-`haiku` callers (prefilter,
validator) carry no `model` threading — untouched by this change.

`test/test_spawn_model_override.py` carries one test per precedence
level (CLI, env, file, default), a whitespace-only-CLI edge case
mirroring the existing whitespace-only-env test convention, and a guard
test asserting `_judge_cmd_and_env(..., model="haiku")`'s emitted argv
still carries `haiku` with `MUSTER_ROLE_MODEL`/`role_model.txt` both set
to a different value.

The `model` parameter on `consult_cmd()`/`panel_cmd()` changed their
call signatures (kwarg always present, default `None`), which broke
four pre-existing tests whose mocks/fakes asserted the old exact
argument list or the old fixed 4-arg `run_session` callback shape, in
`tests/test_spawn.py` (panel CLI wiring test, panel-degrade
error-safety test) and `harness/fixture-concurrent-judgment/test_panel.py`
(both tests in that file). Those four now match the new signature —
mechanical fixes tied to the sanctioned `model` parameter addition, not
new functionality.

## Why

canonical: docs/issue-1736/proposals/model-override.md ## Rationale (read this turn)
The proposal's own Rationale section, approved in phase 1, chose
threading a `cli_model` parameter through `resolved_role_model()` over
having each call site read `args.model` directly, to keep precedence
logic in one place and keep the judge-path guard statable as a single
fact.

## What did not work

None.

## Test results

derived: `python3 -m pytest test/test_spawn_model_override.py -v`
```
test/test_spawn_model_override.py::JudgeModelGuardTest::test_judge_guard_ignores_env_and_cli_style_override PASSED
test/test_spawn_model_override.py::ResolvedRoleModelPrecedenceTest::test_cli_whitespace_only_falls_through PASSED
test/test_spawn_model_override.py::ResolvedRoleModelPrecedenceTest::test_cli_wins_over_env_and_file PASSED
test/test_spawn_model_override.py::ResolvedRoleModelPrecedenceTest::test_default_when_nothing_set PASSED
test/test_spawn_model_override.py::ResolvedRoleModelPrecedenceTest::test_env_wins_over_file_when_no_cli PASSED
test/test_spawn_model_override.py::ResolvedRoleModelPrecedenceTest::test_file_wins_over_default_when_no_cli_or_env PASSED
6 passed in 0.80s
```

Full repo test-tier run per `.on-the-record/test-tiers.json` (this
change touches `spawn.py`, a `slow`-tier `trigger_change_classes`
entry, so both tiers ran):

derived: `python3 -m pytest -q -m "not slow"`
```
2 failed, 2273 passed, 19 xfailed, 2 xpassed in 35.43s
```
The 2 failures (gh-quota-guard sweep-call-budget test, poll-heartbeat
board-wide-sweep call-count test) are pre-existing and unrelated to this
change.

derived: `git stash && python3 -m pytest -q tests/test_gh_quota_guard.py::test_sweep_call_budget tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts; git stash pop`
```
2 failed on pre-change tree (identical failure signatures)
```

derived: `python3 -m pytest -q -m slow`
```
100 passed, 1 xfailed, 1 xpassed in 680.85s (0:11:20)
```

## Rationale for deviations

None — implementation followed the approved proposal's six steps
exactly. The four pre-existing test fixes described above are mechanical
signature-drift repairs on tests outside the proposal's frozen write
set, made necessary by the sanctioned `model` parameter addition; they
are not a scope or design deviation from what the proposal specified.

## Open findings

None.
