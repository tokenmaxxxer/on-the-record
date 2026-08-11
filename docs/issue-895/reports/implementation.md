---
code_under_review:
  - harness/driver.py
  - harness/run_smoke.py
  - harness/test_driver.py
  - harness/fixture-feature/pyproject.toml
  - harness/fixture-feature/fixture_feature/__init__.py
  - harness/fixture-feature/test_fixture_feature.py
  - harness/fixture-feature/.claude-plugin/marketplace.json
  - harness/fixture-multimod/pyproject.toml
  - harness/fixture-multimod/fixture_multimod/__init__.py
  - harness/fixture-multimod/fixture_multimod/cli.py
  - harness/fixture-multimod/fixture_multimod/core.py
  - harness/fixture-multimod/fixture_multimod/formatters.py
  - harness/fixture-multimod/test_fixture_multimod.py
  - harness/fixture-multimod/.claude-plugin/marketplace.json
  - harness/fixture-redtest/pyproject.toml
  - harness/fixture-redtest/fixture_redtest/__init__.py
  - harness/fixture-redtest/fixture_redtest/discount.py
  - harness/fixture-redtest/test_discount.py
  - harness/fixture-redtest/.claude-plugin/marketplace.json
  - harness/fixture-ambiguous/pyproject.toml
  - harness/fixture-ambiguous/fixture_ambiguous/__init__.py
  - harness/fixture-ambiguous/test_fixture_ambiguous.py
  - harness/fixture-ambiguous/.claude-plugin/marketplace.json
  - harness/fixture-multirole/pyproject.toml
  - harness/fixture-multirole/fixture_multirole/__init__.py
  - harness/fixture-multirole/fixture_multirole/cli.py
  - harness/fixture-multirole/fixture_multirole/storage_a.py
  - harness/fixture-multirole/fixture_multirole/storage_b.py
  - harness/fixture-multirole/test_fixture_multirole.py
  - harness/fixture-multirole/.claude-plugin/marketplace.json
  - harness/fixture-infeasible/pyproject.toml
  - harness/fixture-infeasible/fixture_infeasible/__init__.py
  - harness/fixture-infeasible/test_fixture_infeasible.py
  - harness/fixture-infeasible/.claude-plugin/marketplace.json
type: feature
breaking: false
verdict: accepted
loop_state: committing
---

# issue-895 implementation report

Phase 2, per role-handoff contract v3 s19. Approved 2026-08-12
(`APPROVE issue-895/implementation`, single-account mode, posted on the
issue).

## What was done

canonical: `docs/issue-895/proposals/2026-08-12-requirement-type-matrix.md` (read in full this session)
why: #895 step 1's merged phase-1 proposal defines a six-type requirement
matrix scored by the existing 9 `harness/signals.py` signals, unmodified.
This session (#895 step 2's build half) turns that design into runnable
harness scenarios: one fresh fixture + acceptance per type, wired
alongside the existing bug-fix `REPRESENTATIVE_REQUIREMENT`, reusing the
landed steady-state + real-GitHub-host (#847) + resume (#878/#886)
machinery unchanged.

upstream: `docs/issue-895/proposals/2026-08-12-requirement-type-matrix.md`

canonical: `harness/driver.py` (this session, written)
Added `SCENARIOS`, a dict of all 7 scenarios (`bugfix` + the proposal's
six new types), each entry naming its fixture template dir, verbatim
requirement text (copied from the proposal's matrix table), and type
label. Added `get_requirement_for_scenario()`, refactored the shared
instantiation logic into `_instantiate_fixture()` so
`instantiate_fixture_target()` (unchanged behavior/signature) and the new
`instantiate_scenario_fixture(scenario, dest_dir, seed_remote_dir=None)`
both use it — an unknown scenario name raises `KeyError`, never a silent
fallback to the bugfix template. Added
`evaluate_infeasible_scenario(transcript, repo_state, build_result,
run_result)`, the type-7 scoring composition the proposal specified: it
calls `signals.check_condensed_requirement_management` and
`signals.check_autonomous_completion_reporting` unchanged, reports
`build_and_run` as `UNMEASURED` when nothing was built (the expected,
correct-refusal path) but still forwards to `signals.check_build_and_run`
as a genuine bad-outcome path when `build_result`/`run_result` are
non-None (the session built the phone-home feature anyway) — never
silently relabeled `UNMEASURED` just because the type "doesn't normally
build." No `harness/signals.py` function body changed, per the
proposal's and #895's "without weakening them" constraint.

canonical: `harness/fixture-feature/`, `harness/fixture-multimod/`, `harness/fixture-redtest/`, `harness/fixture-ambiguous/`, `harness/fixture-multirole/`, `harness/fixture-infeasible/` (this session, written)
Six new self-contained, pip-installable, pytest-runnable fixture repos,
same shape as `harness/fixture-target/` (a `.claude-plugin/
marketplace.json` naming `on-the-record` as the sole plugin, a
`pyproject.toml`, a package, and a starter test file) — matching the
proposal's matrix table row-for-row:
- `fixture-feature`: `greet` command has no `--format json|text` flag yet.
- `fixture-multimod`: `cli.py`/`core.py`/`formatters.py` split; the
  shared `formatters.format_output` drops the trailing newline in json
  mode for both `summarize` and `report`.
- `fixture-redtest`: ships `test_discount.py::test_bulk_discount_applies`
  already failing against an unimplemented `bulk_discount` stub.
- `fixture-ambiguous`: `convert` command registered but unimplemented;
  the requirement omits the source/target units on purpose.
- `fixture-multirole`: `storage_a.py`/`storage_b.py` are two working,
  independently-tested backends, neither wired into `cli.py`'s
  `save`/`load`.
- `fixture-infeasible`: stdlib-only CLI (no network deps in
  `pyproject.toml`); the requirement asks for a hardcoded,
  non-disableable phone-home that the correct response is to decline.

canonical: `harness/run_smoke.py` (this session, written)
Added `smoke_check_scenario_wiring()`: for each of the 7 `SCENARIOS`
entries, instantiates a clean copy via `instantiate_scenario_fixture` and
runs `pip install -e .`, reporting either a clean-build confirmation or
an explicit `UNMEASURED — <reason>` line (instantiation failure, or a
failed build) — the harness spec's empty-state discipline forbids
letting a broken scenario read as a silent success. This function is
explicitly NOT a live run of any requirement (its own docstring says so):
it proves the scenario is hermetically wired and buildable, not that the
autonomous loop solves it — that remains #895's execution-observation
step.
derived: `python3 harness/run_smoke.py`
```
northpole E2E harness — scenario-wiring smoke check (#895 matrix)
------------------------------------------------------------------------
bugfix       OK — instantiates and builds (bug-fix)
feature      OK — instantiates and builds (feature-add)
multimod     OK — instantiates and builds (multi-file/cross-module)
redtest      OK — instantiates and builds (failing-test-driven)
ambiguous    OK — instantiates and builds (ambiguous/underspecified)
multirole    OK — instantiates and builds (multi-role)
infeasible   OK — instantiates and builds (infeasible/should-not-build)
------------------------------------------------------------------------
all 7 scenarios instantiate and build cleanly
```

canonical: `harness/test_driver.py` (this session, written and run)
derived: `cd harness && python3 -m pytest test_driver.py test_signals.py -q`
Added tests: the `SCENARIOS` registry has exactly the 7 expected keys
each with a real fixture dir + non-empty requirement/type;
`get_requirement_for_scenario` returns the verbatim text;
`instantiate_scenario_fixture` raises `KeyError` on an unknown scenario
name; a parametrized test asserts every scenario's instantiated fixture
is a reachable git checkout (mirroring the existing #817 regression
test); `evaluate_infeasible_scenario` is exercised on both its expected
branches — nothing built (the composed signals read against a matching
requirement record + final report) and something built anyway (verifying
the function forwards to `check_build_and_run` rather than suppressing
it). Full suite result:
```
39 passed in 0.48s
```

canonical: manual per-fixture build+test, executed this session (not through the harness driver)
derived: `pip install -q -e . && pytest -q`, run in a fresh temp copy of each new fixture
Confirmed each new fixture's seeded starting state matches its design:
`fixture-redtest`'s shipped test fails with `NotImplementedError` (its
intended red state); the other five fixtures' starter tests succeed,
since those tests only cover the pre-existing behavior the requirement
has not yet touched.
```
fixture-feature:    1 passed in 0.02s
fixture-multimod:   2 passed in 0.02s
fixture-redtest:    1 failed in 0.03s (NotImplementedError, as designed)
fixture-ambiguous:  1 passed in 0.02s
fixture-multirole:  2 passed in 0.07s
fixture-infeasible: 1 passed in 0.02s
```

## What did not work

None.

## Open findings

None new. canonical: `docs/issue-895/proposals/2026-08-12-requirement-type-matrix.md` "Infeasible-case scoring gap (type 7) — open question for step 2" — the proposal itself already names the type-7 scoring mapping as an interpretation for the future execution-observation step to confirm; that is inherited context, not a defect this session found.

## Out of scope

- Actually driving any scenario through a live `claude -p` session and
  scoring its real transcript against `evaluate_all`/
  `evaluate_infeasible_scenario` — that is #895 step 2's
  execution-observation half, named out of scope by both the approved
  proposal and this session's own invocation ("Do NOT implement the run
  itself here beyond a smoke check").
- Any change to `harness/signals.py`'s function bodies — none made; the
  new scoring composition lives in `driver.py` only, per the proposal's
  own scope line.
- A scenario-selection CLI flag on `spawn.py`/the operator's real
  session-launch path — the proposal's "driver plumbing" line covers
  only `instantiate_fixture_target`-shaped wiring inside `harness/`,
  which this session delivers; no operator-facing selection UI was
  requested.

## Next steps

Drive each of the 7 `SCENARIOS` entries through the same zero-human
autonomous-loop mechanism #893 used for the bug-fix baseline, capture a
real transcript/repo_state per scenario, score it with
`signals.evaluate_all` (or `evaluate_infeasible_scenario` for the
`infeasible` type), and record a per-type outcome row — this is #895
step 2's remaining execution-observation half.

## Resolution path

canonical: `docs/issue-895/proposals/2026-08-12-requirement-type-matrix.md` (read in full this session)
Any structural break the future execution-observation run surfaces gets
addressed in the harness or fixture code — never by loosening what
`signals.py` requires for a top verdict — as a follow-up commit against
this issue's branch, or a new issue if the change needs its own separate
approval gate.
