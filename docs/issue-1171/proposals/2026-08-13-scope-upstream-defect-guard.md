---
status: approved
files:
  - on-the-record/hooks/upstream-defect-scope-guard.sh
  - on-the-record/hooks/test_upstream_defect_scope_guard.py
  - gates/test_upstream_finding_channel.py
---

Skip condition (survey-order-directive): pure bugfix of a landed gate
(#1131/PR #1140) — no new design surface, per issue #1171's own
`validity-consult-skip: trivial` line.

## Request
`upstream-defect-scope-guard.sh` currently denies every `gh pr create`
(and its wider surface: `gh api /pulls`, GraphQL, `hub`, `curl`) with no
scoping, so it also blocks a role session's own delivery PR against
origin — observed live when issue-1163's delivery PR against
`tokenmaxxxer/on-the-record` (this repo's own origin) was denied. Scope
the deny to the upstream-defect channel's own flow only.

## Constraints
- northpole req#7: default-on enforcement must not break the core
  delivery loop.
- #1131 req#4 / R002: the channel stays issues-only — PR creation from
  the channel's own flow must still be denied on every covered surface.
- Full surface coverage (gh api /pulls, GraphQL, GH_REPO, hub/curl) stays
  intact within the channel's scope — only the trigger context narrows.

## Rationale
Considered comparing the PR-creation target repo against the local
git-origin repo alone (deny iff target != origin). Rejected: this repo's
own origin (`tokenmaxxxer/on-the-record`) is also the channel's example
upstream target, so a plain repo-string comparison cannot tell a
same-repo delivery PR from a same-repo channel PR in this
self-hosting case — the exact ambiguity the issue's evidence exposes.
Chosen instead: OR the repo-mismatch signal with the channel's own role
identity (`CLAUDE_ROLE` snapshot == `upstream-defect-report`, read via
the session-role-bind snapshot the same way approval-gate.sh already
does, issue #698's pattern) — a PR-shaped command is in-scope for denial
when either the acting role is the channel's own role, or the resolved
target repo differs from the session's git origin.

## What will be done
- Resolve the session's origin repo (`git remote get-url origin`,
  `owner/repo` parsed out) and the acting role (session-role-bind
  snapshot, falling back to the live `CLAUDE_ROLE` env var).
- For each PR-creation surface already covered, extract the call's
  target repo where the call shape carries one (`--repo`/`-R` flag,
  `GH_REPO` env prefix, a `repos/OWNER/REPO/pulls` path, a curl URL's
  `repos/OWNER/REPO/pulls` segment). GraphQL and `hub pull-request`
  carry no extractable target repo.
- Deny iff role == `upstream-defect-report`, OR a target repo was
  extracted and it differs from the origin repo. Otherwise allow (covers
  the session's own delivery PR against origin, and any command with no
  git origin resolvable — fail-open on origin-resolution failure, same
  posture as approval-gate.sh's unparseable-branch fail-open).
- Update both existing test files: keep full-surface-denied coverage
  under an explicit non-origin target and/or `CLAUDE_ROLE=upstream-defect-report`,
  and add the new origin-delivery-PR-allowed regression cases.

## Out of scope
- Changing `report-upstream.md`'s own instructions or role JSON.
- Any change to `gh issue create` handling (already allowed, untouched).

## How you'll know it worked
`python3 -m pytest on-the-record/hooks/test_upstream_defect_scope_guard.py gates/test_upstream_finding_channel.py -q`
exits 0, including new cases for origin-delivery-allowed and
channel-denied-on-every-surface.
