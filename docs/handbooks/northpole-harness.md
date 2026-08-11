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

## Running it

- Smoke check (signal-emission shape only, no live session):
  `python3 harness/run_smoke.py`
- Confirm the fixture's seeded defect is real: `pip install -e
  harness/fixture-target && fixture-target --version` (reproduces the
  crash), `pytest harness/fixture-target` (one test fails against it).
- Live baseline run against a real session (issue #776 step 3): see
  `harness/README.md`'s "Run the real baseline later" section.
