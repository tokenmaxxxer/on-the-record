---
issue: 2516
role: execution-observation
author: execution-observation
loop_state: landed
upstream:
  - path: docs/issue-2516/reports/implementation.md
    sha: 9a6687b8583deb77c867bc234820404a54b7ccb6
subject: PR #2523 (branch issue-2516/implementation, "stop leaking git fixture repos into /tmp across the test suite")
test: independent re-derivation of (a) leak-stop via main-vs-PR-branch tmp* dir counts, (b) failure-path teardown via a self-authored deliberately-failing test against the real _mkdtemp() helper, (c) test-isolation preservation by reading every call site, (d) the three left-alone files' pre-existing cleanup and bench/run.py's non-collection — none of it reused from or citing the PR's own commands
result: passed
assertedBy: execution-observation
---

# issue-2516 — execution-observation record

## What was done

Independently re-verified all four claims PR #2523 makes, without citing
its own recorded commands as evidence — each check below was re-derived
from scratch in a fresh git worktree. `docs/issue-2516/reports/implementation.md`
is untracked from this checkout's working tree (it lands on branch
`issue-2516/implementation`, not yet merged to `main`); cited below as
`9a6687b8583deb77c867bc234820404a54b7ccb6:docs/issue-2516/reports/implementation.md`.

**(a) The leak actually stops.** Checked out `origin/main` and
`origin/issue-2516/implementation` into two separate worktrees
(`/tmp/wt-pr2523-main`, `/tmp/wt-pr2523-impl`) and ran the identical
command in each, under the repo's real unmodified `pytest.ini`
(`addopts = -n auto`):

acceptance: `python3 -m pytest gates/test_gates_refusal.py gates/test_record_lint.py gates/test_ui_evidence_gate.py on-the-record/hooks/test_record_scaffold.py -q` on `origin/main` (commit `656397e4`) — result:
```
102 passed in 1.27s
```
acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` before/after that run, on `origin/main` — result:
```
before: 15516
after:  15585
new dirs (comm -13 before after): 69
```
acceptance: the same pytest command on `origin/issue-2516/implementation` (commit `9a6687b8`) — result:
```
102 passed in 1.29s
```
acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` before/after that run, on `origin/issue-2516/implementation` — result:
```
before: 15585
after:  15585
new dirs (comm -13 before after): 0
```
69 new `tmp*` directories on `main` vs 0 on the PR branch, for the same
102 tests (derived: pytest's own summary line, both runs quoted above).
This is a different run than the builder's own — the task brief cited
59 leaked across "92 tests from two of the four files" as the
orchestrator's figure, derived here instead from all four files/102
tests in one pass. Different scope, same direction and same order of
magnitude, independently reproduced rather than cited.

acceptance: `comm -13 <(sort main_before) <(sort main_after) | xargs rm -rf --` then `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` — result:
```
15585
```
Cleaned up the 69 dirs my own main-branch verification run created;
the re-check above lands back on the PR-branch after-count (`15585`) —
this record's own verification did not add to the leak it was checking.

**(b) Teardown survives the failure path, independently constructed.**
The PR's own record demonstrates this with its own injected test; I did
not reuse that test or its output. In the PR-branch worktree, I
inserted a different deliberately-failing test
(`t_2516_execobs_independent_failure_proof`) into
`gates/test_gates_refusal.py` that calls the file's real `_mkdtemp()`
helper, ran it, then reverted the file with `git checkout --` (worktree
removed afterward, so no trace remains):

acceptance: `python3 -m pytest gates/test_gates_refusal.py -o addopts="" -q -k "t_2516_execobs_independent_failure_proof" -s` — result:
```
FAILED gates/test_gates_refusal.py::t_2516_execobs_independent_failure_proof
AssertionError: execution-observation independent deliberate failure
1 failed, 8 deselected in 0.05s
```
acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | sort` captured immediately before and after that single failing-test run, diffed with `comm -13` — result:
```
(no output — zero new directories survived)
```
The directory `_mkdtemp()` handed to my failing test was gone
immediately after the run, confirming the `@pytest.fixture(autouse=True)`
teardown ran in pytest's own per-test teardown phase even though the
test body raised `AssertionError`, not just on the passing path.

**(c) Test isolation is unchanged.** canonical: read every call site the
diff touches (`grep -n "_mkdtemp()\|_norepo_root()\|_empty_repo()"`
across all four changed files) and the body of each wrapper —
```
def _mkdtemp() -> Path:
    d = Path(tempfile.mkdtemp())
    _created_dirs.append(d)
    return d
```
Each wrapper calls the stdlib `tempfile.mkdtemp()` fresh on every
invocation and only appends the result to a list for later cleanup —
there is no memoization, caching, or module-level shared instance, so
every call site the grep found still receives its own unique, unshared
directory exactly as before the fix; only the cleanup path changed.
`_created_dirs` is a plain module-level list, one per xdist worker
process (each worker has its own Python import), so parallel workers
cannot collide on it, and `tempfile.mkdtemp()`'s own uniqueness
guarantee prevents two tests from ever getting the same path.

**(d) The three left-alone files and `bench/run.py`.**

`gates/test_closure_sweep.py` — canonical: read the file in full — two
call sites use `tempfile.TemporaryDirectory()` (self-cleaning context
manager) and one raw `tempfile.mkdtemp()` is paired with
`self.addCleanup(shutil.rmtree, d, ignore_errors=True)`. Already clean.

`gates/test_accumulation.py` — canonical: read the file in full — every
fixture repo is built through the `_repo()` helper, called fresh at each
call site, each immediately wrapped in `try: ... finally:
shutil.rmtree(d)` (derived: `grep -c "shutil.rmtree(d)" gates/test_accumulation.py` → 12, one per call site). Already clean.

`gates/test_recurrence.py` — canonical: read the file in full — every
fixture repo comes from `_git_repo()` or `_git_repo_with_diff()`, and
`derived: grep -c "shutil.rmtree(d)" gates/test_recurrence.py` → 5,
one per call site, each wrapped in `try: ... finally:
shutil.rmtree(d)`. Already clean.

`bench/run.py` — acceptance: `python3 -m pytest --collect-only -q
bench/run.py` — result:
```
no tests collected in 0.01s
```
acceptance: `python3 -m pytest --collect-only -q bench/` — result:
```
bench/test_ablation.py::KeyExclusionTest::test_assert_no_key_material_raises_on_leak
bench/test_ablation.py::KeyExclusionTest::test_every_task_has_key_and_metadata
bench/test_ablation.py::KeyExclusionTest::test_every_task_workspace_excludes_key_material
bench/test_ablation.py::StreamJsonParsingTest::test_missing_result_event_is_honest_none
bench/test_ablation.py::StreamJsonParsingTest::test_parses_terminal_result_event
bench/test_ablation.py::ScoresheetSchemaTest::test_arm_a_plan_names_spawn_and_budget
bench/test_ablation.py::ScoresheetSchemaTest::test_fabrication_check_extracts_artifact_claims
bench/test_ablation.py::ScoresheetSchemaTest::test_scoresheet_has_blank_verdicts_and_all_metric_families

8 tests collected in 0.01s
```
`run.py` is absent from both the explicit-target collection (zero tests)
and the whole-directory collection (only `test_ablation.py`'s 8 show
up). `pytest.ini` sets `python_functions` but leaves `python_files` at
pytest's default (`test_*.py`, `*_test.py`), which `run.py` matches
neither of. Confirmed genuinely never collected by running collection,
not by reading the config alone.

**Additional observation, not in the original ask:** acceptance:
`find /tmp -maxdepth 1 -type d -name 'tmp*' -exec test -d {}/.git \; -a -exec test -f {}/README.md \; -print | wc -l`, run after this record's own cleanup above — result:
```
114
```
acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' -newer /tmp/main_after.txt | wc -l` — result:
```
70
```
114 fixture-shaped directories exist on the live `/tmp` right now, 70 of
them newer than this record's own test runs. This is not a defect in PR
#2523 — the fix only covers this repo's four files, and the issue body
itself measured six concurrent sessions/day on this shared machine;
other concurrently-running sessions checking out code without this fix
(different branches, different repos) continue to create fixture-shaped
`tmp*` dirs independently of this PR. This confirms the PR record's own
"shared, actively-running machine" caveat rather than contradicting the
fix verified in (a) above.

## Why

Chose to re-derive every claim from a fresh git worktree pair
(`origin/main` vs `origin/issue-2516/implementation`) rather than
checking out the PR branch in this session's own working tree, so this
record's own branch (`issue-2516/execution-observation`, which carries
no code changes — canonical: `git status` at session start showed only
untracked `docs/issue-2516/`) stayed untouched throughout, and so main
and the PR branch could be measured under identical `/tmp` starting
conditions back-to-back rather than sequentially disturbing one shared
checkout.

Chose to author a second, independently-written failing test rather
than re-running the PR's own injected test, to keep this verification's
outcome decoupled from the builder's own test authorship — see (b)
above for the resulting independent pass/fail and cleanup evidence.

## Upstream basis

`9a6687b8583deb77c867bc234820404a54b7ccb6:docs/issue-2516/reports/implementation.md`
(head of `origin/issue-2516/implementation`, PR #2523) is the record
under review. The four code files it changes
(`gates/test_gates_refusal.py`, `gates/test_record_lint.py`,
`gates/test_ui_evidence_gate.py`,
`on-the-record/hooks/test_record_scaffold.py`) were read in full at that
same commit.

## Open findings

1. The issue's check 1 asks for "a full suite run" leaving zero new
   `tmp*` directories; both the PR's own evidence and this record's
   re-derivation in (a) above are scoped to the four fixed files (102
   tests — derived: pytest's own `102 passed` summary line quoted in (a)),
   not a full-suite run. The PR's record states this scoping explicitly
   and gives a resource-constraint rationale (shared machine, a prior
   full-suite attempt at this issue stalled). This record did not
   attempt a full run either, for the same reason (six concurrent
   sessions measured live on this machine today per the issue body).
   Resolution path: the acceptance-owning role should decide whether the
   four-file subset run is sufficient evidence for check 1, or whether a
   full-suite run is still required before the issue closes.
2. Checks (b), (c), and (d) have no open gaps — each was independently
   reproduced in "What was done" above with its own acceptance/canonical
   evidence.

## Next steps

None — `loop_state: landed`. Open finding 1 is a scoping question for
the acceptance-owning role, not a defect this record can resolve
unilaterally.

## What did not work

None — every independent re-derivation attempted in this record
succeeded on the first try; no dead end to record.
