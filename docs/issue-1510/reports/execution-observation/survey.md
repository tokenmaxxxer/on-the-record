## Scope

Observed: role `implementation` (contract v3 s19, two-phase but combined
into one build session after a pre-existing single-account APPROVE), issue
#1510, PR https://github.com/tokenmaxxxer/on-the-record/pull/1513
("issue-1510: widen poll-heartbeat cadence 60s -> 120s with scaled
staleness constants"), branch `issue-1510/implementation`, commits
`e19e9ac24dc557b5fb7fb147fbbc296da6400d22` and
`0e654b2e7cee4b1d55d6ff6d1116dd9973622c02`, workspace
`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1510-implementation`.

## What was read this session (fresh-eyes order: diff/commits before the observed role's own record)

1. `gh issue view 1510` — full issue text (Problem / Affected constants /
   Requirements / Acceptance / Generator), and `gh issue view 1510
   --comments` — 4 comments: an `APPROVE issue-1510/implementation` comment
   (2026-08-14T15:49:44Z, author `JiwonJung94`, listed in
   `docs/specs/approvers.md`), two delegated-judgment comments ("Judgment
   opened" / "Verdict: ... -> escalate (depth or impact axis did not
   clear)", both 15:55:2x), and a session-end watch comment linking PR
   #1513 (15:55:50Z).
2. `gh pr view 1513 --json body,commits,mergeable,state,files` and `gh pr
   diff 1513` — the full diff, read before opening the observed PR's own
   record narrative.
3. Only after the diff, the three files the observed PR itself added
   (paths as they appear in `gh pr diff 1513`, not present on this
   session's own branch): its proposal (docs/issue-1510/proposals/heartbeat-cadence-widen.md),
   its phase-2 record (docs/issue-1510/reports/implementation.md), and its
   own survey (docs/issue-1510/reports/implementation/survey.md).
4. Independently, against the current tree on
   `origin/issue-1510/implementation` (not just the diff hunks): `git show
   origin/issue-1510/implementation:spawn.py | sed -n '5650,5665p'` and
   `grep -n "기본값 60초다" spawn.py` on that ref, `git show
   origin/issue-1510/implementation:on-the-record/monitors/poll-heartbeat.sh
   | sed -n '150,170p'`, `git show
   origin/issue-1510/implementation:on-the-record/hooks/directive.sh | sed
   -n '170,185p'`, and `git show
   origin/issue-1510/implementation:on-the-record/hooks/stop-poll-rearm.sh`
   grepped for `MONITOR_LIVENESS_STALE_SECONDS`.

## What the diff actually touches (hunks)

- `on-the-record/hooks/directive.sh` — one hunk, `@@ -177,7 +177,7 @@`,
  changing line 180: `MONITOR_LIVENESS_STALE_SECONDS:-180` ->
  `MONITOR_LIVENESS_STALE_SECONDS:-360`.
- `on-the-record/monitors/poll-heartbeat.sh` — one hunk, `@@ -163,7 +163,7
  @@`, changing line 166: `POLL_HEARTBEAT_SLEEP_SECONDS:-60` ->
  `POLL_HEARTBEAT_SLEEP_SECONDS:-120`.
- `spawn.py` — one hunk, `@@ -5658,7 +5658,7 @@`, changing
  `MONITOR_ALIVE_TOUCH_CADENCE_SECONDS = 60` -> `= 120`; the hunk's context
  lines (unchanged) include a Korean comment block at line 5658 that
  literally states `기본값 60초다` ("the default is 60 seconds") —
  in-hunk context, admissible per the diff-scope rule, and now inconsistent
  with the changed value on the very next context-adjacent line.
- tests/test_heartbeat_cadence.py (new file on the observed branch, not
  present on this session's own branch) — whole-file hunk.
- `tests/test_spawn.py` — one hunk adding class `NoConcurrencyCap`.
- Three new record/proposal files under the observed PR's own
  docs/issue-1510/ tree (the observed role's own phase-1/phase-2 record,
  read after the diff per fresh-eyes ordering).

## Off-diff observation (not a diff-hunk citation — logged as context, not step evidence yet)

canonical: `git show origin/issue-1510/implementation:on-the-record/hooks/directive.sh`
lines ~170-175 (read this session, command mode) — the comment block
above the changed hunk states the `MONITOR_LIVENESS_STALE_SECONDS`
threshold convention is duplicated verbatim in `stop-poll-rearm.sh`,
"since that hook does not source this file."

canonical: `gh pr view 1513 --json files` (read this session, command
mode) — confirms on-the-record/hooks/stop-poll-rearm.sh is not in the
PR's file list and has no hunk in `gh pr diff 1513`.

canonical: `git show origin/issue-1510/implementation:on-the-record/hooks/stop-poll-rearm.sh`
| grep -n MONITOR_LIVENESS_STALE_SECONDS (read this session, command mode)
— line 48 still reads `local threshold="${MONITOR_LIVENESS_STALE_SECONDS:-180}"`,
the pre-widen default, unscaled.

This off-diff fact is logged here to be carried into phase 2 as a
candidate step-level finding if approval opens phase 2, per the
DIFF-SCOPE RULE (it is evidence about a missing edit in an untouched
file, not a citation of a touched hunk, so it is flagged distinctly here
rather than treated as in-scope diff evidence).

## Approval-path note

canonical: `gh issue view 1510 --comments` (read this session, command
mode) — the `APPROVE issue-1510/implementation` comment (15:49:44Z)
predates both build commits (`e19e9ac2` 15:54:54Z, `0e654b2e` 15:55:12Z),
i.e. the approval was posted before the phase-2 build ran, in
single-account mode (`JiwonJung94` is both a listed approver per
docs/specs/approvers.md and the commit author). The comment body is the
exact string `APPROVE issue-1510/implementation`, no near-match. This
session did not itself grant or interpret that approval; it is reported
here as read fact for phase 2's trajectory check.

## Skip condition (scout-directive)

Scouting (best-in-class exemplar sweep) is skipped for this survey: this
is a pure-bugfix-shaped observation of a chore-type constant change with
no product-facing or exemplar-comparable design surface — one of the two
stated skip conditions applies verbatim.
