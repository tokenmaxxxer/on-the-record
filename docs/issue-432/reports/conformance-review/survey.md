---
role: conformance-review
subject: issue-432
loop_state: surveying
---

# issue #432 conformance review — survey

canonical: docs/issue-432/reports/implementation.md (implementation
role's own record), git show daa2d27d --stat (merged diff, PR #433,
`issue-432/implementation` -> `main`)

Spec source and diff cited above ground every requirement below.

## Falsifiable requirements extracted

1. `spawn.py:1860` (`_post_stall_comment`) unpacks `_issue_comments`'s
   `(list[dict], ok: bool)` return shape instead of the stale
   `list[dict]`-only shape.
2. `spawn.py:1884` (`_post_stranded_push_comment`, the site named in the
   issue) likewise unpacks the tuple shape.
3. `ok=False` decision: both fixed sites post the comment anyway (accept a
   possible duplicate) rather than silently skip — gated as
   `ok and any(marker in c.get("body", "") for c in comments)`, matching
   `_post_crash_comment`'s pre-existing convention.
4. Exhaustive sweep: every `_issue_comments(` call site in the repo's
   `.py` files unpacks the tuple shape correctly (no other exposed
   old-shape site).
5. Regression tests pin the `ok=False` -> "post anyway" behavior for both
   fixed functions.
6. canonical: python3 -m pytest -q --ignore=gates (run live this session,
   see acceptance section of the review body)
   Full test suite passes on the current merged tree — not trusted from
   the implementation record's own printed count.
7. Scope 3 (#398/#290 cross-record) explicitly not resolved in this PR by
   design — no duplicated fix attempted here.
8. canonical: git show daa2d27d --stat
   Diff scope: only `spawn.py`, `test_spawn.py` (code) plus the record's
   own doc files change — no unrelated code file touched.

## Notes

- canonical: git show daa2d27d --stat
  Requirement 7 is a scope-boundary claim, not a behavior to verify in
  code; checked for diff-stat consistency only (no #398/#290-related
  file in the diff).
