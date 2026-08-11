# Current-state survey (issue #729) — test directory layout

Scope: read-only survey of every test home in the repository, the
hardcoded references that name them, the one existing gate that
constrains where a test file may live, and the pytest import mechanics
that decide whether moving a file breaks its imports. No files changed
in this pass.

## The five homes, as they stand today

derived: `wc -l test_*.py conftest.py shape_contracts.py` (repo root)

```
     133 test_approve_scope.py
     165 test_flows.py
    1561 test_gates.py
      83 test_issue_bundling.py
      47 test_repo_scope_gate.py
    8210 test_spawn.py
      90 test_spec_index.py
      27 test_vocab_coherence_roles.py
      51 conftest.py
     187 shape_contracts.py
   10554 total
```

- **Root** — the eight `test_*.py` files above, plus `conftest.py` and
  `shape_contracts.py`, sit next to `spawn.py` with no owning directory.
- **`test/`** (singular) — five Python unit-test files
  (`test_bootstrap_timing.py`, `test_latency_report.py`,
  `test_portability_audit_table.py`, `test_side_effect_round.py`,
  `test_silent_failure_repros.py`) and two shell tests
  (`check-write-set-conflicts.test.sh`, `claim-scan-preflight.test.sh`).
- **`tests/`** (plural) — one shell test (`test_stop_gate.sh`), one shell
  test *runner* (`run-orchestrate-tests.sh`, drives
  `on-the-record/hooks/*.sh` — not itself a test), and `fixtures/`
  (`golden/`, `rulebooks/`), the fixture data root that `conftest.py`
  and `shape_contracts.py` already point at.
- **`gates/`** — forty-plus `test_*.py` files, each colocated with the
  gate module it exercises (e.g. the gate-shape tests sit next to
  `gates.py`).
- **`on-the-record/hooks/`** — one Python test per shell hook script
  (e.g. `test_approval_gate.py` next to `approval-gate.sh`).

No directory anywhere in the tree carries an `__init__.py` — the whole
suite collects into one flat pytest namespace. That fact is load-bearing
for two things found below: import mechanics, and the one gate that
already polices this layout.

## Why `test/` and `tests/` are not a deliberate split

`test/` holds Python unit tests and two shell tests; `tests/` holds one
shell test, a shell runner, and fixtures. Neither directory maps to a
single principle ("python vs shell", "unit vs integration"). The
plural-named directory is the one already anchored by code: `conftest.py`
builds its fixture root from `Path(__file__).parent / "tests" /
"fixtures" / "rulebooks"` (issue #204), and `shape_contracts.py`
verifies a captured sample under `tests/fixtures/golden/`. Nothing
anchors `test/` (singular) the same way. Every file the two directories
hold today has plenty of historical references from past issue reports
(`docs/issue-*/reports/...`, `docs/issue-*/proposals/...`) — expected,
since those are point-in-time records the issue's own scope explicitly
excludes from rewriting.

## The one gate that already constrains this layout

`gates/gates.py` defines `duplicate_test_basenames` (issue #398): it
walks the whole tree, skips any directory containing `__init__.py`, and
fails if two test-shaped basenames collide outside that boundary. It
exists precisely because a file once named gates/test_gates.py collided
with root `test_gates.py` (issues #330/#337) and broke collection only
after merge, invisibly to either PR alone (the gates-side file has since
been renamed to `gates/test_duplicate_test_basenames.py`, which
regression-guards the current tree with a permanent assertion):

```
def t_duplicate_test_basenames_passes_on_current_tree():
    root = Path(__file__).parent.parent
    bad = gates.duplicate_test_basenames(root)
    assert bad == [], bad
```

derived: `python3 gates/test_duplicate_test_basenames.py`

```
  ok  t_duplicate_test_basenames_catches_reintroduced_collision
  ok  t_duplicate_test_basenames_ignores_directories_with_init_py
  ok  t_duplicate_test_basenames_no_runs_dir_behaves_identically
  ok  t_duplicate_test_basenames_passes_on_current_tree
  ok  t_duplicate_test_basenames_passes_with_no_collision
  ok  t_duplicate_test_basenames_skips_gitignored_runs_dir
  ok  t_duplicate_test_basenames_still_catches_collision_outside_runs

7 passed
```

Consequence for any move: consolidating root/`test/`/`tests/` into one
directory is safe against this gate today (no two files share a
basename across the five homes), but the gate is the mechanical fence
against a future rename accidentally re-introducing a collision — it
does not itself argue for or against colocation.

## Import mechanics: why colocation for `gates/` and `on-the-record/hooks/` is a real constraint, not an accident

Every test file that imports `spawn` from outside repo root does it
explicitly, because pytest's default import mode only puts a collected
file's own directory on `sys.path` — nothing walks up to repo root on
its own:

derived: `grep -B1 "^import spawn" gates/closure_sweep.py gates/test_closure_sweep.py test/test_bootstrap_timing.py`

```
gates/closure_sweep.py-sys.path.insert(0, str(Path(__file__).parent.parent))
gates/closure_sweep.py:import spawn  # noqa: E402
gates/test_closure_sweep.py-sys.path.insert(0, str(Path(__file__).parent.parent))
gates/test_closure_sweep.py:import spawn
test/test_bootstrap_timing.py-sys.path.insert(0, str(Path(__file__).parent.parent))
test/test_bootstrap_timing.py-import spawn  # noqa: E402
```

Every one of the eight root `test_*.py` files that imports `spawn`,
`shape_contracts`, or a `gates/`-only module (`test_approve_scope.py`,
`test_flows.py`, `test_gates.py`, `test_issue_bundling.py`,
`test_repo_scope_gate.py`, `test_spawn.py`, `test_spec_index.py`) relies
on its *own* directory already being repo root — none of them currently
need a `sys.path.insert` for that, because they already sit there. Move
any of them into a `tests/` directory and that implicit path breaks
unless a `sys.path.insert(0, str(Path(__file__).parent.parent))` (the
exact line already used by `gates/closure_sweep.py`, `test/test_bootstrap_timing.py`,
and others) is added. `shape_contracts.py` is imported bare
(`import shape_contracts`) only by `test_spawn.py` and
`gates/test_closes_gate_ci.py` — the latter already inserts repo root
onto its path for `spawn`, so moving `shape_contracts.py` alongside the
root test files into `tests/` keeps both import sites working (same-directory
import needs no insert; `gates/test_closes_gate_ci.py`'s existing
root-level insert already reaches it).

This means "move the eight root test files" is not a pure `git mv`: it
is a `git mv` plus a one-line `sys.path.insert` addition in each file
that imports a root-level module implicitly today.

## The three fragile points named in the issue, confirmed

1. **Hardcoded invocation strings.** `spawn.py` builds a tuple of
   command prefixes it recognizes as "makes progress" (used to decide
   whether a session's bash call fires a progress event):

   derived: `grep -n "python3 test_spawn.py" spawn.py test_spawn.py`

   ```
   spawn.py:2197:                           "python3 test_spawn.py", "python3 gates/ci.py")
   test_spawn.py:2810:                        "python3 test_spawn.py", "python3 gates/ci.py ."):
   ```

   Line 2197 is production code — the literal string is matched against
   real bash commands during a live session, not just asserted in a
   test. Moving `test_spawn.py` without updating this tuple silently
   stops recognizing the (now-wrong) invocation string; the test at
   line 2810 asserts against the same tuple and would need the same
   edit to stay meaningful. A second, cosmetic pair of hardcoded
   examples sits around lines 6006 and 6010 (an example bash command fed to
   a command-description function, plus its expected description
   string) — these do not gate real behavior, but would describe a path
   that no longer exists if left unedited.

2. **`conftest.py`'s root position.** Confirmed by the import-mechanics
   finding above and independently by the scout brief
   (`docs/issue-729/reports/implementation/scout-brief.md`): pytest
   applies a `conftest.py`'s fixtures to every test file in its own
   directory subtree (siblings and descendants), not to siblings of the
   directory. Root is the only position from which one `conftest.py`
   reaches every one of the five homes at once. Moving it to any
   subdirectory would silently stop applying the issue #204 env-default
   fixture and the issue #360 session-leak check to every test file
   outside that subdirectory — a functional regression with no error
   message, since pytest just quietly does not load a conftest.py for
   directories outside its reach.

3. **`pytest.ini`.** `python_functions = test_* t_*` (the repo mixes
   `unittest`-style `test_*` methods and bare `t_*` functions — both
   conventions are already in live use, e.g. `test_flows.py` uses
   `t_*`) and `norecursedirs = runs` (excludes the gitignored session-checkout
   tree). Neither setting names a specific test directory, so
   consolidating `test/`+`tests/` does not require touching this file.

## A fourth fragile point, not in the issue's pre-investigation list

`test_vocab_coherence_roles.py` resolves its fixture directory relative
to its own file location, not repo root:

```
ROLES_DIR = os.path.join(os.path.dirname(__file__), "roles")
```

`roles/` is a repo-root directory (role `.json` specs), reachable today
only because the test file's own directory already is repo root. Moved
without a path fix, `ROLES_DIR` would resolve to a nonexistent
subdirectory under the new location; `glob.glob` on a missing directory
returns an empty list, `offenders` stays empty, and the test keeps
*passing* — silently checking zero files instead of raising
`FileNotFoundError` or failing loudly. This is the one file in the move
set where a naive `git mv` produces no error and no test-count change,
yet quietly stops enforcing anything. Confirmed present-tense (repo root
does hold a `roles/` directory):

derived: `test -d roles && echo present`

```
present
```

## Live (non-historical) documents that name these paths

`docs/handbooks/operations.md` is a currently-maintained handbook (not a
frozen `docs/issue-*/` record) and names root test paths in live
prose: a self-check command example (`python3 test_gates.py`) and, in a
section explicitly marked "retired historical record" of the deleted CI
workflow, a full pytest node ID naming
`RulebookCheckoutMemo::test_ttl_marker_does_not_dirty_clone` inside
`test_spawn.py`. `docs/handbooks/operations.md` is also one of the files
hashed in `docs/specs/reconciled-index.md`'s tracked-documents table —
any edit to it requires regenerating that hash
(`python3 gates/spec_index.py --update`).

derived: `grep -c "docs/handbooks/operations.md" docs/specs/reconciled-index.md`

```
1
```

No standing doc anywhere in `docs/handbooks/` or `docs/specs/` states a
test-placement rule today — confirmed by an empty grep for
placement-shaped phrasing across both directories.

A second live handbook also names a root-relative path: `docs/handbooks/test-fixture-shape-contracts.md`
states "`shape_contracts.py` (repo root)" (found by the after-proposal
warrant hunt, not the initial pass — see
`docs/issue-729/reports/implementation/hunt-2026-08-11-consolidate-test-homes.md`).
Moving `shape_contracts.py` into `tests/` makes that line wrong. This
file is not one of the documents hashed in
`docs/specs/reconciled-index.md`, so editing it needs no companion hash
regeneration, unlike `docs/handbooks/operations.md`.

derived: `grep -c "test-fixture-shape-contracts" docs/specs/reconciled-index.md`

```
0
```

## What did not surface as a blocker

- No `__init__.py` exists anywhere, so package-boundary import rules
  never come into play for any of the four decisions.
- No CI workflow currently runs the suite (the GitHub Actions test
  workflow was retired per issue #460, per `docs/handbooks/operations.md`)
  — so there is no CI YAML path to update as part of this move.
- Production references to a root test filename outside `spawn.py` line
  2197 do not exist: `spawn.py`, every `gates/*.py`, and every
  `on-the-record/hooks/*.py`/`*.sh` file were grepped for all eight root
  test-file basenames, `conftest.py`, and `shape_contracts.py`; the only
  hit was the one already described above.
