---
kind: current-state-survey
loop_state: handed-off
---

# Current-state survey — issue #848 step 2 (implementation)

## Scope

canonical: docs/issue-848/reports/defect-verification/current-state.md,
"Conclusion" 1-3 (merged PR #849) — `spawn.py`'s own
`fork()+setsid()+Popen(start_new_session=True)` watcher is immune to
parent-turn death; what actually died in #845 was the Claude Code CLI's
`run_in_background` Bash-tool task, armed by a plain (`CLAUDE_ROLE`
unset) top-level session; the #782/#829 poll backstop (`poll-rearm.sh` +
`directive.sh` + `stop-poll-rearm.sh` + the #835/#841
`poll-heartbeat.sh` Monitor) is the deterministic catch for a **spawned
role session's** post-turn terminal event, as long as the orchestrating
session's own process stays alive.

This step determines whether that backstop path already deterministically
covers a post-turn `session-end`, and what remains missing (test,
documentation) to close the loop for issue #848 step 2.

code_under_review:
- on-the-record/hooks/poll-rearm.sh
- on-the-record/monitors/poll-heartbeat.sh
- spawn.py (roster_watchdog, diagnose_health, session_end_verdict)
- docs/specs/platform-capabilities.md
- tests/test_spawn.py
- on-the-record/monitors/test_poll_heartbeat.py

## Finding 1 — the Monitor tick already reaches the same detection path the turn-driven hooks use, independent of turns

canonical: on-the-record/monitors/poll-heartbeat.sh (lines 1-10, read
this session) — `poll-heartbeat.sh` is a `sleep 60` loop that calls the
SAME `poll_rearm_arm_if_due()` (`on-the-record/hooks/poll-rearm.sh`,
lines 54-64, read this session) that `directive.sh` (UserPromptSubmit)
and `stop-poll-rearm.sh` (Stop) already call. Per
`docs/specs/platform-capabilities.md` (lines 34-46, read this session), a
plugin Monitor is session-bound but runs for the *lifetime of the
session*, not just its turns — it keeps ticking every ~60s across quiet
gaps between turns, as long as the orchestrating session's own process is
alive. This matches the issue's own framing: "the newly-landed Monitor
(#841) now polls every ~60s independent of turns."

## Finding 2 — a due tick already runs `roster_watchdog`, which already has a completion-detection branch for a dead-but-registered entry

canonical: spawn.py, `roster_watchdog` (lines 2278-2303, read this
session) — for every roster entry whose pid is no longer alive
(`if not _alive(e.get("pid", 0))`), the function calls
`diagnose_health()` and prints a `[poll-report] {key}: {label} —
{detail}` line every tick (not ledger-gated), where `label` is
`"COMPLETED"` when `diagnose_health()` returns `state=None`.

canonical: spawn.py, `diagnose_health` (lines 2166-2181, read this
session) — when the pid is dead, it calls `session_end_verdict()` on the
workspace's `.events.jsonl`; `verdict == "normal"` (a matched
`session-start` → `session-end` pair, `spawn.py` lines 1543-1580) returns
`{"state": None, "detail": "completion, not a health diagnosis"}` — a
`session-end` that landed in the workspace's event log after the roster
entry's process died is picked up and reported as `COMPLETED` on the very
next tick that scans that entry, whether that tick was armed by a
turn-driven hook or by the Monitor's turn-independent ~60s loop.

canonical: spawn.py, the same `roster_watchdog` dead-entry branch (lines
2281-2285, read this session) — for a dead entry still carrying an issue
number, this branch also calls `_post_session_end_comment()`, the actual
"report to the human" step that posts a `[watch] {key}: session-end: ...`
issue comment.

## Finding 3 — the existing test suite exercises the Monitor tick's plumbing and the roster's completion branch separately, never together as one post-turn scenario

canonical: on-the-record/monitors/test_poll_heartbeat.py (lines 65-107,
read this session) — its three tests confirm `poll-heartbeat.sh` arms
`spawn.py watchdog --auto-respawn` on a due tick, using a **fake**
`spawn.py` that just writes a marker; none exercises the real
`roster_watchdog`/`diagnose_health` completion path.

canonical: `grep -n "class Watchdog" tests/test_spawn.py` output (read
this session, `spawn.py:3503`) — the `Watchdog` test class covers
STALLED/DEADLOCKED/anomaly-count cases and a clean/empty roster, but no
test in this class asserts the `COMPLETED` label for a dead-but-registered
entry whose `session-end` was written after its process died — the exact
shape of "a spawned session's terminal event lands after the arming turn
ends."

No test in the repository currently demonstrates, end-to-end, that a
`session-end` written to a workspace's `.events.jsonl` *after* its roster
entry's process has already died is captured (reported, not silently
dropped) by the poll backstop's completion branch. The underlying
mechanism (Finding 1 + 2) already exists and needs no new production
code — only the test that pins it, and a documentation line
distinguishing it from the ephemeral CLI watch pinned as the actual
dying mechanism in #849's Conclusion 2 (see Finding 4 below).

## Finding 4 — the ephemeral CLI `run_in_background` watch is stated in spawn.py's own task prefix, but not contrasted against the poll backstop anywhere a reader of the backstop's own code would see it

canonical: spawn.py, `_spawn_one` task-prefix block (lines 4783-4841,
read this session, quoted in full in the merged #849 survey) — the only
place this repository currently states "`run_in_background` 로 넘긴
작업은 부모 턴이 끝나는 순간 함께 죽는다" is inside the task text handed
to a spawned role session, gated on `issue is not None`.

canonical: docs/specs/platform-capabilities.md (lines 26-49, read this
session) — the Monitor section documents the session-bound boundary
precisely, but says nothing about the *other* channel (the CLI's own
`run_in_background` Bash-tool task) or which of the two a reader should
trust as authoritative for "did the event get reported." A reader
auditing the poll backstop's own hard-boundary documentation has no
adjacent line stating that the ephemeral watch is best-effort and this
backstop is the authoritative catch — the missing cross-link the issue
text asks for ("document that the ephemeral watch is best-effort while
the poll backstop is authoritative").

## Conclusion

1. The #782/#829 poll backstop, via the #835/#841 Monitor's
   turn-independent ~60s tick, already reaches `roster_watchdog()`'s
   existing dead-entry/`diagnose_health()` completion branch — this
   already deterministically catches a post-turn `session-end` for a
   spawned role session, as long as the orchestrating session's own
   process stays alive (Findings 1-2). No new production-code path is
   needed for the acceptance criterion itself.
2. No existing test demonstrates this end-to-end (Finding 3) — a
   regression test closes that gap.
3. No existing doc line contrasts the ephemeral CLI watch (best-effort,
   dies with its turn) against the poll backstop (authoritative) at the
   point a reader would look (Finding 4) — a short addition to
   `docs/specs/platform-capabilities.md` closes that gap.

## What did not work

None.
