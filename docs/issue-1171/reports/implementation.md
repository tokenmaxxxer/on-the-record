---
code_under_review:
  - on-the-record/hooks/upstream-defect-scope-guard.sh
  - on-the-record/hooks/test_upstream_defect_scope_guard.py
  - gates/test_upstream_finding_channel.py
type: fix
breaking: false
# canonical: python3 -m pytest on-the-record/hooks/test_upstream_defect_scope_guard.py gates/test_upstream_finding_channel.py -q, executed live this session (see Acceptance section)
verdict: pass
loop_state: landed
---

## What was done
canonical: `python3 -m pytest on-the-record/hooks/test_upstream_defect_scope_guard.py gates/test_upstream_finding_channel.py -q`, executed live this session (see Acceptance section).

Scoped `upstream-defect-scope-guard.sh`'s PR-creation deny to the
upstream-defect channel's own flow, instead of denying every
`gh pr create` (and its wider surface: `gh api /pulls`, GraphQL,
`GH_REPO`, `hub`, `curl`) universally. A call is now in-scope for denial
iff the acting role is the channel's own role
(`CLAUDE_ROLE == "upstream-defect-report"`, read via the session-role-bind
snapshot with a live-env-var fallback — approval-gate.sh's issue #698
pattern) OR the call carries an extractable target repo that differs
from this session's own git origin repo. All five previously-covered
surfaces (`gh pr create`, `gh api /pulls`, GraphQL `createPullRequest`,
`hub pull-request`, `curl`/`wget`) keep full coverage within that scope —
only the trigger context narrowed, per the issue's requirement 2.

Updated both existing test files: `on-the-record/hooks/test_upstream_defect_scope_guard.py`
and `gates/test_upstream_finding_channel.py` now assert channel-scope
denial (non-origin target repo, or `CLAUDE_ROLE=upstream-defect-report`)
on every surface, and add new origin-delivery-PR-allowed cases (with and
without an explicit `--repo` flag).

## Why
Issue #1171: the guard's regex had no channel/repo scoping, so it fired
on issue-1163's own delivery-PR creation against origin
(docs/issue-1163/reports/implementation.md, 2026-08-13 "Open findings"),
blocking every future role session's delivery PR. northpole req#7
(default-on must not break the core delivery loop) and #1131's R002
(channel stays issues-only, correctly scoped) both require the fix.

## Upstream
based on: docs/issue-1131/proposals/2026-08-13-upstream-defect-channel-requirements.md
docs/issue-1171/proposals/2026-08-13-scope-upstream-defect-guard.md

## What did not work
None.

## Open findings
None.

## Acceptance
derived: `python3 -m pytest on-the-record/hooks/test_upstream_defect_scope_guard.py gates/test_upstream_finding_channel.py -q`
```
24 passed in 1.03s
```
canonical: `python3 -m pytest on-the-record/hooks/test_upstream_defect_scope_guard.py gates/test_upstream_finding_channel.py -q` — result: pass

Also re-ran the wider `gates/` upstream-scoped slice to confirm #1131's
own acceptance gate still passes unmodified by this change:

derived: `python3 -m pytest gates/ -q -k upstream`
```
9 passed, 464 deselected in 0.76s
```
canonical: `python3 -m pytest gates/ -q -k upstream` — result: pass
