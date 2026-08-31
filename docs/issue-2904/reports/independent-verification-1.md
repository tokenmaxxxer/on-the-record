---
issue: 2904
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: 3a65f414:spawn.py, 3a65f414:watchdog.py, 3a65f414:test/test_session_completion_heartbeat.py, 3a65f414:test/test_workspace_progress_tracking.py
type: verification-record
breaking: false
verdict: mechanism-confirmed-live, one-residual-crash-window-gap, two-of-four-acceptance-checks-still-lack-executed-live-evidence
loop_state: landed
upstream:
  - path: PR #2905 (issue-2904/silent-failure-audit-efd0df1c)
    sha: 3a65f414ac087b93e5f64cec8726e931cbe9987e
  - path: 3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md
    sha: 3a65f414ac087b93e5f64cec8726e931cbe9987e
skill-verdict: work-in-english — applied: invoked; loaded the SKILL.md via the Skill tool before writing this record. This record, all commands, and the PR/commit text are in English; only the final chat summary to the user is in Korean.
other mounted skills: not triggered — read-only audit-and-record task (checkout a branch, re-run existing tests, construct live reproductions, read a diff); no multi-module decomposition, no growth/JTBD framing question, no prior-art search, and freelunch's fan-out threshold (width >= 2 units, ~100+ lines each) does not apply to a single-branch audit.
---

# issue-2904 — independent-verification-1 record

amendments-reconciled: issuecomment-5472536977 — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5472536977`, read this session after `pr-preflight`'s hook flagged it as posted mid-session. The comment asks both spawned verifications to go beyond re-deriving the subject's own claims: (1) attack the root-cause claim from source and by constructing the failure live, including the converse -- does the durable queue survive a process dying between recording and draining; (2) construct all three of working/investigating/stalled live and confirm no two read identically; (3) measure per-tick cost at 0/1/8 sessions and confirm the transcript read does not re-scan from the top as logs grow; (4) verify the absolute-timestamp line actually survives delta-suppression across consecutive identical ticks; (5) four standing invariants each with a command and its output, including an enumeration of every pre-existing watchdog signal still emitting. All five are addressed below with fresh, non-mocked reproductions built by this session, superseding the code-read-only pass from before this comment landed.

## What was done

canonical: `gh issue view 2904` (full body plus 4 comments, including the two mid-flight direction corrections, the session-end comment, and the round-2 verification-scope comment) and `gh pr view 2905 --json title,body,files,commits,additions,deletions,mergeable,baseRefName,headRefName` -- read before checking out the branch.

Fetched PR #2905 (`issue-2904/silent-failure-audit-efd0df1c`, tip `3a65f414`) into isolated worktrees and read the full diff against `origin/main` (`git diff origin/main...pr-2905 -- spawn.py watchdog.py`, 277 lines) end to end, plus both new test files (`3a65f414:test/test_session_completion_heartbeat.py`, `3a65f414:test/test_workspace_progress_tracking.py`) and the subject's own record (`3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md`, its deviation log, and the product-priorities entry it appended).

### 1. Numeric claims, re-run rather than trusted

1. New tests -- derived: `python3 -m pytest test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q` on `3a65f414` -- result:
```
21 passed
```
Matches the PR body's own count exactly.
2. Watchdog-adjacent regression set -- derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_reconcile_crash_verdict_race.py on-the-record/monitors/test_poll_heartbeat.py test/test_unrecovered_commit_count.py test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q` on `3a65f414` -- result:
```
74 passed
```
Matches the PR body's own count exactly.
3. Full suite, no new bug (invariant) -- derived: `python3 -m pytest . -q` on `3a65f414` -- result:
```
17 failed, 686 passed, 3 xfailed
```
Re-ran the identical command against `origin/main` (`fa52c0c8`) -- result:
```
17 failed, 665 passed, 3 xfailed
```
Diffing the two sorted 17-name FAILED lists shows zero name-set difference -- every failure on both sides is the same pre-existing, network/sandbox-shaped case (e.g. `fatal: 'origin' does not appear to be a git repository`, and `tests/test_spawn_gate_wiring.py`'s `HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present`), unrelated to this change. `686 - 665 = 21`, matching the 21 new tests counted in step 1.
4. Retirement-count invariant (no return of the retired role axis) -- derived: `python3 gates/retirement_count.py` on both `3a65f414` and `fa52c0c8`, output byte-compared -- identical, no new `role`/`roles` token.

### 2. Root-cause claim, attacked from source and by live construction

Read the exact ordering in `3a65f414:spawn.py`, not the record's prose description of it: `roster_remove(roster_key)` executes inside a `finally` block ending at line 4793; the new `_record_session_completion(...)` call is 107 lines later (line ~4907), after `fail_closed_downgrade()`, a `ledger_write()`, several `print()`s, and two more subprocess calls (`git rev-parse --abbrev-ref HEAD`, `_pr_open_or_merged_for_branch()`). Quoted verbatim from `3a65f414:spawn.py`:
```
        roster_remove(roster_key)
    finally:
```
```
    sid = f" (session {result.get('session_id')})" if result.get("session_id") else ""
    if issue is not None:
        completion_branch = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True).stdout.strip()
        completion_pr = (_pr_open_or_merged_for_branch(Path(cwd), completion_branch)
                         if completion_branch else None)
        _record_session_completion(roster_key, issue, skill,
                                   result.get("session_id"), completion_pr, outcome)
```
This confirms the record's own root-cause narrative (a normally-exiting session's roster entry is gone before the next `roster_watchdog()` tick, so the old dead-scan `COMPLETED` line structurally cannot fire on the clean-exit path) as a fact about control flow, verifiable from the source without running anything.

**The converse the operator asked for -- does the queue survive a process dying between recording and draining?** Yes, and this is not the risky direction: `_record_session_completion()`'s write path (`with PENDING_COMPLETIONS.open("a") as out: out.write(...)`, inside a `with open(lock_path) ...: flock/write/funlock`) returns only after the write is flushed and the file handle is closed -- the entry is durably on disk before the function returns, independent of whether the writing process later exits or crashes. derived: confirmed this by writing a completion in one Python process, then draining it from a second, wholly separate Python process invocation:
```
$ python3 -c "import sys; sys.path.insert(0,'.'); import spawn; spawn.PENDING_COMPLETIONS=__import__('pathlib').Path('/tmp/pc-durability-test.jsonl'); spawn._record_session_completion('issue-2904/x', 2904, 'demo', 'sess-1', 2905, 'progressed')"
$ python3 -c "import sys; sys.path.insert(0,'.'); import spawn; spawn.PENDING_COMPLETIONS=__import__('pathlib').Path('/tmp/pc-durability-test.jsonl'); print(spawn._drain_pending_completions())"
([{'key': 'issue-2904/x', 'issue': 2904, 'skill': 'demo', 'session_id': 'sess-1', 'pr_number': 2905, 'outcome': 'progressed', 'ts': ...}], None)
```
Two fully separate process invocations, the first long exited before the second starts -- the entry survived. This direction of the converse holds up.

**The other direction -- a process dying between `roster_remove()` and reaching `_record_session_completion()` -- is a real, narrower residual gap.** If the process running `_spawn_one()` (the orchestrator's own wrapper around the finished child session, not the child session's own process, which has already fully exited via `proc.wait()` by this point) is itself killed somewhere in that ~107-line window, the roster entry is already gone (so the old dead-scan path cannot see it either) and the queue was never written -- the completion signal is lost by both the old and new mechanisms. This is real and the subject's record does not mention it. It is not, however, an equally-sized blind spot merely relocated: before this PR, every clean exit (the entire common path) missed the signal; after this PR, only a wrapper-process crash inside this specific ~107-line window misses it -- a categorically rarer failure (the orchestrating process itself dying mid-tail, not the long-running agentic session dying) and a much narrower window. Logged as an open finding below rather than closed in this verification-only session; a straightforward mitigation -- move the completion-queue write to immediately follow `roster_remove()`, ahead of the more expensive board-delta/PR-lookup work -- is a one-line reordering a follow-up round could make.

### 3. The tri-state, constructed live with the real functions, no mocks

canonical: this session's own three live `watchdog.diagnose_health()`/`spawn.watchdog_check_one()` calls (not the existing test suite's mocked scenarios), built against three real temp-git-repo sessions:

- **Working**: workspace has `spawn.py` dirty, transcript log's last line is an `Edit` tool call at `09:00:00 UTC`.
- **Investigating**: identical dirty-file set to "working" (so `git status` output is byte-identical -- the exact case the operator's own comment names as the one that produced a wrong read on this issue's own earlier live check), but a new `Bash pytest ...` tool call appended to the log at `09:01:30 UTC`.
- **Stalled**: identical dirty-file set again, log mtime pushed back past `WATCHDOG_SILENCE_MIN` (90 minutes, `3a65f414:watchdog.py` line 99) and run through the real `spawn.watchdog_check_one()` (not a synthetic anomalies list) to compute the actual `log-silence` anomaly string, which is then supplied to `diagnose_health()`.

derived: three calls made this session, live, against the real functions, output:
```
working:       HEALTHY | ...RUNNING -- 손댄 파일 1건: spawn.py, 기록 아직 없음; 마지막 도구 호출: Edit spawn.py (09:00:00 UTC)
investigating: HEALTHY | ...RUNNING -- 손댄 파일 1건: spawn.py, 기록 아직 없음; 마지막 도구 호출: Bash python3 -m pytest test/x.py (09:01:30 UTC)
stalled:       STALLED | issue-2904/demo: idle > 90분, RUNNING
```
canonical: the three output strings above, this session's own run -- all three differ from each other pairwise. Working and investigating differ solely in the tool-activity clause despite an identical file-diff clause -- the exact discrimination the operator's comment asked for ("if any two of the three still read the same, the defect is intact"). Stalled excludes both the workspace and tool-activity text entirely, routed away from the HEALTHY branch by the pre-existing alive/anomaly-based branching that this PR left unmodified -- the source-of-truth separation holds up as a live behavior, not only as a claim in the subject's record.

### 4. Per-tick cost, measured at 0/1/8 sessions and across log sizes

derived: live timing via `timeit`, 20 iterations per point, real temp-git-repo sessions with real 5MB synthetic transcript logs each, output:
```
sessions=0, no entries to check: 0.00 ms/tick
sessions=1, 5MB log each:        27.40 ms/tick  (27.40 ms/session)
sessions=8, 5MB log each:       159.15 ms/tick  (19.89 ms/session)
```
A quiet tick with nothing registered costs nothing extra (0.00 ms), consistent with the must-not on overhead growth when nothing changed. Per-session cost stays roughly flat as the fleet grows from 1 to 8 -- no super-linear blowup from checking more sessions in one tick.

Whether the transcript read re-scans from the top as logs grow -- derived: same `diagnose_health()` call against a single session, log size varied 1MB -> 20MB -> 100MB by padding with filler JSONL lines ahead of the final real tool-call line, output:
```
log ~1MB:   25.83 ms/call  (file bytes: 1,048,734)
log ~20MB:  10.35 ms/call  (file bytes: 20,971,659)
log ~100MB: 11.91 ms/call  (file bytes: 104,857,659)
```
Cost stays flat as file size grows two orders of magnitude, confirmed empirically rather than only by reading the `fh.seek(max(0, size - 65536))` line in `3a65f414:watchdog.py`. One precision note for the subject's own record: `_last_tool_activity_summary()`'s bounded cost comes from its own independent last-64KB tail-read, not from reusing `watchdog_check_one()`'s offset-tracked incremental scan state (that scan advances a persisted `offset` per key across ticks; `_last_tool_activity_summary()` re-seeks from `size - 65536` fresh on every call, unrelated to that offset). The subject's record's phrasing ("the exact same file `watchdog_check_one()` already scans incrementally... no new file") is literally true about file identity but could be read as implying the read method itself is shared, which it is not -- the two functions read the same file by two independent mechanisms that both happen to be bounded-cost.

### 5. Absolute-timestamp / delta-suppression, verified live through the real script

derived: four consecutive calls into `on-the-record/monitors/poll_heartbeat_delta.py` itself, not the unit test's assertions about it, output:
```
tick1 (first sight, t=1000):            emits the full [poll-report] line
tick2 (identical text, t=1010):         '' (suppressed)
tick3 (identical text again, t=1020):   '' (suppressed)
tick4 (tool call changed, t=1030):      emits the changed line (new tool + new timestamp)
```
canonical: the four outputs above, this session's own run -- the absolute-timestamp design holds up across multiple consecutive identical ticks, not merely one, and does not turn an idle-but-HEALTHY session noisy, the reverse failure the operator's comment named as a real risk.

### 6. Every pre-existing watchdog signal, enumerated and checked for survival

derived: `grep -oE '"\[[a-z-]+\]' watchdog.py spawn.py | sort -u` on `3a65f414` vs. the same command on `origin/main` (`fa52c0c8`) -- the "after" tag set is exactly the "before" 14-tag set (`checkpoint`, `consult`, `drive`, `health`, `orphaned`, `poll-report`, `rebase`, `reconcile-poll-disagreement`, `reconcile`, `resume`, `spawn-attempt`, `spawn`, `standing-red`, `watchdog`) plus exactly one new tag (`poll-report-drain-failed`). derived: `git diff origin/main...3a65f414 -- watchdog.py` shows only 2 line deletions in the whole file, both in-place edits to existing lines rather than removals (the static HEALTHY detail string becomes an f-string with the new summaries folded in; `anomaly_count = ...` becomes `anomaly_count += ...` to add the drain-failure count on top of the pre-existing computation rather than replacing it) -- no existing print statement or anomaly condition was removed or narrowed.

## Why

derived: this section's assessment of each acceptance check is based directly on the six live reproductions in "What was done" 1-6 above (durability-across-processes test, tri-state construction, cost measurements, delta-suppression run, and the tag-set diff), not on the subject's own description of its work.

The subject's own record cites `provenance: executed-live` against all four of the issue's acceptance checks. Following the round-2 verification directive (above), the deeper checks in "What was done" 2-6 replace what was originally a code-read-only pass in this record and substantially narrow, though do not fully close, the remaining gap:

- **Check 1** ("spawn a session, let it finish, and show the orchestrator-visible signal naming the issue, the session, and its PR") -- this session confirmed the mechanism live end to end (write in one process, drain in a fully separate process, "What was done" 2) and confirmed the root-cause claim from source rather than the record's assertion of it. Still missing is a demonstration through the actual `poll-heartbeat.sh` Monitor loop with a real spawned agent session, as distinct from this session's own direct calls into `spawn`/`watchdog`'s Python functions -- spawning and waiting out a full agent session purely to observe this one signal was judged out of proportion to a review task and is left as an open item rather than attempted partially.
- **Check 2** ("on a running session with no commit, show what the tracking reports") -- the tri-state construction in "What was done" 3 covers this directly and live, including the specific "investigating" case the operator's comment names. Adequately demonstrated by this round for the workspace/tool-activity content itself; what remains unverified is its appearance inside a real Monitor-loop tick, the same gap as check 1.
- **Check 3** ("session end timestamp versus signal timestamp") -- still has no measurement in the PR, its tests, or its record, and this session did not construct one either, since it needs the same live `poll-heartbeat.sh` cadence context as check 1. Still open.
- **Check 4** ("demonstrate on a fresh orchestrator context that did not ask for it") -- still has no demonstration anywhere. Still open.

The residual crash-window finding from "What was done" 2 (a wrapper-process death between `roster_remove()` and the completion-queue write) is new this round; the subject's record does not mention it at all. Smaller in scope than the defect the issue reports, but real, and worth a follow-up round closing (e.g. by reordering the two calls to shrink the window).

## What did not work

None -- every reproduction attempted in this session (durability across processes, tri-state construction, cost measurement at three fleet sizes and three log sizes, delta-suppression across four ticks, signal-set enumeration) succeeded on the first attempt and produced the results quoted above.

## Upstream basis

- `3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md` (PR #2905's own record) -- read in full; its "What was done"/"Verification" sections are the claims independently re-derived above.
- PR #2905 diff (`spawn.py`, `watchdog.py`, `3a65f414:test/test_session_completion_heartbeat.py`, `3a65f414:test/test_workspace_progress_tracking.py`) at sha `3a65f414ac087b93e5f64cec8726e931cbe9987e`.
- issuecomment-5472536977 (round-2 verification-scope directive), reconciled above.

## Open findings

derived: `git log --all --diff-filter=A --name-only -- 'docs/issue-2904/reports/*'` -- confirms `3a65f414:docs/issue-2904/reports/silent-failure-audit-efd0df1c.md` is the only deliverable record for this subject as of this session; no follow-up round has yet addressed any finding below.

1. A wrapper-process crash between `roster_remove()` and the `_record_session_completion()` call (spawn.py, the ~107-line window quoted in "What was done" 2) loses the completion signal on both the old dead-scan path and the new queue path. Real but narrower than the defect this issue reports (requires the orchestrator's own wrapper process to die mid-tail, not the spawned session). Resolution path: reorder the completion-queue write to run immediately after `roster_remove()`, before the board-delta/ledger/PR-lookup computation, shrinking the window to a few lines.
2. Acceptance checks 3 ("session end timestamp versus signal timestamp") and 4 ("demonstrate on a fresh orchestrator context that did not ask for it") still have no evidence anywhere, despite both being tagged `provenance: executed-live` in the issue body. Resolution path: a follow-up round should either produce the missing live demonstrations through the real `poll-heartbeat.sh` Monitor loop with a real spawned session, or the operator should explicitly accept the evidence gathered so far as sufficient and say so.
3. Checks 1 and 2 are now confirmed live at the function level (this record, "What was done" 2-3) but not yet through an actual `poll-heartbeat.sh` Monitor-loop tick observing a real spawned session end to end. Resolution path: same as finding 2.

## Next steps

None -- `loop_state: landed`. The findings above are handed off via this record's Open findings, not further work in this session.
