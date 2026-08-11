# Test layout

Where a new test file goes, by default and by exception (issue #729).

## Default: `tests/`

Every Python and shell test file that imports `spawn`, `gates`, or a
root-level module through a repo-root-relative `sys.path.insert` lives
under `tests/` — this is the single consolidated home for what used to
be split across a root-level `test/` directory and nine loose
`test_*.py`/`shape_contracts.py` files directly at repo root. `tests/`
was kept as the survivor name (over `test/`) because it was already
anchored by code: `conftest.py`'s fixture root and `shape_contracts.py`'s
golden-sample path both already resolved under `tests/fixtures/` before
this consolidation, and it matches the pytest-ecosystem convention.

A test file under `tests/` that needs the repo root (for a `sys.path`
insert, a `Path(__file__)`-relative constant, or a fixture directory)
resolves it as `Path(__file__).parent.parent` (or the `os.path`
equivalent) — one level up from `tests/`, not `Path(__file__).parent`.

## Exceptions: colocation next to implementation

Two areas keep their tests colocated with the code they test, and do
**not** move into `tests/`:

- `gates/` — every `gates/test_*.py` file imports its sibling
  implementation module through a same-directory `sys.path.insert`
  (e.g. `sys.path.insert(0, str(Path(__file__).parent))`).
- `on-the-record/hooks/` — same pattern, same reason.

This is a deliberate, recognized pattern (tests living next to the
module they exercise), not scatter to be cleaned up. Moving either into
`tests/` would force either a repo-wide import-path rewrite or
introducing package boundaries (`__init__.py`) that change how
`gates.duplicate_test_basenames` (issue #398) reasons about the tree —
out of scope unless a future issue takes that on deliberately.

## `conftest.py` stays at repo root

pytest only applies a `conftest.py`'s fixtures to test files in its own
directory subtree (siblings and descendants) — never to siblings of
that directory. Since `gates/` and `on-the-record/hooks/` tests stay
outside `tests/`, moving `conftest.py` into `tests/` would silently stop
injecting its fixtures (the issue #204 environment-default fixture, the
issue #360 session-leak check) for every test outside `tests/`. It stays
at root so its fixtures reach the whole tree.

## Picking a location for a new test file

- Testing a `gates/*.py` or `on-the-record/hooks/*` module? Colocate:
  put the test next to the module, same directory, same
  `sys.path.insert(0, str(Path(__file__).parent))` pattern the rest of
  that directory already uses.
- Everything else (testing `spawn.py`, a root-level module, or anything
  that isn't `gates/`/`on-the-record/hooks/`-scoped): put it under
  `tests/`, and reach the repo root via `Path(__file__).parent.parent`.

Whichever location, keep the test's basename unique repo-wide —
`gates.duplicate_test_basenames` (issue #398) fails the build on a
collision, colocated or not.
