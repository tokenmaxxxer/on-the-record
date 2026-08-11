---
status: proposed
files:
  - harness/fixture-target/pyproject.toml
  - harness/fixture-target/fixture_target/__init__.py
  - harness/fixture-target/test_fixture_target.py
  - harness/fixture-target/.claude-plugin/marketplace.json
  - harness/driver.py
  - harness/signals.py
  - harness/run_smoke.py
  - harness/README.md
  - docs/issue-776/reports/implementation/survey.md
  - docs/issue-776/proposals/2026-08-11-northpole-e2e-harness-implementation.md
  - docs/issue-776/reports/implementation.md
---

# Northpole E2E acceptance harness — implementation (issue #776 step 2)

## Request

Build the E2E acceptance harness exactly as frozen in
`docs/specs/northpole-harness.md`: the fixture target repo (single-file
Python CLI with a seeded defect), on-the-record installed as plugin-only,
a driver that gives the one representative requirement to a plain session
with zero human intervention, and the per-requirement signal checks (7
signals + build-and-run) with the UNMEASURED empty-state rule. This step
delivers a runnable harness and a smoke check that it emits the correct
signal structure — not a baseline run against a live session (issue
#776 step 3, out of scope here).

## Constraints

- Follow `docs/specs/northpole-harness.md` exactly; no new design
  decisions on fixture shape, requirement text, signal table, or
  build/run commands — those are frozen.
- No CI, no repo-level skill/command invocation inside the fixture repo;
  on-the-record present only via a Claude Code plugin install pointer.
- Harness code must not introduce a new dependency/toolchain — Python
  only, matching the rest of the repo's automation (`spawn.py`,
  `gates/*.py`) and the fixture target itself.
- This step does not run a live plain-session E2E pass (step 3); it
  delivers a runnable driver + signal checker and proves the checker's
  output shape via a smoke check against a synthetic transcript/repo
  fixture.
- Output layout: code/tests/docs in their proper buckets; the fixture
  repo's own pyproject.toml counts as an operational-surface file for
  contract §21 purposes only within the fixture, but since
  `harness/fixture-target/` is a template checked in under this repo's
  own tree (not a live git submodule), commit it alongside
  `harness/README.md` (a handbook-shaped doc) in the same commit to
  satisfy contract §21's pairing rule.

## Rationale

Two placement/shape alternatives were weighed during the survey:

1. **Chosen: a top-level `harness/` directory** holding both the
   fixture-target template and the driver/signal-check scripts,
   mirroring how `gates/`, `roles/`, and `spawn.py` already sit outside
   `src/`/`test/` for repo-operational tooling.
2. **Rejected: nest the fixture template under `docs/issue-776/`** as a
   documentation asset, keeping only a thin runner elsewhere. Rejected
   because the fixture-target repo is not documentation — it is
   real, buildable, installable code (a pyproject.toml, a package, a
   test file) that must be `pip install -e`-able and `pytest`-able on
   its own; docs/ is reserved for the six standing document buckets, not
   for a checked-in software project, and burying real code under docs/
   would violate the repo's own code-under-src/docs-under-docs
   separation in spirit even though `harness/` isn't literally `src/`.

For the driver's implementation language, Python was chosen over shelling
out to a language-agnostic script because it lets `driver.py` reuse the
same subprocess/log-capture patterns already established in
`gates/*.py`, and avoids introducing a second language's toolchain into
a repo whose existing automation is uniformly Python — no alternative
language was seriously in contention given that constraint.

## What will be done

1. **Fixture target repo template** (`harness/fixture-target/`):
   - `pyproject.toml` — minimal setuptools/pyproject package named
     `fixture-target`, console-script entry point `fixture-target`.
   - `fixture_target/__init__.py` — CLI entrypoint (`argparse`-based)
     plus a small argument-parsing helper function, one layer removed
     from the entrypoint, that raises on `--version` due to a seeded
     bug (reads a version constant via a broken lookup) so the crash's
     root cause is not the first place a naive fix would look — matching
     the design's signal-#5 non-obvious-defect requirement.
   - `test_fixture_target.py` — one test file; starts with a test that
     currently fails against the seeded defect (proving the defect is
     real and mechanically detectable), giving the driven session real
     failing-test signal to work from.
   - `.claude-plugin/marketplace.json` — plugin-install pointer that
     references the on-the-record plugin path, mirroring
     `on-the-record/.claude-plugin/plugin.json`'s shape; this is the
     fixture repo's *only* reference to on-the-record (no CI, no skill
     invocation elsewhere in the fixture).
2. **`harness/driver.py`** — operator-only actions per spec §4: given a
   target directory, copies/instantiates the fixture-target template
   into a clean working copy, and provides the scripted steps (paste the
   representative requirement text, wait for halt or wall-clock cap,
   capture transcript/log) as callable functions. Actually launching a
   live Claude Code session is left as an integration point (a callable
   the operator wires to their session-launch mechanism) — step 2 does
   not itself perform a live run; step 3 does.
3. **`harness/signals.py`** — implements the 7-row signal table (spec
   §3) plus the build-and-run assertion (spec §5) as pure functions over
   (a) a transcript/log structure and (b) a fresh checkout of the
   resulting fixture repo state, each returning PASS / FAIL / UNMEASURED
   per the empty-state rule — never silently omitting a row.
4. **`harness/run_smoke.py`** — this step's own deliverable per the
   issue's Acceptance: runs `signals.py` against a small synthetic
   transcript + repo-state fixture (not a live session) and prints the
   8-row report (7 signals + build-and-run), asserting all 8 rows are
   present and each is one of PASS/FAIL/UNMEASURED. Exits non-zero if any
   row is missing.
5. **`harness/README.md`** — how to run the smoke check now
   (`python3 harness/run_smoke.py`) versus how to run the real baseline
   later (step 3, wiring `driver.py` to a live session).
6. Write this step's phase-2 record at `docs/issue-776/reports/implementation.md`
   once phase 2 opens.

## Out of scope

- Running the harness against a real, live plain session (issue #776
  step 3 — a separate execution-plan step / separate role invocation).
- Any change to `docs/specs/northpole-harness.md`,
  `docs/specs/northpole.md`, or the 17-row conformance backlog.
- A CI workflow that runs the harness automatically (the fixture must
  have none, and this repo's own CI is out of this issue's scope).
- Extending to more than the one representative requirement.

## How you'll know it worked

`python3 harness/run_smoke.py` runs from repo root, exits 0, and prints a
report naming all 7 northpole requirements plus the build-and-run
assertion, each tagged PASS/FAIL/UNMEASURED — no row silently missing.
Separately, `pip install -e harness/fixture-target && fixture-target
--version` reproduces the seeded crash (proving the fixture's defect is
real) and `pytest harness/fixture-target` shows the seeded test failing
for the same reason — both confirming the fixture is a genuine,
buildable target before any fix is applied.

## Accumulation

Not accumulation-cost-shaped: a one-time harness build with a fixed
7-signal table and one fixture, not a per-instance-scaling artifact. N/A.
