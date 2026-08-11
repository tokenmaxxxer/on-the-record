---
code_under_review:
  - tests/check-write-set-conflicts.test.sh
  - tests/claim-scan-preflight.test.sh
  - tests/test_bootstrap_timing.py
  - tests/test_latency_report.py
  - tests/test_portability_audit_table.py
  - tests/test_side_effect_round.py
  - tests/test_silent_failure_repros.py
  - tests/test_approve_scope.py
  - tests/test_flows.py
  - tests/test_gates.py
  - tests/test_issue_bundling.py
  - tests/test_repo_scope_gate.py
  - tests/test_spawn.py
  - tests/test_spec_index.py
  - tests/test_vocab_coherence_roles.py
  - tests/shape_contracts.py
  - spawn.py
  - docs/handbooks/operations.md
  - docs/handbooks/test-fixture-shape-contracts.md
  - docs/specs/reconciled-index.md
  - docs/handbooks/test-layout.md
  - gates/test_closes_gate_ci.py
  - roles/implementation.json
  - roles/specs/implementation.spec.json
  - on-the-record/hooks/delegated-judgment-gate.sh
  - gates/role_spec_shape.py
type: refactor
breaking: "false"
verdict: pass
loop_state: landed
---

# Implementation record — issue-729 (consolidate test homes)

## Upstream

Basis: `docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md`
(phase-1, merged to main via PR #739). Approved via issue-level comment
`APPROVE issue-729/implementation` (single-account mode, jjongkwann,
listed in `docs/specs/approvers.md`), followed by a non-reverting
feedback comment narrowing this delivery to move-only: the feedback
explicitly puts the `test_spawn.py` split into a separate follow-up
issue, to start only once this move lands (ordering forced because the
split's target paths aren't fixed until after the move).

## Why

Root-level test scatter (a `test/` directory, nine root-level test
files, plus test files already colocated next to their implementation
modules under `gates/` and `on-the-record/hooks/`) made it hard for a
new test author to know where a file belongs. This delivery consolidates
the scattered directory and the root-level files into one `tests/` home,
leaving the colocated `gates/`/`on-the-record/hooks/` tests and the root
`conftest.py` untouched (import-mechanics reasons — proposal Rationale
(b)/(c)) and `test_spawn.py` unsplit (proposal Rationale (d), reaffirmed
by the approval feedback comment).

## What was done

- Moved (`git mv`) every file the proposal's `files:` list named out of
  the old `test/` directory and repo root into `tests/`; the old `test/`
  directory no longer exists at all.
- Fixed every moved file's own import-path assumption so it still finds
  `spawn`, `gates/`, and its sibling modules from its new one-level-
  deeper location: added a `sys.path` insert ahead of a previously bare
  import in two files, and widened an existing `sys.path` insert (and,
  in one file, a directory constant) from "my own directory" to "my
  parent's directory" in the rest — the full proposal-named set, plus
  one instance the proposal's own enumerated list omitted (see "What did
  not work" below).
- Updated every moved file's own docstring usage-line example to name
  its new `tests/`-prefixed invocation path, so a reader copy-pasting
  the docstring's own example command gets a path that still resolves.
- Updated the one runtime consumer outside `tests/` that names a moved
  file by its old path — `spawn.py`'s progress-detection prefix tuple —
  to the new path, and updated the moved test file's own matching
  assertion plus its two illustrative command-string examples to match.
- Updated `docs/handbooks/operations.md`'s self-check example command
  and its one live (non-historical-block) path reference to the new
  locations, then regenerated `docs/specs/reconciled-index.md`'s
  recorded hash for that handbook via `gates/spec_index.py --update`.
- Updated `docs/handbooks/test-fixture-shape-contracts.md` (after-
  proposal hunt finding): its "repo root" location claim and its
  `test_spawn.py`-named code-comment example both now name the new
  `tests/` location.
- Added `docs/handbooks/test-layout.md`, documenting the single `tests/`
  home and why, the two colocation exceptions and why, `conftest.py`'s
  root position and why, and where a new test file goes by default vs.
  when colocation applies.
- Confirmed `pytest.ini` needs no edit (it names no directory) and
  `conftest.py` needs no edit (its own fixture-root reference already
  named `tests/`, unaffected by files moving into that same directory).

## Acceptance checks (proposal's "How you'll know it worked")

**1. Node ID set equivalence.** Captured `pytest --collect-only -q`
before the move and after, normalized the before-set's path prefixes to
match the after-set's new `tests/`-relative form, and diffed the two
sorted sets:

```
derived: python3 -m pytest --collect-only -q   (before move, on the pre-move tree)
-> 1095 tests collected in 2.16s

derived: python3 -m pytest --collect-only -q   (after move)
-> 1041 tests collected, 1 error in 2.08s

derived: diff <(sort normalized-before-node-ids) <(sort after-node-ids)
-> 54 lines removed, 0 lines added; every removed line has the form
   gates/test_closes_gate_ci.py::t_<name>
```

Once the path-prefix change is normalized away, every remaining node ID
matches exactly — no test name silently disappeared or reappeared as a
side effect of the move itself. The only divergence is a single file's
worth of node IDs vanishing because that file can no longer be imported
(see Rationale for deviations) — not a rename, not a path-prefix
mismatch, and not a file this delivery moved or edited.

**2. Full-suite pass/skip parity.** Captured a clean before-move baseline
by stashing this delivery's working-tree changes, running the suite,
then restoring them:

```
derived: python3 -m pytest -q   (before move, clean baseline via git stash)
-> 3 failed, 1090 passed, 2 skipped in 172.05s (0:02:52)

derived: python3 -m pytest -q   (after move)
-> 1 error in 1.77s
```

Not parity: the same collection failure that breaks check 1 aborts the
whole run before any test executes, so there is no passed/skipped count
to compare on the "after" side at all. The three pre-existing failures
on the "before" side are unrelated to this move — two are an unrelated
gate script missing from two enforcement-tracking documents (issues
#441 and #684), and the third is a `tmp_path`-scoped subprocess failure
inside a fixture that never creates its own subdirectory; none of the
three names a file this delivery touches, and none of the three test
files is in this delivery's write set.

**3. Zero broken references.** The proposal's specified check — grep
`spawn.py`, every file under `gates/`, and every file under
`on-the-record/` for each moved file's exact name:

```
derived: for each of the 16 moved filenames, grep it across
  spawn.py gates/ on-the-record/
```

`spawn.py` shows only the one intentionally-updated line naming the new
`tests/test_spawn.py` path. Every hit inside `gates/` is a pre-existing,
unchanged-by-this-move comment about a historical basename-collision
precedent (root-level `test_gates.py` colliding with a same-named file
under `gates/`, the reason `gates/test_gates_refusal.py` carries that
name instead) — none of these files are in this delivery's write set,
none was edited, and the same hits exist identically on the pre-move
tree. None asserts a path that this move breaks.

That grep has a blind spot the proposal didn't anticipate: a bare
`import shape_contracts` statement contains no `.py` suffix, so a grep
for the literal filename never finds it. A supplemental sweep for bare
module imports:

```
derived: grep -rn "^import shape_contracts\|^import spawn$" gates/ on-the-record/
-> gates/ci.py: import spawn
   gates/test_closes_gate_ci.py: import spawn
   gates/test_closes_gate_ci.py: import shape_contracts
   gates/test_closure_sweep.py: import spawn
```

The three `import spawn` hits are unaffected (`spawn.py` did not move).
The `import shape_contracts` hit is the real broken reference this
supplemental sweep catches and the proposal's literal check would have
missed — see Rationale for deviations.

Handbook staleness (supplemental, after-proposal hunt finding):

```
derived: grep -n "repo root" docs/handbooks/operations.md docs/handbooks/test-fixture-shape-contracts.md
-> (no output)
```

**4. `gates.duplicate_test_basenames`.**

```
derived: python3 gates/test_duplicate_test_basenames.py
-> 7 passed
```

No basename collision introduced by the consolidation.

**5. `docs/handbooks/test-layout.md` exists** and documents the
placement rule — present in this commit's `code_under_review:` list
above.

## What did not work

- Expected the proposal's enumerated import-path fix list for the moved
  spec-drift test file to be complete. Actual: that file also computes
  its own idea of the repo root in a separate constant used to locate
  the tracked-document index, and the proposal's list didn't name that
  constant — only found by reading the file's full body before editing,
  not from the proposal text. Fixed within this delivery since the file
  was already in the frozen write set; left unfixed, the file's
  baseline-repo-passes check would have silently checked the wrong tree
  instead of the real one.
- Expected the proposal's filename-string "Zero broken references" grep
  to be sufficient to prove nothing broke. Actual: it missed a bare
  module import in a `gates/`-colocated test file, which aborted
  collection for the *entire* repository, not just that one file. Found
  only by actually running collection and the full suite after the
  move, not by the grep the proposal specified as the check.

## Rationale for deviations

`gates/test_closes_gate_ci.py` is outside this proposal's frozen
`files:` list — Rationale (b) explicitly kept every `gates/`-colocated
test file untouched. That file imports `shape_contracts` by resolving
its own parent's parent directory onto `sys.path`, which reached repo
root before this move (where `shape_contracts.py` used to live). After
the move, no directory on that file's `sys.path` contains a
`shape_contracts` module, so the import raises and pytest cannot collect
that module — which in turn aborts collection for the whole repository,
not just that one file's tests.

Making the suite collect again requires editing
`gates/test_closes_gate_ci.py` — a file outside the frozen write set.
Per the SCOPE-EXCEEDED RULE, this delivery does not widen the write set
to include it: every file the proposal's `files:` list names is finished
and committed, and this gap is reported here rather than silently
patched by reaching outside that list. The fix itself needs no design
decision — one more `sys.path` insert line, mirroring the pattern the
same file already uses for its own directory's insert — but it is still
an edit to a file the human approver did not get to review before
approving this proposal's scope. The next proposal for this repo should
apply it before or alongside merging this delivery: until it lands,
the full suite does not run on `main` at all.

## Open findings

**Blocking, first**: `gates/test_closes_gate_ci.py` fails to import once
this move lands, which aborts the entire suite run — see "Rationale for
deviations" above for the full mechanism and reproduction. Not caused by
editing that file (this delivery does not touch it) — caused by moving
`shape_contracts.py`, which that file's existing import path can no
longer reach.

Resolution path: a follow-up proposal adds `gates/test_closes_gate_ci.py`
to a frozen write set and extends its existing repo-root `sys.path`
insert to also add the new `tests/` directory, ahead of its
`shape_contracts` import — the same pattern the file already uses for
its own directory's insert, no new design decision required. Until that
lands, the full suite does not run on `main`.

**Blocking, second**, surfaced by the before-landing warrant hunt (see
`docs/issue-729/reports/implementation/hunt-2026-08-11-consolidate-test-homes.md`'s
before-landing section for the full reproduction): `roles/implementation.json`
and `roles/specs/implementation.spec.json` still declare a `write_scope`
entry naming the old directory this move renamed away — this delivery's
frozen write set never included `roles/`, so it was left untouched. That
`write_scope` field is not decorative: `on-the-record/hooks/delegated-judgment-gate.sh`
reads it live to compute which roles "stand" for a changed-file list
(driving judgment-panel quorum/escalation), and `gates/role_spec_shape.py`'s
`check_axis_evaluation_entry` reads it to validate a review finding's
target path. The hunt's reproduction shows a change confined to the new
test directory now resolves to no standing roles where the identical
old-path change correctly resolved to the `implementation` role, and a
review finding targeting the new directory gets rejected as not
resolving against any role's write scope — silently, with no error
surfaced anywhere. This is a governance-mechanism regression, not a
test-running one, and it is silent rather than loud (unlike the first
finding above, which fails loudly at collection time).

Resolution path: a follow-up proposal adds `roles/implementation.json`
and `roles/specs/implementation.spec.json` to a frozen write set and
extends each one's `write_scope` array to also name the new test
directory, alongside (not replacing) the existing entry — no new design
decision required, since the intent ("implementation owns the test
tree") is unchanged; only the directory name needs to stay current.
Until that lands, any future change confined to the new test directory
silently loses its standing-role coverage under the judgment-panel gate.

## Next steps

File the `test_spawn.py`-split follow-up issue per the approval
feedback (deferred out of this delivery's scope), and raise both
blocking open findings above for the human reviewer's decision: fold
either or both fixes into this PR's scope before merging, or land this
PR with both fixes tracked as immediate follow-ups.

## Hunt

Before-landing hunt dispatched and consumed within this same turn; see
`docs/issue-729/reports/implementation/hunt-2026-08-11-consolidate-test-homes.md`
for the appended before-landing section.
