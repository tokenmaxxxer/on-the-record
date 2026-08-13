skip-condition: spec leaves no design decision open — issue #1177 itself
states `validity-consult-skip: trivial — process-gap fix with a clear
mechanical check, no open design decision`, and the enforcement mechanism
(a PreToolUse hook on `gh pr create/edit`) is fully prescribed by the
issue's own Requirements section. Scout sweep skipped per this condition.

## Write set surveyed

- `on-the-record/hooks/pr-preflight.sh` — the existing PreToolUse hook on
  `gh pr create`/`gh pr edit` (issue #459). It already: parses the current
  branch into `issue`/`role`, fetches `gh issue view <n> --json comments`
  to determine phase, and denies (exit 2) with a `deny(msg, hint)` helper
  before the PR is created. Extending this file (rather than a new
  sibling hook) reuses its already-fetched `comments`/`issue`/`role`/
  branch-parse instead of re-deriving them, and keeps one hook owning
  "things that block `gh pr create`" — matching the file's own header
  precedent (contract-guard.sh is the other deny-before-effect hook, kept
  separate because it gates a *different* verb, `gh pr merge`).
- `on-the-record/hooks/test_pr_preflight.py` — the hook's existing test
  file, end-to-end `test_hook_*` cases drive the real script via
  subprocess with a stubbed `gh`. New cases follow that exact pattern.
- `spawn.py` (read-only, not modified): "directive-load time" lives at
  `_append_event(events_path, "session-start", {"pid": ..., "ts":
  time.time()})`, written to `_events_path(work)` = `Path(str(work) +
  ".events.jsonl")` — a sibling file next to the session's worktree
  directory, not inside it.
  canonical: spawn.py:6059-6061 (`_append_event` call site) and
  spawn.py:3104-3105 (`_events_path`)/spawn.py:2930 (`EVENTS_SUFFIX =
  ".events.jsonl"`), read this session.
- Record path convention (read-only): `docs/issue-<n>/reports/<role>.md`.
  canonical: `ls docs/issue-1160/reports` (this session) shows
  `implementation.md` and `execution-observation.md` as sibling files
  named after their role, matching branches `issue-1160/implementation`
  and `issue-1160/execution-observation`.

## What the field already does (no scout needed, but noted for continuity)

`pr-preflight.sh`'s existing phase-determination block already fetches
`gh issue view <n> --json comments -q .comments` and iterates each
comment's `body`/`author`/`createdAt` (canonical: on-the-record/hooks/
pr-preflight.sh lines ~130-140, `comments = gh_json("issue", "view",
str(issue), "--json", "comments", "-q", ".comments")`, read this
session) — the amendments check can reuse that same `comments` list
instead of issuing a second `gh` call.

`gh issue view --json comments` returns each comment object carrying
`createdAt` (ISO-8601) and `url` (ending `#issuecomment-<numeric id>`),
but no bare numeric `id` field (only a GraphQL node id) — so citation
uses the numeric id parsed from `url`, the same id GitHub's own UI and
permalinks use.
canonical: `gh issue view 1177 --json comments -q '.comments'`, run this
session — returned one comment object with `"url":
"https://github.com/tokenmaxxxer/on-the-record/issues/1177#issuecomment-5276062763"`
and `"createdAt":"2026-08-13T04:43:51Z"`, no `id` field of that shape.
