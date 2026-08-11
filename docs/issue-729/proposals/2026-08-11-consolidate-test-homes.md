---
status: proposed
files:
  - test/test_bootstrap_timing.py
  - test/test_latency_report.py
  - test/test_portability_audit_table.py
  - test/test_side_effect_round.py
  - test/test_silent_failure_repros.py
  - test/check-write-set-conflicts.test.sh
  - test/claim-scan-preflight.test.sh
  - test_approve_scope.py
  - test_flows.py
  - test_gates.py
  - test_issue_bundling.py
  - test_repo_scope_gate.py
  - test_spawn.py
  - test_spec_index.py
  - test_vocab_coherence_roles.py
  - shape_contracts.py
  - spawn.py
  - docs/handbooks/operations.md
  - docs/specs/reconciled-index.md
  - docs/handbooks/test-layout.md
---

# Consolidate the scattered test homes into one, keeping deliberate colocation

## Request

Operator asked (2026-08-11): clean up the repo root, move what can move
into a test folder. Issue #729 narrows that into four decisions this
proposal has to make and justify: single home or role split for
`test/`/`tests/`; whether `gates/`/`on-the-record/hooks/` colocation
moves too; whether `conftest.py` stays at root; and whether the large
`test_spawn.py` gets split along with the move.

## Constraints

- Move-only for `test_spawn.py` in this PR unless a justified reason to
  mix move-and-split is stated (issue's own default).
- Do not rewrite path strings inside `docs/issue-*/` historical records.
- Whatever the unified home turns out to be, `gates.duplicate_test_basenames`
  (issue #398) must keep passing — no basename collision introduced.
- Acceptance requires comparing the pytest-collected node ID *set*
  before and after, not just a pass/skip count — a rename that drops a
  test silently must be visible.
- The placement rule must end up recorded in exactly one document a new
  test author can read to pick a location without guessing.

## Rationale

**(a) Single home, named `tests/`; `test/` merges into it and is
removed.** Alternative considered: keep both directories and formalize
a role split between them (e.g. `test/` for Python unit tests, `tests/`
for shell tests and fixtures). Rejected — the current contents don't
actually follow that split (`test/` already holds two `.test.sh` shell
files alongside its five Python files), so writing that rule down would
misdescribe the real state rather than fix it. `tests/` is kept as the
survivor name over `test/` because it is already anchored by code
(`conftest.py`'s fixture root and `shape_contracts.py`'s golden-sample
path both already resolve under `tests/fixtures/`) and matches the
documented pytest-ecosystem convention (scout brief,
`docs/issue-729/reports/implementation/scout-brief.md`) — renaming to
`test/` instead would mean moving the fixtures too, for no benefit.

**(b) `gates/` and `on-the-record/hooks/` keep their colocated tests;
neither moves.** Alternative considered: move every test in the repo
into the one unified home for total consistency. Rejected — those tests
import their sibling implementation module through an explicit
`sys.path.insert` that assumes same-directory placement (confirmed
across dozens of files in the survey); moving them would force either a
sweeping import-path rewrite or introducing package boundaries
(`__init__.py`) that change how `duplicate_test_basenames` reasons about
the tree. That is a materially larger and riskier change than what the
issue actually asked for (root clutter), and the survey's scout pass
found colocation-next-to-implementation to be a recognized, legitimate
pattern in its own right, not a mistake to correct.

**(c) `conftest.py` stays at root.** Alternative considered: move it
into the new `tests/` home alongside the files that move there.
Rejected — pytest only applies a `conftest.py`'s fixtures to test files
in its own directory subtree (siblings and descendants), never to
siblings of that directory. Since (b) keeps `gates/` and
`on-the-record/hooks/` tests outside `tests/`, relocating `conftest.py`
would silently stop injecting the issue #204 environment-default fixture
and the issue #360 session-leak check for every test outside the new
directory — a functional regression the survey's import-mechanics
research surfaced, not a style call.

**(d) Move `test_spawn.py`, do not split it in this PR.** Alternative
considered: split it into topic files in the same PR, since the file is
already being touched for the location-driven `sys.path` fix anyway.
Rejected — deciding logical split boundaries across an eight-thousand-plus-line
file, and verifying no test is lost or silently renamed in the process,
is a separate, judgment-heavy piece of work with its own real risk, not
a natural side effect of a location change. Relocation alone already
fully closes the "root clutter" problem this issue targets; a split can
be scoped as its own follow-up issue if still wanted.

## What will be done

- `git mv` the seven `test/` files into `tests/`; remove `test/`.
- `git mv` the eight root `test_*.py` files and `shape_contracts.py`
  into `tests/`. Every moved file that relied on its own directory
  already being repo root gets a `sys.path.insert(0,
  str(Path(__file__).parent.parent))` added ahead of its `spawn`/`shape_contracts`/`gates`-module
  imports (the same line already used by `gates/closure_sweep.py` and
  the pre-existing `test/` files) — concretely `test_approve_scope.py`
  and `test_spawn.py` (currently bare `import spawn`), plus a `.parent`
  → `.parent.parent` fix to the existing `sys.path.insert` lines in
  `test_flows.py`, `test_gates.py`, `test_issue_bundling.py`,
  `test_repo_scope_gate.py`, and `test_spec_index.py`.
- `test_vocab_coherence_roles.py`'s `ROLES_DIR` gets the same
  `.parent` → `.parent.parent` fix — without it, the move would leave
  the test passing but silently checking zero files (survey's fourth
  fragile-point finding).
- `conftest.py` is left untouched at root.
- `spawn.py`'s `_PROGRESS_BASH_PREFIXES` tuple (around line 2197) gets
  its `test_spawn.py` invocation string updated to the new path, and
  `test_spawn.py`'s own matching assertion plus its two illustrative
  command-string examples get the same update, so none of the three
  describe a path that no longer exists.
- Each moved file's own docstring usage line (e.g. "python3
  test_gates.py") gets its path updated to match the new location.
- `docs/handbooks/operations.md`'s self-check example command and the
  one live (non-historical-block) path reference get updated to the new
  location; `docs/specs/reconciled-index.md`'s hash for that file gets
  regenerated afterward.
- A new docs/handbooks/test-layout.md file is added, recording: the single
  `tests/` home and why; the two colocation exceptions and why;
  `conftest.py`'s root position and why; where a new test file goes by
  default and when colocation applies instead.
- `pytest.ini` is confirmed to need no edit (`python_functions`/`norecursedirs`
  name no directory) — left as-is.

## Accumulation

The identical one-line fix (`.parent` → `.parent.parent` in an existing
`sys.path.insert`, or adding that line where it is missing) repeats
across six files: `test_approve_scope.py`, `test_flows.py`,
`test_gates.py`, `test_issue_bundling.py`, `test_repo_scope_gate.py`,
`test_spec_index.py` (plus `test_spawn.py` getting the bare-import
version and `test_vocab_coherence_roles.py` getting the analogous
`ROLES_DIR` fix). This is a closed, enumerated set — every file that
needs it is already named in this proposal's `files:` list; nothing
about the change discovers new instances at build time the way a
sweep-and-fix issue would. A shared helper is not warranted at this
count: a bare `sys.path.insert(0, str(Path(__file__).parent.parent))`
line is already the established idiom elsewhere in the repo
(`gates/closure_sweep.py`, the pre-existing `test/` files) — introducing
an abstraction over eight call sites to save one line each would be the
premature-abstraction failure mode, not a fix for one. If a future,
separate issue needs the same fix applied to a much larger set (rough
threshold: another ten-plus files, e.g. moving `gates/` or
`on-the-record/hooks/` tests despite this proposal's Rationale (b)
against it), that is the point where a small one-off codemod script
would replace manual per-file edits — not before, and not as part of
this PR.

## Out of scope

- Any change to test content, new tests, or rewriting existing tests.
- Splitting `test_spawn.py` (deferred; see Rationale (d)).
- Moving or restructuring `gates/` or `on-the-record/hooks/` tests.
- Rewriting path strings inside `docs/issue-*/` historical records.
- Registering CI or adding a workflow to run the suite (none exists
  today; out of this issue's scope).

## How you'll know it worked

- Node ID set equivalence, not a count: capture `python3 -m pytest
  --collect-only -q` output before the move and after, diff the two
  sorted node ID sets (not just the trailing summary count) — the only
  allowed difference is each moved file's path prefix changing from the
  old location to `tests/`; no test name disappears or reappears
  unexplained.
- Full-suite pass/skip parity: `python3 -m pytest -q` produces the same
  passed/skipped totals before and after.
- Zero broken references: grepping `spawn.py`, every file under
  `gates/`, and every file under `on-the-record/` for each moved
  filename turns up either nothing or only the intentionally-updated
  `spawn.py` line.
- `python3 gates/test_duplicate_test_basenames.py` still passes (no
  basename collision introduced by the consolidation).
- docs/handbooks/test-layout.md exists and is the one place a new
  test author needs to read to pick a file's location without asking.
