---
status: proposed
files:
  - tests/test_flows.py
---

Skip condition: pure bugfix — see
docs/issue-1077/reports/implementation/survey.md for the bisection and
root-cause trace; no design decision is open.

## Request

`python3 -m pytest tests/ gates/` in one process produces ~234
failures that don't occur when either suite runs alone. Requirement
R001 (real verification must be trustworthy) needs the combined run to
be a usable health check.

## Constraints

- Fix must not change any suite's behavior when run standalone.
- Fix must not widen the write set beyond the actual polluter.
- Acceptance: `python3 -m pytest tests/ gates/` passes except the one
  already-known pre-existing failure (`t_rulebook_version_is_recorded`).

## Rationale

Considered adding a session-scoped `os.environ` snapshot/restore
fixture in `conftest.py` (belt-and-suspenders isolation for the whole
suite) instead of fixing the one call site. Rejected: the bisection in
the survey shows exactly one polluter — a single misordered
`addCleanup` pair in `tests/test_flows.py`'s
`DecisionQueueSessionScope.setUp` — and fixing it directly resolves
the entire combined-run failure count to just the known pre-existing
one. A repo-wide conftest safety net would mask this class of bug
instead of removing it, and would touch a shared fixture file outside
the actual defect's location for no added correctness.

## What will be done

Swap the two `self.addCleanup(...)` registration lines in
`tests/test_flows.py`'s `DecisionQueueSessionScope.setUp` so
`unittest.addCleanup`'s LIFO execution order runs `os.environ.clear()`
before `os.environ.update(old_env)`, instead of after. This makes the
teardown restore the pre-test environment exactly, instead of wiping
it.

## Out of scope

- The pre-existing `t_rulebook_version_is_recorded` failure (not
  cross-suite pollution; acceptance already excludes it).
- Any other test-isolation hardening (env snapshot fixtures, cwd
  isolation) not needed to make this specific pollution stop.

## How you'll know it worked

`python3 -m pytest tests/ gates/` run in one process shows 0 failures
beyond the one known-marked `t_rulebook_version_is_recorded` case —
confirmed locally in survey.md before this proposal was written
(1 failed, 1038 passed, 1 xfailed).
