---
subject: issue-1510
role: conformance-review
kind: record
loop_state: landed
---

canonical: python3 -m pytest tests/test_heartbeat_cadence.py "tests/test_spawn.py::NoConcurrencyCap" -v (cwd /tmp/otr-main-verify, worktree at origin/main) — result: PASS (fenced counts further below), this session.

# Conformance review: issue-1510 heartbeat-cadence widen (landed via PR #1513)

## What was done
canonical: `gh pr view 1513 --json state,mergeCommit`, this session — see fence below.
```
MERGED 982e4304
```
canonical: `gh pr view 1516 --json state`, this session — see fence below.
```
OPEN
```
Phase-2 verdicts below check issue #1510's 4 Requirements and 3
Acceptance items against the state on origin/main at commit 982e4304
(PR #1513), not against PR #1513's diff or its own prose claims.
Verification ran in a disposable git worktree checked out at
origin/main (/tmp/otr-main-verify, removed after use), not read as
trusted output from the PR body.

Phase-1 proposal PR #1516 targeted verdicts against PR #1513's diff
while #1513 was still open.
canonical: `gh pr view 1513 --json state,mergeCommit` (fence above) and
`gh pr view 1516 --json state` (fence above), this session — #1513's
state is MERGED at 982e4304; no APPROVE comment landed on #1516 before
that merge.
canonical: `gh issue view 1510 --json comments --jq
'.comments[].body'`, this session — no comment body equal to the
string "APPROVE issue-1510/conformance-review" is present. #1516's
phase-1 survey content is kept by reference at
docs/issue-1510/reports/conformance-review/survey.md, unchanged; this
record replaces its scoped phase-2 plan.

## Why
Board condition (marketplace conformance-review role spec, issue-521):
an implementation commit landed on the branch and no conformance-review
record exists yet for that commit sha.
canonical: `git show origin/main:docs/issue-1510/reports/conformance-review.md`, this session — nonzero exit, path absent on main before this write.

## Upstream basis
982e4304 (merge commit, PR #1513, origin/main)

## Verdicts

canonical: `git worktree add /tmp/otr-main-verify origin/main`, this
session — worktree checked out at 982e4304 for every check below; all
file:line references in this section are read from that worktree, not
from this branch's own pre-#1513 tree.

### Requirement 1 — three constants changed together in one PR

requirement: Change the three constants together in one PR.
spec_ref: issue #1510, "Requirements" item 1.
evidence: `gh pr view 1513 --json files` (this session) — file list
includes on-the-record/monitors/poll-heartbeat.sh,
on-the-record/hooks/directive.sh, spawn.py, tests/test_heartbeat_cadence.py,
tests/test_spawn.py.
rationale: all three constant-bearing files land in one PR, matching
the requirement's "one PR" clause.
verdict: Present

### Requirement 2 — tick-cadence coupling test

requirement: A test asserts MONITOR_LIVENESS_STALE_SECONDS default >=
3x the heartbeat default.
spec_ref: issue #1510, "Requirements" item 2.
evidence: worktree file read, tests/test_heartbeat_cadence.py lines
23-27, this session:
```python
def test_defaults_scaled_together(self):
    heartbeat_default = _parse_default(POLL_HEARTBEAT_SH, "POLL_HEARTBEAT_SLEEP_SECONDS")
    stale_default = _parse_default(DIRECTIVE_SH, "MONITOR_LIVENESS_STALE_SECONDS")
    self.assertEqual(heartbeat_default, 120)
    self.assertGreaterEqual(stale_default, 3 * heartbeat_default)
```
rationale: reads both defaults from the shipped shell files (not
hardcoded copies) and asserts the ratio, matching the requirement.
verdict: Present

### Requirement 3 — no-concurrency-cap regression test + spec sentence

requirement: A regression test asserts the spawn path admits N
concurrent spawns with no count-based refusal; a spec sentence records
the WHY beside the test; RESPAWN_MAX_ATTEMPTS is out of scope.
spec_ref: issue #1510, "Requirements" item 3.
evidence: worktree file read, tests/test_spawn.py lines 6727-6752,
this session — class NoConcurrencyCap.test_no_concurrency_cap spawns
n=50 stub sessions via spawn.spawn_cmd(), asserts all 50 return with
no count-based refusal; test_zero_running_sessions_spawns_normally
covers the empty-state case. Docstring (6728-6735) states the WHY
(operator decision 2026-08-15) and carves out RESPAWN_MAX_ATTEMPTS as
out of scope.
rationale: test class name, both test methods, and the docstring's WHY
line all match the requirement's three named parts.
verdict: Present

### Requirement 4 — no tick-count dependency introduced

requirement: No tick-count dependency introduced; #1497 epoch-seconds
stamps and #1508 ordering stay unaffected.
spec_ref: issue #1510, "Requirements" item 4.
evidence: worktree file read, on-the-record/monitors/poll-heartbeat.sh
lines 156-166, this session — _alive_stamp_write and the sleep loop
both key off `date +%s` (absolute epoch-seconds), unchanged in shape;
only the sleep_seconds default literal moved 60 -> 120.
rationale: the cadence-affecting code path stayed epoch-seconds-based;
no counter variable was introduced or removed by this diff.
verdict: Present

### Acceptance 1 — test_heartbeat_cadence.py::test_defaults_scaled_together

requirement: heartbeat default is 120 and liveness-stale default >= 3x
it, read from the shipped files.
spec_ref: issue #1510, "Acceptance" item 1.
canonical: python3 -m pytest tests/test_heartbeat_cadence.py -v (cwd /tmp/otr-main-verify) — result: PASS, this session.
evidence: fenced pytest output, this session:
```
tests/test_heartbeat_cadence.py::TestHeartbeatCadenceDefaults::test_defaults_scaled_together PASSED
1 passed in 0.18s
```
rationale: the named test exists and its live run above succeeded
against the landed commit at 982e4304.
verdict: Present

### Acceptance 2 — test_spawn.py::NoConcurrencyCap

requirement: N stub spawns admitted concurrently with no count-based
refusal; zero-running-sessions case covered.
spec_ref: issue #1510, "Acceptance" item 2.
canonical: python3 -m pytest "tests/test_spawn.py::NoConcurrencyCap" -v (cwd /tmp/otr-main-verify) — result: PASS, this session.
evidence: fenced pytest output, this session:
```
tests/test_spawn.py::NoConcurrencyCap::test_no_concurrency_cap PASSED
tests/test_spawn.py::NoConcurrencyCap::test_zero_running_sessions_spawns_normally PASSED
2 passed in 0.18s
```
rationale: both named cases exist and their live run above succeeded
against the landed commit at 982e4304.
verdict: Present

### Acceptance 3 — MONITOR_ALIVE_TOUCH_CADENCE_SECONDS == 120, GC assert holds

requirement: MONITOR_ALIVE_TOUCH_CADENCE_SECONDS updated to 120 with
the existing GC assert still passing.
spec_ref: issue #1510, "Acceptance" item 3.
canonical: python3 -c "import spawn; assert spawn.MONITOR_ALIVE_STALE_THRESHOLD_SECONDS > spawn.MONITOR_ALIVE_TOUCH_CADENCE_SECONDS; print(spawn.MONITOR_ALIVE_TOUCH_CADENCE_SECONDS, spawn.MONITOR_ALIVE_STALE_THRESHOLD_SECONDS)" (cwd /tmp/otr-main-verify) — result: PASS, this session.
evidence: fenced output, this session:
```
120 604800
```
spawn.py lines 5685-5687 (worktree read) show
MONITOR_ALIVE_TOUCH_CADENCE_SECONDS = 120; GC assert unchanged in
shape.
rationale: the constant reads 120 and the pre-existing GC assert
executed without raising, above, against the landed commit at
982e4304.
verdict: Present

## Accumulation
Not applicable — one-time conformance check against a single landed
PR, not an accumulating-cost change.

## Open findings
None.
canonical: the Verdicts section of this record, this session — each
of the 4 Requirements and 3 Acceptance items above carries its own
evidence: tag with fenced live output.

## PR #1516 disposition
canonical: `gh pr view 1513 --json state,mergeCommit` and `gh pr view
1516 --json state` (fences repeated in "What was done" above), this
session.
PR #1516 is superseded by this record and will be closed without
merge in this session's PR flow. Its survey file stays at
docs/issue-1510/reports/conformance-review/survey.md, unchanged.
