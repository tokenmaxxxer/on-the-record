# Execution observation — issue #1510, PR #1513 (implementation)

kind: execution-observation
loop_state: handed-off

## Independence statement

This session did not author or edit the observed artifact. It reviewed
PR https://github.com/tokenmaxxxer/on-the-record/pull/1513 (branch
issue-1510/implementation, merge commit 982e4304c646826908051c8c7fc1b483a0481fa2
into origin/main at 1425c881d0ec4d7124d73be013db5dde14589f17) without
touching any file under its src/, test/, or docs/issue-1510/ paths
outside this role's own report path. All evidence below was gathered by
running the observed role's own shipped tests against origin/main
(worktree /tmp/main-check, checked out from origin/main) and reading
the shipped constant files directly — never by re-implementing or
re-deriving the change.

## What was done

Executed the two acceptance tests PR #1513 landed, against the current
origin/main tree, and independently re-read the three shipped constant
sites the issue named. Also re-checked the off-diff candidate finding
this role's own phase-1 survey had logged, and folded PR #1515's own
disposition into this record.

## Why

Issue #1510 requires phase-2 execution judgment for PR #1513: whether the
tests it shipped run clean against the live tree, whether the three
named constants carry their scaled values in the shipped files, and
whether the phase-1 survey's off-diff candidate finding survives
independent re-check.

## Upstream basis

- PR https://github.com/tokenmaxxxer/on-the-record/pull/1513, merge commit
  982e4304c646826908051c8c7fc1b483a0481fa2.
- docs/issue-1510/reports/execution-observation/survey.md (this role's own
  phase-1 survey, same branch, commit 4cd120be0da1aea9179c98ab87cf0e7e5ee443c0).

## code_under_review

- on-the-record/monitors/poll-heartbeat.sh
- on-the-record/hooks/directive.sh
- spawn.py
- tests/test_heartbeat_cadence.py
- tests/test_spawn.py

## Step-level findings

### 1. tests/test_heartbeat_cadence.py::TestHeartbeatCadenceDefaults::test_defaults_scaled_together

subject: tests/test_heartbeat_cadence.py (shipped by PR #1513)
test: executed this session against origin/main in an isolated worktree
```
$ cd /tmp/main-check && python3 -m pytest tests/test_heartbeat_cadence.py -v
tests/test_heartbeat_cadence.py::TestHeartbeatCadenceDefaults::test_defaults_scaled_together PASSED [100%]
1 passed in 0.05s
```
canonical: pytest tests/test_heartbeat_cadence.py -v — result: PASS
result: passed
assertedBy: execution-observation (this role, this session); mode: command
(worktree /tmp/main-check created via `git worktree add /tmp/main-check origin/main`,
so the test ran directly against the shipped files, not a copy.)

### 2. tests/test_spawn.py::NoConcurrencyCap (both tests)

subject: tests/test_spawn.py::NoConcurrencyCap (shipped by PR #1513)
test: executed this session against origin/main in the same worktree
```
$ cd /tmp/main-check && python3 -m pytest tests/test_spawn.py::NoConcurrencyCap -v
tests/test_spawn.py::NoConcurrencyCap::test_no_concurrency_cap PASSED    [ 50%]
tests/test_spawn.py::NoConcurrencyCap::test_zero_running_sessions_spawns_normally PASSED [100%]
2 passed in 0.15s
```
canonical: pytest tests/test_spawn.py::NoConcurrencyCap -v — result: PASS
result: passed
assertedBy: execution-observation (this role, this session); mode: command

### 3. Live constants in the shipped files

subject: on-the-record/monitors/poll-heartbeat.sh:166, on-the-record/hooks/directive.sh:180, spawn.py:5685
test: read directly from origin/main (worktree /tmp/main-check), independent of the tests above
```
$ cd /tmp/main-check
$ sed -n '160,168p' on-the-record/monitors/poll-heartbeat.sh
sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"
$ sed -n '176,182p' on-the-record/hooks/directive.sh
local threshold="${MONITOR_LIVENESS_STALE_SECONDS:-360}"
$ sed -n '5678,5690p' spawn.py
MONITOR_ALIVE_TOUCH_CADENCE_SECONDS = 120
MONITOR_ALIVE_STALE_THRESHOLD_SECONDS = 7 * 24 * 3600
assert MONITOR_ALIVE_STALE_THRESHOLD_SECONDS > MONITOR_ALIVE_TOUCH_CADENCE_SECONDS
```
canonical: bash -c "sed -n '160,168p' on-the-record/monitors/poll-heartbeat.sh" (see full output above) — result: PASS
result: passed
assertedBy: execution-observation (this role, this session); mode: command.
360 = 3 x 120 (the 3-tick tolerance ratio issue #1510's requirement 2
demands), and the GC assert (7d > 120s) still holds at the new cadence —
matching issue #1510's Acceptance items 1 and 3.

### 4. Deficiency: on-the-record/hooks/stop-poll-rearm.sh:48 left unscaled

subject: on-the-record/hooks/stop-poll-rearm.sh:48
test: read directly from origin/main (worktree /tmp/main-check); this file carries no hunk in PR #1513's diff
```
$ cd /tmp/main-check && grep -n MONITOR_LIVENESS_STALE_SECONDS on-the-record/hooks/stop-poll-rearm.sh
48:  local threshold="${MONITOR_LIVENESS_STALE_SECONDS:-180}"
```
canonical: bash -c "grep -n MONITOR_LIVENESS_STALE_SECONDS on-the-record/hooks/stop-poll-rearm.sh" (see full output above) — result: FAIL
result: failed
assertedBy: execution-observation (this role, this session); mode: command.
canonical: `gh pr view 1513 --json files` (read this session, command
mode, prior turn) confirms on-the-record/hooks/stop-poll-rearm.sh has no
entry in the PR's file list, i.e. no hunk in the diff.

**Impact:** directive.sh's own comment block (read by this role's phase-1
survey, off-diff, commit 4cd120be0da1aea9179c98ab87cf0e7e5ee443c0) states
the MONITOR_LIVENESS_STALE_SECONDS threshold convention is duplicated
verbatim in stop-poll-rearm.sh "since that hook does not source this
file." That duplicate default was never widened. canonical: the two
sed/grep outputs above in findings 3 and 4 (both run this session) show
stop-poll-rearm.sh still reading 180 while directive.sh reads 360 — at
the new 120s heartbeat cadence a single delayed tick (gap ~240s) sits
above the former threshold and below the latter, so this hook alone can
false-fire a "monitor dead" re-arm at a cadence the other copy tolerates.

**Timeline:** introduced at PR #1513's merge, 2026-08-14 16:02:09Z.
canonical: `gh pr view 1513 --json state,mergedAt` (read this session,
command mode, prior turn) — the constant change touched two of the three
sites issue #1510 named plus spawn.py, but not this fourth,
undocumented-in-the-issue duplicate.

**Root cause:** issue #1510's own "Affected constants" inventory does not
list stop-poll-rearm.sh. canonical: `gh issue view 1510` (read this
session, command mode) — it was never in the change's stated scope, so
PR #1513's diff never touched it, and tests/test_heartbeat_cadence.py
only parses poll-heartbeat.sh and directive.sh, not this third copy
(canonical: `git show origin/main:tests/test_heartbeat_cadence.py`, read
this session, command mode, shown in full earlier this session).

**Action item:** a follow-up change (new issue, user-filed per this
role's contract — this role does not file issues) should widen
stop-poll-rearm.sh:48's default to 360 alongside directive.sh's, and
either have stop-poll-rearm.sh source the same constant as directive.sh
or extend test_defaults_scaled_together to parse this third copy too.

### 5. Non-blocking: stale comment in spawn.py

subject: spawn.py (comment block above line 5685, in-diff-hunk context per this role's phase-1 survey)
test: read directly from origin/main
```
$ cd /tmp/main-check && sed -n '5678,5684p' spawn.py
```
canonical: sed -n '5678,5684p' spawn.py above — text-only, no PASS/FAIL semantics
result: cantTell
assertedBy: execution-observation (this role, this session); mode: command.
The comment still reads "그 스크립트 자신의 tick cadence 상수가
POLL_HEARTBEAT_SLEEP_SECONDS 기본값 60초다" (states the default is 60
seconds), inconsistent with the changed value on the next line — see
finding 3's `MONITOR_ALIVE_TOUCH_CADENCE_SECONDS = 120` output above,
same file, same command run. Documentation-only drift, no behavioral
effect — recorded as cantTell (not failed) because unlike finding 4 it
changes no runtime behavior.

## PR #1515 disposition

subject: PR https://github.com/tokenmaxxxer/on-the-record/pull/1515 (this
role's own phase-1 proposal PR, branch issue-1510/execution-observation)
canonical: `gh issue view 1510 --comments` (read this session, command
mode, prior turn) — the exact-string comment "APPROVE
issue-1510/execution-observation" was posted by JiwonJung94 (listed in
docs/specs/approvers.md), opening phase 2 in single-account mode (same
account as the PR's author). No near-match ambiguity: the comment body is
the exact required string.
canonical: `gh pr view 1515 --json state` (read this session, command
mode, prior turn) — state OPEN at time of this record; this record and
its commit land on the same branch/PR per contract v3 s19 (record is
phase-2 output like code, delivered through the same PR, not a new one).

## Outcome verdict

canonical: bash -c "pytest tests/test_heartbeat_cadence.py tests/test_spawn.py::NoConcurrencyCap -v" (see findings 1-4's command output above, this record, this session) — result: FAIL
Outcome = **not fully met** — worst case among the cited step-level
results (findings 1-3 pass, finding 4 fails), not a standalone summary.
Issue #1510's three stated Acceptance items check out individually
against findings 1-3 above, but finding 4's command output shows the
change leaves a duplicate copy of the same tolerance constant unscaled —
in spirit within the issue's own stated rationale ("cadence and its
derived staleness tolerance are one decision") even though that file
falls outside the issue's own enumerated inventory.

## Trajectory verdict

- scouted-when-required: not applicable. canonical: this role's own
  phase-1 survey (docs/issue-1510/reports/execution-observation/survey.md,
  commit 4cd120be0da1aea9179c98ab87cf0e7e5ee443c0, read this session) logs
  a scout-directive skip record for the observed PR's own change class:
  "pure-bugfix-shaped observation of a chore-type constant change with no
  product-facing or exemplar-comparable design surface."
- surveyed-before-proposing: pass. canonical: `gh pr diff 1513` (read
  this session, command mode, prior turn) shows the observed role's
  survey and proposal files as separate commits/files on branch
  issue-1510/implementation; this role's own survey (commit 4cd120be)
  records reading that diff/those commits before the observed role's own
  record narrative, per fresh-eyes ordering.
- approved-by-human: pass. canonical: `gh issue view 1510 --comments`
  (read this session, command mode) shows the exact string "APPROVE
  issue-1510/implementation" posted 2026-08-14T15:49:44Z by JiwonJung94
  (listed in docs/specs/approvers.md), predating both of PR #1513's build
  commits (e19e9ac2 15:54:54Z, 0e654b2e 15:55:12Z, per `gh pr view 1513
  --json commits` read this session) — a real Approve, not an inferred
  one, in single-account mode.

## Open findings

- Finding 4 above (on-the-record/hooks/stop-poll-rearm.sh:48 unscaled
  duplicate constant) is open. Resolution path: a user-filed follow-up
  issue (this role does not file issues per contract) to widen the
  default to 360 and either share the constant with directive.sh or
  extend test_defaults_scaled_together to cover the third copy.
- Finding 5 (stale comment in spawn.py) is open but non-blocking.
  Resolution path: fold into the same follow-up issue as a one-line
  comment fix, or leave for the next touch of that file.

## Next steps

- Human reviews this record's outcome verdict (not fully met, per finding
  4) and decides whether to file the stop-poll-rearm.sh follow-up issue.
- This role's own PR #1515 awaits merge to close loop_state to a terminal
  state.

## What did not work

None.
