---
code_under_review:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
type: feature
breaking: false
canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q — result: 12 passed in 0.99s
verdict: pass
loop_state: landed
---

kind: implementation
subject: issue-1177
Proposal: docs/issue-1177/proposals/amendments-reconciled-preflight.md

## What was done

canonical: this branch, `git diff main -- on-the-record/hooks/pr-preflight.sh
on-the-record/hooks/test_pr_preflight.py` — built exactly the frozen write
set:

- `on-the-record/hooks/pr-preflight.sh` — added an amendments-reconciled
  check to the existing GUARD script, inserted right after phase
  determination (between the `phase = "phase2" if phase2 else "phase1"`
  line and the plan-parsing section). It reads the session's
  directive-load time as the last `session-start` event's `ts` from
  `<cwd>.events.jsonl` (the sibling events file spawn.py already writes
  — `_last_session_start_ts()`), finds the newest comment by `createdAt`
  from the `comments` list already fetched for phase determination, and
  — only when that newest comment postdates spawn — checks
  `docs/issue-<n>/reports/<role>.md` for a line containing both
  `amendments-reconciled` and the comment's numeric id (parsed from its
  `url`'s `#issuecomment-<digits>` suffix). Missing/unreconciled → `deny()`
  (exit 2, same helper the rest of the file uses). Every other branch
  (no events file, no session-start event, no comments, no comment newer
  than spawn) fails open, matching the file's existing fail-open
  convention.
- `on-the-record/hooks/test_pr_preflight.py` — 5 new `test_hook_*` cases:
  denies on an unreconciled post-spawn comment
  (`test_hook_denies_pr_when_post_spawn_comment_unreconciled`), allows
  once the record cites the comment id
  (`test_hook_allows_pr_when_post_spawn_comment_reconciled`), allows with
  a comment older than spawn
  (`test_hook_allows_pr_when_no_post_spawn_comments`), allows with no
  comments at all (`test_hook_allows_pr_when_no_comments_at_all`), and
  allows (fail-open) with no events file at all
  (`test_hook_allows_pr_when_no_events_file`) — plus a `_write_session_start()`
  helper that writes the sibling `<repo_dir>.events.jsonl` fixture the
  same way spawn.py does.

## Why

Per docs/issue-1177/proposals/amendments-reconciled-preflight.md's
Rationale: extending `pr-preflight.sh` (rather than a new sibling hook)
reuses the `comments` list it already fetches for phase determination
instead of a second `gh` round-trip per `gh pr create`/`edit`, and keeps
one file owning every "block `gh pr create`" rule. Directive-load time is
read from spawn.py's own `session-start` event (the actual moment the
session process started) rather than a proxy like record-file mtime or
branch first-commit time, neither of which reflects spawn time reliably.

## Upstream basis

Based on: docs/issue-1177/proposals/amendments-reconciled-preflight.md,
docs/issue-1177/reports/implementation/survey.md

## Acceptance

checked: fixture issue with a post-spawn comment blocks PR creation
until the record carries the amendments-reconciled citation; without
post-spawn comments, no block
canonical: `python3 -m pytest on-the-record/hooks/test_pr_preflight.py -v`
(this session), pasted below — result: 12 passed

```
test_hook_denies_pr_when_post_spawn_comment_unreconciled PASSED
test_hook_allows_pr_when_post_spawn_comment_reconciled PASSED
test_hook_allows_pr_when_no_post_spawn_comments PASSED
test_hook_allows_pr_when_no_comments_at_all PASSED
test_hook_allows_pr_when_no_events_file PASSED
12 passed in 0.99s
```

## What did not work

None.

## Open findings

None.
