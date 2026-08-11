---
proposal: docs/issue-878/proposals/2026-08-11-async-completion-drive.md
---

# Hunt record — async-completion-drive

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the design captures one `session_id` "per roster entry, the same way roster_watchdog already tracks PID/branch," but a single orchestrator session routinely spawns multiple roles in one session (multiple roster entries), so those entries would share the identical orchestrator `session_id` — nothing in the proposal (or in the existing per-tick loop it says it reuses unchanged) serializes or dedupes the resume action when two roster entries under the same session_id become ready in the same poll window, so the design's own reuse target can issue two concurrent `claude -p --resume "$session_id"` calls against one session.
Kind: design-error
Seed: docs/issue-878/proposals/2026-08-11-async-completion-drive.md, "What will be done" bullet 2 (spawn.py session_id capture) and case-2 rationale paragraph
cap_seconds: 120
tier: default
diff_stat_lines: ~489 (docs-only)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:10:00Z

### Reproduce
Read `roster_watchdog()` in spawn.py (on-the-record-issue-878-product-discovery/spawn.py:2241-2325): it loads the whole roster dict (`_roster_load()`) and iterates every live entry in one tick (`for key, e in sorted(d.items())`), each entry keyed `issue-{n}/{role}` independently by role, with no field tying two entries back to "same orchestrator process/session." One orchestrator turn commonly spawns more than one role for the same issue (the roster already supports N concurrent entries per issue by role name). The proposal's own bullet says `session_id` is captured "the same way roster_watchdog already tracks PID/branch" — i.e. per-entry — but PID/branch are genuinely distinct per spawned child process, while the orchestrator's own session_id (the thing case 2 needs to `--resume`) is a property of the single orchestrator process that did the spawning, so it is identical across every roster entry that process created. The proposal never states what happens when the poll tick observes two such entries ready in the same tick, nor how the resume-invoke action (added "at an EXISTING poll tick path") avoids firing twice for the same `session_id` inside `roster_watchdog`'s single-pass loop.

### Observed
The proposal text ("What will be done", bullet 2) commits to per-roster-entry `session_id` storage and a per-tick resume action reusing `roster_watchdog`'s existing loop verbatim, with no mention of a lock, queue, or single-owner check across entries sharing a session_id.

### Expected
A design that captures a value which is actually per-orchestrator-session (not per-role-entry) should say explicitly how the per-tick, per-entry watchdog loop is prevented from invoking `--resume` more than once concurrently for the same session_id when multiple delegations under one orchestrator session become ready close together — e.g. a session_id-keyed lock/claim distinct from the per-entry PID/branch tracking it's compared to. As written, the state that would prevent a double/racing resume is asserted to exist ("the same per-entry tracking... already does") but nothing in the reused mechanism actually maintains it at the session_id granularity.
