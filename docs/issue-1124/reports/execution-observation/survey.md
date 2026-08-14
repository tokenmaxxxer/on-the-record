---
status: survey
---

Subject: issue-1124

## Scope statement

canonical: gh pr view 1146 --json number,title,body,mergedAt,mergeCommit,commits,files,baseRefName,headRefName (read this session)
canonical: gh pr diff 1146 (read this session, full diff, all hunks)

Observed: the implementation role's session on issue #1124, branch
`issue-1124/implementation`, delivered through two PRs — phase-1 PR
#1127 (proposal + survey; merge commit `5360f6ed` per `git log
--oneline --all`, read this session) and phase-2 PR #1146 (code +
record; merge commit `0d58769b` per the same `git log` read).

Read in FRESH-EYES ORDER: `gh pr diff 1146` (the full diff) and the
landing commits `b62e57dc` (code) and `612537ab` (record) per `git log
--oneline --all` (read this session) were read before
`docs/issue-1124/reports/implementation.md` (the observed role's own
narrative, read this session after the diff).

Diff hunks read this session (`gh pr diff 1146`, full diff, all hunks):
`docs/issue-1124/reports/implementation.md` (new, 93 lines),
`gates/test_clean_reconcile_safety.py` (new, 113 lines), and every
hunk touching `spawn.py` — the `LANDED_OUTCOMES` /
`_ledger_log_outcomes()` addition near `classify()`, the existence-check
hunk inside `_roster_reconcile_unreported`, the new `roster_clean()`
function, and the `main()` hunk replacing the old inline `clean` branch
with a call to `roster_clean()`.

Also read this session: issue #1124's body and comment thread (`gh
issue view 1124 --comments`, read this session), the phase-1 proposal
(`docs/issue-1124/proposals/clean-reconcile-safety.md`, read this
session), the phase-1 survey
(`docs/issue-1124/reports/implementation/survey.md`, read this
session), the after-proposal hunt record
(`docs/issue-1124/reports/implementation/2026-08-13-hunt-clean-reconcile-safety.md`,
read this session), `docs/specs/approvers.md` (read this session).

canonical: git log --oneline --all --grep=1283 (read this session, mode: command)

That command shows commit `dbb864a3` (issue #1283, merged via PR
#1286) on `main`.

canonical: python3 -m pytest gates/test_clean_reconcile_safety.py -q (executed live this session, this turn's own run — not the observed role's cited run)

That live re-run against current main produced `1 failed, 10 passed`;
the failing case was
`CleanReconcileSafetyTest::test_reconcile_unreported_skips_missing_workspace`
(pytest output, this session).

canonical: spawn.py:2900-2966 on current main (read this session, mode: read)

Cross-referencing that range shows commit `dbb864a3` later removed the
exact missing-workspace-skip behavior issue #1124 added to
`_roster_reconcile_unreported`, leaving PR #1146's regression test
unmatched against current main. This is a candidate step-level finding
for phase 2, not yet a rendered verdict (verdict language deferred to
phase 2 per the proposal below).

## R001

canonical: gh issue view 1124 (read this session)

Issue #1124's own body states `infrastructure/no-direct-requirement —
session lifecycle tooling; R001 is not this issue's target`. R001 is
not applicable to this subject.

## Scouting

Skip condition: this is a judgment/audit task (three-level execution
verdict against an already-landed PR) with no product design surface —
the spec being applied
(roles/specs/execution-observation.spec.json in
tokenmaxxxer/on-the-record) and this session's role directives fully
determine what gets checked; there is no open design decision to scout
exemplars for. Scouting skipped under the scout-directive's
no-open-design-decision condition.
