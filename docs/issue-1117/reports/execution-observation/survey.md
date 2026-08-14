# issue-1117 execution-observation: current-state survey

## Scope statement

Observed role/session: the (unnamed to this role) role/session that
delivered branch `issue-1117/implementation` and its PRs against issue
#1117 ("poll-heartbeat delta-suppression: unchanged watchdog ticks must not
interject the session"), requirement R001 cited by the issue.

canonical: `gh pr view 1122 --json number,state,mergedAt,commits,files,baseRefName,headRefName,mergeCommit`, executed live this session.

Observed PR: https://github.com/tokenmaxxxer/on-the-record/pull/1122, state
MERGED, merge commit `1a259a653d9b149b5b82cc813bcc94fc47b15ea0`, merged
2026-08-13T00:33:39Z (from the command above). An earlier PR on the same
branch, #1120, carried the phase-1 proposal round.

canonical: `gh issue view 1117 --comments --json comments`, executed live this session — comment body: "[watch] issue-1117/implementation: session-end: PR https://github.com/tokenmaxxxer/on-the-record/pull/1120 opened".

Observed commits, from the `gh pr view 1122` command above:
`d3db195cf4a5800ccff9c77be2b52269b7596252` (phase-2 code + priorities
record), `ff8bdf3a61976147456b0a5db2bc3c7aa8e385d9` (phase-2 implementation
record), `024056a41000eb9f5c2de79b5c54423fefe96672` (deviation-log entry).

## What was read to arrive at this scope (fresh-eyes ordering)

In order this session: `gh issue view 1117` (issue text + 8-comment thread);
`gh pr view 1122 --json ...` (file list: `docs/issue-1117/decisions/priorities.md`,
`docs/issue-1117/reports/implementation.md`,
`docs/issue-1117/reports/implementation/deviation-log.md`,
`gates/test_poll_heartbeat_delta.py`, `on-the-record/monitors/poll-heartbeat.sh`);
`gh pr diff 1122` (full diff, read before the observed role's own record
narrative, per fresh-eyes ordering) — the diff's single hunk in
`on-the-record/monitors/poll-heartbeat.sh` touches only the due-tick branch
(hash-and-compare wrapping the existing `printf`); the other four changed
paths are new files, so every line in them is in-diff. Then
`docs/issue-1117/reports/implementation.md` (the observed role's own
narrative, read after the diff). Then phase-1 artifact existence:

canonical: `ls docs/issue-1117/reports/implementation/`, executed live this session.

```
$ ls docs/issue-1117/reports/implementation/
deviation-log.md
hunt-poll-heartbeat-delta-suppression.md
survey.md
```

`docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md` also read in
full this session.

canonical: `git log --oneline --all | grep -i 1117`, executed live this session.

That command's output confirms the phase-1 commits (`c841bff0`, `443e6ade`)
precede the phase-2 commits (`d3db195c`, `ff8bdf3a`, `024056a4`) in the
branch's own history — full output:

```
$ git log --oneline --all | grep -i 1117
1a259a65 Merge pull request #1122 from tokenmaxxxer/issue-1117/implementation
024056a4 issue-1117: deviation log entry for docs/product path refusal
ff8bdf3a issue-1117 phase-2: implementation record
d3db195c issue-1117 phase-2: poll-heartbeat delta-suppression + priority record
4ff257a1 Merge pull request #1120 from tokenmaxxxer/issue-1117/implementation
c841bff0 issue-1117 phase-1: fix hash scope per warrant-hunt finding
443e6ade issue-1117 phase-1: poll-heartbeat delta-suppression proposal
```

## Live re-execution (this session, on current tree)

derived: `python3 gates/test_poll_heartbeat_delta.py`

```
$ python3 gates/test_poll_heartbeat_delta.py
ok  t_change_after_suppression_emits
ok  t_changed_tick_emits
ok  t_fresh_state_first_tick_always_emits
ok  t_identical_second_tick_suppressed
ok  t_anomaly_rc_produces_no_crash_label
ok  t_clean_rc_produces_neither_label
ok  t_dead_session_line_always_emits_even_unchanged
ok  t_non_due_tick_produces_no_output
ok  t_only_changed_line_emitted_not_full_report
ok  t_reserved_sentinel_rc_produces_crash_label
ok  t_returned_pr_line_always_emits_even_unchanged
ok  t_signal_death_rc_produces_crash_label
ok  t_watchdog_anomaly_bullets_survive_round_trip

13/13 passed
```

canonical: `python3 gates/test_poll_heartbeat_delta.py`, executed live this session (output immediately above).

All four of #1117's own named Acceptance cases pass; the file now carries 9
additional tests beyond those 4, added by later, unrelated work (see below).

derived: `python3 on-the-record/monitors/test_poll_heartbeat.py`

```
$ python3 on-the-record/monitors/test_poll_heartbeat.py
ok  t_heartbeat_arms_watchdog_when_due
FAIL t_heartbeat_attaches_on_board_repo: board target repo must get an alive marker
FAIL t_heartbeat_refuses_to_arm_on_non_git_root: poll tick: due, watchdog ran (rc=0, no output)
ok  t_heartbeat_respects_kill_switch
FAIL t_heartbeat_skips_attachment_on_non_board_repo: non-board target repo must not get a poll_heartbeat_last_state.json
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller

3/8 failed
```

canonical: `python3 on-the-record/monitors/test_poll_heartbeat.py`, executed live this session (output immediately above).

canonical: `git log --oneline --follow -- on-the-record/monitors/test_poll_heartbeat.py`, executed live this session.

```
$ git log --oneline --follow -- on-the-record/monitors/test_poll_heartbeat.py
bc32816c fix(monitor): refuse to arm on a non-git/non-board root
c490bc47 issue-1245: monitor attachment board gate (phase 2 delivery)
0ee817b5 feat(implementation): delta-only monitor emission for poll-heartbeat.sh
6e90fcef issue-922 implementation phase2: surface watchdog report on poll-heartbeat.sh due ticks (#944)
8ce2a5d2 issue-835: implement plugin Monitor for default-on ~60s poll heartbeat (#841)
```

canonical: the two `git log` command outputs immediately above (this section and the scope section).

The 3 failing tests trace to commits `c490bc47` and `bc32816c`, which do not
appear in the `git log --oneline --all | grep -i 1117` output's #1117 commit
set and which list before (more recently than) `d3db195c` in `git log
--oneline --all`'s default recency ordering — i.e. added to the tree after
#1122's `d3db195c` landed, by issue #1245's later work, not part of what
#1122 delivered or was checked against at its own merge time.

canonical: `grep -n "poll_heartbeat_last_hash\|new_hash\|prev_hash" on-the-record/monitors/poll-heartbeat.sh`, executed live this session (no output — zero matches).

The specific hash-file mechanism #1122 shipped is no longer present in the
current file's due-tick branch; the file's own comments (read this session)
cite issues #1220/#1274 as having replaced it with a different, line-keyed
mechanism.

## Approval state for #1117's own delivery (read this session)

canonical: `gh issue view 1117 --comments --json comments`, executed live this session.

A comment whose entire body is exactly `APPROVE issue-1117/implementation`
was posted by `JiwonJung94` at 2026-08-13T00:25:29Z.

canonical: `cat docs/specs/approvers.md`, executed live this session — lists `- JiwonJung94` and `- jjongkwann`.

canonical: `gh pr view 1122 --json author`, executed live this session — author `JiwonJung94`.

PR author and approver are the same account — single-account mode, where an
exact-string issue comment (not a PR review) is the approval path.

## Research (discovery-over-guessing)

This session read PR #1122's actual number, its three commit SHAs, and its
own record file directly (not summarized secondhand, not assumed from the
issue title) — cited above with hashes and command outputs.
