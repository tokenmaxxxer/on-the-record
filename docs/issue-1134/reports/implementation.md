---
code_under_review:
  - spawn.py
  - tests/test_gates.py
loop_state: landed
type: feature
breaking: false
# canonical: python3 -m pytest tests/test_gates.py -q (113 passed, this turn's own run)
verdict: pass
---

## Acceptance

canonical: python3 -m pytest tests/test_gates.py -q -k "consult or rulebook_version" (4 passed, 109 deselected, this turn's own run)
canonical: python3 -m pytest tests/test_gates.py -q (113 passed, this turn's own full-suite run)

## What was done

Implemented the approved phase-1 proposal
(canonical: docs/issue-1134/proposals/consult-trace-auto-commit.md,
git log shows PR #1153 merged into main): added `_commit_consult_trace()`
to spawn.py and wired it into `consult_cmd()`'s `finally` block (git add
of the trace-log path plus any raw-failure side files written this
call, then git commit with a fixed message shape carrying `Subject:
issue-<n>` when issue-scoped; `CalledProcessError` is caught and logged,
never raised past `finally`). Also fixed a bug the new gate test caught
during the build: only the last attempt's raw-failure file was being
committed (`raw_path` was overwritten each retry loop iteration) —
changed to accumulate all raw paths written this call into `raw_paths`
and commit all of them.

## Why

northpole req#2 (docs/specs/northpole.md) — a trace only existing as
uncommitted local state is not a record. Full rationale already recorded
in the phase-1 proposal; not restated here.

## Upstream

Based on: docs/issue-1134/proposals/consult-trace-auto-commit.md

## What did not work

- Wrote `_commit_consult_trace()` passing only the last loop iteration's
  `raw_path` to commit -> the scratch-clone gate test for the failure
  path caught it (`git status --porcelain` left an untracked line for
  the first attempt's raw-failure file, since only the second attempt's
  `raw_path` survived the loop overwrite). Fixed by accumulating into a
  `raw_paths` list and committing all of them.
- First version of the scratch-clone gate test's `fake_run` mock
  intercepted every `subprocess.run` call unconditionally, including the
  real git add/commit inside `_commit_consult_trace()` — so the commit
  never actually happened and the clean-checkout assertion kept failing.
  Fixed by routing any non-`claude` command in the mock to the real
  `subprocess.run` instead.
- The test's own `git status --porcelain` check first used the
  module-level `subprocess.run`, which is the same object being
  monkeypatched (`spawn.subprocess is subprocess`), so the status check
  itself was being intercepted by the fake. Fixed by capturing the
  original `subprocess.run` before monkeypatching and using it for the
  status check.

## Open findings

None.

## Rationale for deviations

The pre-existing consult-mock test in gates/ (not in this proposal's
frozen write set) regressed as a side effect of the new git-commit call
in `consult_cmd()`'s `finally` block: that file's `fake_run` mock
intercepts every `subprocess.run` call unconditionally, not just the
`claude` invocation, so the new git add/commit calls also land in its
recorded call count, which the test asserts equals exactly 2. This
proposal's frozen write set is spawn.py, tests/test_gates.py, and
docs/issue-1134/reports/implementation.md — per the scope-exceeded rule,
finished the covered work, did not widen the write set, and filed the
deviation instead of an inline fix:
docs/issue-1134/reports/implementation/deviation-log.md.

## Next steps

None further planned in this issue. The gates/ consult-mock regression
noted above is the one loose end; it needs a follow-up issue to update
that file's mock (outside this proposal's scope to touch here).

## Resolution path

The gates/ consult-mock regression: file a follow-up issue to route its
`fake_run` mock's non-`claude` commands to the real `subprocess.run`,
mirroring the fix already applied in this issue's own new test.
