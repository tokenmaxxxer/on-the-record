# devrel — deviation log (issue #1174)

canonical: this session's own `gh pr create` tool-call history this
turn (5 consecutive refusals, each citing a newly-arrived issue
comment) and docs/issue-1174/reports/issue-retrospective/deviation-log.md
(read this turn), which documents the identical `pr-preflight.sh`
comment-race on a sibling role's branch (commit 005e2c6).

- 2026-08-13T14:52:00Z | filed | `pr-preflight.sh`'s comment-race
  recurred across this branch's `gh pr create` attempts: 6 new issue
  comments (issuecomment-5277587585, -5277592017, -5277597622,
  -5277602100, -5277606613) arrived across consecutive `gh pr create`
  attempts, each requiring an `amendments-reconciled` line before the
  next retry, and a new comment kept landing before each retry could
  clear the check — the same structural collision as the precedent
  cited above. Stopping retries after this turn's budget per that
  identical precedent; commits through ff91dbc are pushed to
  `issue-1174/devrel` for on-the-record's outside relay to open the
  PR. reported, not spawned.
