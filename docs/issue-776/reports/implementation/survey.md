# Current-state survey — issue #776 step 2 (implementation)

Scout skip condition invoked: the spec (`docs/specs/northpole-harness.md`,
merged from the approved product-discovery design PR #777) leaves no
product-facing design decision open — fixture repo shape, representative
requirement text, the 7-signal table, the observation method, and the
build-and-run commands are all frozen. This step only has to translate
that frozen design into files and a runnable driver; scouting a
category's best-in-class E2E harness product would not change any of
those already-fixed choices. Per scout-directive this is recorded here
as the mandatory skip line rather than run.

## What already exists

- `docs/specs/northpole-harness.md` — the frozen design (fixture repo
  layout, requirement text, signal table, observation method, build/run
  commands, decision rule).
- `docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-design.md`
  — the approved phase-1 proposal for the design step (product-discovery
  role), landed via PR #777.
- Repo root layout (`ls .`): `on-the-record/` (the plugin itself, with
  `on-the-record/.claude-plugin/plugin.json`), `roles/`, `gates/`,
  `spawn.py`, `docs/`. No existing harness or fixture-target directory
  anywhere in the tree — this is new ground.
- `on-the-record/.claude-plugin/plugin.json` — reference shape for a
  Claude Code plugin manifest (`name`, `description`, `author`). This is
  the manifest format the fixture repo's own `.claude-plugin/` install
  pointer must match when it references on-the-record as a plugin
  dependency.
- No existing prior art under this step's own report directory; this is
  the first implementation-role work on this issue.

## Write-set unknowns the design left to this step

The design (`northpole-harness.md`) fully specifies the fixture repo's
*content* (pyproject.toml + module + test) and the 7 signals, but not:

1. **Where in the on-the-record tree the fixture-repo template and the
   harness driver/checks live.** The design says the fixture repo must
   NOT be nested inside on-the-record as a *live git repo* (so it can be
   git-init'd and built standalone), but the harness needs a checked-in
   template to instantiate from and driver/check code to commit. Given
   the repo's enforced output layout (code, tests, and docs each in
   their own standing bucket, with non-src/test operational tooling —
   `gates/`, `roles/`, `spawn.py` — already living at top level), the
   natural home is a top-level `harness/` directory holding the
   fixture-target template plus the driver and signal-check scripts,
   following that existing precedent rather than inventing a new one.
2. **Driver implementation language/shape.** Design only specifies what
   the driver *does* (install plugin, paste requirement, wait for halt,
   capture transcript). Python is the natural choice: the rest of
   on-the-record's automation (`spawn.py`, `gates/*.py`) is Python, and
   the fixture target itself is Python, so no new language/toolchain
   enters the write set (avoids an operational-surface commit needing a
   handbook touch per contract §21 — no new dependency manifest needed
   beyond what already exists).
3. **Signal-check implementation.** The design's 7-row table needs a
   concrete script that reads a transcript log + repo state and emits
   the UNMEASURED/PASS/FAIL verdicts. This does not exist yet anywhere
   in the repo.
4. **What "smoke check" (this turn's actual deliverable, per the
   issue's step 2 scope) means mechanically**: run the signal-emission
   code against a canned/synthetic transcript+repo-state fixture (not a
   live plain-session run — that is step 3, explicitly out of scope
   here) and assert it emits all 8 rows (7 signals + build-and-run) in
   the UNMEASURED/PASS/FAIL vocabulary, never silently omitting a row.

## Write set this step will need (frozen into the proposal)

- `harness/fixture-target/pyproject.toml`
- `harness/fixture-target/fixture_target/__init__.py`
- `harness/fixture-target/test_fixture_target.py`
- `harness/fixture-target/.claude-plugin/` install pointer (per design
  §1: on-the-record present only via plugin install path)
- `harness/driver.py` — orchestrates operator-only actions (§4 of spec)
- `harness/signals.py` — the 7-signal + build-and-run check logic (§3, §5)
- `harness/run_smoke.py` — this step's smoke entry point: exercises
  `signals.py` against a synthetic transcript fixture, prints the
  8-row report
- `harness/README.md` — how to run the harness for real (step 3) vs. the
  smoke check (this step)
- this step's own phase-2 record, under this issue's implementation
  report path
