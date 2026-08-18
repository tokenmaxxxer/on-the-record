---
proposal: docs/issue-1732/proposals/2026-08-18-drop-monitoring-active-heartbeat-line.md
---

# Hunt record — drop-monitoring-active-heartbeat-line

## after-proposal — stance 1: composition/silent-failure/design-error in the to_emit-empty/1800s-bound rewrite (first_tick, BOARD_SWEEP_LOCK_SKIP_RE carry-forward, last_emit_epoch left untouched, and the two new bound-forcing tests)

Verdict: NO FINDING
Seed: docs/issue-1732/proposals/2026-08-18-drop-monitoring-active-heartbeat-line.md; on-the-record/monitors/poll-heartbeat.sh:326-343; on-the-record/monitors/test_poll_heartbeat.py (_run_tick, t_returned_pr_unchanged_set_produces_no_output_on_due_tick, t_returned_pr_new_item_emits_on_due_tick)
cap_seconds: unspecified (phase-1 hunt dispatch)
tier: default
diff_stat_lines: 0 (proposal only, no code changed yet)
started_at: 2026-08-18T00:00:00Z
ended_at: 2026-08-18T00:40:00Z

Applied the proposed edit to a scratch copy of poll-heartbeat.sh (the
to_emit-empty/bound branch replaced with: collect returned-pr:-keyed lines
from curr; emit + set emitted_now=True only if non-empty), swapped it into
place, and drove it through subprocess-level ticks mirroring
_run_tick + a last_emit_epoch-rewriting helper as the proposal describes:

1. Unchanged report with NO returned-pr lines, bound forced to fire
   (last_emit_epoch rewritten to 0 between ticks): tick2 stdout is empty,
   state file's last_emit_epoch stays pinned at 0 (untouched) — as the
   proposal predicts. A third tick run immediately afterward (no
   re-forcing) also produces empty stdout, so the "epoch pinned in the
   past forever" state is inert, not a leak: `to_emit` stays empty because
   nothing changed, so no wrong output is ever produced by the pinned
   epoch. The moment any line actually changes, that line goes through
   the unconditional `if to_emit:` branch (unaffected by this proposal),
   which sets emitted_now=True and resets last_emit_epoch to real "now"
   regardless of how stale the prior epoch was.
2. Unchanged report WITH a returned-pr line, bound forced to fire: tick2
   stdout is exactly the returned-pr line (age-advanced), no
   "monitoring active" text (the string no longer exists in the patched
   script), and last_emit_epoch is updated to real "now" — matching the
   proposal's second described test exactly.
3. first_tick: printed_text (poll-heartbeat.sh:195-198) always falls back
   to a non-empty "poll tick: due, watchdog ran (rc=..., no output)" line
   when the watchdog prints nothing, so `order` is never empty and
   first_tick's `to_emit.append` for every line always fires — the
   to_emit-empty/bound branch this proposal touches is structurally
   unreachable on a first tick. No first_tick/bound interaction exists.
4. BOARD_SWEEP_LOCK_SKIP_RE carry-forward only ever populates
   board-sweep-prefixed keys in new_lines/curr; the bound branch's
   returned-pr filter reads curr by "returned-pr:" prefix, an entirely
   disjoint keyspace, so there is no interaction to regress.

All four candidate angles named in the brief reproduced exactly the
behavior the proposal describes, with no contradiction, no wrong output,
and no test that fails to exercise what it claims. Restored
on-the-record/monitors/poll-heartbeat.sh to its original committed content
afterward (git diff / git status confirm no residual change).
