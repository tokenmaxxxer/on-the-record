---
issue: 2904
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: 3a65f414:spawn.py, 3a65f414:watchdog.py, 3a65f414:test/test_session_completion_heartbeat.py, 3a65f414:test/test_workspace_progress_tracking.py
type: verification-record
breaking: false
verdict: tests-confirmed, two-of-four-acceptance-checks-lack-executed-live-evidence
loop_state: landed
upstream:
  - path: PR #2905 (issue-2904/silent-failure-audit-efd0df1c)
    sha: 3a65f414ac087b93e5f64cec8726e931cbe9987e
  - path: 3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md
    sha: 3a65f414ac087b93e5f64cec8726e931cbe9987e
skill-verdict: work-in-english — applied: invoked; loaded the SKILL.md via the Skill tool before writing this record. This record, all commands, and the PR/commit text are in English; only the final chat summary to the user is in Korean.
other mounted skills: not triggered — read-only audit-and-record task (checkout a branch, re-run existing tests, read a diff); no multi-module decomposition, no growth/JTBD framing question, no prior-art search, and freelunch's fan-out threshold (width >= 2 units, ~100+ lines each) does not apply to a single-branch audit.
---

# issue-2904 — independent-verification-1 record

## What was done

canonical: `gh issue view 2904` (full body plus 3 comments, including the two mid-flight direction corrections and the session-end comment) and `gh pr view 2905 --json title,body,files,commits,additions,deletions,mergeable,baseRefName,headRefName` — read before checking out the branch.

Fetched PR #2905 (`issue-2904/silent-failure-audit-efd0df1c`, tip `3a65f414`) into an isolated worktree (`git worktree add /tmp/pr2905-wt pr-2905`) and read the full diff against `origin/main` (`git diff origin/main...pr-2905 -- spawn.py watchdog.py`, 277 lines) end to end, plus both new test files (`3a65f414:test/test_session_completion_heartbeat.py`, `3a65f414:test/test_workspace_progress_tracking.py`) and the subject's own record (`3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md`, its deviation log, and the product-priorities entry it appended).

Independently re-ran, rather than trusted, every numeric claim in the PR body:

1. New tests — derived: `python3 -m pytest test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q` on `3a65f414` — result: `21 passed`. Matches the PR body's "21 passed" exactly.
2. Watchdog-adjacent regression set — derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_reconcile_crash_verdict_race.py on-the-record/monitors/test_poll_heartbeat.py test/test_unrecovered_commit_count.py test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q` on `3a65f414` — result: `74 passed`. Matches the PR body's "74 passed" exactly.
3. Full suite, no new failures — derived: `python3 -m pytest . -q` on `3a65f414` — result: `17 failed, 686 passed, 3 xfailed`. Re-ran the identical command against `origin/main` (`fa52c0c8`, a second worktree at `/tmp/main-wt`) — result: `17 failed, 665 passed, 3 xfailed`. Diffing the two sorted 17-name FAILED lists (both captured from the two pytest runs above) shows zero name-set difference — every failure on both sides is the same pre-existing, network/sandbox-shaped case (e.g. `fatal: 'origin' does not appear to be a git repository`), including `tests/test_spawn_gate_wiring.py` (test `HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present`), unrelated to this change. `686 - 665 = 21`, matching the 21 new tests counted in step 1.
4. Retirement-count invariant — derived: `python3 gates/retirement_count.py` on both `3a65f414` and `fa52c0c8`, output byte-compared — identical, no new `role`/`roles` token.

Read the code itself, not just the tests, for correctness:

- `_record_session_completion()`/`_drain_pending_completions()` (`spawn.py`) — derived: `grep -n "^import fcntl\|^import time" spawn.py`, result: both already imported at module scope. The lock file and completion queue paths are consistent between the write and drain sides, and both fallible operations (`open`/`flock`/`read_text`/`write_text`) are wrapped so a disk/permission failure degrades to an advisory print (write side) or a non-`None` error tuple (read side) rather than raising out of `_spawn_one()`'s completion tail or silently returning an empty list.
- The new drain call in `roster_watchdog()` (`watchdog.py`) runs before the `if not d:` early return, so a fully-emptied roster (the exact shape a self-removing completed session leaves behind) still surfaces a queued signal — verified this placement directly by reading the diff context, not inferring it from the test alone.
- `_last_tool_activity_summary()` (`watchdog.py`) — derived: `grep -n "^from datetime import datetime, timezone" watchdog.py`, result: already imported. Confirmed it reports an absolute `HH:MM:SS UTC` stamp (not a relative age), matching the PR's own stated rationale for delta-suppression compatibility.
- Source-of-truth separation the issue explicitly demanded ("must not report a session as finished when it crashed, or as running when it is dead") is structural, not just asserted: `diagnose_health()`'s `if not alive:` gate (`_alive(pid)`, a raw `os.kill` liveness check) is what decides whether execution can reach the new HEALTHY/workspace-summary branch at all; a dead pid is routed to the separate dead-scan branch regardless of workspace contents, and that branch's crash-vs-clean-exit distinction (`session_end_verdict()`) is untouched by this PR — confirmed by reading both branches in the diff, not just trusting the record's description of them.
- derived: `grep -rn "roster_watchdog\|diagnose_health" on-the-record/monitors/poll-heartbeat.sh` — result: `roster_watchdog()` is invoked by the existing, already-auto-started `poll-heartbeat.sh` Monitor loop, not new orchestrator-side code requiring opt-in, so the "holds without the orchestrator opting in" acceptance requirement is met structurally.

## Why

derived: `grep -n "COMPLETED" 3a65f414:watchdog.py` (read via `git show 3a65f414:watchdog.py | grep -n "COMPLETED"` inside the fetched worktree) — confirmed the label that both the pre-existing dead-scan branch and this PR's new drain-before-early-return branch print is the same string, printed from two distinct call sites: the old dead-entry scan (for a session whose owning process itself crashed before self-removal) and the new pending-completions drain (for the common clean-exit path this issue is about).

The subject's own record cites `provenance: executed-live` against all four of the issue's acceptance checks. Comparing that claim against what the record and PR actually contain surfaces a gap worth reporting even though the underlying mechanism reads as correct and is well-tested:

- **Check 1** ("spawn a session, let it finish, and show the orchestrator-visible signal naming the issue, the session, and its PR") is exercised only by `RosterWatchdogEmitsCompletionTest::test_completion_surfaces_even_with_fully_empty_roster` in `3a65f414:test/test_session_completion_heartbeat.py`, which mocks out `_roster_load`, `_board_wide_sweep_all`, `lease_reconcile_sweep`, and five other dependencies and calls `watchdog.roster_watchdog()` directly against a synthetic queue entry — a real, passing unit test of the new mechanism, but not a live spawn observed through the actual `poll-heartbeat.sh` Monitor loop. The one piece of genuinely live evidence available — the issue's third comment, posted 2026-08-31T01:18:20Z, naming PR #2905 — comes from a *different*, pre-existing channel (`_post_session_end_comment()`, a durable GitHub issue comment, per the subject's own record's "What was done" Part 1), not the new heartbeat line this PR adds. That existing channel is exactly the `gh`-based, comment-based signal the issue's non-goals list asks not to rely on ("Do not build the tracking on `gh` polling").
- **Check 2** ("on a running session with no commit, show what the tracking reports — files touched, record started, branch state") is exercised by `WorkspaceSummaryTest`/`DiagnoseHealthIncludesWorkspaceSummaryTest` in `3a65f414:test/test_workspace_progress_tracking.py` against synthetic temp-directory git repos, not against an actual running session's workspace mid-flight through a live `roster_watchdog()` tick.
- **Check 3** ("session end timestamp versus signal timestamp") has no corresponding measurement anywhere in the PR, its tests, or its record. Nothing computes or reports the latency between the write side and the next watchdog tick's drain-and-print for a real process — the unit test calls both in the same synchronous test function, which cannot represent this latency.
- **Check 4** ("demonstrate on a fresh orchestrator context that did not ask for it") has no corresponding demonstration anywhere in the PR or its record.

This does not mean the mechanism is wrong. The code-level review above found the placement (drain before the early return), the source-of-truth separation (the alive-gate), and the failure-mode handling (advisory-not-raised on write, error-not-silent-empty on read) all correct and well-reasoned, and the unit-test coverage for the underlying logic is thorough (21 new tests, including explicit empty-state and dead-pid-never-HEALTHY cases). The gap is specifically that the issue's acceptance section asked for `provenance: executed-live` — a real spawn observed through the real Monitor loop, timestamped — and the delivered evidence for two of the four checks is unit-test-level in substance, and for two of the four checks is absent. An issue whose whole framing is "every gap ended with the operator asking, not the orchestrator noticing" is more exposed than most to the difference between "the function is correct in isolation" and "the actual Monitor loop, running unattended, prints this signal in time" — the second is what checks 3 and 4 specifically ask to see, and a synchronous, mocked-dependency unit test cannot stand in for it.

## What did not work

None — this record's own checks (test re-runs, diff read, code-path trace) all reproduced cleanly; the finding above is a gap in the *subject's* evidence, not a failure in this verification session's own checks.

## Upstream basis

- `3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md` (PR #2905's own record) — read in full; its "What was done"/"Verification" sections are the claims independently re-derived above.
- PR #2905 diff (`spawn.py`, `watchdog.py`, `3a65f414:test/test_session_completion_heartbeat.py`, `3a65f414:test/test_workspace_progress_tracking.py`) at sha `3a65f414ac087b93e5f64cec8726e931cbe9987e`.

## Open findings

derived: `git log --all --diff-filter=A --name-only -- 'docs/issue-2904/reports/*'` — confirms `3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md` is the only deliverable record for this subject as of this session; no follow-up round has yet addressed the gap below.

1. Acceptance checks 3 ("session end timestamp versus signal timestamp") and 4 ("demonstrate on a fresh orchestrator context that did not ask for it") have no evidence — live or simulated — anywhere in PR #2905 or its record, despite both being tagged `provenance: executed-live` in the issue body. Resolution path: a follow-up round should either produce the missing live demonstrations, or the operator should explicitly accept unit-test-level evidence as sufficient for these two checks and say so.
2. Checks 1 and 2 are exercised only through mocked-dependency unit tests (`3a65f414:test/test_session_completion_heartbeat.py`, `3a65f414:test/test_workspace_progress_tracking.py`), not a live spawned session observed through the actual `poll-heartbeat.sh` Monitor loop. Resolution path: same as finding 1 — either a live run demonstrating the new signal appearing in real Monitor output, or an explicit operator acceptance of the unit-test substitute.

## Next steps

None — `loop_state: landed`. The findings above are handed off via this record's Open findings, not further work in this session.
