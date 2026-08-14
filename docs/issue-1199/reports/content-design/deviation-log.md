# content-design deviation log (issue-1199)

- 2026-08-13T16:50:00Z | filed | after phase 2 opened via the
  "APPROVE issue-1199/content-design" comment, pr-preflight.sh's
  comment-race recurred repeatedly: 4 new issue comments
  (issuecomment-5277489599, -5277572544, -5277577397, -5277582073)
  arrived across consecutive `gh pr create` attempts, each reconciled
  in turn (commits 3790af4, 71c6055, b359282) except the last, which
  again named this unit's own branch mid-retry. Stopping retries after
  this turn's budget per the identical precedent already logged on
  issue-1174 (commit 005e2c6) and issue-1199/accessibility (commit
  a445a50) — this hook pair's collision is structural, not a one-off.
  Commits through b359282 are pushed to origin/issue-1199/content-design
  (canonical: `git log --oneline -5`, `git push` output, this session)
  for on-the-record's outside relay to open the PR. reported, not
  spawned.
