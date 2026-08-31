---
issue: 2904
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
code_under_review: 3a65f414:spawn.py, 3a65f414:watchdog.py, 3a65f414:test/test_session_completion_heartbeat.py, 3a65f414:test/test_workspace_progress_tracking.py
type: verification-record
breaking: false
verdict: tests-confirmed, one-acceptance-provenance-gap-found
loop_state: landed
upstream:
  - path: PR #2905 (issue-2904/silent-failure-audit-efd0df1c)
    sha: 3a65f414ac087b93e5f64cec8726e931cbe9987e
  - path: 3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md
    sha: 3a65f414ac087b93e5f64cec8726e931cbe9987e
skill-verdict: work-in-english — applied: invoked; SKILL.md loaded via the Skill tool before any file was written this session. All code reading, test runs, this record, and commit/PR text are in English; the final user-facing chat summary alone is in Korean.
other mounted skills: not triggered — read-only audit-and-record task (checkout a branch, re-run existing tests, read a diff, verify claims against code), no multi-module fan-out, no separate artifact needing an adversarial reviewer beyond this role, no visualization, no config change.
---

# issue-2904 — independent-verification-2 record

## What was done

canonical: `gh issue view 2904 --repo tokenmaxxxer/on-the-record` (full body, acceptance criteria read before checkout) and `gh pr view 2905 --repo tokenmaxxxer/on-the-record` (summary, test plan, `Closes #2904` trailer), both read this session.

Checked out `issue-2904/silent-failure-audit-efd0df1c` (tip `3a65f414`, the only open PR against issue #2904 — derived: `gh pr list --repo tokenmaxxxer/on-the-record --search "2904" --state all`, this session, result: exactly one row, PR #2905) into a separate worktree (`/tmp/verify-2904`, `git worktree add`) and read the full diff (`gh pr diff 2905`, this session) end to end against the PR's own summary claims.

### Re-derived numeric claims (not trusted from the PR body)

derived: `python3 -m pytest test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q` run in `/tmp/verify-2904` on `3a65f414`, this session — result: `21 passed`. Matches the PR body's "21 passed" exactly.

derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_reconcile_crash_verdict_race.py on-the-record/monitors/test_poll_heartbeat.py test/test_unrecovered_commit_count.py test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q` run in `/tmp/verify-2904` on `3a65f414`, this session — result: `74 passed`. Matches the PR body's "74 passed" exactly.

derived: `python3 -m pytest . -q` run in `/tmp/verify-2904` on `3a65f414`, this session — result: `17 failed, 686 passed, 3 xfailed`; the identical command run in this session's own worktree on `origin/main` (`fa52c0c8`) — result: `17 failed, 665 passed, 3 xfailed`. `686 - 665 = 21`, exactly the 21 new tests above. Both `FAILED` line sets were extracted with `grep '^FAILED' | sort` into `/tmp/before_fail.txt` / `/tmp/after_fail.txt`; `diff /tmp/before_fail.txt /tmp/after_fail.txt`, this session — result: no output (byte-identical 17-item failing-test-name sets: `test_convention_equivalence.py` x2, `harness/fixture-operator-experience/test_flow.py`, `test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py` x5, `test_spawn_artifact_skill_pairing.py` x2, `test_spawn_skill_judge_haiku_timeout_overlap.py` x4, `tests/test_spawn_gate_wiring.py` — none touch `spawn.py`'s completion path or `watchdog.py`'s health-diagnosis path). Matches the PR body's "no new failures" claim.

derived: `git diff fa52c0c8 -- spawn.py watchdog.py test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py | grep -iE '\brole'` run in `/tmp/verify-2904`, this session — result: no output. Confirms the PR body's "no new `role`/`roles` token" claim.

All four re-derivations above match the PR's own numbers (each cited with its own `derived:` command and result directly above).

### Code-level verification of the three parts' central claims (read the actual control flow, not just the PR's prose)

canonical: `3a65f414:spawn.py:4792-4794`, read directly this session — `roster_remove(roster_key)` runs unconditionally in `_spawn_one()`'s tail (right after `rc = proc.wait()`), confirming a normally-exiting session really does remove its own roster entry before any later watchdog tick can see it via the dead-entry scan.

canonical: `3a65f414:watchdog.py:1642-1762`, read directly this session — `_sp._drain_pending_completions()` is called at line 1698, and the `if not d:` early return the PR claims it precedes is at line 1762 (confirmed by reading the actual line numbers, not by trusting the PR's prose). A drain error (`_pc_err is not None`) is printed as `[poll-report-drain-failed] ...` and added to `anomaly_count`; a successful drain's `COMPLETED` lines are not added to `anomaly_count`, matching the PR's "completion is not an anomaly" claim. derived: `grep -n "ALWAYS_RE\s*=" on-the-record/monitors/poll_heartbeat_delta.py` and reading the matched line, this session — result: `COMPLETED` is one of the literal alternatives in `ALWAYS_RE`, so this line survives delta-suppression on every tick it's emitted, as claimed.

canonical: `3a65f414:watchdog.py:216-247` (`_live_session_workspace_summary`) and `3a65f414:watchdog.py:253-320` (`_last_tool_activity_summary`), read directly this session. Confirmed the `-uall` flag is present in the `git status --porcelain -uall` call (the PR's own self-audit finding); confirmed `_last_tool_activity_summary()` reads only `entry["log"]`'s last 64KB and renders the timestamp with `datetime.fromtimestamp(last_ts, tz=timezone.utc).strftime("%H:%M:%S")` — an absolute clock time, not an elapsed-seconds computation, matching the "delta-suppression-friendly" claim. Confirmed the dead-pid gate: `3a65f414:watchdog.py` (`diagnose_health()`)'s `alive = _sp._alive(pid)` / `if not alive:` returns before the code path that computes `workspace_summary`/`activity_summary` is reached — derived: `sed -n '330,510p' watchdog.py | grep -n "alive\|HEALTHY\|STALLED\|DEADLOCKED\|return "` run in `/tmp/verify-2904`, this session — result confirms the `if not alive:` branch (offset 79-80 in that excerpt) precedes the `HEALTHY` return (offset 175) — a dead session structurally cannot reach the `HEALTHY`/workspace-summary line, independently confirming the PR's answer to the issue's must-not ("must not report a session as ... running when it is dead").

derived: `grep -n "class \|def test_" test/test_workspace_progress_tracking.py` run in `/tmp/verify-2904`, this session — confirms the specific test names the PR's record cites for its most load-bearing claims actually exist: `test_record_file_touch_is_named_as_started`, `test_dead_pid_never_gets_a_running_workspace_summary`, `DeltaSuppressionForWorkspaceProgressTest::test_unchanged_workspace_progress_line_suppressed_next_tick` / `test_new_file_touched_reemits_the_changed_line`, `LastToolActivitySummaryTest::test_unchanged_log_produces_byte_identical_text_not_a_ticking_age` / `test_investigating_vs_stalled_distinguished_by_a_new_tool_call`.

## Why

The approach here mirrors the prior independent-verification precedent for this repo (`fa52c0c8:docs/issue-2893/reports/independent-verification-1.md`, PR #2901): re-derive every numeric claim independently rather than trust the PR body, and separately read the actual code paths the PR's prose describes (line numbers, gate conditions, regex membership) rather than accepting the prose's description of them. canonical: the "Re-derived numeric claims" and "Code-level verification" subsections above, this session's own `derived:`/`canonical:` tags — both layers came back matching the PR's claims, no discrepancy found.

### Acceptance criteria — the mechanism checks out; the issue's own `provenance: executed-live` tag is not met by what the PR ships

The issue's Acceptance section tags every one of its four checks `provenance: executed-live`: (1) spawn a session, let it finish, show the orchestrator-visible signal; (2) on a running session with no commit, show what mid-flight tracking reports; (3) session-end timestamp versus signal timestamp; (4) demonstrate on a fresh orchestrator context that did not ask for it.

derived: `git show 3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md | grep -n live` run in `/tmp/verify-2904`, this session — every match is either the operator's own **pre-fix** live check quoted from the two issue comments (used as the failure-mode description the fix targets, not as evidence the fix works) or the phrase "live roster entry"/"live session" used descriptively inside code-reading prose. derived: `git diff --stat fa52c0c8 3a65f414` run in `/tmp/verify-2904`, this session — result: 7 files changed (the record, a deviation log, a product-priorities note, `spawn.py`, `watchdog.py`, and the two test files); no transcript file, no timing log, no orchestrator-context capture appears anywhere in that changed-file list. No section of the record and no file in the diff contains an actual post-fix spawn-a-session-and-observe run, an end-to-end timestamp delta, or a demonstration against a context that never asked for the check.

This is a gap in the acceptance section as literally written, not a correctness defect in the shipped mechanism — the "Code-level verification" subsection above independently confirms the mechanism does what the record claims (drain-before-early-return placement, `ALWAYS_RE` membership, dead-pid gating, absolute-timestamp delta-suppression), each traced to its own `canonical:`/`derived:`-tagged file:line location this session read directly. The unit-test coverage this session re-ran (see "Re-derived numeric claims" above, each figure matching the PR's own numbers) is real, but it substitutes for, rather than satisfies, the issue's specific "spawn it for real and watch it happen" bar. This review is a read-only audit of an already-landed PR; spawning a new live session to close this gap itself would consume the resources the check is meant to observe, so this session did not attempt it — flagged below as an open finding with a resolution path instead.

## What did not work

None in this verification session's own process — the worktree checkout, diff read, and all `derived:`/`canonical:` re-derivations above in "What was done" succeeded on the first attempt.

## Upstream basis

- PR #2905 (`issue-2904/silent-failure-audit-efd0df1c`, tip `3a65f414`) — the deliverable under review; full diff read via `gh pr diff 2905`, this session.
- `3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md` — the subject's own implementation record, read in full and checked claim-by-claim above.
- `gh issue view 2904 --repo tokenmaxxxer/on-the-record` — the issue's own acceptance criteria, quoted verbatim in "Why" above.

## Open findings

- **Acceptance provenance gap**: all four of the issue's acceptance checks are tagged `provenance: executed-live`; the PR ships unit-test and code-reading evidence for the underlying mechanism (independently re-confirmed correct by this session — see "Code-level verification" in "What was done") but no post-fix live spawn-and-observe run, no measured end-to-end session-end-to-signal timestamp delta, and no demonstration against a context that did not ask for it (derived: `git show 3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md | grep -n live` and `git diff --stat fa52c0c8 3a65f414`, both this session, cited in "Why" above). Resolution path: a follow-up session could spawn one real session through `spawn.py`, let it finish, and capture the `[poll-report] ...: COMPLETED` line plus a wall-clock delta from session end to that line's emission — closing this without touching the already-verified mechanism itself.
- No correctness defect found in the shipped mechanism itself — see "Code-level verification" in "What was done" above for the specific `sha:file:line` locations and gate conditions independently traced (drain-before-`if not d:` placement, `ALWAYS_RE` membership for `COMPLETED`, the `-uall` fix, the dead-pid-never-`HEALTHY` gate, absolute-vs-relative timestamp choice).

## Next steps

None further from this role; `loop_state: landed` (see frontmatter). Whether to open a follow-up closing the live-provenance gap above is a decision for the subject's own author or a future session, not this verification record.
