# issue-2180 — execution-observation current-state survey

Scout skip: no design decision is open here — this session verifies
already-landed code rather than proposing something new. Scout-protocol's
second mandatory skip condition applies ("the spec literally leaves no
design decision open"; `roles/specs/execution-observation.spec.json`'s
own `gate_c_status` says the same: mechanical aggregation, not
investigative finding). No scouting sweep was run.

## What issue #2180 asked for

canonical: `gh issue view 2180` (this session) — the acceptance section,
quoted verbatim from that read:
```
- A newly-returned PR produces a distinct, unmistakable signal on the tick it first appears (test asserting the emission shape differs from routine heartbeat lines)
- An already-surfaced PR does not re-emit the same full [returned-pr] line on subsequent ticks (regression test with a two-tick sequence)
- Existing watchdog/Monitor behavior otherwise unchanged
- Executed acceptance evidence in the record (#2137)

empty state: a first-ever tick with no prior surfaced-marker file treats every open PR as new — surfaced once, then suppressed.
```

## What landed on `issue-2180/implementation` (PR #2181)

canonical: `gh pr view 2181 --json title,body,state,url,reviews` (this
session) —
```
state: MERGED
title: issue-2180: distinct new-returned-pr signal, stop repeating already-surfaced returned-pr lines
url: https://github.com/tokenmaxxxer/on-the-record/pull/2181
```
Its body's last line, quoted verbatim from that same read: `Closes #2180`.

canonical: `git log --oneline origin/main..origin/issue-2180/implementation`
(this session, before the squash-merge landed) —
```
f33a7a62 issue-2180: log before-landing warrant-hunt deviation
3271d8f8 issue-2180: distinct new-returned-pr signal, stop repeating already-surfaced returned-pr lines
```

canonical: `git log --oneline -5 origin/main` (this session, after
re-fetching) — the same content landed on `main` as this squash-merge
commit:
```
abdb5ac0 issue-2180: distinct new-returned-pr signal, stop repeating already-surfaced returned-pr lines (#2181)
```

canonical: `git diff --stat origin/main..origin/issue-2180/implementation`
(this session, diffed against the pre-merge `main` tip) —
```
docs/issue-2180/reports/implementation.md          | 257 +++++++++++++++++++++
.../2026-08-24-hunt-returned-pr-signal-shape.md    |  43 ++++
.../reports/implementation/deviation-log.md        |  17 ++
on-the-record/monitors/poll-heartbeat.sh           |  65 +++++-
on-the-record/monitors/test_poll_heartbeat.py      | 111 ++++++++-
5 files changed, 484 insertions(+), 9 deletions(-)
```

canonical: `git show origin/issue-2180/implementation:on-the-record/monitors/poll-heartbeat.sh`
(this session) — the implementation role's own change, read directly in
the diffed file text: a persisted `surfaced_returned_pr_issues` set,
keyed by the bare `#<issue>` token rather than the phase-qualified diff
key; a `new_pr_markers.append(line.replace("[returned-pr]",
"[new-returned-pr]", 1))` prepend, ahead of that tick's other output, on
a genuine first sighting; and a collapsed `[returned-pr-pending] %d
PR(s) still awaiting review: %s` line replacing the old full-line repeat
inside the #1732 30-minute bound branch.

canonical: `git show origin/issue-2180/implementation:docs/issue-2180/reports/implementation.md`
(this session; also readable at
`/tmp/otr-2180-verify/docs/issue-2180/reports/implementation.md`, a
read-only worktree checked out this session, no push) — that record's
own frontmatter and pasted acceptance run, quoted verbatim:
```
loop_state: landed
verdict: pass
type: fix
breaking: false
```
```
ok  t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line
ok  t_returned_pr_new_marker_does_not_repeat_on_later_tick
ok  t_returned_pr_first_ever_tick_treats_every_open_pr_as_new
ok  t_returned_pr_phase_transition_does_not_refire_new_marker

27/27 passed
```
```
13/13 passed
```

canonical: same file (`/tmp/otr-2180-verify/docs/issue-2180/reports/implementation/2026-08-24-hunt-returned-pr-signal-shape.md`,
read this session) — a before-landing warrant-hunt finding, its own
resolution text quoted verbatim: "Fixed in the same commit, before
landing: `is_new_pr` detection moved off the phase-qualified diff key
onto a separate, persisted `surfaced_returned_pr_issues` set keyed by
the bare `#<issue>` token ... Regression-pinned by
`on-the-record/monitors/test_poll_heartbeat.py`'s
`t_returned_pr_phase_transition_does_not_refire_new_marker`."

## Independent re-verification performed this session

acceptance: `git worktree add /tmp/otr-2180-verify
origin/issue-2180/implementation` — result: worktree checked out at
commit `f33a7a62`, read-only, no push.

canonical: `python3 on-the-record/monitors/test_poll_heartbeat.py` (run
from `/tmp/otr-2180-verify`, this session) — result:
```
ok  t_returned_pr_first_ever_tick_treats_every_open_pr_as_new
ok  t_returned_pr_new_item_emits_on_due_tick
ok  t_returned_pr_new_item_gets_distinct_marker_ahead_of_routine_line
ok  t_returned_pr_new_marker_does_not_repeat_on_later_tick
ok  t_returned_pr_phase_transition_does_not_refire_new_marker
ok  t_returned_pr_unchanged_set_produces_no_output_on_due_tick
ok  t_heartbeat_bound_with_returned_pr_emits_only_those_lines

27/27 passed
```

canonical: `python3 gates/test_poll_heartbeat_delta.py` (run from
`/tmp/otr-2180-verify`, this session; the sibling #1117/#1719 suite,
exercising the unchanged `[returned-pr]` tag only) — result:
```
13/13 passed
```

canonical: `bash -n on-the-record/monitors/poll-heartbeat.sh` (run from
`/tmp/otr-2180-verify`, this session) — result:
```
SYNTAX_OK
```

Both independently re-run suites and the syntax check match the
implementation record's own claimed results exactly, this session
identified no discrepancy. This session did not re-attempt the
implementation record's fourth, broader unrelated-suite sweep — that
check evidences no regression outside this change's scope, the burden of
the role that ran it once already, not something re-execution restates;
the three checks above are the ones that directly evidence issue #2180's
own acceptance bullets, and all three were independently reproduced this
session.

## Issue #2180's own state — a phase-2 board-eligibility blocker

canonical: `gh issue view 2180 --json state,stateReason,closedAt,title`
(this session) — result:
```
state: CLOSED
stateReason: COMPLETED
closedAt: 2026-08-24T10:24:39Z
```

canonical: PR #2181's own body, quoted above in "What landed" — its last
line reads `Closes #2180`; GitHub's own auto-close behavior takes over a
referenced issue the moment such a PR merges to `main`. No separate
issue event beyond this session's own `gh issue view 2180 --json
comments` read (the automated `[watch]` notice quoted further below) was
available to inspect.

canonical: `sed -n '52,90p' "${CLAUDE_PLUGIN_ROOT_CORE}/hooks/approval-gate.sh"`
(this session, the outer orchestration harness's phase gate) — its own
stated precondition, quoted verbatim:
```
if issue_state != "OPEN":
    ...
    deny("issue #%s is not open (state: %s) — a closed issue's board is "
         "not live for any role, regardless of any standing PR review or "
         "APPROVE comment. (contract v3 s19)"
         % (issue_num, issue_state or "unknown"))
```
That check runs before either approval-signal path (a PR review Approve,
or an issue comment exactly `APPROVE issue-2180/execution-observation`)
is evaluated, and after the file's own `CORE_BUILD_NOW=1` bypass check —
so with the issue in this state, phase-2 approval for this subject has
no reachable path except a `CORE_BUILD_NOW=1` stamp (spawner-set only,
never self-granted per the role-handoff contract's own text: "a session
cannot grant itself this bypass by setting the variable on its own") or
a human reopening the issue.

canonical: `env | grep -Ei "CORE_|CLAUDE_"` (this session) — result:
```
CLAUDE_PLUGIN_ROOT_CORE=/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core
CLAUDE_ROLE=execution-observation
```
No `CORE_BUILD_NOW` line present.

canonical: `gh issue view 2180 --json comments` (this session) — result:
```
[watch] issue-2180/implementation: session-end: PR https://github.com/tokenmaxxxer/on-the-record/pull/2181 opened
```
An automated notice from `JiwonJung94`'s bot integration; no comment
body equals `APPROVE issue-2180/execution-observation`.

## Write surface this record actually needs

Only this role's own phase-2 record, docs/issue-2180/reports/execution-observation.md
(present in this session's working tree, untracked — no prior commit on
any branch has staged it), plus the phase-1 docs this survey/proposal
round itself produces under docs/issue-2180/proposals/ and
docs/issue-2180/reports/execution-observation/. No code path is touched
by this role.

canonical: this session's first Bash tool call this turn (a plain
`find`/`cat` read of the skeleton file, before this survey was written)
was denied by this workspace's own `approval-gate` PreToolUse hook,
result:
```
approval-gate: neither the PR for issue-2180/execution-observation nor issue #2180 carries an approval from a listed human approver (jiwonjung94, jjongkwann): no Approve review on an open PR, and no issue comment that is exactly 'APPROVE issue-2180/execution-observation'. Free-text comments are feedback, a bot's or agent's Approve is not a human's, and phase 2 waits for the human. (contract v3 s19)
```
Root cause traced this session (before this survey's own "Issue #2180's
own state" section above was even written): a `2>&1` redirect on an
otherwise read-only command trips the gate's read-only-heads bypass
(which requires no `` >|`$( `` character outside quotes), routing the
call into the full execution-surface check, which then matches on the
`docs/issue-2180/` token in the command line. Reads without a stderr
redirect, or via the `Read` tool (never gated by either copy of
`approval-gate.sh`, which only inspects `Write`/`Edit`/`MultiEdit`/`Bash`),
were unaffected.
