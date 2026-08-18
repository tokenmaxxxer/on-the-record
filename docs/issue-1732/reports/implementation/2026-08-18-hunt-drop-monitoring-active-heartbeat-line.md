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

## after-proposal — stance 2: does the removal's own justification ("liveness is already covered by the alive marker") actually hold, given the landed diff's cross-file reference?

Verdict: FINDING — the comment added by the landed diff cites the wrong (and functionally incapable) marker as covering the liveness signal it just deleted, so a fully quiet, multi-hour poll-heartbeat session now emits zero stdout ever again, making a silently-dead loop indistinguishable from a silently-healthy one on the one channel (Monitor stdout) #1220 built this line specifically to keep non-silent.
Kind: silent-failure
Seed: git diff on-the-record/monitors/poll-heartbeat.sh (lines ~330-341, the landed patch's new comment block)
cap_seconds: (not specified to me — used default budget)
tier: default
diff_stat_lines: 71 (19 +/- in poll-heartbeat.sh, 61 added in test_poll_heartbeat.py — from `git diff --stat`)
started_at: 2026-08-18T00:00:00Z (session-relative; wall clock not exposed to this shell)
ended_at: 2026-08-18T00:00:00Z (session-relative; wall clock not exposed to this shell)

### Reproduce
```bash
rm -rf /tmp/otr1732_repro; mkdir -p /tmp/otr1732_repro/checkout /tmp/otr1732_repro/home
cat > /tmp/otr1732_repro/checkout/spawn.py <<'PY'
#!/usr/bin/env python3
import os, sys
if sys.argv[1:2] == ["poll-due"]:
    sys.exit(1)   # never due -> loop just idles every tick, report stays fully quiet
sys.exit(0)
PY
env -i HOME=/tmp/otr1732_repro/home PATH="$PATH" \
  TOKENMAXXXER_CHECKOUT=/tmp/otr1732_repro/checkout \
  FAKE_SPAWN_MARKER=/tmp/otr1732_repro/checkout/marker.log \
  POLL_HEARTBEAT_MAX_TICKS=4 \
  POLL_HEARTBEAT_SLEEP_SECONDS=1 \
  bash on-the-record/monitors/poll-heartbeat.sh \
  > /tmp/otr1732_repro/stdout.log 2>/tmp/otr1732_repro/stderr.log
echo "stdout-bytes=$(wc -c </tmp/otr1732_repro/stdout.log)"
python3 -c "
import glob, os
for p in glob.glob('/tmp/otr1732_repro/home/.claude/tokenmaxxxer/monitor-alive/*/alive'):
    print('one-shot alive marker mtime:', os.stat(p).st_mtime)
p2 = '/tmp/otr1732_repro/checkout/runs/poll_heartbeat_alive.json'
print('per-tick liveness stamp mtime:', os.stat(p2).st_mtime)
"
```

### Observed
- `stdout-bytes=0` across all 4 simulated ticks (a single continuous `bash poll-heartbeat.sh` process, not 4 separate invocations) — after the change, a quiet session never prints anything again, ever, once the initial state is recorded.
- `one-shot alive marker mtime: 1787043044.67` — the marker the new comment names (`poll-heartbeat.sh:105-114`, the `~/.claude/tokenmaxxxer/monitor-alive/<hash>/alive` `touch`) is written exactly **once**, before the `while true; do` loop starts (poll-heartbeat.sh:105-114 sits above `tick=0`/`while true` at lines 169/185). It never updates again for the rest of the process's life — 4 ticks and ~4s later its mtime is unchanged.
- `per-tick liveness stamp mtime: 1787043048.93` (~4s later, i.e. it *did* advance every tick) — but this is a *different* file, `runs/poll_heartbeat_alive.json`, written by `_alive_stamp_write()` (poll-heartbeat.sh:159-167, issue #1497 req 2) — the comment added by this diff never names it, and it is never written to stdout; it is consumed only by other hooks (`on-the-record/hooks/directive.sh:161-178` `_monitor_liveness_check_and_notify`, `on-the-record/hooks/stop-poll-rearm.sh:46`) as an internal re-arm backstop with its own 360s threshold, surfaced as a hook directive to the orchestrator — not as anything the user sees via the Monitor tool's own notification channel.
- Cross-checked what the marker the comment *does* name is actually documented to mean: poll-heartbeat.sh:90-100 says directive.sh "infers whether THIS session's own Monitor **ever started** by checking this marker's mtime against its own recorded session-start time" — a one-shot "did it start" fact, not an ongoing "is it still ticking" signal. directive.sh:44-46 confirms the same reading ("the heartbeat's alive marker ... hashed by the resolved arm-root path").

### Expected
The new comment (poll-heartbeat.sh:332-338) asserts "liveness is already covered by the alive marker (poll-heartbeat.sh:105-114)" as the reason it's safe to delete the periodic stdout line that issue #1220 added specifically "so the Monitor channel never goes silent past a bound" (poll-heartbeat.sh:222-223, unchanged by this diff). For that claim to hold, the named marker would need to be refreshed periodically and be visible on the same channel. It is neither: it's a session-start-only touch consumed by a different hook for a different purpose, and the file that *is* refreshed per tick is never surfaced to the user at all. A fully quiet, hours-long session now produces the identical zero-stdout signature whether poll-heartbeat.sh is healthy-and-idle or has silently died — exactly the invisible-absence failure mode #1220 was written to prevent, and the comment's own cited justification does not close that gap.
