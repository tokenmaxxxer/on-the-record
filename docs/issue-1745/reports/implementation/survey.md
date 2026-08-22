---
subject: issue-1745
role: implementation
kind: survey
---

# Survey: fast-tier 2 pre-existing failures

## Scope confirmed

After #1969's repair (PR #1971), the fast tier is green everywhere
except two tests (file `tests/test_gh_quota_guard.py`, function
`test_sweep_call_budget`; file `tests/test_spawn.py`, class
`PollHeartbeatMarkerRelocationTest`, method
`test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`).

Reproduced live this session:

canonical: `python3 -m pytest -q tests/test_gh_quota_guard.py::test_sweep_call_budget -x` (executed this session)
```
AssertionError: 407 gh calls for 400 subjects: [['gh', 'api', 'rate_limit'],
['gh', 'repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner'],
['gh', 'api', 'rate_limit'], ['gh', 'issue', 'list', ...],
['gh', 'pr', 'list', '--head', 'issue-0/implementation', '--state', 'all', ...],
['gh', 'pr', 'list', '--head', 'issue-1/implementation', ...], ...]
```

canonical: `python3 -m pytest -q "tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts" -x` (executed this session)
```
AssertionError: 1 != 0
Captured stdout: [watchdog] closure-sweep: 확인 불가 (gh 실패) 3건
```

## Root cause (traced, not the issue-comment's literal framing)

The 2026-08-22 issue comment attributes the failure to
`_board_wide_sweep` issuing one `gh pr list --head issue-N/<role>` call
per subject. That call site exists (`spawn._pr_open_or_merged_for_branch`,
canonical: spawn.py:789-807 (read this session)), but it is a
**deliberate fallback**, not the normal path:

- `gates/closure_sweep.py` function `find_violations()` (canonical:
  gates/closure_sweep.py:318-345, read this session) already prefetches
  a bulk PR index via `_pr_index_all()` (canonical:
  gates/closure_sweep.py:163-230, read this session — since issue #1702
  it calls `gh api repos/{slug}/pulls` with pagination, not `gh pr
  list`) and joins it locally per subject — O(1) gh calls regardless of
  subject count.
- `gates/spawn_on_pr.py` function `missing_verification()` (canonical:
  gates/spawn_on_pr.py:151-209, read this session) does the same: it
  calls `closure_sweep._pr_index_all()` once and, only **if that index
  comes back `None`**, falls back to
  `spawn._pr_open_or_merged_for_branch()` per subject via
  `_pr_number_for_branch()` (canonical: gates/spawn_on_pr.py:75-87, read
  this session).

`_pr_index_all` starts with `slug = spawn._repo_slug(root); if not
slug: return None, False` (canonical: gates/closure_sweep.py:195-197,
read this session). `_repo_slug` (canonical: spawn.py:734-757, read
this session) runs `gh repo view --json nameWithOwner -q
.nameWithOwner` and caches `None` if the call fails OR returns empty
stdout.

Both failing tests' `subprocess.run` stubs answer only three command
shapes — `gh api rate_limit`, `gh issue list`, `gh pr list` (canonical:
tests/test_gh_quota_guard.py:33-41 `_fake_run_factory`, and
tests/test_spawn.py:4731-4737 the `fake_run` closure inside
`PollHeartbeatMarkerRelocationTest`, both read this session) — and fall
through to a bare `mock.Mock(returncode=0, stdout="")` for everything
else, including `gh repo view` and `gh api repos/.../pulls`. That
empty-stdout stub makes `_repo_slug` return `None`, which makes
`_pr_index_all` return `(None, False)` immediately (never even reaching
the `gh api .../pulls` call), which makes both call sites take their
intentional O(N) fallback path. The tests are not exercising "sweep
resolves via bulk index" as they intend to — they are exercising "sweep
falls back to per-subject queries because the repo slug can't be
resolved," an unrealistic scenario for these fixtures. In a real
checkout `gh repo view` succeeds, `_repo_slug` caches a real slug, and
the bulk-index path is what actually runs.

This reclassifies the fix: it is a **test-fixture bug** (stubs don't
simulate a resolvable repo), not a production O(N) regression. No
production code path needs to change.

## Write-set candidates

- `tests/test_gh_quota_guard.py` — `_fake_run_factory` (canonical:
  tests/test_gh_quota_guard.py:28-43, read this session) is shared
  across the file's test functions (derived: `grep -c '^def test_' tests/test_gh_quota_guard.py`).
  Any edit to `_fake_run_factory` must not perturb the other tests'
  call-shape assertions — `test_graphql_free_watchdog_reads` in
  particular iterates every recorded call and asserts none is a
  GraphQL-backed subcommand; adding stub branches is safe as long as
  the stubbed commands are themselves REST, which `gh repo view --json
  ...` and `gh api repos/.../pulls` both are.
- `tests/test_spawn.py`, class `PollHeartbeatMarkerRelocationTest`,
  method
  `test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`
  — local `fake_run` closure (canonical: tests/test_spawn.py:4731-4737,
  read this session), used only by this one test.

## #1959 collision check

Issue #1959 is an in-flight split of `tests/test_spawn.py` into smaller
files. canonical: `git log --oneline -5 -- tests/test_spawn.py` (executed
this session) shows no commit moving `PollHeartbeatMarkerRelocationTest`
out of `tests/test_spawn.py` yet, and canonical: Read
`tests/test_spawn.py` (this session) confirms the class is still defined
there today. The proposal below plans explicitly for the class having
moved by phase 2 (locate by class/method name via grep across `tests/`
at phase-2 time, not by a path hardcoded now).

## Skip-condition note

This is a pure bugfix (test-stub gap, not a design decision) — the
scout-directive skip condition applies. No exemplar/pattern scouting
was run.

## Acceptance-verification

checked: `python3 -m pytest -q -m "not slow"` — result: FAIL (current
main). canonical: the two failing-test pytest runs quoted above in
"Scope confirmed", both executed this session; both traced to the same
test-fixture root cause.
