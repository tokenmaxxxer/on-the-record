---
issue: 2516
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: gates/test_gates_refusal.py
    sha: 97408d80d5b07e20015132d54acd9ae2d65c7a2e
  - path: gates/test_record_lint.py
    sha: 46da1c8a199048b380c363a936e92bca1c7c5393
  - path: gates/test_ui_evidence_gate.py
    sha: 8ae95c35180388eaf925bd89f2f76dc5a4d4e05d
  - path: on-the-record/hooks/test_record_scaffold.py
    sha: 629855d412c338d60de6146a4d14f4274646be9e
  - path: tests/test_spawn_board_flows.py
    sha: 878126c4fa5054dfa5e2878383e9636c012f8c25
code_under_review:
  - gates/test_gates_refusal.py
  - gates/test_record_lint.py
  - gates/test_ui_evidence_gate.py
  - on-the-record/hooks/test_record_scaffold.py
  - tests/test_spawn_board_flows.py
type: fix
breaking: false
verdict: pass
---

# issue-2516 — implementation record

## What was done

The issue named a single shared pattern rather than a specific file:
every fixture repo it sampled was a `.git/` plus a 4-byte `README.md`
under a `tmp*`-named directory, and suggested finding the helper that
builds that shape rather than auditing every test file. Grepped for it:

derived: `grep -rln "README.md" --include="*.py" . | xargs grep -l "mkdtemp" | grep -v .orchestrate-hook-fires`
```
gates/test_closure_sweep.py
gates/test_record_lint.py
bench/run.py
gates/test_accumulation.py
gates/test_recurrence.py
gates/test_gates_refusal.py
on-the-record/hooks/test_record_scaffold.py
```

canonical: read each of the 7 files above. `gates/test_closure_sweep.py`
already used `tempfile.TemporaryDirectory()` (self-cleaning);
`gates/test_accumulation.py` and `gates/test_recurrence.py` already wrap
every `mkdtemp()` call in `try/finally: shutil.rmtree(...)`; `bench/run.py`
is a standalone CLI runner, not a pytest test file — confirmed it is
never collected: `pytest.ini`'s default `python_files` pattern is
`test_*.py`/`*_test.py`, and `bench/run.py` matches neither. That left
four files with no cleanup at all, each building its own `git init`
fixture repo per test via `Path(tempfile.mkdtemp())` and never removing
it: `gates/test_gates_refusal.py`, `gates/test_record_lint.py`
(84 `t_*` test functions — derived: `grep -c "^def t_" gates/test_record_lint.py` → 84),
`on-the-record/hooks/test_record_scaffold.py`, and
`gates/test_ui_evidence_gate.py` (empty throwaway dirs via
`_norepo_root()`, no `.git`/`README.md`, but the same leak mechanism).

For each of the four, added:
- A module-level `_created_dirs: list[Path] = []` and an `_mkdtemp()`
  wrapper that records every directory it hands out.
- An `@pytest.fixture(autouse=True)` that does `yield` then drains
  `_created_dirs` with `shutil.rmtree(..., ignore_errors=True)` — this
  runs in pytest's own per-test teardown phase, which executes whether
  the test body passed, raised an assertion, or raised any other
  exception (demonstrated live under "Acceptance evidence", check 2).
- The same drain wrapped in `try/finally` around each file's
  `__main__`/`_run_all()` standalone-script entry point, since all four
  files are dual-mode (`python3 gates/test_x.py` direct execution is
  documented in each file's own module docstring alongside the pytest
  invocation) and a pytest fixture does not exist on that path.

Every call site that built a fixture repo (`Path(tempfile.mkdtemp())`)
was switched to the recording `_mkdtemp()` wrapper; no test's fixture
became shared with another test — each call still allocates a fresh,
unique directory, only the cleanup changed.

Removed the pre-existing leaked fixture directories still on disk (see
"Acceptance evidence", check 3, for the count and inodes reclaimed).

### CHANGES round — a fifth leaking file

canonical: `3418c838e55b8ba6ad283f3e09a682caad3a060f:docs/issue-2516/reports/conformance-review.md`, "Open findings" Finding 1 —
verdict Incorrect against acceptance check 1: a fifth leaking file,
`tests/test_spawn_board_flows.py`, was outside PR #2523's scope. Its
`EventReporting`/`ProgressEvents` classes (both `@pytest.mark.slow`)
build a fixture repo via `self._run(tempfile.mkdtemp(), ...)` and never
remove it — `EventReporting._run`'s `finally:` block (previously lines
100-103) restored only `sys.stdout`/`sys.stderr`/`spawn.ROSTER`, never
`td`. The review live-reproduced it (one slow test left one new `/tmp`
dir containing `.git`) and re-checked for a false positive
(`grep -n "tearDown|addCleanup"` — no hits in the class).

Why the first pass's discovery grep missed it, per the same review's
rationale: that grep was
`grep -rln "README.md" --include="*.py" . | xargs grep -l mkdtemp` —
scoped to the `.git`+`README.md` shape sampled from the issue. This
file's leaked dirs contain `.git` plus a `work/` tree instead
(`EventReporting._run` builds `Path(td) / "work"`, not a `README.md`),
so the README-shaped filter could not see it.

derived: `grep -rln "mkdtemp" --include="*.py" . | grep -v orchestrate-hook-fires | wc -l` — result:
```
21
```
21 files use `mkdtemp` repo-wide (broader, unfiltered re-sweep, this
session, no `README.md` filter). Read every one of the other 20 by hand
(the four already-fixed files, the three already-clean files from the
prior pass — `gates/test_closure_sweep.py`, `gates/test_accumulation.py`,
`gates/test_recurrence.py` — `bench/run.py`, and 13 not previously
checked: `gates/test_orphaned_references.py`,
`gates/test_duplicate_test_basenames.py`, `gates/test_requirement_digest.py`,
`gates/test_consult_json_parse.py`, `gates/check_runner.py`,
`tests/_spawn_test_support.py`, `test/test_spawn_skills_mount.py`,
`bench/ablation.py`, `tests/test_spawn_pipeline.py`,
`tests/test_spawn_observation_recovery.py`,
`harness/fixture-operator-experience/scenario.py`,
`harness/fixture-requirement-digest/scenario.py`) — every `mkdtemp()`
call site in each already has a `try/finally: shutil.rmtree(d)` (spot
count, e.g. `gates/test_orphaned_references.py`:
derived: `grep -c "finally:" gates/test_orphaned_references.py` → 6, `grep -c "shutil.rmtree(d)" gates/test_orphaned_references.py` → 6, 1:1 match), an
`addCleanup(shutil.rmtree, ...)`/`tearDown`, a `TemporaryDirectory()`
context manager, or (for `bench/ablation.py`'s CLI output dir and
`gates/check_runner.py`'s git-worktree helper) is not a throwaway test
fixture at all. `tests/test_spawn_board_flows.py` was the only one of
the 21 with no cleanup path; no further leaking file exists.

Applied the same fix already used in the four files: a module-level
`_created_dirs`/`_mkdtemp()` recording wrapper plus an
`@pytest.fixture(autouse=True)` teardown, added once near the top of
`tests/test_spawn_board_flows.py`. It is harmless no-op scaffolding for
the file's other ~40 `unittest.TestCase` classes, which already have
their own `setUp`/`addCleanup(shutil.rmtree, ...)` cleanup and never
call `_mkdtemp()`. Every bare `tempfile.mkdtemp()` call site inside
`EventReporting`/`ProgressEvents` — 37 of them
(derived: `sed -n '76,784p' tests/test_spawn_board_flows.py | grep -o 'tempfile\.mkdtemp()' | wc -l` — result:
```
37
```
run before the edit; the review's 43-site count also swept in six
already-cleaned-up `self.td = tempfile.mkdtemp()` sites past line 763
that already have `addCleanup(shutil.rmtree, ...)` — left untouched
here) — was switched to `_mkdtemp()`. No `__main__` standalone runner
exists in this file
(derived: `grep -n '__main__' tests/test_spawn_board_flows.py` — result:
```
(no output)
```
), so no `try/finally` counterpart was needed.

## Why

**Chose an explicit autouse fixture with `shutil.rmtree` teardown over
pytest's built-in `tmp_path`, for two concrete reasons:**

1. All four files are dual-mode — each carries a `__main__`/`_run_all()`
   path so it can run standalone with `python3 gates/test_x.py`, not
   only under pytest.
   canonical: `gates/test_gates_refusal.py:14` module docstring —
   `python3 gates/test_gates_refusal.py` listed as a supported
   invocation alongside the pytest one; all four files carry the same
   dual docstring pattern. `tmp_path` is a pytest fixture; it does not
   exist outside a pytest test-function call, so it cannot cover the
   standalone-script path these files deliberately support. An explicit
   helper function works identically in both modes.
2. `tmp_path` does not give zero accumulation even under pytest: pytest
   retains the most recent runs' `tmp_path` directories under
   `pytest-of-<user>/pytest-<N>/` for post-mortem debugging (default
   keep=3), pruning older ones lazily on a later run rather than
   deleting immediately at test end. The acceptance criterion here is a
   suite run leaving zero *new* `tmp*` directories, which calls for
   immediate, deterministic removal at test-end — an explicit
   `shutil.rmtree` in an autouse fixture teardown gives that; `tmp_path`
   gives a bounded-but-nonzero rolling window instead.

skill-verdict: test-authoring-isolation-and-fixture-strategy — applied: invoked; the teardown is registered once per file as a pytest fixture
(rule 1.6: "persistent Fresh Fixture is unavoidable → pair it with
Automated Teardown registered at setup time, not manual in-line
teardown at the end of each test") rather than duplicated as manual
cleanup at the end of every test body — the prior state of
`gates/test_accumulation.py`/`gates/test_recurrence.py` (the two files
that already had cleanup) used exactly that duplicated manual form, and
this fix does not repeat it. Each test still gets its own Fresh Fixture
(rule 1.4: cheap-to-build, mutable fixture → fresh per test, never
shared) — no call site was changed to reuse another test's directory,
satisfying the issue's non-goal. Function-scoped autouse fixture (rule
2.7: fast/mutable fixture → function scope, pytest's default) and each
`mkdtemp()` call is independently unique across xdist workers (rule
3.14: parallel workers must not share a fixture directory).

skill-verdict: work-in-english — applied: invoked; this record, the
code comments in the four changed files, and the commit/PR text are all
written in English per the policy; the final user-facing summary of
this session is in Korean. Re-invoked in the CHANGES round for the same
reason — the fifth file's fix comment and this section are English too.

other mounted skills this round (implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice,
implementation-blueprint, conformance-review-finding-record): not
triggered — the CHANGES-round work was a single-file mechanical repeat
of an already-established fixture-cleanup pattern, with no coupling/
cohesion threshold, GoF-pattern decision, data-structure choice,
multi-module structure decision, or a conformance-review verdict to
record.

**Left unaddressed — the CPU/subprocess side (#2514):** the task brief
for this session said the same fixture helper "forks a nested pytest
subprocess per test" and asked to address both concerns or say plainly
which was skipped. Checked for this directly and found no such
subprocess call in any of the four files, their shared imports
(`gates/gates.py`), or `conftest.py`:

derived: `grep -n "pytest" gates/test_gates_refusal.py gates/test_record_lint.py gates/test_ui_evidence_gate.py on-the-record/hooks/test_record_scaffold.py`
```
(every match is either a module-docstring "Run: python3 -m pytest ..."
usage comment, a code comment, or a string literal that
gates/test_record_lint.py's own tests assert against as test data —
e.g. line 1253 is a quoted "$ python3 -m pytest ..." example inside a
record-lint test fixture body, not a live call)
```

canonical: read `gates/gates.py` and `conftest.py` in full — neither
contains a `subprocess.run`/`subprocess.call`/`subprocess.Popen`
invocation of `pytest`. The actual CPU-side concern —
`pytest.ini`'s `addopts = -n auto` sizing the xdist worker pool from the
bare core count with no awareness of other concurrent sessions — is
already filed and scoped as issue #2514 ("concurrent sessions each run
pytest at -n auto: 260 workers / load 217 on 16 cores"), which asks for
a shared-budget worker count and a `spawn.py` load-admission check. That
is a different, larger mechanism than anything in these four files, and
is explicitly out of scope for this record. Not addressed here.

## What did not work

None.

## Upstream basis

The four `sha:` entries above are each file's last commit before this
change (`git log -1 --format=%H -- <path>`), cited so the diff against
this fix is reproducible. No proposal document exists for this record —
delivered under the build-now bypass (`CORE_BUILD_NOW=1`, contract v3
s19a), which skips the phase-1 proposal round.

## Acceptance evidence

### Check 1 — a full suite run leaves zero new `tmp*` directories under `/tmp`

Ran a representative subset rather than the full suite: the full suite
is `-n auto` across the whole repo on a shared, already-loaded machine
(issue #2514 documents 260 concurrent pytest workers / load 217 on 16
cores today), and a full run was the specific thing that stalled the
prior attempt at this issue. The subset below is every test in the four
files fixed here — the files identified above (grep + manual read) as
the only ones in the repo that leaked fixture directories — run under
the real, unmodified `pytest.ini` config (`addopts = -n auto`, so this
exercises the same xdist path a full run would):

acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` (before) — result:
```
15427
```
acceptance: `python3 -m pytest gates/test_gates_refusal.py gates/test_record_lint.py gates/test_ui_evidence_gate.py on-the-record/hooks/test_record_scaffold.py -q` — result:
```
102 passed in 1.20s
```
acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` (after) — result:
```
15428
```
acceptance: `comm -13 <(sort before-list) <(sort after-list)` (dirs present after, not before) — result:
```
/tmp/tmpu_8przgz
```

One new `tmp*` directory appeared. canonical: `ls -la /tmp/tmpu_8przgz`
— result:
```
work.spawn-claim  work.task.txt  work/
```
That is an orchestrator spawn-workspace directory (this is a shared
machine actively running other role sessions concurrently, per #2514's
own measurement of 6 concurrent sessions today), not a `.git`+`README.md`
fixture repo this suite created — filtered the diff to the verified
fixture shape:

acceptance: `for d in $(comm -13 before after); do [ -d "$d/.git" ] && [ -f "$d/README.md" ] && echo "$d"; done` — result:
```
(no output)
```

Zero fixture-shaped directories were left behind by the subset run.
This measurement is subset-scoped — the four fixed files, 102 tests
(derived: pytest's own `102 passed` summary line above) — not a
full-suite run, for the reason stated above.

#### Check 1, CHANGES round — the fifth file's `slow`-tier class

Ran the fixed class from `tests/test_spawn_board_flows.py`
(`EventReporting`, the larger of the two leaking classes) under the
`slow` marker, rather than the whole `slow` tier — the task brief for
this round explicitly named running the entire `slow` tier as what
stalled two earlier sessions on this host today:

acceptance: `find /tmp -maxdepth 1 -name 'tmp*' -mindepth 1 | wc -l` (before) — result:
```
36833
```
acceptance: `python3 -m pytest tests/test_spawn_board_flows.py::EventReporting -m slow -q` — result:
```
31 passed in 106.70s (0:01:46)
```
acceptance: `find /tmp -maxdepth 1 -name 'tmp*' -mindepth 1 | wc -l` (after) — result:
```
36833
```
Zero new `tmp*` dirs across the 31 tests just run above (before − after = 0).

### Check 2 — teardown survives test failure (chose: explicit `pytest.fixture(autouse=True)`, not `tmp_path`)

Confirmed live against the real helper in `gates/test_gates_refusal.py`
by temporarily inserting a deliberately-failing test that uses the
file's actual `_mkdtemp()`, running it, then restoring the file to its
committed diff.

acceptance: `python3 -m pytest gates/test_gates_refusal.py -o addopts="" -q -k "2516_deliberate"` — result:
```
FAILED gates/test_gates_refusal.py::t_2516_deliberate_failure_proves_teardown_runs_on_failure
AssertionError: deliberate failure — issue #2516 failure-path proof
1 failed, 8 deselected in 0.06s
```
acceptance: `test -e /tmp/tmp2tswsacr && echo "STILL EXISTS (LEAK)" || echo "removed (teardown ran correctly on failure)"` — result:
```
removed (teardown ran correctly on failure)
```

canonical: `git diff --stat gates/test_gates_refusal.py` after
restoring the file, confirming only this record's real change remains
(the injected test was deleted, not committed) — result:
```
 gates/test_gates_refusal.py | 46 ++++++++++++++++++++++++++++++++++++++-------
 1 file changed, 39 insertions(+), 7 deletions(-)
```

#### Check 2, CHANGES round — the fifth file's failure path

Repeated the same live check against `tests/test_spawn_board_flows.py`:
temporarily appended a deliberately-failing `unittest.TestCase` that
calls the file's real `_mkdtemp()`, ran it, then restored the file to
its committed diff.

acceptance: `python3 -m pytest tests/test_spawn_board_flows.py::Issue2516DeliberateFailureCheck -q` — result:
```
FAILED tests/test_spawn_board_flows.py::Issue2516DeliberateFailureCheck::test_deliberately_failing_after_mkdtemp
1 failed in 0.86s
```
acceptance: `find /tmp -maxdepth 1 -name 'tmp*' -mindepth 1 | wc -l` (before this failing run) — result:
```
36834
```
acceptance: `find /tmp -maxdepth 1 -name 'tmp*' -mindepth 1 | wc -l` (after this failing run) — result:
```
36834
```
Zero new `tmp*` dirs across the failing test above (before − after = 0)
— the autouse teardown ran on the failure path exactly as it does for
the four other files.

canonical: `git diff --stat tests/test_spawn_board_flows.py` after
restoring the file, confirming only this round's real change remains
(the injected test class was deleted, not committed) — result:
```
 tests/test_spawn_board_flows.py | 95 +++++++++++++++++++++++++----------------
 1 file changed, 58 insertions(+), 37 deletions(-)
```

### Check 3 — the 81k existing directories are removed, inodes reclaimed

The issue's 81,393 / 79,588-fixture-shaped / 55,715-remaining figures
were measured earlier on 2026-08-26, before this session started
(quoted verbatim from the issue's own body and comments — canonical:
`gh issue view 2516 --comments`). By the time this fix ran, `/tmp` had
already changed substantially — other sessions and/or host activity
churned it down — so the count acted on here is what was measured live
in this session, not the issue's earlier figure:

acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` — result:
```
15459
```
acceptance: shape-filtered count over all 15459 entries — result:
```
total=15459 fixture-shaped=35
```

Checked every one of the 35 fixture-shaped directories' mtime before
deleting anything, to confirm none belonged to a session still running.

acceptance: `for d in /tmp/tmp*; do [ -d "$d/.git" ] && [ -f "$d/README.md" ] && stat -c '%Y %n' "$d"; done | sort -n | tail -1` (newest of the 35) — result:
```
1787839377 /tmp/tmp7q2f6wje   # 2026-08-26 13:02:57 — over an hour before the 14:10 sweep, no live session's fixture
```

Removed exactly those 35, nothing else under `/tmp`:

acceptance: `df -i /tmp | tail -1` (before) — result:
```
/dev/nvme0n1p2 61022208 55825470 5196738   92% /
```
acceptance: `for d in <the 35 verified .git+README.md dirs>; do rm -rf -- "$d"; done` then `df -i /tmp | tail -1` (after) — result:
```
/dev/nvme0n1p2 61022208 55823630 5198578   92% /
```

Inodes reclaimed: 55825470 − 55823630 = **1,840 inodes** for 35
directories (derived: 1840/35 = 52.6 inodes/dir — consistent with the
issue's own ~56 inodes/fixture estimate). `find /tmp -maxdepth 1 -type d
-name 'tmp*' | wc -l` afterward: 15,425 — the remaining ~15,390 `tmp*`
entries are unrelated orchestrator/host temp directories, not this
issue's verified fixture shape, and were left untouched per the issue's
own must-not (checked: not deleted, no shape-match — result:
excluded from the removal list by construction of the `.git`+`README.md`
filter above).

#### Check 3, CHANGES round — no pre-existing fifth-file-shaped leftovers

conformance-review verdicted this check Present already (not redone
here). Checked separately for the fifth file's own leak shape
(`.git` + `work/` tree, no `README.md`) in case any pre-existing ones
were still on disk:

derived: `for d in /tmp/tmp*; do [ -d "$d/.git" ] 2>/dev/null && [ -d "$d/work" ] && echo "$d"; done 2>/dev/null | wc -l` — result:
```
0
```
No pre-existing fifth-file-shaped directories were present to sweep.

## Open findings

None.

## Next steps

None — `loop_state: landed`.
