---
code_under_review:
  - tests/test_flows.py
type: bugfix
breaking: false
canonical: python3 -m pytest tests/ gates/ (this turn) — 1038 passed, 1 xfailed, 1 failed (known pre-existing)
verdict: pass
loop_state: landed
---

## What was done

canonical: tests/test_flows.py setUp (DecisionQueueSessionScope)

Swapped the two `addCleanup` registration lines in
`tests/test_flows.py` (`DecisionQueueSessionScope.setUp`) per the
approved phase-1 proposal: registration order is now
`update(old_env)` then `clear()`, so `unittest`'s LIFO cleanup execution
runs `clear()` first and `update(old_env)` second, restoring the original
`os.environ` (including `PATH`) instead of wiping it for the rest of the
pytest process.

## Why

canonical: docs/issue-1077/proposals/implementation.md, docs/issue-1077/reports/implementation/survey.md

Basis: docs/issue-1077/proposals/implementation.md (approved),
docs/issue-1077/reports/implementation/survey.md (bisection trace).

R001 (issue #1077): `python3 -m pytest tests/ gates/` combined run
produced spurious cross-suite failures, bisected to this single
misordered `addCleanup` pair clobbering `os.environ` mid-process.

## Acceptance verification

canonical: python3 -m pytest tests/ gates/ (this turn)

acceptance: python3 -m pytest tests/ gates/ — result: UNMEASURED-with-reason: no acceptance command on record for this target in docs/specs/acceptance-commands.md; see fenced re-run output below

```
$ python3 -m pytest tests/ gates/ 2>&1 | tail -6
FAILED tests/test_gates.py::t_rulebook_version_is_recorded - AssertionError: ...
=========================== short test summary info ============================
FAILED tests/test_gates.py::t_rulebook_version_is_recorded - AssertionError: ...
================== 1 failed, 1038 passed, 1 xfailed in 57.97s ==================
```

canonical: python3 -m pytest tests/ gates/ (same run above)

The single remaining failure is the pre-existing failure the issue itself
names (asserts the working tree is committed-clean, which it structurally
cannot be while this session has uncommitted work in progress). This
satisfies the issue's acceptance criterion of passing except known-marked
failures.

## What did not work

None.

## Rationale for deviations

None — matches the approved phase-1 proposal exactly (single two-line swap
in tests/test_flows.py).

## Doc placement

No handbook/decision/report doc-placement triggers apply — this is a
one-file test-order bugfix with no new env var, dependency, migration,
public-signature change, or library/format choice.

## Open findings

canonical: docs/issue-1077/reports/hunt-implementation.md

None open. The phase-1 warrant hunt (docs/issue-1077/reports/hunt-implementation.md) found nothing.

## Next steps

None — loop_state: landed, terminal for type: bugfix.
