---
status: proposed
files:
  - gates/closure_sweep.py
  - gates/test_closure_sweep.py
---

## Request

Repo has grown past 1701 PRs. `_pr_index_all` issues a single
`gh pr list --limit 1000` call; at ≥1000 entries it always treats the
result as possibly truncated and returns `(None, True)`, which makes every
subject/role in the sweep fall back to per-item skips ("확인 불가 (gh
실패)"). Paginate the index build so it stays complete as the repo grows,
keeping a hard safety ceiling beyond which the existing truncation-safe
`(None, True)` fallback still applies.

## Constraints

- Repos under 1000 PRs must behave exactly as today: one call, one page.
- The existing `(index, ok)` return contract and the "index is `None`
  only past a ceiling, `ok=False` only on a hard `gh` failure" semantics
  must not change — callers (`find_violations`) read both today.
- The returned index's `state` values must stay `"OPEN"/"CLOSED"/"MERGED"`
  (call sites compare `pr_state == "MERGED"` and pass it into `classify()`).
- No change to `spawn.py` (parallel #1697 session owns it).
- Unit tests must be able to assert "multiple page calls" against a mocked
  `gh` runner (per the issue's acceptance criterion).

## Rationale

Two approaches were on the table:

1. **Raise `_PR_INDEX_LIMIT` to a large ceiling (e.g. 5000) and keep the
   single `gh pr list --limit N` call.** `gh`'s CLI already internally
   issues multiple GraphQL requests to satisfy a large `--limit` in one
   subprocess invocation, so this would work in production. Rejected: a
   single subprocess call cannot be observed as "multiple page calls" by a
   Python-level `subprocess.run` mock, since gh's internal paging happens
   inside gh's own process, invisible to the mock. This fails the issue's
   own acceptance criterion outright, and leaves the saturation cutoff just
   as opaque as before (still one call, still one hard limit, no
   caller-visible page granularity).

2. **Walk `gh api repos/{slug}/pulls?state=all&per_page=100&page=N` page by
   page** (chosen). Each page is a real, separately-mockable subprocess
   call, so a pagination fixture can assert multiple invocations and a full
   entry count. Cost: REST `pulls` fields differ from `gh pr list --json`'s
   GraphQL fields (`head.ref` vs `headRefName`; lowercase `state` +
   `merged_at` vs a tri-state string) — the mapping step reconstructs
   `"MERGED"` from `merged_at` presence, else `state.upper()`, preserving
   the shape callers already depend on.

## What will be done

- Rewrite `_pr_index_all` (gates/closure_sweep.py:159-202) to:
  - Resolve `owner/repo` via `spawn._repo_slug(root)` (already imported,
    already used by `issue_state_index_all`); `ok=False` if it can't
    resolve.
  - Page through `gh api repos/{slug}/pulls -f state=all -F per_page=100
    -F page=N` starting at `page=1`, accumulating entries into the same
    `branch -> {number, state, body}` index shape as today (first entry per
    branch wins, unchanged semantics).
  - Map each page's REST-shaped items to the existing state vocabulary:
    `"MERGED"` if `merged_at` is set, else `state.upper()` (`"OPEN"` /
    `"CLOSED"`).
  - Stop paging when a page returns fewer than `per_page` items (natural
    end of data).
  - Stop and return `(None, True)` if the running total exceeds a hard
    safety ceiling (`_PR_INDEX_SAFETY_CEILING = 5000`, i.e. 50 pages) —
    same truncation-safe contract as today, just at a much higher bar.
  - `ok=False`, `index=None` on any `gh` call failure or unparseable JSON,
    same as today.
- Add unit tests in `gates/test_closure_sweep.py`: a mocked `gh` runner
  fixture returning >1000 synthetic PRs across multiple pages, asserting
  (a) multiple page-call invocations happened, (b) the returned index has
  the full entry count; and a ceiling-saturation case asserting `(None,
  True)` when the mocked total exceeds `_PR_INDEX_SAFETY_CEILING`.
- Run one live closure-sweep on this repo after the change lands and record
  its exact command + output in the delivery PR (per the issue's live
  acceptance check and the command-identity rule).

## Accumulation

This adds one more inline `subprocess.run(["gh", ...])` call site to
`gates/closure_sweep.py`, alongside the existing ones (`_pr_view_state_body`,
`issue_state_index_all`'s two call sites, `_conditional_issue_list`). It
does not add a new *pattern* — inline `gh`/subprocess calls are already the
established shape in this file (issue #419/#424 rejected a generic
duplicate-call detector as noise-prone) — it replaces one existing inline
call with a paging loop around the same shape. If this repo needs N more
`gh`-backed index builders in the future, each would still be one more
inline call site in this file; that is the accepted status quo here, not a
new accumulation this change introduces.

## Out of scope

- `spawn.py` and anything under #1697's ownership.
- `issue_state_index_all`'s own saturation behavior (sibling function,
  same shape, not touched by this issue).
- Any change to `find_violations`'s skip/fallback logic itself — only the
  index build underneath it changes.

## How you'll know it worked

- `python3 -m unittest gates.test_closure_sweep` passes, including the new
  pagination-fixture tests (multi-page call assertion + full entry count,
  and exact-ceiling-saturation still returning `(None, True)`).
- A live closure-sweep run on this repo reports 0 "확인 불가 (gh 실패)"
  skips attributable to the PR index, with the exact command and output
  recorded in the delivery PR.
- Repos under 1000 PRs still make exactly one `gh api ... page=1` call.
