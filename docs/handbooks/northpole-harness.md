# Northpole E2E acceptance harness

The northpole harness (issue #776) lives under `harness/` at repo root, not
under `src/`/`test/` — it is repo-operational tooling, the same category as
`gates/`, `roles/`, and `spawn.py`. Full design: `docs/specs/northpole-harness.md`.
How to run it: `harness/README.md`.

## Operational surface

`harness/fixture-target/pyproject.toml` is a standalone, installable Python
package (`fixture-target`) with its own build backend
(`setuptools>=61.0`). It is not part of on-the-record's own package — it is
a fixture repo template that gets copied out and `pip install -e`'d
separately, per `harness/driver.instantiate_fixture_target`. Installing it
does not touch or depend on on-the-record's own environment.

## The plugin pointer

`harness/fixture-target/.claude-plugin/marketplace.json` is the fixture
repo's only reference to on-the-record anywhere in its tree — no CI config,
no explicit skill/command invocation. It points at
`tokenmaxxxer/on-the-record` on GitHub, mirroring the shape of this repo's
own root `.claude-plugin/marketplace.json`, so an operator installing the
fixture's marketplace gets on-the-record as a plugin exactly the way any
other user would.

## Steady-state faithful GitHub host (issue #847)

The steady-state scenario needs a real GitHub host so a delegated role's
`gh` issue/PR/merge calls succeed (a local bare `file://` remote passes
`git remote get-url origin` but `gh` refuses it — issue #847). Two
harness-only env vars, read by `harness/driver.py`, never by anything a
normal plugin install reads:

- `NORTHPOLE_HARNESS_GH_REPO` — `owner/repo` of the throwaway, private
  fixture host repo. Defaults to `JiwonJung94/northpole-harness-fixture`.
- `NORTHPOLE_HARNESS_GH_TOKEN` — a token scoped to that repo. If unset,
  falls back to the ambient `gh auth token` (the account `gh auth login`
  already authenticated).

`driver.seed_steady_state_github_host(dest_dir)`:
- when a repo + token resolve, deletes every non-default branch on the
  host via `gh api` and force-pushes `dest_dir`'s current HEAD as the
  default branch, so every run starts from the same clean slate, then
  wires `origin` to the real GitHub remote;
- when no repo/token resolves, returns `{"available": False, "reason":
  ...}` and leaves `dest_dir` untouched — the scenario must report this
  as UNMEASURED-with-reason, never a crash and never a false PASS.

To run the delegated role's own `gh` calls against this host, also export
the same token as `GH_TOKEN` (or `GITHUB_TOKEN`) in the session's own
environment before launch — `gh` reads that var directly, with no `gh
auth login` step needed (`gh` docs:
https://cli.github.com/manual/gh_auth_token).

## Requirement-type matrix (issue #895)

`harness/driver.SCENARIOS` extends the single bug-fix scenario above to
seven: `bugfix` (existing `fixture-target/`, `REPRESENTATIVE_REQUIREMENT`)
plus six new fixture repos under `harness/fixture-<name>/` — `feature`,
`multimod`, `redtest`, `ambiguous`, `multirole`, `infeasible` — one per
requirement type in `docs/issue-895/proposals/
2026-08-12-requirement-type-matrix.md`'s matrix. Each has the same
operational shape as `fixture-target/` (standalone `pyproject.toml`,
own `.claude-plugin/marketplace.json` pointing at on-the-record, a
starter test file) and is buildable/installable independently of
on-the-record's own environment.

`driver.instantiate_scenario_fixture(scenario, dest_dir,
seed_remote_dir=None)` instantiates any of the seven by name (raises
`KeyError` on an unknown name — never a silent fallback to `bugfix`).
`driver.get_requirement_for_scenario(scenario)` returns that scenario's
verbatim requirement text.

Six of the seven score with the existing `signals.evaluate_all`
unchanged. The `infeasible` type (correct outcome: decline to build) has
no signal whose top verdict means "correctly declined," so
`driver.evaluate_infeasible_scenario(transcript, repo_state,
build_result, run_result)` composes `signals.check_build_and_run`
(reported `UNMEASURED` when nothing was built, the expected path — but
still forwarded to a real bad-outcome check if something WAS built) with
`signals.check_condensed_requirement_management` and
`signals.check_autonomous_completion_reporting`. No `signals.py`
function body is modified by this composition.

Scenario-wiring smoke check (buildability only, not a live requirement
run): `python3 harness/run_smoke.py` also instantiates and `pip install
-e`'s each of the seven scenarios, reporting `UNMEASURED — <reason>` for
any that fails to instantiate or build. Driving each scenario through a
real session and scoring the resulting transcript is issue #895's
execution-observation step, not yet done.

## Concurrent-judgment fixture (issue #973)

`harness/fixture-concurrent-judgment/` is a standalone `pyproject.toml`
package (`fixture-concurrent-judgment`, same `setuptools`/`packages`
shape as `fixture-multirole/`) holding `test_panel.py`: an end-to-end
test of `spawn.py`'s `panel_cmd()` against seeded stand-ins injected
through its `run_session` parameter (the transport-boundary
dependency-injection point — no real `claude -p` process is spawned,
matching every other `harness/fixture-*/` test). One test drives a live
two-judge exchange (position + rebuttal + verdict landing in the panel
record file); one drives the degraded-to-sequential-consult path. Run
with `pytest harness/fixture-concurrent-judgment`.

## Running it

- Smoke check (signal-emission shape only, no live session):
  `python3 harness/run_smoke.py`
- Confirm the fixture's seeded defect is real: `pip install -e
  harness/fixture-target && fixture-target --version` (reproduces the
  crash), `pytest harness/fixture-target` (one test fails against it).
- Live baseline run against a real session (issue #776 step 3): see
  `harness/README.md`'s "Run the real baseline later" section.
