---
status: proposed
files:
  - pytest.ini
  - test_spawn.py
---

files: pytest.ini, test_spawn.py

## Request

#540: in a live checkout with a populated (gitignored) `runs/rulebooks/`
tree, `python3 -m pytest -q` walks into it during collection and
collides with same-basename modules under `test/`, producing collection
ERRORs; the same live checkout also shows `test_spawn.py::Drive`
failures (`FileNotFoundError '/x'`) that a clean worktree doesn't show.
Fix collection so it matches the clean-worktree result, and determine
whether the `Drive` failures share that root cause or a different one.

SCOUT SKIP: pure bugfix, no design decision open — see
`docs/issue-540/reports/implementation/survey.md`.

## Constraints

- Collection must exclude `runs/` (and anything else `.gitignore`
  marks) without narrowing what legitimate test files get collected
  under `test/`/`tests/`.
- No behavior change to `spawn.py` production code — the `Drive` test
  fix is test-only isolation, not a change to `ROSTER`'s real path.

## Rationale

`norecursedirs = runs` (adding it to the existing `[pytest]` section)
was considered against setting `testpaths = test tests` explicitly.
`testpaths` was rejected as the primary fix: it would silently exclude
any *other* directory a future test file might live in (e.g. a new
top-level `test_*.py` at repo root — several already exist there:
`test_approve_scope.py`, `test_flows.py`, `test_gates.py`, etc.) unless
that directory is added to the allow-list too, which is a wider,
easier-to-forget surface than a targeted deny-list of the one directory
that's actually gitignored and actually the problem. `norecursedirs`
matches the failure mode precisely (don't walk gitignored trees) without
having to enumerate every legitimate test location by hand.

For the `Drive` test isolation, patching `spawn.ROSTER` directly (rather
than `spawn.ROOT`, which `RequireDoctor._with_root` patches) was chosen
because `ROSTER` is a module-level constant computed once from `ROOT` at
import time — patching `ROOT` after import has no effect on the
already-bound `ROSTER` value, confirmed by reading `spawn.py:1670`.

## What will be done

- Add `norecursedirs = runs` to `pytest.ini`'s `[pytest]` section so
  collection skips the gitignored `runs/` tree entirely.
- In `test_spawn.py`'s `Drive` class, monkeypatch `spawn.ROSTER` to a
  path under a `tempfile.TemporaryDirectory()` for each test (mirroring
  `RequireDoctor._with_root`'s patch-and-restore-in-`finally` shape) so
  the tests exercise `_roster_load()` against an isolated, empty/known
  fixture instead of whatever `runs/active.json` happens to hold in the
  real checkout.
- Run `python3 -m pytest -q` locally to confirm collection is clean and
  `Drive` tests pass regardless of what's in the live `runs/` tree.

## Out of scope

- Changing where `runs/rulebooks/**` clones live, or how orchestration
  populates them — this issue is about test/collection isolation from
  that tree, not the tree's own design.
- Any other live-only test divergence not already identified as the
  `Drive` class's `ROSTER` leak.

## Accumulation

`test_spawn.py` already crosses the inline-subprocess-call-site
threshold this repo's accumulation guard watches for (shape 1), from
pre-existing tests unrelated to this change (e.g.
`IssueScopedPrompt.test_preparation_and_preamble_happen_once`'s `git`
invocations). This proposal's edits to the `Drive` class add zero new
subprocess/gh call sites — only a `tempfile.TemporaryDirectory()` +
monkeypatch pattern already used by `RequireDoctor._with_root` in the
same file. If this pattern repeats N more times it stays bounded: each
addition is one more test class reusing the same small
patch-and-restore helper shape, not a new inline subprocess site, so it
does not compound the counted accumulation shape.

## How you'll know it worked

- `python3 -m pytest -q` collects with zero collection ERRORs in a
  checkout containing a populated `runs/rulebooks/` (simulated via a
  temp directory with a same-basename test file dropped under `runs/`
  during verification).
- `python3 -m pytest -q test_spawn.py -k Drive` passes both in a clean
  worktree and with a non-empty `runs/active.json` present.
