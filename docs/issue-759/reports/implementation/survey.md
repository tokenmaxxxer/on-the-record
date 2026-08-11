# Current-state survey — issue-759

## Reproduction (confirmed on `main` @ `b70e3c5`, same commit as `origin/main`)

derived: `python3 -m pytest gates/ tests/ -q`
```
FAILED gates/test_boundary.py::t_all_gates_modules_recorded
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
FAILED tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge
3 failed, 908 passed, 2 skipped in 139.77s
```
Matches the issue body's pasted output exactly (issue text cites `e3266fa`;
this session's HEAD is `b70e3c5`, three merges later — the three failures
are unchanged, so nothing landed since re-fixed them).

## Failure 1 & 2 — same root cause

Both `t_all_gates_modules_recorded` and `t_all_generators_recorded_and_disjoint`
name the same file:

derived: `python3 -m pytest gates/test_boundary.py::t_all_gates_modules_recorded gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint -q`
```
AssertionError: record-claim-shape-directive.sh 가 docs/specs/enforcement-boundary.md 에 판정(verdict)이 기록된 행으로 없다 (#441).
AssertionError: record-claim-shape-directive.sh 가 docs/specs/generated-paths.md 에 판정이 기록된 행으로 없다 (issue #684).
```

`on-the-record/hooks/record-claim-shape-directive.sh` landed via issue-730
(PR #733 phase-1, merged 04:12; PR #738/#740 phase-2, merged ~04:24-05:20,
2026-08-11) — a `UserPromptSubmit` hook that prints `record-claim-guard.sh`'s
citation shape, generated from `gates/record_lint.py` docstrings at hook-run
time. It writes `on-the-record/hooks/hooks.json` (wiring),
`on-the-record/hooks/record-claim-shape-directive.sh` itself, and
`on-the-record/hooks/test_record_claim_guard.py`. Neither issue-730 PR
touched `docs/specs/enforcement-boundary.md` or `docs/specs/generated-paths.md`
— the exact omission class #441/#684 exist to catch, and the exact class
#689 (PR #691, merged 2026-08-11 00:08) already repaired once for three
other files (`ui_evidence_gate.py`, `remediation_spawn.py`,
`role-axis-completeness-guard.sh`).

Classification for the two missing rows, derived by reading the file and
matching existing analogous rows:

- `on-the-record/hooks/record-claim-shape-directive.sh` has no
  `write_text(`/`open(..., "w"`/`.mkdir(`/`shutil.copy|move`/`mkdir -p`/
  `git clone` call —
  derived: `grep -nE "write_text\(|open\([^)]*['\"]w|\.mkdir\(|shutil\.(copy|move)|mkdir[[:space:]]+-p|git[[:space:]]+clone" on-the-record/hooks/record-claim-shape-directive.sh` returns nothing (exit 1).
  It only imports `gates/record_lint.py` and prints to stdout — same shape
  as the already-recorded `record-claim-guard.sh` row in
  `generated-paths.md` (`n/a — reads/validates only, no write call`).
- In `enforcement-boundary.md` it is a `UserPromptSubmit` role-directive
  hook, same act-class as the already-recorded `directive.sh` row
  (`contract | already shipped; UserPromptSubmit role directive injection`)
  — verdict `contract`, reachable zero-install (ships with the plugin,
  fails open on missing `CLAUDE_ROLE`/import failure per its own header
  comment).

## Failure 3 — different root cause

derived: `python3 -m pytest tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge -q`
```
FileNotFoundError: [Errno 2] No such file or directory: PosixPath('.../t_find_violations_uses_record_0/repo')
  gates/closure_sweep.py, in find_violations
    pr_index, pr_index_ok = _pr_index_all(root)
  gates/closure_sweep.py, in _pr_index_all
    r = subprocess.run(["gh", "pr", "list", "--state", "all", "--json", ...
```

The test in `tests/test_gates.py` (function
`t_find_violations_uses_record_evidence_for_keywordless_merge`) mocks
`spawn._pr_for_branch`, `closure_sweep._pr_view_state_body`, and
`ci._fetch_ref_file`, then calls `closure_sweep.find_violations(root, ...)`
expecting those mocks to be exercised. It does **not** mock
`closure_sweep._pr_index_all`. Issue #682 (PR #683, commit `7a39b01`) added
`_pr_index_all` as a list-based fast path that `find_violations` now tries
*first*; the per-branch `_pr_for_branch`/`_pr_view_state_body` fallback
this test targets only fires when `_pr_index_all` reports a truncated list
(`(None, True)`). Un-mocked, `_pr_index_all` shells out to the real
`gh pr list` with `cwd=root` — a pytest tmp_path that was never created on
disk — hence `FileNotFoundError`, not an assertion failure.

This is the *same* defect class that broke a sibling test in
`gates/test_closure_sweep.py` — the `FindViolationsSkips` class's
pr-view-failure-is-a-skip case — which PR #691 (closing #689) already
fixed by adding exactly this mock (see that file's `FindViolationsSkips`
class, around the point where it patches `closure_sweep._pr_index_all`):
```python
orig_pr_index_all = closure_sweep._pr_index_all
closure_sweep._pr_index_all = lambda root: (None, True)
self.addCleanup(setattr, closure_sweep, "_pr_index_all", orig_pr_index_all)
```

derived: `git log -S_pr_index_all --oneline --all -- gates/closure_sweep.py` shows `7a39b01` (issue-682) as the sole commit introducing `_pr_index_all`; `git log -S t_find_violations_uses_record_evidence_for_keywordless_merge --oneline --all` shows the test predates that commit (`bceafac`, issue-383) — issue-682 broke it, #689/#691 fixed one sibling test broken the same way but missed this one.

**Verdict: the test states the contract correctly** (that `find_violations`
computes `has_record_evidence` from the record file via the per-branch
fallback path) — the fix belongs in the test (add the same
`_pr_index_all` mock + cleanup), not in `gates/closure_sweep.py`.

## Recurrence: why #689's fix did not hold

#689 (merged 2026-08-11 00:08) added the 3 missing rows existing then and
fixed the one broken closure_sweep test it found. It did not add any
mechanism that checks a *future* new file/test against the same rule at
write time. Within 5 hours, issue-730 landed a new hook
(`record-claim-shape-directive.sh`) through the normal phase-1/phase-2 PR
flow with no gate objecting to the missing spec rows — nothing runs
`gates/test_boundary.py`/`gates/test_generated_paths.py` at commit or
PR-create time. This repo does not run CI (#460), so the only existing
enforcement point for "was a new gate module classified" is the pytest
suite itself, which nobody is required to run before merging (unlike
`git commit`, which several existing hooks already gate on).

## Existing prior art for a git-commit-time registration guard

Two hooks already implement the exact shape needed — `PreToolUse`+`Bash`,
intercept `git commit`, read the staged file set via
`git diff --cached --name-only`, compare staged content
(`git show :<path>`) against a `docs/specs/*.md` table, fail open on any
environment gap, fail closed only on a positively-determined violation:

- `on-the-record/hooks/spec-index-preflight.sh` (issue #459) — denies a
  commit that changes a spec-index-tracked file's content without a
  matching `docs/specs/reconciled-index.md` hash update in the same
  staged set. Ports `gates/spec_index.py`'s row-regex/hash-compare logic
  inline (no import — zero-install, no guaranteed `gates/` checkout at
  hook-invocation time in a consumer repo).
- `on-the-record/hooks/role-axis-completeness-guard.sh` (issue #650) —
  denies a commit whose staged+working-tree `roles/*.json` set has an
  axis owned by zero or by more than one role. Imports
  `gates/role_spec_shape.py` (tries `on-the-record/gates` then top-level
  `gates` as candidate dirs — the packaged copy can lag).

Both are wired in `on-the-record/hooks/hooks.json`'s `PreToolUse`+`Bash`
matcher array, each with a sibling test file in `on-the-record/hooks/`
named after the hook with underscores (e.g. `spec-index-preflight.sh` ->
`test_spec_index_preflight.py`). This is the established, repo-native
pattern for "catch a registration/completeness gap at landing time
without CI" — the write set for a new guard mirrors it exactly: one new
hook script, one new sibling test file, one new wiring line in
`hooks.json`, one new row each in `docs/specs/enforcement-boundary.md`
and `docs/specs/generated-paths.md` for the guard itself (both
`n/a`/`contract` respectively, since it only reads and denies, same as
its two siblings), and the mandatory `docs/specs/reconciled-index.md`
regen (`python3 gates/spec_index.py --update`) that any `docs/specs/*`
edit requires.

## #744 relationship

derived: `gh issue view 744 --json title,body,state`

#744 ("게이트 잡음 3종") is OPEN, scoped to exactly three named noise
sources: (1) `docs/specs/reconciled-index.md` companion-regen requirement
stated nowhere at write time, (2) `record-claim-guard`'s backtick-path
refusal firing on paths a proposal will create later, (3) `reports/hunt-*.md`
role-ownership routing. None of the three names
`docs/specs/enforcement-boundary.md`, `docs/specs/generated-paths.md`, or
any git-commit-time registration guard. #744's own acceptance criterion
explicitly requires legitimate denials to keep denying
("정당한 거부는 계속 거부된다... 각 게이트의 기존 레드 케이스가 그대로
실패로 남는지 회귀 테스트로 확인") — a guard that denies a commit for a
*genuinely* unregistered gate module is a legitimate denial by
construction (that is what #441/#684 exist to catch), not the kind of
noise #744 is scoped to remove. No mechanism overlap found; recorded as a
proposal Rationale item rather than merging the two issues.

Note on this survey's own drafting: an early draft of this file backtick-
quoted several existing paths with a trailing `:<line>`/`:<line-range>`
or `::<test-node-id>` suffix, and two not-yet-created future file paths —
`record-claim-guard.sh`'s write-time shape check (issue #330) correctly
refused all of them as unresolved references. Fixed by dropping the line/
node suffix from backtick-quoted real paths and stating not-yet-created
paths in prose without backticks, matching #744's item 2 (a real,
legitimate denial from the same gate #744 investigates for false
positives on genuinely-future paths).

## Write set this survey found (feeds the proposal)

- `docs/specs/enforcement-boundary.md` — 2 new rows
- `docs/specs/generated-paths.md` — 2 new rows
- `docs/specs/reconciled-index.md` — regen (mandatory companion)
- `tests/test_gates.py` — add missing `_pr_index_all` mock
- a new `on-the-record/hooks/*.sh` guard script (name to be finalized in
  the proposal)
- a new sibling `on-the-record/hooks/test_*.py` for that guard
- `on-the-record/hooks/hooks.json` — wire the new hook
- the phase-2 implementation record under `docs/issue-759/reports/`
  (docs/, always writable)

No new dependency, no new env var, no migration, no `.env.example` change.
