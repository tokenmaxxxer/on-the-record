## Scope statement

Observed role: implementation. Observed session/branch:
issue-1044/implementation. Observed issue: #1044.

canonical: gh pr view 1048 (this session).
Observed PR (phase-1 proposal, merged): #1048, merge commit
3d8725ef5532a2e7332d6b3fb9ec6282e41ffb50.

canonical: gh pr view 1056 (this session).
Observed PR (phase-2 delivery, merged): #1056, merge commit
a269692a0cba919e9ed6bf06c832aa280dec04ae. Both on branch
issue-1044/implementation.

Read this session, in order: `gh issue view 1044` and `gh issue view
1044 --comments` (issue text and full comment thread); `gh pr view
1048` + `gh pr diff 1048` (phase-1 diff and commits); `gh pr view 1056`
+ `gh pr diff 1056` (phase-2 diff, commits, body); `git log a269692a -1`
and `git show a269692a --stat` (delivery commit). Only after these were
read did this session read the observed role's own record narrative
(embedded in the PR #1056 diff) — this scope statement is built from
the PR diffs/commits themselves, not from that record's own framing
(FRESH-EYES ORDERING).

## Current state

canonical: gh issue view 1044 (this session).
Issue #1044 asked to wire `spawn.py panel <role_a> <role_b>
"<question>" [--issue n]` into `main()`, mirroring `consult`, mention it
in the orchestrator directive, and add a CLI-dispatch test asserting the
argv path reaches `panel_cmd` (run_session stubbed). Acceptance check
named: `python3 -m pytest tests/test_spawn.py -k panel_cli`.

canonical: gh issue view 1044 (this session, `state: CLOSED` field).
Issue state is CLOSED.

canonical: gh pr diff 1048 (this session).
PR #1048 (phase-1) adds only
docs/issue-1044/proposals/panel-cli-dispatch.md and
docs/issue-1044/reports/implementation/survey.md, no code. No
Closes/Fixes/Resolves trailer in its body (correct for a phase-1 PR
per the phase-trailer-split rule).

canonical: gh pr diff 1056 (this session).
PR #1056 (phase-2) adds the `if a.role == "panel":` branch to
`spawn.py`, one sentence to `on-the-record/hooks/directive.sh`, and
`PanelCliWiring` tests
(test_panel_cli_subcommand_calls_panel_cmd,
test_panel_cli_subcommand_missing_args_exits,
test_panel_cli_subcommand_same_role_twice_exits) to
`tests/test_spawn.py`.

canonical: gh pr view 1056 --json body (this session, body field).
The PR body carries `Closes #1044`.

canonical: gh pr diff 1056 (this session).
The diff also embeds a record file, a deviation-log file, and a
before-landing warrant-hunt file under
docs/issue-1044/reports/implementation/ — the hunt found a missing
`role_a != role_b` guard, inline-fixed in the same PR.

canonical: git merge-base --is-ancestor a269692a HEAD (this session),
exit 0.
This session's own branch already contains PR #1056's merge commit, so
the merged code is directly readable from the current working tree, not
only from the diff.

canonical: Read tool on spawn.py, this session, lines 5629-5640; grep
`panel` on-the-record/hooks/directive.sh, this session, line 305
matched.
Both confirm the working tree matches what the PR diffs claim landed.

canonical: python3 -m pytest tests/test_spawn.py -k panel_cli -v,
executed this session.
Result: 3 passed (test_panel_cli_subcommand_calls_panel_cmd,
test_panel_cli_subcommand_missing_args_exits,
test_panel_cli_subcommand_same_role_twice_exits).

canonical: gh issue view 1044 --comments --json comments (this
session).
An exact-match `APPROVE issue-1044/implementation` comment from
JiwonJung94, who is listed in docs/specs/approvers.md (canonical: Read
tool, this session). PR author for both #1048 and #1056 is also
JiwonJung94 (canonical: gh pr view output for both PRs, this session)
— single-account mode.

## No execution-observation record exists yet

canonical: this session's own Write attempt to
docs/issue-1044/reports/execution-observation.md, blocked this session
by the repo's approval-gate.sh hook (no `APPROVE
issue-1044/execution-observation` comment found from a
docs/specs/approvers.md-listed account).
That block is why this session is writing phase-1 material (this
survey plus the accompanying proposal) instead of the phase-2 record.

## Skip condition

Not skipped. Field-comparison scouting (comparable products/practices)
does not apply to this role in the scout-directive sense — this role
checks an already-landed artifact against an already-stated acceptance
criterion; there is no external field to survey for direction. This
document itself serves as the CURRENT-STATE SURVEY and RESEARCH
requirement for phase 1: PR numbers, commit SHAs, and the observed
role's own record file were all read this session (not summarized
secondhand, not assumed from the issue title), per the RESEARCH
criterion.
