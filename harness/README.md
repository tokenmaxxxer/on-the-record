# Northpole E2E acceptance harness

Design: `docs/specs/northpole-harness.md`. Issue: #776.

## What's here

- `fixture-target/` — a minimal, real-buildable single-file Python CLI
  package with a seeded defect (`--version` crashes) and on-the-record
  installed as its only plugin (`.claude-plugin/marketplace.json`), no CI,
  no explicit skill invocation.
- `signals.py` — the 7 per-requirement pass/fail signal checks (spec §3)
  plus the build-and-run assertion (spec §5), each returning
  `PASS`/`FAIL`/`UNMEASURED`.
- `driver.py` — operator-only actions (spec §4): instantiate a clean
  fixture-target working copy, run build/test commands, and hold the
  representative requirement text. Launching a live Claude Code session is
  an integration point the operator wires themselves.
- `run_smoke.py` — this step's own deliverable: proves `signals.py` emits
  the correct 8-row report shape against a synthetic transcript/repo-state
  fixture. NOT a live baseline run.

## Run the smoke check now

```
python3 harness/run_smoke.py
```

Exits 0 and prints all 8 rows (7 signals + build-and-run), each tagged
PASS/FAIL/UNMEASURED, when the signal-emission shape is correct. Exits
non-zero if any row is missing or carries an invalid verdict.

## Confirm the fixture is a genuine target (before any fix)

```
pip install -e harness/fixture-target
fixture-target --version   # reproduces the seeded crash
pytest harness/fixture-target   # one test fails for the same reason
```

## Run the real baseline later (issue #776 step 3)

1. Use `harness.driver.instantiate_fixture_target(dest_dir)` to get a clean
   working copy.
2. Install the on-the-record plugin into that copy.
3. Paste `harness.driver.get_representative_requirement()` verbatim as the
   first and only message to a fresh plain session.
4. Do not respond to anything else until the session halts on its own or a
   wall-clock cap is reached; capture the full transcript.
5. Build a `transcript` dict and a `repo_state` dict from that capture (see
   the shapes consumed by `signals.evaluate_all` — `run_smoke.py`'s
   synthetic fixtures show the expected keys), run
   `driver.run_build` / `driver.run_version_check` / `driver.run_tests`
   against the resulting repo state, and call
   `signals.evaluate_all(transcript, repo_state, build_result, run_result)`
   for the real baseline.

## Requirement digest & drift guard (issue #930)

`fixture-requirement-digest/scenario.py` proves the merged design's
four acceptance points on a seeded scratch repo — no live session
needed, since the design is a plugin/hook mechanism, not an LLM
behavior: digest condensation stays O(requirement count) even as
synthetic records pile up, the commit-time hook denies/allows
correctly (including the `-a`-rewrites-status-to-stale path), a
digest-only selection picks a still-`open` requirement, and
`spawn.requirement_drift()` fires advisory findings without blocking
anything.

```
python3 harness/fixture-requirement-digest/scenario.py
```

Exits 0 and prints all 5 rows PASS (4 acceptance points + the req#7
`.github/workflows/` wiring check). Exits non-zero otherwise.
