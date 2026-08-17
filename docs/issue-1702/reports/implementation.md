---
code_under_review:
  - gates/closure_sweep.py
  - gates/test_closure_sweep.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

Subject: issue-1702

## What was done

canonical: gates/closure_sweep.py:189-234 (`_pr_index_all`, read in this
session)
`_pr_index_all` pages through `gh api repos/{slug}/pulls --method GET -f
state=all -F per_page=100 -F page=N` instead of a single `gh pr list
--limit 1000` call. `owner/repo` is resolved via `spawn._repo_slug(root)`.

canonical: gates/closure_sweep.py:224-231 (state-mapping block, read in
this session)
Per that block, REST fields map to the existing vocabulary as: MERGED
when merged_at is set, else state.upper().

canonical: gates/closure_sweep.py:206-209 (loop stop conditions, read in
this session)
Per those lines, paging stops on a short page or when the running total
reaches _PR_INDEX_SAFETY_CEILING = 5000 (50 pages), returning (None,
True). ok=False on any gh call failure, unparseable JSON, non-list
response, or unresolvable slug.

canonical: gates/test_closure_sweep.py:199-322 (`PrIndexAllPagination`
class, written in this session)
That class covers: a >1000-PR mocked fixture (1250 entries across 13
pages) asserting multiple page calls and the full entry count, a
single-page case, a merged_at mapping case, an
exact-safety-ceiling-saturation case, a gh call-failure case, and an
unresolvable-slug case.

canonical: gates/test_closure_sweep.py:99-126
(`test_sweep_gh_call_count_is_constant_in_board_size`, edited in this
session)
That test was updated to route through the new gh api .../pulls call
shape instead of the retired gh pr list call.

derived:
```
$ python3 -m pytest -q gates/test_closure_sweep.py
...........................                                              [100%]
27 passed in 1.18s
```

acceptance: `python3 gates/closure_sweep.py --repo .` — result:
```
$ python3 gates/closure_sweep.py --repo .
종결 일관성 스윕: 위반 없음
$ echo $?
0
$ grep -c "확인 불가" /tmp/sweep-output.txt
0
```
canonical: /tmp/sweep-output.txt (this session's own live run of
`python3 gates/closure_sweep.py --repo .`, transcribed above) — 0
"확인 불가 (gh 실패)" lines in the output.

## Why

canonical: docs/issue-1702/proposals/pr-index-pagination.md (read in
this session)
Per that proposal's Request section: this repo grew beyond 1000 PRs, and
_pr_index_all's single gh pr list --limit 1000 call always hit that
ceiling, degrading the bulk index into per-item skips for every
subject/role.

acceptance: `python3 gates/closure_sweep.py --repo .` — result:
"종결 일관성 스윕: 위반 없음", exit 0, 0 skip lines (see above) — live
evidence that pagination resolves the degradation for this repo's
current PR count.

## Upstream

canonical: docs/issue-1702/proposals/pr-index-pagination.md (read in
this session)
That file is the basis for this delivery; it landed via PR #1704,
commit 8cbfe87c.

## What did not work

None.

## Open findings

None.
