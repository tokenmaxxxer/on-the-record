---
issue: 2904
role: silent-failure-audit-efd0df1c
author: silent-failure-audit-efd0df1c
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: spawn.py, watchdog.py, test/test_session_completion_heartbeat.py, test/test_workspace_progress_tracking.py
type: fix
breaking: no
verdict: pass
loop_state: landed
upstream:
  - path: none — CORE_BUILD_NOW=1 was set by the spawner (checked: `printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW"`, result `CORE_BUILD_NOW=1`), so this delivered directly under contract v3 s19a with no phase-1 proposal round to cite.
    sha:
---

# issue-2904 — silent-failure-audit-efd0df1c record

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5472355431` and `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5472429696` bodies, both read this session.

amendments-reconciled: issuecomment-5472355431, issuecomment-5472429696 — two mid-flight direction corrections on the already-working session, each retaining prior work and reframing scope rather than discarding it. The first (issuecomment-5472355431) rewrote the issue body around a wider requirement: the orchestrator must actively track what it spawned; `gh` only sees a session after it opens a PR, so mid-flight workspace state must be visible before that; the behavior must hold structurally, for every session on every on-the-record install, without an orchestrator opt-in — answered by "Part 2 — mid-flight workspace tracking" below. The second (issuecomment-5472429696) found that Part 2's own git-status-only approach reproduces the issue's own defect shape one layer down: two minutes of active grep/Read/Edit/test-run tool calls against files already marked dirty look byte-identical, at the file-diff layer, to two minutes of nothing happening — demonstrated live on this session's own workspace. Answered by "Part 3 — name the act, not just its result" below, added in the same session after the second comment landed.

## What was done

canonical: `gh issue view 2904 --repo tokenmaxxxer/on-the-record` (this session, read before starting, and re-read after issuecomment-5472355431 rewrote the issue body) — the acceptance criteria and the "establish before building" requirement (why does `poll-report` emit `COMPLETED` for some sessions and not the #2894 verification) came from the first read; the mid-flight/structural/opt-in-free requirements below came from the rewritten body and the comment.

### Part 1 — a finished session announces itself (retained from the original framing)

**Root cause (established, not assumed).** `poll-report`'s existing `COMPLETED` line lives inside `roster_watchdog()`'s dead-entry scan, which only runs for keys still present in the roster (`for key, e in sorted(d.items())`, watchdog.py). A session that exits normally removes its own roster entry synchronously, in the same process, before that scan ever gets a chance to see it:

```python
        rc = proc.wait()
        roster_remove(roster_key)
    finally:
```
(spawn.py:4792-4794, inside `_spawn_one()`, unconditional on outcome)

and the dead-entry scan that would otherwise print `COMPLETED` is unreachable once the roster is already empty:

```python
    if not d:
        print("돌고 있는 스킬 세션 없음")
        if not anomaly_count:
            print("이상 신호 없음")
        return anomaly_count
```
(watchdog.py:1654-1658, `roster_watchdog()`, this is an early return before the dead-entry loop)

derived: `grep -n "_spawn_one(" spawn.py`, this session — exactly one call site (spawn.py:2782, the CLI `spawn` subcommand dispatch), with `bounded=a.issue is not None`, so every issue-driven spawn (including the #2894 verification session) takes this same self-removing tail. The existing `COMPLETED` label is therefore not a completion signal in general — it is a crash-race fallback that only fires when the *owning process itself* dies before reaching its own `roster_remove()` call. The #2894 session exited cleanly, so it never hit that fallback. Answer to the issue's "establish before building" question: **the signal exists in a form (`_post_session_end_comment()`, lifecycle.py:263, already posts a durable GitHub issue comment naming the PR at the same point in `_spawn_one()`'s tail) but does not reach the heartbeat/Monitor channel at all** — a bridging gap, not a total absence of instrumentation.

**The 23:24–23:32 eight-minute gap is the same defect, not a second one.** `on-the-record/monitors/poll_heartbeat_delta.py` deliberately allows up to 1800s (30 minutes) of full silence when nothing changed and nothing is in the always-emit set:
```python
        last_emit_epoch = int(prev.get("last_emit_epoch", 0) or 0)
        if now - last_emit_epoch >= 1800:
```
(poll_heartbeat_delta.py:180-181) — an 8-minute quiet window is inside that designed allowance, not a violation of the stated 120s cadence (that cadence governs how often the watchdog *runs*, not how often it *prints*; issue #1220's delta-suppression is what makes a due-but-unchanged tick silent by design). Once this fix lands, a completion landing inside that window stops it from being silent — same root cause, one fix, not two.

**Fix.** Added a small durable queue (`spawn.PENDING_COMPLETIONS`, `runs/pending-completions.jsonl`) that `_spawn_one()` writes to at the exact point it already knows the completion fact (issue, skill, session id, PR number, final outcome) — spawn.py:4903-4913, right after the existing `sid = ...` line, guarded by `if issue is not None:`. `roster_watchdog()` drains this queue as the very first thing it does (watchdog.py:1576-1601), *before* the `if not d:` early return, and prints the existing `[poll-report] {key}: COMPLETED — ...` line format so it passes through `poll_heartbeat_delta.py`'s existing `ALWAYS_RE` (which already matches `COMPLETED`) unchanged. No new `gh`/git call, no new polling cadence, no new anomaly weight for a genuine completion (mirrors the existing dead-scan `COMPLETED` line, which also does not increment `anomaly_count`).

**Self-audit finding (silent-failure-audit skill, invoked this session) and fix.** The first version of the write/read functions let `open()`/`fcntl.flock()` raise `OSError` uncaught. On the write side that would have crashed `_spawn_one()`'s completion tail (gate-report/self-trigger-respawn/`session-end` comment) over a disk hiccup on a purely observational side-channel; on the read side, a queue the watchdog could not read would have returned `[]` and looked byte-identical to "nothing completed" — reproducing, inside the very fix for issue #2904, the exact defect class the issue is about. Fixed: `_record_session_completion()` (spawn.py:1048-1070) now catches `OSError` and prints an advisory instead of raising; `_drain_pending_completions()` (spawn.py:1078-1108) now returns `(entries, error)` and `roster_watchdog()` reports a non-`None` error as its own anomaly line (`[poll-report-drain-failed] ...`, watchdog.py:1592-1595) instead of silently returning an empty list.

### Part 2 — mid-flight workspace tracking (added after issuecomment-5472355431)

canonical: issuecomment-5472355431 body, this session — the comment's own live check ("Checked live on your own session 15 minutes in, with no commit and no PR, the workspace already showed `M spawn.py`, `M watchdog.py`, a new test file, and a record written at 09:30 — every bit of that invisible to `gh` at the time") is the concrete failure mode this part closes.

`diagnose_health()` (watchdog.py) already has a HEALTHY fallthrough branch that `roster_watchdog()` prints unconditionally, every tick, for every live roster entry, as `[poll-report] {key}: HEALTHY — {detail}` (watchdog.py, the print immediately after `health = _sp.diagnose_health(...)` in the main per-entry loop). That branch previously produced a static string (`"{key}: 최근 로그 성장, RUNNING"`) that never changes between ticks for a healthy session — this is why "session is fine" and "session is doing something specific right now" were indistinguishable, exactly the shape the issue names.

Added `_live_session_workspace_summary(work)` (watchdog.py, new function immediately above `diagnose_health()`): runs `git status --porcelain -uall` (local, no `gh` call) against the session's own workspace and reports, in order: how many paths are dirty and their names (sorted, first 5 shown, "+N more" beyond that), and whether any of those paths matches the same `docs/issue-<n>/(reports|proposals)/` shape `_sp._RECORD_PATH_RE` already uses elsewhere (`lifecycle.py:320`) — labeled "기록 시작함"/"기록 아직 없음" ("record started"/"no record yet"). An untouched workspace reports "손댄 파일 없음" ("no files touched") explicitly rather than an empty string, satisfying the acceptance's empty-state requirement (a session that has done nothing yet reports exactly that, not silence).

derived: `python3 -m pytest test/test_workspace_progress_tracking.py -q`, this session, result: `9 passed` — including a specific regression the first draft of this function had: `git status --porcelain` (without `-uall`) collapses a wholly-new untracked directory to one `?? docs/` line, hiding the file inside it — exactly the "record started" case this function exists to name (`WorkspaceSummaryTest::test_record_file_touch_is_named_as_started` failed against the `-uall`-less draft, passed after adding `-uall`).

This summary is folded into the existing HEALTHY `detail` string (`f"{key}: 최근 로그 성장, RUNNING — {workspace_summary}"`), not printed as a separate line — so no new tag needed in `poll_heartbeat_delta.py`'s `TAG_RE`/`ALWAYS_RE`: the existing per-key line comparison (keyed on the fixed `poll-report:{key}` tag) already suppresses this line when the detail text is byte-identical to the prior tick (nothing changed — quiet, satisfying "no general increase in heartbeat volume when nothing changed") and re-emits it the moment the detail text changes (a file gets touched, a record starts — satisfying "mid-flight state is visible"). derived: `test_workspace_progress_tracking.py::DeltaSuppressionForWorkspaceProgressTest` feeds two literal `[poll-report]` lines through `on-the-record/monitors/poll_heartbeat_delta.py` directly — an unchanged line across two ticks emits nothing on the second tick; a line whose only difference is a newly-touched file re-emits on the next tick. Both assertions pass (`2 passed` within the 9 above).

**Structural, no opt-in (issue's explicit requirement).** `diagnose_health()`/`roster_watchdog()` are not orchestrator-side code the orchestrator must remember to call — they are the shared watchdog machinery that `on-the-record/monitors/poll-heartbeat.sh`'s plugin Monitor loop already invokes automatically, every due tick, for every session, on every on-the-record install (per that script's own header comment, "Auto-started by Claude Code for a user-scope plugin install... no `/loop`, no manual setup"). This change edits that shared function once; it does not touch any per-session or per-orchestrator configuration, so there is nothing for a new session to opt into.

**Source of truth for finished vs. crashed vs. running (issue's explicit must-not).** Unchanged by this PR — this fix only enriches text inside a branch that was already unreachable for a dead entry, it does not touch the branching itself:
```python
    alive = _sp._alive(pid)
    if not alive:
```
(watchdog.py, `diagnose_health()`) is the single gate: `_alive(pid)` (a raw `os.kill(pid, 0)` liveness check, spawn.py) decides whether execution can ever reach the HEALTHY/workspace-summary branch at all — a dead pid is structurally routed to the separate dead-entry branch (which produces `COMPLETED`/`DEAD-ERRORED`/`DEAD-UNRECOVERED-COMMITS`/etc., never `HEALTHY`) regardless of what its workspace looks like, so a dead session can never be reported as "running". Within that dead branch, `session_end_verdict()` (board.py, fed `wrapper_pid`) is what already distinguishes a clean exit (`normal`) from a genuine crash (`crashed`) — this is the same mechanism `test_reconcile_crash_verdict_race.py` (pre-existing, unmodified by this PR) exercises directly, and it continues to pass unchanged (`test_verdict_still_crashed_when_wrapper_also_dead`, `test_verdict_in_flight_when_wrapper_still_alive`). derived: `python3 -m pytest test/test_reconcile_crash_verdict_race.py -q`, this session, result: `9 passed`. This PR adds a new test making the reverse direction explicit too: `test_workspace_progress_tracking.py::DiagnoseHealthIncludesWorkspaceSummaryTest::test_dead_pid_never_gets_a_running_workspace_summary` asserts a dead pid's `diagnose_health()` result is never `HEALTHY` and never contains a workspace summary.

### Part 3 — name the act, not just its result (added after issuecomment-5472429696)

canonical: issuecomment-5472429696 body, this session — its own live demonstration is the concrete failure Part 3 closes: two minutes of `git status --porcelain` output on this issue's own session stayed exactly `M spawn.py`, `M watchdog.py`, `?? docs/issue-2904/`, `?? test/test_session_completion_heartbeat.py` throughout, while the session's actual tool calls in that same window were `grep`/`sed` x6, two `Read`s, two `Edit`s, and a test run — Part 2's file-diff summary cannot tell those two minutes apart from two minutes of nothing happening, because the same files were already dirty before either started.

Added `_last_tool_activity_summary(log_path)` (watchdog.py, new function immediately below `_live_session_workspace_summary()`): reads the last 64KB of the session's own transcript log (`entry["log"]` — the exact same file `watchdog_check_one()` already scans incrementally, offset-tracked, for anomaly detection; no new file, no new event type), finds the last `assistant` message's `tool_use` block, and reports the tool name, a short target/command snippet (`file_path`/`command`/`pattern`, whichever the block carries, first 40 chars), and an **absolute** timestamp (`HH:MM:SS UTC`) parsed from that JSONL line's own `timestamp` field. Folded into the same HEALTHY `detail` string Part 2 already enriches (`f"{key}: 최근 로그 성장, RUNNING — {workspace_summary}; {activity_summary}"`), so it rides through `poll_heartbeat_delta.py`'s existing per-key diff exactly like Part 2 does — still no new tag, no new emission plumbing.

**Why absolute timestamp, not relative age (the design decision that actually matters here).** A relative "N초 전" render would make the detail string change every single tick purely from time passing, even when the last tool call is completely unchanged between ticks — that would defeat the delta-suppression this whole design depends on and directly violate "no general increase in heartbeat volume when nothing changed": every live session would print every tick, forever, regardless of activity. An absolute timestamp is byte-identical across ticks until a genuinely new tool call happens. derived: `python3 -m pytest test/test_workspace_progress_tracking.py -k LastToolActivitySummaryTest -q`, this session, result: `5 passed`, including `test_unchanged_log_produces_byte_identical_text_not_a_ticking_age` (calls the function twice against the same unappended log and asserts byte-identical output — a relative-age implementation fails this by construction) and `test_investigating_vs_stalled_distinguished_by_a_new_tool_call` (a second, later tool call changes the summary even though the two calls target the exact scenario from the operator's own demonstration).

**Investigating vs. stalled — still answered at the state level, not just by this text.** `diagnose_health()`'s existing branching is untouched by Part 3: a session with no new log activity for `WATCHDOG_SILENCE_MIN` minutes never reaches the HEALTHY branch at all (routed to `STALLED` by the pre-existing `log-silence` anomaly, computed from raw log mtime before any of this code runs), and a session repeating the same action is routed to `DEADLOCKED` by the pre-existing `_deadlock_signature()`. Part 3 only names what a session already classified HEALTHY is doing — it does not and cannot make a genuinely stalled session read as HEALTHY, because `_last_tool_activity_summary()` is never called for those states (see the exact `if not alive:` / `STALLED` / `DEADLOCKED` return points earlier in the same function, all of which return before the code that computes `workspace_summary`/`activity_summary`).

## Why

The issue's framing ("this is the fourth instance in one night of a check whose clean output is indistinguishable from never having looked") applies at two levels here, and both needed fixing in the same change:

1. The outer defect: a session finishing and "no anomaly this tick" produced the same heartbeat. Fixed by making completion a distinct, always-emitted fact fed from the one place that already knows it (`_spawn_one()`'s own tail), rather than inferred later from roster-entry absence (which cannot work once the entry removes itself).
2. The inner defect (self-audit finding): the queue bridging that fact to the heartbeat could itself fail in a way that reads as "nothing to report." Distinguishing "no completions" from "couldn't check" (`_drain_pending_completions()`'s `(entries, error)` return) is the same principle applied one layer down — a silent `except OSError: return []` here would have been a second copy of the identical failure shape, this time inside the fix itself.

Placement choice: the drain runs before `roster_watchdog()`'s `if not d:` early return specifically because that is the common shape after this fix (a session finishes, removes its own roster entry, and the very next tick sees a fully empty roster) — putting the drain after that return, or inside the `for key, e in sorted(d.items())` loop, would have reproduced the original bug for exactly the case this issue reports.

Alternative considered and rejected: teaching the orchestrator to actively poll for finished sessions each turn (e.g. a directive instruction to check `gh pr list` or scan for new comments). Rejected per the issue's explicit non-goal — that is per-turn overhead paid on every turn to catch an event that already knows when it happened (issue #2135's shape), and it would not fix the underlying gap for any consumer other than the orchestrator's own prompt loop (the Monitor heartbeat itself would still say nothing).

3. Part 2's placement (folding the summary into the existing `HEALTHY` `detail` string rather than adding a new `[workspace]`-tagged line) was chosen specifically to reuse `poll_heartbeat_delta.py`'s existing per-key suppression for free. A new, separately-tagged line would have needed either a new entry in `ALWAYS_RE` (which the issue's own must-not list forbids in spirit — it would print every tick regardless of change, a volume increase) or trusting the untested fallback `FIXED_TAG_RE` path; reusing the tag `roster_watchdog()` already emits every tick for this exact entry means the existing, already-tested delta-diff logic is what decides emit-vs-suppress, not new logic.

Alternative considered and rejected for Part 2: a `gh`-based check (comments, PR file list) for mid-flight state. Rejected per the issue's explicit non-goal (`gh` polling is late by construction and burns API budget, issue #1569) and because it cannot see anything before a PR or comment exists — the exact gap the issue's own live check demonstrated (`M spawn.py`, a new test file, and a record file were all invisible to `gh` 15 minutes into a session with no commit).

## What did not work

None.

## Upstream basis

No phase-1 proposal exists for this issue — `CORE_BUILD_NOW=1` was set by the spawner (checked: `printf 'CORE_BUILD_NOW=%s\n' "$CORE_BUILD_NOW"`, result `CORE_BUILD_NOW=1`), so contract v3 s19a's build-now bypass applies and this record is the only artifact.

## Open findings

None. derived: `python3 -m pytest test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q`, this session, result: `16 passed` (7 + 9) — the write/read hardening found during this session's own silent-failure-audit pass (uncaught `OSError` in the two new fallible sites, see "What was done", Part 1) landed in the same commit as the feature it was found in, exercised by two cases in `test_session_completion_heartbeat.py::PendingCompletionsQueueTest` (test_write_failure_is_advisory_not_raised, test_read_failure_is_reported_as_error_not_silent_empty); the `-uall` correctness gap found while building Part 2 (see "What was done", Part 2) is exercised by `test_workspace_progress_tracking.py::WorkspaceSummaryTest::test_record_file_touch_is_named_as_started`.

## Next steps

None — `loop_state: landed`.

## Verification

skill-verdict: silent-failure-audit — applied: invoked; ran the skill's procedure against this change's own two new fallible-operation sites (`_record_session_completion`'s file/lock write, `_drain_pending_completions`'s file/lock read-and-clear) — both were originally Silently-Absorbed-shaped (an uncaught `OSError` on write would abort the caller's remaining tail; a caught-and-swallowed `OSError` on read would return `[]` indistinguishably from a genuinely empty queue) and both are now Handled (write: advisory print, execution continues; read: `(entries, error)` so the caller reports a real anomaly instead of quiet emptiness) — see "What was done" and the two new tests in `test/test_session_completion_heartbeat.py`. `_live_session_workspace_summary()`'s own fallible operation (the `git status` subprocess call, Part 2) is also Handled: a non-zero return code reports an explicit "확인 실패" detail rather than raising or returning an empty-looking string, exercised by `test_workspace_progress_tracking.py::WorkspaceSummaryTest::test_non_git_directory_fails_safe_not_raise`.
other mounted skills: not triggered (only `silent-failure-audit` was mounted for this session; `work-in-english` guidance applies via core hook enforcement, not a Skill-tool invocation).

Four standing invariants, each executed this session:

1. No return of the retired role axis. derived: `git stash && python3 gates/retirement_count.py > /tmp/retire_before2.txt 2>&1; git stash pop && python3 gates/retirement_count.py > /tmp/retire_after2.txt 2>&1; diff <(sed -E 's/^[a-zA-Z0-9._\/-]+:[0-9]+:/FILE:LINE:/' /tmp/retire_before2.txt) <(sed -E 's/^[a-zA-Z0-9._\/-]+:[0-9]+:/FILE:LINE:/' /tmp/retire_after2.txt)`, this session, result: identical content modulo line-number drift from this diff's own insertions — no new `role`/`roles` token introduced (also checked directly: `git diff | grep -iE '\brole'` → no output).
2. No new bug — failing-test set vs origin/main as sets of names. derived: `python3 -m pytest . -q` run on `origin/main` (HEAD at `fa52c0c81d3c529e6e39b8e9b9a6c876fc263423`, before any edit) and again after the complete change (all three parts, self-audit hardening, and both new test files), from the repo root both times, result: `17 failed, 665 passed, 3 xfailed` before / `17 failed, 686 passed, 3 xfailed` after (686 = 665 + 21 new tests across `test/test_session_completion_heartbeat.py` and `test/test_workspace_progress_tracking.py`); `diff <(sort before-FAILED-names) <(sort after-FAILED-names)` → no output, i.e. the two 17-item failing-test-name sets are identical (all 17 are pre-existing sandbox/network failures, e.g. `fatal: 'origin' does not appear to be a git repository`, unrelated to this change) — re-checked after each of Parts 2 and 3 landed, still identical every time.
3. No overhead increase — a quiet tick stays as quiet as today. derived: this session's own reproduction, `roster_watchdog()` called against a fully-empty roster with an empty completions queue, before and after this change, via `python3 -c "..."` scripts run in this session (both a mocked-dependency call into `watchdog.roster_watchdog()` and, for the delta layer, direct subprocess calls into `on-the-record/monitors/poll_heartbeat_delta.py`) — result before/after: identical stdout (`돌고 있는 스킬 세션 없음` / `이상 신호 없음`, `rc: 0`); a second-tick run of `poll_heartbeat_delta.py` with unchanged input beyond one newly-queued completion emits only the new `[poll-report] ...: COMPLETED` line and nothing else (the prior tick's unchanged `돌고 있는 스킬 세션 없음`/`이상 신호 없음` lines did not re-print). Part 2 has its own direct test of the same property (`test_workspace_progress_tracking.py::DeltaSuppressionForWorkspaceProgressTest::test_unchanged_workspace_progress_line_suppressed_next_tick`): an unchanged `[poll-report] ...: HEALTHY` line across two ticks emits nothing on the second.
4. Monitor/watch machinery unbroken and not quieter. derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_reconcile_crash_verdict_race.py on-the-record/monitors/test_poll_heartbeat.py test/test_unrecovered_commit_count.py test/test_session_completion_heartbeat.py test/test_workspace_progress_tracking.py -q`, this session, result: `74 passed` (53 + 7 + 14 = 74: 53 pre-existing, 7 from Part 1's test file, 14 from Part 2/3's shared test file); no existing anomaly line's condition or wording was touched — Part 1's two edited functions (`_record_session_completion`, `_drain_pending_completions`) and one new call site in `roster_watchdog()`, Part 2's one new function (`_live_session_workspace_summary`), and Part 3's one new function (`_last_tool_activity_summary`) folded into the same existing `HEALTHY` branch's `detail` string, are all additive or in-place text enrichment, and every watchdog-adjacent test file above passes unchanged.
