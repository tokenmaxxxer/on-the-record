---
issue: 2516
role: conformance-review
author: conformance-review
loop_state: complete
upstream:
  - path: 9a6687b8583deb77c867bc234820404a54b7ccb6:docs/issue-2516/reports/implementation.md
    sha: 9a6687b8583deb77c867bc234820404a54b7ccb6
subject: PR #2523 (issue-2516/implementation, head 9a6687b8583deb77c867bc234820404a54b7ccb6)
test: gates/test_gates_refusal.py, gates/test_record_lint.py, gates/test_ui_evidence_gate.py, on-the-record/hooks/test_record_scaffold.py (independently re-run on both the PR branch and main, in separate git worktrees); a deliberately-failing test independently written against the real `_mkdtemp()` helper; an independent repo-wide `mkdtemp` grep broader than the PR's own scoped grep; live leak reproduction against `tests/test_spawn_board_flows.py`'s slow tier
result: failed
assertedBy: conformance-review (independent re-run, this session)
---

# issue-2516 — conformance-review record

## What was done

Independent conformance review of PR #2523 against issue #2516's three
acceptance checks. Re-derived every claim from primary evidence rather
than citing `9a6687b8583deb77c867bc234820404a54b7ccb6:docs/issue-2516/reports/implementation.md`
(PR #2523's own implementation record).

canonical: `gh pr view 2523 --json headRefName,baseRefName -q '.headRefName + " " + .baseRefName'` — result: `issue-2516/implementation main`

Set up two isolated git worktrees to compare branches without touching
this session's own working tree:
derived: `git worktree add /tmp/wt-pr2523 origin/issue-2516/implementation && git worktree add /tmp/wt-main origin/main` — result: both created cleanly, PR branch at head `9a6687b8`, main at head `656397e4`.

### Check 1 — full suite run leaves zero new `tmp*` dirs

Re-ran the PR's own claimed subset (the four fixed files) on both
branches, counting `/tmp` before and after each run myself:

acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` (before, PR branch) — result:
```
15585
```
acceptance: `python3 -m pytest gates/test_gates_refusal.py gates/test_record_lint.py gates/test_ui_evidence_gate.py on-the-record/hooks/test_record_scaffold.py -q` (PR branch, real `pytest.ini` `-n auto`) — result:
```
102 passed in 1.27s
```
acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` (after, PR branch) — result:
```
15585
```
Zero new dirs on the PR branch for these 102 tests (derived above:
before=15585, after=15585, `after - before = 0`) — matches the PR's
own claim, independently re-derived rather than cited.

acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` (before, main) — result:
```
15585
```
acceptance: `python3 -m pytest gates/test_gates_refusal.py gates/test_record_lint.py gates/test_ui_evidence_gate.py on-the-record/hooks/test_record_scaffold.py -q` (main, same four files, same command) — result:
```
102 passed in 1.30s
```
acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` (after, main) — result:
```
15654
```
derived: `comm -13 <(sort before) <(sort after) | wc -l` (main) — result:
```
69
```
Of those 69 new dirs, shape-filtered for `.git`+`README.md`:
derived: `for d in <the 69>; do [ -d "$d/.git" ] && [ -f "$d/README.md" ] && echo "$d"; done | wc -l` — result:
```
59
```
So on `main` this same subset leaks 69 new `tmp*` dirs, 59 of them the
exact `.git`+`README.md` fixture shape the issue names (the other 10
are the empty-dir shape from `test_ui_evidence_gate.py`'s
`_norepo_root()`). This session's own spawning task text quoted a prior
orchestrator measurement:
```
the orchestrator measured 59 leaked dirs on main vs 0 on this branch
across 92 tests from two of the four files
```
canonical: this session's own task-assignment text (quoted verbatim above, from the prompt that launched this review) — my independent re-derivation, run across all four files rather than two, produced the same 59-fixture-shaped figure on `main` (derived above), corroborating rather than merely citing it. All 69 dirs from this
main-branch measurement were removed immediately after counting them
(`for d in <the 69>; do rm -rf -- "$d"; done`) so this review's own
measurement does not itself add to the leak.

This establishes the fix works for the four files it targets — but see
"Open findings" below: check 1 as the issue states it ("a full suite
run") is not met, because a fifth leaking file outside the PR's scope
was found by broadening the grep past the PR's own search.

### Check 2 — teardown survives the failure path

Rather than relying on the PR's own inserted-then-reverted failing
test, independently authored a different deliberately-failing test
against the real, unmodified `_mkdtemp()` helper on the PR branch:

derived: appended to `gates/test_gates_refusal.py` (PR-branch worktree, reverted after the check — never committed):
```python
def t_2516_independent_failure_check():
    d = _mkdtemp()
    (d / "marker_for_independent_check").write_text("x")
    globals()['__INDEPENDENT_CHECK_DIR__'] = d
    assert False, "independent reviewer's deliberate failure"
```
acceptance: `python3 -m pytest gates/test_gates_refusal.py -o addopts="" -q -k "independent_failure_check"` — result:
```
FAILED gates/test_gates_refusal.py::t_2516_independent_failure_check - AssertionError: independent reviewer's deliberate failure
1 failed, 8 deselected in 0.05s
```
acceptance: `comm -13 <(sort before) <(sort after)` (new `tmp*` dirs across this failing run) — result:
```
(no output)
```
Zero new dirs survived (derived above: empty diff) — the directory
`_mkdtemp()` handed out was gone immediately after the failing test
finished, while the pytest worker process was still running (not a
process-exit artifact). Confirms the PR's stated choice — an explicit
`pytest.fixture(autouse=True)` over `tmp_path` — actually delivers the
failure-path guarantee the issue's non-goal requires, independently of
the PR's own claim.

### Check 3 — isolation unchanged

canonical: read the diff and the current state of all four call-site
patterns (`_repo_with_record`, `_norepo_root`, `_empty_repo`) in the PR
branch worktree (`gates/test_gates_refusal.py`, `gates/test_record_lint.py`,
`gates/test_ui_evidence_gate.py`, `on-the-record/hooks/test_record_scaffold.py`,
sha `19829a30e51e38a157927f14c4bef9ded44dd7e9` for all four) — each
helper still calls `tempfile.mkdtemp()` (inherently unique per call)
exactly once per invocation, and every test function calls the helper
fresh; `_created_dirs` is only an append-only recording list drained by
the teardown fixture, never a cache that could hand back an existing
directory. No call site was changed to reuse another test's directory.
Under `pytest-xdist` (`-n auto`, the real `addopts`), `_created_dirs` is
a separate in-memory list per worker process, and the autouse fixture
drains it after each individual test within that worker — no
cross-test or cross-worker sharing.

### Check 4 — the three untouched files, and `bench/run.py`

Independently re-ran a broader version of the PR's own audit grep,
without the PR's own `README.md`-content filter, to check whether the
PR's four-file scope was actually complete:

derived: `grep -rln "mkdtemp" --include="*.py" . | grep -v orchestrate-hook-fires | wc -l` (PR-branch worktree) — result:
```
20
```
20 files use `mkdtemp`, not the 7 the PR's own narrower grep surfaced —
see "Open findings" for what this broader scope turns up beyond the
PR's own list.

For the three files the PR's implementation record says it read and
left alone:

canonical: read `gates/test_closure_sweep.py` in full — `AccumulationTrend._repo()` (line 466) calls `Path(tempfile.mkdtemp())` and immediately registers `self.addCleanup(shutil.rmtree, d, ignore_errors=True)` (line 475); `unittest.TestCase.addCleanup` runs on pass, fail, and error alike, the same guarantee class as a pytest fixture teardown. The other two `TemporaryDirectory()` uses in this file are self-cleaning context managers. Genuinely clean.

canonical: read `gates/test_accumulation.py` in full — derived: `grep -c "finally:" gates/test_accumulation.py` → 11, derived: `grep -c "shutil.rmtree(d)" gates/test_accumulation.py` → 11 — every `Path(tempfile.mkdtemp())` call site is immediately followed, in the same test function, by a `try/finally: shutil.rmtree(d)`; the counts match 1:1 across all 11 test functions. Genuinely clean.

canonical: read `gates/test_recurrence.py` in full — the two mkdtemp-building helpers (`_git_repo`, `_git_repo_with_diff`) return `d` uncleaned, but derived: counting call sites of `_git_repo(`/`_git_repo_with_diff(` outside their own `def` → 5, and `finally: shutil.rmtree(d)` blocks → 5 — every one of the 5 call sites wraps the returned `d` in its own `try/finally: shutil.rmtree(d)`, a 1:1 match. Genuinely clean.

acceptance: `python3 -m pytest bench/ --collect-only -q` — result:
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
Only `bench/test_ablation.py` is collected under `bench/`; zero tests
come from `bench/run.py`. Independently confirmed never collected —
its filename matches neither `pytest.ini`'s default `python_files`
pattern (`test_*.py`/`*_test.py`, unmodified — derived: `grep -n "python_files" pytest.ini` → no match, so the pytest default applies) nor any override.

## Why

Chose independent re-derivation over citing the PR's own numbers for
every check, per this role's mandate and
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; ran the same commands myself on both branches in separate worktrees (canonical: the acceptance/derived command-and-result pairs under "What was done" above, all executed this turn) rather than trusting the PR's before/after figures, deliberately wrote a fresh failing test rather than reusing the PR's inserted-then-reverted one, and broadened the audit grep past the PR's own README.md-content filter specifically because a narrower filter is exactly the kind of scope-shaping the skill warns against carrying over from an upstream author's own search.

Used git worktrees (`git worktree add`) instead of checking out
branches in-place, so the PR-branch and main-branch runs could be
measured back-to-back without disturbing this session's own branch
state or requiring a `git stash`.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split the issue's three acceptance bullets into requirements below, each carrying its own "must not" as an explicit sub-clause rather than folding it silently into the parent bullet.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used Test (re-running the actual suite) for checks 1–2 since executable tests already exist and were reused rather than manually re-derived, and Inspection for check 4's static "does this file already clean up" property.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Incorrect rather than Present to requirement 1 because the built fix does not fire on the full suite the requirement names, and Unverifiable rather than a guessed Present/Absent to requirement 3 because the pre-sweep `/tmp` state it would need to be re-counted against no longer exists on this shared, continuously-mutating host.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; cited each of the four fixed files' individual commit sha (all `19829a30e51e38a157927f14c4bef9ded44dd7e9`) plus the untouched fifth file's own sha (`878126c4fa5054dfa5e2878383e9636c012f8c25`, `tests/test_spawn_board_flows.py` on `main`) as separate contributing-file links rather than one bundled citation.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of the mkdtemp-using files was feasible (one grep, 20 files, all read/categorized) and was performed, so no sampling scope was needed.
skill-verdict: conformance-review-finding-record — applied: invoked; each verdict block below carries its own evidence pointer, e.g. `19829a30e51e38a157927f14c4bef9ded44dd7e9:gates/test_gates_refusal.py:44` for requirement 2's evidence, rather than a bare pass/fail summary.
skill-verdict: conformance-review-severity-classification — not-applicable: this review's scope was not explicitly extended into risk-weighting; findings are recorded but not banded.

## Upstream basis

- `9a6687b8583deb77c867bc234820404a54b7ccb6:docs/issue-2516/reports/implementation.md` — the record under review.
- `gates/test_gates_refusal.py`, `gates/test_record_lint.py`, `gates/test_ui_evidence_gate.py`, `on-the-record/hooks/test_record_scaffold.py` — each last touched at sha `19829a30e51e38a157927f14c4bef9ded44dd7e9` (PR #2523's own commit).
- `tests/test_spawn_board_flows.py` — last touched at sha `878126c4fa5054dfa5e2878383e9636c012f8c25` on `main`, untouched by PR #2523; the file this review's own broadened grep surfaced as a fifth, unaddressed leak source.
- `.on-the-record/test-tiers.json` (current `main`/PR-branch content, identical on both) — defines this repo's own two-command test suite: `fast` = `python3 -m pytest -q -m "not slow"`, `slow` = `python3 -m pytest -q -m slow`; `tests/test_spawn_board_flows.py` is explicitly listed as a `slow`-tier `trigger_change_classes` file.

## Open findings

**Finding 1 — requirement "a full suite run leaves zero new `tmp*`
directories" is not met; a fifth leaking file was never in the PR's
scope.**

- requirement: issue #2516 acceptance check 1 — "a full suite run leaves zero new `tmp*` directories under `/tmp`"
- spec_ref: issue #2516, Acceptance, bullet 1
- verdict: Incorrect
- evidence: `tests/test_spawn_board_flows.py:66` starts `EventReporting._run` (sha `878126c4fa5054dfa5e2878383e9636c012f8c25`), which builds a git-backed workspace at `Path(td) / "work"` where `td` is `tempfile.mkdtemp()` passed inline at the call site; derived: `awk '/@pytest.mark.slow/{flag=1} flag' tests/test_spawn_board_flows.py | grep -c "tempfile.mkdtemp()"` → 43 such call sites after the `@pytest.mark.slow` marker on this one class. `_run`'s own `finally:` block (`tests/test_spawn_board_flows.py:100`-`103`) restores only `sys.stdout`/`sys.stderr`/`spawn.ROSTER` — it never calls `shutil.rmtree` on `td`. Live-reproduced: `timeout 60 python3 -m pytest tests/test_spawn_board_flows.py -q -m slow -o addopts="" -k "test_end_turn_result_is_not_a_gate_refusal"` (single slow-tier test) — result:
```
1 passed, 133 deselected in 14.56s
```
and `comm -13` of `find /tmp -maxdepth 1 -type d -name 'tmp*'` before/after that one test left exactly one new dir, confirmed via `ls -la` to contain a `.git` directory, then removed by this review.
- rationale: the issue names "a full suite run," and this repo's own `.on-the-record/test-tiers.json` defines the full suite as two tiers (`fast` + `slow`), explicitly listing `tests/test_spawn_board_flows.py` as a `slow`-tier file. PR #2523's own acceptance evidence (`9a6687b8583deb77c867bc234820404a54b7ccb6:docs/issue-2516/reports/implementation.md`, Check 1) explicitly scopes its run to the four files it fixed, never runs the `slow` tier, and its own file-discovery grep (`grep -rln "README.md" ... | xargs grep -l "mkdtemp"`) is narrower than a plain `mkdtemp` grep — narrow enough to miss this file, since its leaked directories don't contain a `README.md` (they contain `.git` + a `work/` tree instead). The fix is real and correctly implemented for the four files it covers, but the acceptance criterion as the issue states it — a full suite run, zero new dirs — is not met, because a fifth file with a materially identical leak (git-init'd fixture directory via bare `tempfile.mkdtemp()`, no teardown at all) sits entirely outside the PR's `code_under_review`.
- spec_vs_built: spec requires a full suite run to leave zero new `tmp*` directories; built thing achieves zero only across the 4-file subset of the `fast` tier it targeted (derived above: 102 passed, 0 new dirs on the PR branch) — the `slow` tier is untested by the PR and independently confirmed still leaking (derived above: 43 leaking call sites in one file's slow-marked class alone, 1 confirmed leaked dir from running just one of its tests).

**Finding 1, re-check pass (per verdict-assignment rule 6) — is this a false positive from a stale/near-miss match?**

Re-checked before finalizing: derived: `grep -n "tearDown\|addCleanup" tests/test_spawn_board_flows.py` — result: no hits inside the `EventReporting` class body, confirming `td` is never threaded into any cleanup path elsewhere in the class. Combined with the live single-test reproduction above (one test run, one dir left behind, confirmed via direct `ls`), this is not a false positive.

**Requirement 2 (teardown mechanism, failure path) — for the four
files in scope.**

- requirement: issue #2516 acceptance check 2 — "fixture repos are created through a mechanism that removes them even when the test fails or errors ... confirm the teardown runs on the failure path with a deliberately failing test"
- spec_ref: issue #2516, Acceptance, bullet 2
- verdict: Present
- evidence: `gates/test_gates_refusal.py:44`-`57` (`_created_dirs` + `@pytest.fixture(autouse=True) def _cleanup_fixture_repos`), same pattern at `gates/test_record_lint.py`, `gates/test_ui_evidence_gate.py`, `on-the-record/hooks/test_record_scaffold.py`, sha `19829a30e51e38a157927f14c4bef9ded44dd7e9` for all four. Independently re-verified live with a self-authored failing test (see "What was done", Check 2 above) — teardown ran, directory removed, while the pytest worker process was still alive (not a process-exit artifact).
- rationale: the chosen mechanism (explicit autouse fixture, not `tmp_path`) runs in pytest's own per-test teardown phase regardless of test outcome, and this review's own independently-constructed failure — not the PR's — confirms it (derived above: zero new dirs survived the failing run). Satisfies the issue's explicit "must not rely on process-exit cleanup alone."
- Note: this verdict is scoped to the four files PR #2523 actually changed. It does not extend to `tests/test_spawn_board_flows.py` (Finding 1), which has no teardown mechanism of any kind.

**Requirement 3 — 81k existing directories removed, inodes quoted.**

- requirement: issue #2516 acceptance check 3 — "the 81k existing directories are removed, and the record quotes inodes reclaimed"
- spec_ref: issue #2516, Acceptance, bullet 3
- verdict: Unverifiable
- evidence (missing): `9a6687b8583deb77c867bc234820404a54b7ccb6:docs/issue-2516/reports/implementation.md`'s Check 3 quotes a live sweep of 35 fixture-shaped directories (1,840 inodes, via `df -i` before/after) measured at implementation time, after noting the issue's original 81,393 figure had already fallen to a live-measured 15,459-total/35-fixture-shaped state by the time that session ran. This review cannot re-count against either the issue's original 81k snapshot or the implementation's own 35-dir snapshot — both describe `/tmp` states that no longer exist on this shared, continuously-mutating host.
- rationale: independently counted the current live state instead — acceptance: `find /tmp -maxdepth 1 -type d -name 'tmp*' | wc -l` — result: `15594`; derived: shape-filter (`.git`+`README.md` present) over all current `/tmp/tmp*` entries → 114 fixture-shaped dirs present right now, more than the 35 the implementation record swept. On a shared host under continuous concurrent test-suite activity (issue #2514's own measurement, cited in the issue body, documents six-plus concurrent orchestrator sessions per day) this is consistent with unrelated sessions creating fresh fixture-shaped directories since the sweep, not necessarily a regression of the sweep itself — but this review has no static, single-tenant `/tmp` to measure against, so it cannot attribute the current 114 to "created after the sweep by other sessions" versus "the sweep undercounted." The sweep's *mechanism* (shape-filter by `.git`+`README.md`, mtime-check every candidate before deleting, `df -i` before/after) is sound on inspection of the implementation record's own transcript; whether it fully discharged the specific "81k" figure is not independently re-derivable after the fact.

## Next steps

The three requirement verdict blocks above are each independently
evidenced with their own commit-pinned citation — e.g.
`878126c4fa5054dfa5e2878383e9636c012f8c25:tests/test_spawn_board_flows.py:66`
for requirement 1, `19829a30e51e38a157927f14c4bef9ded44dd7e9:gates/test_gates_refusal.py:44`
for requirement 2 — and every acceptance bullet in issue #2516 now has
an assigned verdict with no further check pending for this review
pass, so `loop_state: complete`.

Recommend the fix return to implementation to add
`tests/test_spawn_board_flows.py` to `code_under_review` (the same
`_created_dirs` + autouse-fixture pattern already proven correct in the
other four files would apply directly — `_run`'s existing `finally:`
block only needs `shutil.rmtree(td, ignore_errors=True)` added), and to
state explicitly in the acceptance evidence whether "a full suite run"
means the `fast` tier alone or both `fast` + `slow` tiers per
`.on-the-record/test-tiers.json`, since the issue's own wording ("a
full suite run") does not name a tier and this repo's test-tier
contract makes that ambiguity resolvable rather than a matter of
interpretation.
