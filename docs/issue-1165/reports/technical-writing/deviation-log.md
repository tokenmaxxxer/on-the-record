kind: deviation-log
subject: issue-1165

# issue-1165 deviation log (technical-writing)

- 2026-08-13T00:00:00Z | filed | `gh pr create` for this branch's phase-1
  proposal is refused unconditionally by
  `on-the-record/hooks/upstream-defect-scope-guard.sh` (canonical: read
  this turn), which denies every `gh pr create` shape repo-wide per
  issue #1131 req#4 ("consumers file issues only, never PRs" against
  upstream on-the-record). That guard's stated scope (a consumer
  repo's channel back to upstream on-the-record) does not obviously
  match this session's actual situation — a normal in-repo phase-1 PR
  required by role-handoff contract v3 s19 inside the on-the-record
  repo itself — but resolving that mismatch is a repo-policy judgment
  call outside this role's frozen scope, so it is reported here rather
  than bypassed (`ORCHESTRATE_OFF` kill switch left untouched).
  Reported, not spawned. The commit (338b73f, branch
  issue-1165/technical-writing) is made and pushed to origin; only PR
  creation is blocked.
