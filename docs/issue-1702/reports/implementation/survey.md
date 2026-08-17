# Current-state survey — issue #1702

## Write set

- `gates/closure_sweep.py` — `_pr_index_all` (lines ~159-202) and its docstring.
- `gates/test_closure_sweep.py` — add pagination-fixture unit tests; existing tests
  (lines 62-192) stub `closure_sweep._pr_index_all` wholesale via monkeypatch, so
  they are unaffected by an internal rewrite of the function body.

## What exists today

canonical: gates/closure_sweep.py:159-202 (read directly)
`_pr_index_all` issues one
`gh pr list --state all --json number,headRefName,state,body --limit 1000`
subprocess call.

canonical: gates/closure_sweep.py:181-183 (read directly)
`gh pr list --json ... --state` returns GraphQL-flavored
state strings directly: `"OPEN" | "CLOSED" | "MERGED"` (uppercase) — this is
the shape `classify()` and the skip-reason branch depend on.

canonical: gates/closure_sweep.py:345-361 (read directly)
The call site reads `pr_state == "MERGED"`, `entry["state"]`, `entry["body"]`
off the index this function returns.

canonical: gates/closure_sweep.py:193-194 (read directly)
`len(data) >= _PR_INDEX_LIMIT` (1000) is read as "possibly truncated" and the
function deliberately returns `(None, True)` so callers fall back to
per-subject skips rather than silently dropping PRs (`gh pr list`'s CLI
`--limit` flag has no accompanying cursor/page flag exposed to the caller —
you cannot ask it "give me items 1000-2000", so a fixed `--limit` call
structurally cannot express "keep going past N").

canonical: `gh issue view 1702` (executed live this session)
Issue #1702 confirms this is live: repo has 1701 PRs, every `_pr_index_all`
call now saturates at 1000, and closure-sweep reports ~484 subject/role rows
"확인 불가 (gh 실패)" per tick (as stated in the issue body).

## What already solves a sibling problem in this file

canonical: gates/closure_sweep.py:208-266 (read directly)
`issue_state_index_all` hit the identical shape for issues and already
resolved the *fixed-endpoint* half of it via `_conditional_issue_list`'s
ETag ≤100-item ✕ ceiling. It does not paginate a >1000-item board either —
it falls through to a second unconditional
`gh issue list --limit _ISSUE_INDEX_LIMIT` call and still saturates the same
way past that ceiling. Not a template for pagination, only a precedent for
the `(index, ok)` / truncation-safe return shape this function must keep.

## The real constraint: no page cursor on `gh pr list`

`gh pr list --json ... --limit N` is a *single* CLI invocation; the GitHub
CLI internally issues as many paged GraphQL requests as needed to satisfy
`--limit`, but this happens inside gh's own process and is invisible to (and
therefore unmockable by) a Python-level `subprocess.run` mock. A unit test
asserting "multiple page calls" (per the issue's acceptance criterion) must
observe multiple our-side subprocess invocations — which `gh pr list` alone
cannot produce no matter how `--limit` is raised.

`gh api repos/{slug}/pulls?state=all&per_page=100&page=N` (plain REST, not
GraphQL) *does* expose page-at-a-time control to the caller: each `page=N`
value is one subprocess call, so a page-walk loop calling this repeatedly is
both real pagination and unit-testable via a subprocess mock keyed on the
`page` argument.

canonical: GitHub REST API docs for `GET /repos/{owner}/{repo}/pulls` (prior knowledge, not read this session)
REST `pulls` list fields differ from `gh pr list --json`'s GraphQL fields:
`head.ref` (nested) instead of `headRefName`.

canonical: GitHub REST API docs for `GET /repos/{owner}/{repo}/pulls` (prior knowledge, not read this session)
`state` is lowercase `"open"/"closed"` with a separate `merged_at` timestamp
instead of a tri-state `"OPEN"/"CLOSED"/"MERGED"` string.

canonical: gates/closure_sweep.py:360-370 (read directly)
The field mapping has to reconstruct the same `"OPEN"/"CLOSED"/"MERGED"`
shape `classify()` already depends on: `merged_at` present → `"MERGED"`;
else `state.upper()`.

canonical: spawn.py:1152, gates/closure_sweep.py:21,232 (read directly)
`spawn._repo_slug(root)` resolves `owner/repo` for the REST path and is
already imported into this file and used by `issue_state_index_all`.

## Alternative considered

Simply raising `_PR_INDEX_LIMIT` past 1701 (e.g. to 5000) and keeping the
existing single `gh pr list --limit N` call. This is a real 2-line fix and
gh CLI's internal paging would in fact fetch >1000 PRs correctly in
production. Rejected because it fails the issue's own acceptance criterion
("pagination fixture asserts multiple page calls") — a single subprocess
call cannot be asserted as having made "multiple page calls" under a mocked
`subprocess.run`, since gh's internal multi-request behavior is opaque to
any Python-level mock. It also leaves saturation handling structurally
identical (still one hard ceiling, still an opaque cutoff) rather than
giving the caller genuine page-by-page control.
