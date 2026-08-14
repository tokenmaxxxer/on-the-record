# issue-1199 capacity-planning deviation log

- 2026-08-13T07:47:30Z | filed | pr-preflight.sh's amendments-reconciled
  check races new issue comments faster than `gh pr create` can finish —
  the same structural pr-preflight comment-race pattern already logged
  by other roles on this issue (e.g. issue-1174's issue-retrospective
  role, `docs/issue-1174/reports/issue-retrospective/deviation-log.md`,
  commits b00156d/005e2c6). Two automated "Judgment opened ... branch
  `issue-1199/capacity-planning`" delegated-judgment comments
  (issuecomment-5277534838, issuecomment-5277538833) arrived across
  consecutive `gh pr create` attempts; the first was reconciled into the
  record in turn (commit 5339bb9). Stopping retries after this turn's
  budget per the identical precedent — commits through 5339bb9 are
  pushed to issue-1199/capacity-planning for on-the-record's outside
  relay to open the PR. reported, not spawned.

- 2026-08-14T00:00:00Z | filed | `gh pr create --repo
  tokenmaxxxer/capacity-planning-rulebook` was refused by this working
  tree's own `upstream-defect-scope-guard.sh` hook ("the upstream
  defect channel files issues only, never PRs" — issue #1131 req#4),
  discovered while trying to open the PR for the 2026-08-14 tool-
  landscape rework commit (95dc4b6). Also discovered: the prior unit's
  record claimed an "External PR #23" that was never actually opened
  (`gh pr list --repo tokenmaxxxer/capacity-planning-rulebook --state
  all --search "1199"` returns empty) — the branch had been pushed but
  no PR existed, so that citation was stale/incorrect; corrected in
  this turn's record update. The rework commit is pushed to
  `issue-1199/capacity-planning` on `capacity-planning-rulebook`; PR
  creation there needs a session without this guard, or a human/
  orchestrator action outside this turn. reported, not spawned.
