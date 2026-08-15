---
code_under_review:
  - gates/closure_sweep.py
  - gates/test_closure_sweep.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

issue #1613 reported that `closure_sweep` permanently skips subjects
per tick on `tokenmaxxxer-core` with reason `gh 실패`, and hypothesized
(explicitly "verify, don't trust") that cross-repo subject numbers were
being queried against the wrong repo.

canonical: gates/closure_sweep.py:275-276, read directly (spawn.board() call site inside find_violations)
`spawn.board()` (spawn.py:1579-1600, read directly) only ever enumerates
local `docs/issue-<n>/` directories inside the target repo's own
working tree — no cross-repo lookup path exists there.

canonical: gates/closure_sweep.py:95-98, read directly before the fix
```
    cmd = ["gh", "api", f"repos/{slug}/issues", "-f", "state=all",
           "-f", "per_page=100", "-i"]
    if etag:
        cmd = cmd + ["-H", f"If-None-Match: {etag}"]
```
That command omitted `--method GET`. `gh api` defaults to POST whenever
any `-f`/`-F` flag is present unless `--method` is stated explicitly.

derived:
```
$ cd /home/jwjung/tokenmaxxxer-core && gh api repos/tokenmaxxxer/tokenmaxxxer-core/issues -f state=all -f per_page=100 2>&1 | tail -2
{"message":"Invalid request.\n\n\"title\" wasn't supplied.","documentation_url":"https://docs.github.com/rest/issues/issues#create-an-issue","status":"422"}
gh: Invalid request.
```
That reproduces the bug: the call was silently sent as POST and
rejected. `issue_state_index_all` returned `(None, False)` every time
as a result, which made `find_violations` mark every subject on the
board (not just cross-repo-numbered ones) as a `gh-issue-list-failed`
skip.

derived:
```
$ cd /home/jwjung/tokenmaxxxer-core && gh api repos/tokenmaxxxer/tokenmaxxxer-core/issues -f state=all -f per_page=100 --method GET 2>&1 | head -1
HTTP/2.0 200 OK
```

Fix applied: added `--method GET` to that command in
`gates/closure_sweep.py:95`. Separately verified (and pinned with a
test) that `find_violations` already skips silently, with no `gh 실패`
reason, past a subject whose issue number is absent from a
successfully-fetched index.

## Why

reason: the issue's own "Suspected shape" section asked to verify, not
trust, its hypothesis; the reproduction above shows the actual root
cause is the `gh api` POST/GET default, not a cross-repo lookup that
does not exist in the code.

## Upstream

basis: issue #1613 (issue body), verified against gates/closure_sweep.py and spawn.py `board()`.

## What did not work

- Initially planned to implement cross-repo subject resolution / an
  out-of-scope classification path, per the issue's suspected shape.
  canonical: spawn.py:1579-1600, read directly — abandoned once this
  confirmed `board()` has no cross-repo subject path at all, before
  writing any such code.

## Rationale for deviations

The issue's hypothesis (cross-repo subject queried as a local issue)
did not hold under verification — canonical: spawn.py:1579-1600, read
directly, board() enumerates only the target repo's own
`docs/issue-<n>/` tree. The actual defect (missing `--method GET`,
reproduced above) produces the identical observable symptom and is what
was fixed instead, in the same file the issue named. Acceptance checks
2 and 3 (live 0-skip ticks, byte-identical empty state) are satisfied
by this fix; check 1 (a subject not in a resolved index isn't reported
`gh 실패`) was already true of the existing code and is now pinned by a
regression test, since no cross-repo subject path exists to add
out-of-scope classification to.

## Verification performed

derived:
```
$ python3 -m pytest gates/test_closure_sweep.py -q
19 passed in 5.92s
```
canonical: python3 -m pytest gates/test_closure_sweep.py -q — result: 19 passed
Covers the unit-test acceptance check via
`OutOfIndexSubjectIsNotAGhFailureSkip` and
`ConditionalIssueListUsesExplicitGetMethod` in gates/test_closure_sweep.py.

derived:
```
$ for i in 1 2 3; do python3 gates/closure_sweep.py --repo /home/jwjung/tokenmaxxxer-core 2>&1; echo "---"; done
종결 일관성 스윕: 위반 발견
issue #189 / PR #194: merged-delivery-issue-open
issue #222 / PR #224: merged-delivery-issue-open
---
종결 일관성 스윕: 위반 발견
issue #189 / PR #194: merged-delivery-issue-open
issue #222 / PR #224: merged-delivery-issue-open
---
종결 일관성 스윕: 위반 발견
issue #189 / PR #194: merged-delivery-issue-open
issue #222 / PR #224: merged-delivery-issue-open
---
```
canonical: python3 gates/closure_sweep.py --repo /home/jwjung/tokenmaxxxer-core (run 3 times) — result: 위반 발견 x3, 확인 불가/gh 실패 x0
Live acceptance check: three consecutive ticks, each resolves to a real
verdict (pre-existing violations unrelated to this fix), none prints
`확인 불가`/`gh 실패`.

derived:
```
$ python3 gates/closure_sweep.py --repo /tmp/empty-board-test; echo "exit=$?"
종결 일관성 스윕: 위반 없음
exit=0
```
canonical: python3 gates/closure_sweep.py --repo /tmp/empty-board-test — result: 위반 없음, exit=0
`/tmp/empty-board-test` is a fresh `git init`'d repo with no
`docs/issue-*/` tree — matches pre-fix behavior for an empty board (the
fix only changes the `gh api` invocation used once a board is
non-empty).

## Open findings

None.

## Closed checks (warrant hunt)

closed_checks:
- name: gh-api-method-default-audit
  code_sha: (working tree at record-write time; branch issue-1613/implementation)
  note: >
    canonical: spawn.py:1368-1375, read directly (same `-f`-without-
    `--method-GET` shape in an issue-comments ETag probe).
    derived: `cd /home/jwjung/tokenmaxxxer-core && gh api
    repos/tokenmaxxxer/tokenmaxxxer-core/issues/1/comments -f
    per_page=100 -i` returns HTTP 422, same failure mode. Left
    untouched — outside `gates/closure_sweep.py` and `spawn.board()`,
    the write set this issue named (SCOPE-EXCEEDED RULE); worth a
    follow-up issue.
