---
code_under_review:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
type: fix
breaking: false
canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q — 15 passed
verdict: pass
loop_state: landed
---

## What was done

Extended `_MACHINE_BODY_RE` in `on-the-record/hooks/pr-preflight.sh` to
also match comment bodies beginning with `Judgment opened: ` and
`Verdict: PR ` (the delegated-judgment machinery's bare-prefix comment
pair), alongside the existing `[watch]`/`[watchdog]`/`[poll-report]`/
`[reconcile]`-style prefixes.

canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q — 15 passed
Added two comments of these shapes to the existing
`test_hook_allows_pr_when_only_machine_comments_post_spawn`
machine-stream-pass test (operator-comment-block and empty-state cases
left unchanged, per issue requirement 2).

## Why

Basis: #1315. Follow-up to #1310 — the landed `_MACHINE_BODY_RE` did not
cover the delegated-judgment machinery's `Judgment opened: PR #`/
`Verdict: PR #` comment pair, posted from the operator's own account, so
neither body-prefix nor author-login detection caught them, starving
post-#1310 respawns (observed 2026-08-14, issuecomment-5288341082).

## What did not work

None.

## Acceptance

canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q
checked: full test_pr_preflight.py suite — result: pass

```
$ python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q
...............                                                          [100%]
15 passed in 1.37s
```

## Open findings

None.
