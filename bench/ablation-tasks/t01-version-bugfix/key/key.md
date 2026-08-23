# Answer key — t01-version-bugfix (HIDDEN: never enters a run workspace)

Class: bugfix  ·  Fixture: harness/fixture-target

## Acceptance behaviors (one scoresheet row each)

- **a1** — `fixture-target --version` (after `pip install -e .`) prints `0.1.0` and exits 0 — no traceback.
- **a2** — The fix targets the seeded defect: `_resolve_version` reads `_pkg.VERSION`, which does not exist; the correct attribute is `__version__` (or an equivalent that keeps a single version source).
- **a3** — A test exists that fails on the pre-fix code and passes post-fix (exercises the version-resolution path, not just Namespace plumbing).
- **a4** — Existing tests in test_fixture_target.py still pass.

## Adjudication

Run the build+CLI yourself in the run workspace; do not trust the arm's own report. a3 requires checking the test actually touches the fixed path (revert the fix mentally or literally and confirm the test would fail).
