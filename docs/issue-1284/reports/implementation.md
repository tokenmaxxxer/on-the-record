---
code_under_review:
  - gates/acceptance_gate.py
  - tests/test_acceptance_gate_tests_dir.py
type: bugfix
breaking: false
canonical: python3 -m pytest tests/ -k acceptance -q — result: pass, 10 passed, 664 deselected, executed this turn against sha 4cc04b6b
verdict: pass
loop_state: landed
---

# issue-1284: acceptance gate tests-dir regex fix

## What was done

`_ARTIFACT_REF` in `gates/acceptance_gate.py` matched backticked paths
containing `test/` or `gates/` but not `tests/` (this repo's actual test
directory), so real test paths were rejected as prose-only. Changed the
backtick-path alternative from `test/` to `tests?/` so both the singular
and plural forms count as executable artifact references; the
`gate:`/`check:` line alternative was not touched.

Added `tests/test_acceptance_gate_tests_dir.py` with five named cases:
backticked `tests/` path accepted, prose-only body still rejected,
existing singular `test/` form still accepted, existing `gates/` form
still accepted, and `check:` line form still accepted.

## Why

Bug: real test paths such as `tests/test_spawn.py` were rejected as
prose-only, refusing spawns that legitimately cited executable test
files (reproduced twice during issue #1280 spawn attempts, per the
issue body).

## Upstream basis

Issue #1284.

## What did not work

None.

## Doc placement

No env var, config key, dependency, migration, or setup step was
introduced — nothing to place on the doctrine ladder.

## Acceptance verification

canonical: python3 -m pytest tests/ -k acceptance -q — result: pass, 10 passed, 664 deselected, executed this turn against sha 4cc04b6b

```
$ python3 -m pytest tests/ -k acceptance -q
..........                                                               [100%]
10 passed, 664 deselected in 0.11s
```

## Open findings

None.
