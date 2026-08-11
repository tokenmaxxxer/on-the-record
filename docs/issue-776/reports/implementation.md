---
code_under_review:
  - harness/fixture-target/pyproject.toml
  - harness/fixture-target/fixture_target/__init__.py
  - harness/fixture-target/test_fixture_target.py
  - harness/fixture-target/.claude-plugin/marketplace.json
  - harness/driver.py
  - harness/signals.py
  - harness/run_smoke.py
  - harness/README.md
  - docs/handbooks/northpole-harness.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Northpole E2E acceptance harness — implementation record (issue #776 step 2)

## What was done

Built the runnable harness per `docs/specs/northpole-harness.md` and the
approved proposal at
`docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-implementation.md`:

- `harness/fixture-target/`: a minimal, real-buildable single-file Python
  CLI package (`pyproject.toml`, `fixture_target/__init__.py`,
  `test_fixture_target.py`) with a seeded defect — `--version` crashes
  because the version lookup, done inside an argument-parsing helper one
  layer removed from the entrypoint, reads a wrong attribute name
  (`_pkg.VERSION` instead of `_pkg.__version__`).
  `.claude-plugin/marketplace.json` points at the on-the-record plugin
  path — the fixture's only reference to on-the-record.
- `harness/signals.py`: pure functions implementing the 7-row signal
  table (spec §3) plus the build-and-run assertion (spec §5), each
  returning `PASS`/`FAIL`/`UNMEASURED` per the empty-state rule.
- `harness/driver.py`: operator-only actions (spec §4) — instantiate a
  clean copy of the fixture-target template, run build/version/test
  commands, and hold the representative requirement text. Launching a
  live session is left as an integration point wired by the operator
  (step 3), not performed here.
- `harness/run_smoke.py`: runs `signals.py` against a synthetic
  transcript + repo-state fixture (not a live session) and asserts all 8
  rows (7 signals + build-and-run) are present, each one of
  PASS/FAIL/UNMEASURED. Exits non-zero on a missing/malformed row.
- `harness/README.md` and `docs/handbooks/northpole-harness.md`: how to
  run the smoke check now vs. the real baseline later (step 3), and the
  operational-surface notes for the fixture's `pyproject.toml` and plugin
  pointer.

## Why

Per the approved proposal: the harness judges whether the northpole
backlog's fixes actually move the 7 requirements to MET, rather than
trusting static gap analysis. This step delivers the harness itself and
proves its signal-emission shape via a smoke check; running it against a
live session is step 3, out of scope here.

## Upstream / basis

Based on: `docs/specs/northpole-harness.md` (frozen design spec, issue
#776 step 1) and
`docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-implementation.md`
(approved phase-1 proposal, this issue).

## Verification performed

```
$ python3 harness/run_smoke.py
northpole E2E harness — smoke check (synthetic fixture, not a live run)
------------------------------------------------------------------------
orchestration_to_completion            PASS
full_record_ability                    PASS
real_wired_verification                PASS
autonomous_completion_reporting        PASS
problems_not_pushed_back               PASS
condensed_requirement_management       PASS
inviolable_constraint                  PASS
build_and_run                          PASS
------------------------------------------------------------------------
PASS: all 8 rows present, each PASS/FAIL/UNMEASURED
```

Separately, confirmed the fixture is a genuine buildable target before any
fix is applied (run against a scratch venv, not committed to the repo):

```
$ pip install -e harness/fixture-target && fixture-target --version
...
AttributeError: module 'fixture_target' has no attribute 'VERSION'
(exit 1 — seeded crash reproduces)

$ pytest harness/fixture-target -q
F.
1 failed, 1 passed in 0.01s
(the seeded-defect test fails for the expected reason; the flag-unset test passes)
```

## What did not work

None.

## code_under_review

- harness/fixture-target/pyproject.toml
- harness/fixture-target/fixture_target/__init__.py
- harness/fixture-target/test_fixture_target.py
- harness/fixture-target/.claude-plugin/marketplace.json
- harness/driver.py
- harness/signals.py
- harness/run_smoke.py
- harness/README.md
- docs/handbooks/northpole-harness.md

## Open findings

None.
