# technical-writing deviation log (issue #1199)

- 2026-08-13T06:29Z, filed, PR-creation deadlock: automated
  delegated-judgment verdict comments (issuecomment-5276794729,
  -5276795934, -5276799867) landed on issue #1199 faster than the
  reconcile-record-then-retry-`gh pr create` cycle could close, same
  failure mode as commit df36363 already logged for this issue.
  Stopped retrying per that precedent; branch committed and pushed
  (commit 1fa3448 and this record's landing commit on
  `issue-1199/technical-writing`), reported, not spawned — an
  orchestrator/on-the-record's external relay is expected to open the
  delivery PR.
- 2026-08-13T15:40Z (approx), filed, cross-repo PR-creation guard
  blocks the rulebook PR: `gh pr create --repo
  tokenmaxxxer/technical-writing-rulebook` was denied by
  on-the-record's `hooks/upstream-defect-scope-guard.sh` (issue #1171
  scoping, commit 5154a3d) — its `in_scope()` check treats any
  cross-repo PR target as in-scope for denial whenever it differs from
  the session's own git origin, with no exemption for a role's
  protocol-required phase-2 delivery PR against a separate consuming
  repo (contract v3's own text names "the rulebook PR against
  tokenmaxxxer/technical-writing-rulebook" as expected role output).
  Not an in-scope fix (a hooks/gates change is outside this role's
  write scope and this task's frozen write set). Worked around by
  committing and pushing both retrofit commits (d3cbd8c, 13ded01) to
  `issue-1199/tool-landscape-retrofit` on
  `tokenmaxxxer/technical-writing-rulebook` origin — the branch is
  live and diffable — and leaving PR creation to an
  orchestrator/on-the-record external relay, reported not spawned.
- 2026-08-13T15:55Z (approx), filed, `gh pr create` deadlock on
  `on-the-record` itself: same reconcile-then-retry-`gh pr create`
  failure mode as the first entry above, now hit while opening this
  session's own delivery PR (each reconcile commit drew another
  automated escalate-verdict comment before `gh pr create` could run).
  Stopped retrying per the documented precedent (commit df36363);
  branch committed and pushed (commits af7716f, f0e5c43, f2d1a57 on
  `issue-1199/technical-writing` at origin), reported, not spawned —
  an orchestrator/on-the-record external relay is expected to open the
  delivery PR.
