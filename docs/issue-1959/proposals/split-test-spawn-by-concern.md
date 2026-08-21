---
status: proposed
files:
  - tests/test_spawn_pipeline.py
  - tests/test_spawn_observation_recovery.py
  - tests/test_spawn_board_flows.py
  - tests/test_spawn_consult_panel.py
  - tests/test_spawn_checkout_network.py
  - tests/test_spawn_gate_wiring.py
  - tests/test_spawn.py
  - tests/_spawn_test_support.py
  - .on-the-record/test-tiers.json
  - docs/issue-1959/reports/test-authoring.md
---

Note on survey location: this proposal's current-state survey lives at
`docs/issue-1959/reports/test-authoring/survey.md` (this role's own record
area per contract v3 s11 — a test-authoring session may not write under
`docs/issue-1959/reports/implementation/`, which belongs to a different
role). No design decision here was left unscout — the survey was written
first and read in full before this proposal was drafted.

## Request

Split `tests/test_spawn.py` (11,509 lines, 106 `unittest.TestCase` classes,
524 tests — see `docs/issue-1959/reports/test-authoring/survey.md`) into six
concern-scoped files, and prune redundant/overlapping coverage found during
the split, naming for every pruned test the surviving test that covers its
behavior. This is a follow-up to the change-class-scoped tiering effort:
per-concern files let `.on-the-record/test-tiers.json` target a `slow`
trigger at one concern instead of the whole monolith.

## Constraints

- `python3 -m pytest tests/ -q` must collect the same-or-documented test
  count as today (920 repo-wide, 524 in the spawn-test set) and pass.
- Every pruned test must be listed in the phase-2 record together with the
  surviving test that covers its behavior.
- Each new `tests/` file must map to exactly one of the six concern groups
  named below — no file straddling two groups.
- Output stays inside `tests/`, `pytest.ini`, `.on-the-record/test-tiers.json`,
  `docs/` per the issue's declared scope; no production code under `spawn.py`
  changes as part of this split.
- `tests/test_spawn.py` either stops existing or drops under 2,000 lines
  serving as a shim/entry point (issue's stated empty-state for the first
  acceptance check).

## Rationale

Two structural approaches were considered for where the split boundary
runs, and one file-naming scheme.

**Split boundary: by concern group (chosen) vs. by file size / mechanical
chunking (rejected).** A pure line-count split (e.g. six ~1,900-line
chunks cut at arbitrary class boundaries) would satisfy the "smaller
files" goal without touching class order, and is less work than reading
every class. It was rejected because the issue's second acceptance check
is structural — "each new tests/ file maps to one concern group named in
the proposal" — and a size-only cut produces files with no coherent
concern, which is exactly what the change-class-scoped tiering follow-up
(the issue's stated motivation) needs to *not* have: a `slow` trigger keyed
to, say, `checkout-network` changes must be able to name one file, not
"whichever third of the alphabet". The concern-group boundary costs more
scout time (106 classes, individually read) but is the only cut that keeps
the tiering promise the issue exists to enable.

**Class placement: one class per exactly one group (chosen) vs. allowing
a class to split across two files by test method (rejected).** Several
classes (e.g. `EventReporting`, `Watchdog`) contain tests that lean toward
more than one concern at the margins. Splitting a class's *methods* across
files was rejected: `unittest.TestCase` setup/teardown and shared instance
state live at the class level, so splitting methods would either duplicate
setup or require extracting a shared base class mid-migration — a second,
separate refactor entangled with the file split. Keeping each class whole
and assigning the *class* to its dominant concern (per the survey's
per-class read) keeps the split mechanical and reversible per class.

**Naming: `test_spawn_<concern>.py` (chosen) vs. dropping the `test_spawn_`
prefix (e.g. `test_pipeline.py`) (rejected).** The repo's `tests/` directory
already holds concern-named files outside the monolith
(`test_watchdog_freshness.py`, `test_watchdog_local_signals.py`) that do
not carry a `test_spawn_` prefix. Dropping the prefix would read as more
consistent with that existing convention, but was rejected here because
`spawn.py` is the single module under test by all six new files, and a
`test_spawn_` prefix keeps `pytest tests/test_spawn_*.py` a valid single
glob for "everything that tests spawn.py" — useful for the test-tiers `slow`
trigger which today names `tests/test_spawn.py` as one literal entry and
will need per-concern globs after this split.

## What will be done

1. Create `tests/_spawn_test_support.py` to hold the module-level imports
   and `_make_*`/`_stub_*` helper functions from `test_spawn.py` that are
   used by classes landing in more than one of the six target files (per
   the survey's call-site trace, not yet done — first step of execution).
   Helpers used by only one target file's classes move into that file
   directly instead.
2. Create six new files, one per concern group, each importing shared
   helpers from `tests/_spawn_test_support.py`:
   - `tests/test_spawn_pipeline.py` — 12 classes / 62 tests (spawn cmd,
     session args, workspace identity)
   - `tests/test_spawn_observation_recovery.py` — 30 classes / 166 tests
     (watchdog, respawn, liveness, staleness)
   - `tests/test_spawn_board_flows.py` — 18 classes / 134 tests
     (board/roster reads, watch/follow, event reporting)
   - `tests/test_spawn_consult_panel.py` — 14 classes / 59 tests
     (consult/panel CLI, closure-sweep, reconcile)
   - `tests/test_spawn_checkout_network.py` — 17 classes / 46 tests
     (git/gh network calls, checkout caching, PR comments)
   - `tests/test_spawn_gate_wiring.py` — 15 classes / 57 tests
     (policy refusals, requirement/doctor gates, sandbox/env allowlists)
   The exact class list for each file is the mapping recorded in
   `docs/issue-1959/reports/test-authoring/survey.md`.
3. Per class, during the move: apply the refactoring-legacy skill's
   characterization-test-scope method to check for behavioral overlap
   against every other class already placed in the same target file (not
   across files — cross-concern duplication is out of scope for this pass,
   since two tests covering the same behavior from different concern
   angles are not necessarily redundant). Where a genuine duplicate is
   found, prune the weaker of the pair and record it.
4. Delete the moved classes from `tests/test_spawn.py`. If anything
   remains that does not cleanly fit one of the six groups (none identified
   in the survey's inventory, but execution may surface one), leave it in
   `tests/test_spawn.py` as the shim/entry file: it must be under 2,000
   lines to satisfy the issue's declared empty state, or removed
   entirely if nothing remains.
5. Update `.on-the-record/test-tiers.json`'s `slow.trigger_change_classes`
   entry `"tests/test_spawn.py"` to the six new per-concern globs (plus
   `tests/test_spawn.py` itself if it survives as a shim), so a diff
   touching only one concern's file still triggers the `slow` tier
   correctly instead of losing coverage silently.
6. Run `python3 -m pytest tests/ -q` and record the collected count
   against the 920 baseline in the phase-2 record
   (`docs/issue-1959/reports/test-authoring.md`), which also lists every
   pruned test with its surviving-coverage counterpart.

## Accumulation

`.on-the-record/test-tiers.json`'s `slow.trigger_change_classes` list grows
by one entry per new per-concern test file (six entries replacing the one
`tests/test_spawn.py` entry). If a future issue splits one of these six
files further (e.g. `observation-recovery`'s 166 tests outgrowing one file
again), the same list grows by one more entry per further split — that is
the intended shape, not an accumulation risk: each entry maps 1:1 to a real
concern-scoped file, so N further splits produce N more precise,
individually named trigger entries rather than N copies of the same
boilerplate line. There is no shared-helper-free inline subprocess/gh-call
accumulation in this change: `tests/_spawn_test_support.py` (step 1) is
exactly the shared home that keeps helper duplication from accumulating
across the six new files as each is written.

## Out of scope

- Any change to `spawn.py` or other production code.
- Cross-concern deduplication (a test in `pipeline` that overlaps a test in
  `gate-wiring`, for instance) — pruning in this pass is scoped to
  within-file duplication surfaced while placing classes into their target
  file, per the Rationale's per-class-whole constraint.
- Rewriting existing test bodies, renaming test methods, or changing
  assertions beyond what pruning requires — this is a location/organization
  change, not a test-quality rewrite.
- Restructuring `unittest.TestCase` classes into pytest-native
  fixtures/functions — out of scope; the split preserves the existing
  `unittest.TestCase` style class-for-class.

## How you'll know it worked

- `python3 -m pytest tests/ -q` collects a count that is either exactly 920
  (no pruning) or less than 920 with every removed test named in
  `docs/issue-1959/reports/test-authoring.md` alongside its surviving
  counterpart, and the full run passes.
- `tests/test_spawn.py` no longer exists, or is under 2,000 lines and
  contains no more `unittest.TestCase` classes than a thin shim would need.
- Each of the six new `tests/test_spawn_*.py` files contains only classes
  from its one named concern group per the survey's mapping — checkable by
  grepping `^class ` in each file and confirming every name appears in
  exactly one group's list above.
- `.on-the-record/test-tiers.json`'s `slow` trigger list names the new
  per-concern files (or globs) instead of the single old
  `tests/test_spawn.py` entry.
