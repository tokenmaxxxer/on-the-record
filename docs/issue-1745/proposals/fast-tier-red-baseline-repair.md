---
status: proposed
files:
  - tests/test_gh_quota_guard.py
  - tests/test_spawn.py
---

# Fast-tier red baseline repair: gh-call-count tests' stubs don't resolve a repo slug

## Request

Issue #1745 asks the fast tier
(`python3 -m pytest -q -m "not slow"`) to be green on main. Two tests
fail today: `tests/test_gh_quota_guard.py::test_sweep_call_budget` and
`tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`.
The issue's own comment frames this as `_board_wide_sweep` issuing one
`gh pr list --head issue-N/<role>` call per subject (407 calls for 400
subjects), and asks for a batched-query fix. This proposal also plans
around issue #1959's in-flight split of `tests/test_spawn.py`.

## Constraints

- Skip condition (scout-directive): this is a pure bugfix — no design
  decision is open. Confirmed by the survey
  (`docs/issue-1745/reports/implementation/survey.md`); no scout brief
  was written.
- Must not touch production code paths the fast tier's other passing
  tests already pin (`test_graphql_free_watchdog_reads`,
  `test_bulk_loop_skipped_below_floor`, `test_sweep_backoff_on_rate_limit`,
  `test_recheck_backoff` in the same file; the other
  `PollHeartbeatMarkerRelocationTest` methods and the rest of
  `tests/test_spawn.py`).
- Must not weaken what either test actually verifies: `test_sweep_call_budget`
  must still assert an O(1)-ish gh-call ceiling for 400 subjects;
  `test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`
  must still assert `_issue_view` call count stays constant as subject
  count grows.
- Must plan around issue #1959 (`tests/test_spawn.py` split in flight):
  by phase 2, `PollHeartbeatMarkerRelocationTest` may live in a
  different file.

## Rationale

The survey traced the failure to a **test-fixture gap**, not a
production regression: `_pr_index_all()` (the bulk PR-index path
`find_violations()` and `missing_verification()` both use) starts by
resolving the repo slug via `gh repo view`. Both tests' `subprocess.run`
stubs answer `gh repo view` with the catch-all
`mock.Mock(returncode=0, stdout="")`, which makes `_repo_slug()` cache
`None`, which makes `_pr_index_all()` short-circuit to `(None, False)`
before ever attempting `gh api repos/.../pulls`. Both call sites then
correctly take their designed O(N) fallback (`_pr_open_or_merged_for_branch`
per branch, `_issue_view` per issue) — the fallback exists specifically
so a `gh` failure degrades to slow-but-correct instead of silently
wrong. The tests were not asserting "the bulk path holds up"; they were
accidentally asserting "the fallback path fires," which is the opposite
of what their names and comments say they check.

**Alternative considered and rejected: batch the sweep's `gh pr list`
calls in production code** (the issue comment's literal ask — e.g.
replace the fallback loop with one `gh pr list --state all --json
headRefName,...` call, filtered locally). Rejected because the survey
found the O(N) fallback loop is not actually reachable in a working
checkout — it only fires when the bulk index itself failed to resolve,
at which point a repo-wide bulk query would likely fail for the same
underlying reason (auth/repo-detection failure) and a "batched" call
would not help; more importantly, `gates/closure_sweep.py`'s
`_pr_index_all()` already **is** that batched query (added by issue
#1702), and `gates/spawn_on_pr.py` already routes through it in the
normal case. Adding a second, redundant batching layer in the fallback
path would change working production behavior to fix a test-only
symptom, is out of the frozen write set the survey identified, and adds
code the survey found no evidence is exercised outside test fixtures
that fail to stub a resolvable repo.

**Alternative considered and rejected: mock `spawn._repo_slug`
directly** instead of stubbing the underlying `gh repo view` call.
Rejected because it would bypass the caching/failure-handling logic in
`_repo_slug()` itself, meaning the test would no longer exercise the
real code path from `subprocess.run` through to the bulk index — a
regression in an already-failing gh call would go undetected again.
Stubbing at the `subprocess.run` layer (consistent with how every other
call in these fixtures is already stubbed) keeps the whole chain real.

## What will be done

1. In `tests/test_gh_quota_guard.py`, extend `_fake_run_factory` (lines
   28-43) with two more matched command shapes, added before the
   existing catch-all:
   - `cmd[:3] == ["gh", "repo", "view"]` → return a fake
     `nameWithOwner` (e.g. `stdout="owner/repo\n"`), so `_repo_slug()`
     resolves.
   - `cmd[:2] == ["gh", "api"]` and `"pulls"` in the request path
     (i.e. `cmd[3]` starts with `repos/` and ends with `/pulls`) →
     return `stdout="[]"`, so `_pr_index_all()` gets an empty-but-valid
     page and stops paginating (`len(data) < per_page` breaks the
     loop).
   These are both REST calls, so `test_graphql_free_watchdog_reads`'s
   "no GraphQL-backed subcommand" assertion is unaffected — the new
   stub responses do not add any `gh issue view`/`gh pr view`/`gh pr
   merge` calls.
2. In `tests/test_spawn.py`'s `PollHeartbeatMarkerRelocationTest.test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`
   (currently ~line 4713-4765; locate by class+method name at phase-2
   time via grep, in case #1959 has moved the file by then), extend the
   local `fake_run` closure the same way: add `gh repo view` and `gh
   api .../pulls` branches ahead of the generic
   `mock.Mock(returncode=0, stdout="")` fallback, so `_repo_slug()` and
   `_pr_index_all()` resolve instead of short-circuiting.
3. Re-run `python3 -m pytest -q -m "not slow"` and confirm 0 failures;
   also re-run the full `tests/test_gh_quota_guard.py` file and the
   full `PollHeartbeatMarkerRelocationTest` class in isolation to
   confirm no other test in either file regresses from the stub
   change.
4. If #1959 has moved `PollHeartbeatMarkerRelocationTest` to a new file
   by phase-2 time, apply step 2's edit to wherever the class now
   lives instead of `tests/test_spawn.py`, and record that path
   deviation in the phase-2 report per the record-shape directive.

## Out of scope

- Any change to `spawn.py`, `gates/closure_sweep.py`, or
  `gates/spawn_on_pr.py` production code — the survey found no
  production-path defect.
- Any change to the sweep's real-world gh-call budget or batching
  strategy — `_pr_index_all()` already batches via `gh api
  repos/.../pulls` pagination (issue #1702); this issue does not ask
  for a second batching mechanism.
- Fixing `tests/test_spawn.py`'s other xfail-marked or unrelated tests.
- Doing the `tests/test_spawn.py` split itself — that is issue #1959's
  scope, not this issue's.

## Accumulation

Both edited fixtures are inline `subprocess.run` stub closures, not a
shared test-helper module — a pattern this repo's test suite already
repeats per-file rather than centralizing (`_fake_run_factory` in
`tests/test_gh_quota_guard.py` vs. the local `fake_run` closure in
`tests/test_spawn.py` are two independent implementations of the same
"answer these three gh shapes" idea). This proposal adds the same two
new branches (`gh repo view`, `gh api .../pulls`) to both, rather than
extracting a shared stub helper, because: (a) the write set is frozen
at exactly these two tests per the scout-directive bugfix skip
condition, and introducing a new shared test-helper module is a design
decision outside that scope; (b) if a third fast-tier test needs the
same `gh`-shape stubbing in the future, that is the trigger to extract
a shared helper (e.g. `tests/_gh_stub.py`) — this proposal does not
pre-build one for a case that has not occurred a third time. No
`roles/*.json`-style repeated-file accumulation is involved; the write
set is two fixed test files, not a growing list.

## How you'll know it worked

- `python3 -m pytest -q -m "not slow"` exits 0 (the issue's stated
  acceptance check), run against a clean `main`-based branch after this
  change lands.
- `python3 -m pytest -q tests/test_gh_quota_guard.py` — all 5 tests
  pass, `test_sweep_call_budget` in particular now exercises the bulk
  `_pr_index_all()` path (assertable by checking the recorded call list
  no longer contains any `gh pr list --head issue-N/...` entries).
- `python3 -m pytest -q -k PollHeartbeatMarkerRelocationTest` (or the
  equivalent target if #1959 relocated the class) — all pass, with
  `test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`
  asserting `result == 0` (no "확인 불가 (gh 실패)" skip) alongside its
  existing constant-call-count assertion.
