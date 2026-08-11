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

**Revision basis**: PR #746 (this delivery's own PR) carries a
change-requested review comment (jjongkwann) that independently
reproduced the collection failure below and directed both of this
record's own previously-self-declared "Open findings" to be resolved
inside this same delivery — both files were already anticipated in
this record's `code_under_review:` list before this revision, so
fixing them stays inside the already-frozen write set, not a new
widening of it.

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
- (Revision, this session) Extended `gates/test_closes_gate_ci.py`'s
  existing repo-root `sys.path` insert to also add the new `tests/`
  directory ahead of its `import shape_contracts` line — the same
  pattern the file already uses for its own directory's insert.
- (Revision, this session) Added `"tests/**"` alongside the existing
  `"test/**"` entry in `roles/implementation.json`'s and
  `roles/specs/implementation.spec.json`'s `write_scope` arrays.
- (Revision, this session) Running the full suite once collection
  worked again surfaced two more instances of the same "repo-root-
  relative to `__file__`" class of bug the original move's fix list
  missed — both inside `tests/test_spawn.py`, both outside the
  proposal's enumerated import-fix list because they don't touch a
  module import: `FixtureShapeContracts.GOLDEN_GH_PATH` and
  `PlainSessionDirectiveNorms._render`'s `repo_root`. Fixed within this
  delivery since the file was already in the frozen write set — see
  "What did not work" for the mechanism.

## Acceptance checks (proposal's "How you'll know it worked")

**1. Node ID set equivalence.** (Revision, this session, post-fix.)
Captured `pytest --collect-only -q` on an independent `origin/main`
worktree (the pre-move tree — `origin/main` resolves to the same commit
this branch was forked from) and on this branch after today's fix
commit, normalized the `origin/main` set's path prefixes to match the
after-set's new `tests/`-relative form (`test/<f>` → `tests/<f>`, and
each of the eight moved root `test_*.py` files → `tests/test_*.py`),
then compared the two sets in Python — a plain-set comparison rather
than a text `diff`, because an earlier same-session attempt using shell
`sort` on both sides produced spurious reordering-only differences
between two files with identical content, traced to `sort`'s
locale-dependent collation disagreeing with the generation order:

```
derived: git fetch origin main && git rev-parse origin/main
-> 5f0d198b359a035c646c7a7289babd25f24f69db

derived: git worktree add /tmp/otr-main-baseline origin/main
derived: (cd /tmp/otr-main-baseline && python3 -m pytest --collect-only -q)
-> 1095 tests collected in 0.97s

derived: python3 -m pytest --collect-only -q   (this branch, after this
session's fix commit 336a7e3)
-> 1095 tests collected in 1.47s

derived: python3 set-comparison, origin/main's node IDs normalized per
the path-prefix mapping above, against this branch's node IDs:
-> baseline normalized set size: 1095
-> branch set size: 1095
-> only in baseline, not in branch: 0
-> only in branch, not in baseline: 0
```

Exact match after normalization — no test name disappeared, reappeared,
or silently renamed beyond the moved files' own path-prefix change.
This closes the collection-blocking gap PR #746's review comment
identified. Before today's fix commit, the after-side of this
comparison could not be produced at all, per the reviewer's own
independent reproduction, quoted from the PR #746 review comment:

```
quoted from PR #746 review comment (independent reproduction on this
branch, before this session's fix commit):
$ python3 -m pytest --collect-only -q
ERROR gates/test_closes_gate_ci.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1041 tests collected, 1 error in 2.70s

$ python3 -m pytest -q
    import shape_contracts
E   ModuleNotFoundError: No module named 'shape_contracts'
```

— see "Rationale for deviations" for the prior state and its fix.

**2. Full-suite pass/skip parity.** (Revision, this session, post-fix.)
Same `origin/main` worktree as check 1, full run (not `--collect-only`):

```
derived: (cd /tmp/otr-main-baseline && python3 -m pytest -q)
-> 3 failed, 1090 passed, 2 skipped in 172.82s

derived: python3 -m pytest -q   (this branch, after fix commit 336a7e3,
clean working tree confirmed via `git status --short` producing no
output immediately before this run)
-> 3 failed, 1090 passed, 2 skipped in 169.03s
```

Exact parity: identical passed/skipped/failed counts, and the three
failing node IDs match one-to-one (path-prefix-normalized) across both
runs:

```
derived: failing node IDs, origin/main baseline
-> gates/test_boundary.py::t_all_gates_modules_recorded
-> gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
-> test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge

derived: failing node IDs, this branch (fix commit 336a7e3, clean tree)
-> gates/test_boundary.py::t_all_gates_modules_recorded
-> gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
-> tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge
```

All three are unrelated to this move (two are an unrelated gate script
missing from two enforcement-tracking documents, issues #441 and #684;
the third is a `tmp_path`-scoped subprocess failure inside a fixture
that never creates its own subdirectory — same failure mode and same
error text on both sides). None of the three names a file this delivery
touches, and none of the three test files is in this delivery's write
set.

A fourth failure appeared transiently mid-session, in the node named
`t_rulebook_version_is_recorded` inside `tests/test_gates.py`, while
this session's fix commit was still an uncommitted working-tree diff —
that test asserts a git-status-derived version string for this same
repo checkout carries no "dirty" marker, so it fails by design whenever
the tree carrying the fix is itself dirty. It is not counted above
because the check above intentionally runs against the clean,
already-committed tree — the same condition that test itself is
designed to be evaluated under.

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
- (Revision, this session) Expected the previous session's `sys.path`/
  `__file__` import-path fix pass to have covered every repo-root-
  relative assumption in the moved files. Actual: two more instances
  survived in `tests/test_spawn.py` that don't touch a module import at
  all — `FixtureShapeContracts.GOLDEN_GH_PATH` built its golden-fixture
  path by joining `os.path.dirname(__file__)` with a literal `"tests"`
  path segment (correct when `__file__` was at repo root; after the
  move, `__file__`'s own directory is itself `tests/`, so the literal
  segment double-counted that same directory name and pointed one level
  too deep, at a path that does not exist), and
  `PlainSessionDirectiveNorms._render`'s `repo_root` used
  `Path(__file__).resolve().parent` (one level too shallow post-move,
  so the `directive.sh` path it built was one directory short of the
  real one, and every `subprocess.run` call in that class returned exit
  code 127). Neither surfaced during collection — only running the full
  suite after this session's collection fix caught them, as 6 of that
  run's 9 failures (`FixtureShapeContracts` x2, `PlainSessionDirectiveNorms`
  x3, one more accounted for by a transient dirty-tree artifact — see
  Acceptance check 2) that a node-ID-set-only comparison would have
  missed entirely, since none of these tests were removed, added, or
  renamed by the move — they still collected, they just failed at
  runtime.

## Rationale for deviations

`gates/test_closes_gate_ci.py`, `roles/implementation.json`, and
`roles/specs/implementation.spec.json` are outside this proposal's
original phase-1 `files:` frontmatter — Rationale (b) explicitly kept
every `gates/`-colocated test file untouched, and the proposal never
named `roles/` at all. All three were nonetheless already named in this
delivery's own `code_under_review:` frontmatter list before this
session (the previous session flagged both as blocking Open findings
with a fully-specified, no-new-judgment fix, but did not apply either
fix itself, citing the SCOPE-EXCEEDED RULE against the *original*
phase-1 proposal's write set).

This session resolves both, on explicit direction from PR #746's own
review comment (jjongkwann, an approvers.md account, revising this same
delivery on the same branch/PR — ordinary feedback-driven revision, not
a fresh phase-1 approval): `gates/test_closes_gate_ci.py`'s import of
`shape_contracts` resolved its own parent's parent directory onto
`sys.path`, which reached repo root before this move (where
`shape_contracts.py` used to live); after the move, no directory on
that file's `sys.path` contains a `shape_contracts` module, so the
import raised and aborted collection for the whole repository, not just
that one file's tests. `roles/implementation.json` and
`roles/specs/implementation.spec.json` still declared `write_scope`
entries naming the old, now-nonexistent `test/` directory — read live
by `on-the-record/hooks/delegated-judgment-gate.sh` (standing-role
computation for judgment-panel quorum) and `gates/role_spec_shape.py`
(review-finding target-path validation), so any change confined to the
new `tests/` directory silently resolved to zero standing roles.

Both fixes landed exactly as each finding's own resolution path
specified — an added `sys.path` insert line mirroring the file's
existing pattern, and an added `"tests/**"` array entry alongside the
existing `"test/**"` one — no new design decision was needed for
either, and none was made. See "Acceptance checks" above for the
re-run evidence and "Open findings" below for closure.

## Open findings

Both findings this record previously carried as blocking are resolved
in this session's fix commit (`336a7e3`, `fix(issue-729): resolve
collection-blocking import and stale write_scope`):

- `gates/test_closes_gate_ci.py`'s collection-aborting import failure —
  resolved by extending its existing repo-root `sys.path` insert to
  also add `tests/`. Verified via Acceptance checks 1 and 2 above (node
  ID set equivalence and full-suite pass/skip parity, both now exact
  matches against the `origin/main` baseline).
- `roles/implementation.json`'s and `roles/specs/implementation.spec.json`'s
  stale `write_scope` — resolved by adding `"tests/**"` alongside the
  existing `"test/**"` entry. Verified by re-running the same
  `write_scope`-resolution reproduction the before-landing warrant hunt
  used (`docs/issue-729/reports/implementation/hunt-2026-08-11-consolidate-test-homes.md`):

```
derived: python3 -c "<load_roles/glob_matches/role_scope/standing_roles_for
  reproduction, identical to the one in the hunt record above, run
  against this session's fixed roles/*.json>"
-> OLD path test/test_gates.py  -> {'implementation'}
-> NEW path tests/test_gates.py -> {'implementation'}
```

No open findings remain.

## Next steps

File the `test_spawn.py`-split follow-up issue per the approval
feedback (deferred out of this delivery's scope; unaffected by this
session's revision).

## Hunt

Before-landing hunt dispatched and consumed within this same turn in
the previous session; see
`docs/issue-729/reports/implementation/hunt-2026-08-11-consolidate-test-homes.md`
for the appended before-landing section — that hunt is what supplied
this session's resolution path for the `write_scope` finding, and this
session's Acceptance-check reproduction above re-runs its exact repro
script against the fix as a closed-check confirmation rather than
re-hunting blind.

No new warrant-hunter dispatch was made this session: the two findings
being closed were already fully diagnosed (mechanism, reproduction, and
no-new-judgment fix) by the prior session's own record and hunt, this
session's PR #746 review comment, and this session's own direct
reproduction of both fixes (Acceptance checks 1–2, and the `write_scope`
repro immediately above) — a mechanical revision of two already-hunted
findings, not new-surface work a fresh stance would add coverage for.
