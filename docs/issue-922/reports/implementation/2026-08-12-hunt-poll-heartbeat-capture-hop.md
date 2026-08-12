---
proposal: docs/issue-922/proposals/poll-heartbeat-capture-hop.md
---

# Hunt record — poll-heartbeat-capture-hop

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — the frozen write set (poll-heartbeat.sh + test_poll_heartbeat.py only) cannot deliver foreground stdout capture without either editing hooks/poll-rearm.sh (outside the write set) or duplicating the watchdog invocation (which the proposal explicitly says it will not do)
Kind: design-error
Seed: docs/issue-922/proposals/poll-heartbeat-capture-hop.md
cap_seconds: 120
tier: default
diff_stat_lines: ~240 (2-file docs-only diff, proposal doc)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
grep -n "poll_rearm_arm_if_due" /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-922-implementation/on-the-record/hooks/poll-rearm.sh
```
Shows `poll_rearm_arm_if_due()` is defined in `hooks/poll-rearm.sh` (line 54), a file NOT in the proposal's frozen write set (`files:` front matter lists only `on-the-record/monitors/poll-heartbeat.sh` and `on-the-record/monitors/test_poll_heartbeat.py`). Reading its body:
```
poll_rearm_arm_if_due() {
  ...
  if [ "$due_rc" -eq 0 ]; then
    mkdir -p "${HOME}/.claude/tokenmaxxxer" 2>/dev/null
    nohup python3 "${checkout}/spawn.py" watchdog --auto-respawn \
      >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>&1 &
    disown 2>/dev/null || true
    return 0
  fi
  ...
  return 1
}
```
The function only ever returns a boolean (0/1) to its caller; the watchdog's stdout is redirected straight into a log file by the detached `nohup` launch and never passed back through the function's return value or any output channel `poll-heartbeat.sh` can read.

### Observed
The proposal's "What will be done" section claims the mechanism choice — "poll_rearm_arm_if_due is given a capture-and-return variant callable from poll-heartbeat.sh" — is "an implementation decision made during phase 2, inside this frozen write set." That claim is false: `poll_rearm_arm_if_due` is defined in `hooks/poll-rearm.sh`, which is not one of the two files listed in the proposal's `files:` front matter or write set. Giving it a "capture-and-return variant" necessarily means editing `hooks/poll-rearm.sh`.

The proposal's other named option — `poll-heartbeat.sh` calling `spawn.py watchdog --auto-respawn` itself, foreground, while `poll-rearm.sh`'s existing detached launch stays "as-is in parallel" — does fit inside the frozen write set mechanically, but it means the watchdog process runs TWICE per due tick (once via the existing detached nohup call inside `poll_rearm_arm_if_due`, once via `poll-heartbeat.sh`'s own new foreground call), which directly contradicts the same document's explicit claim in "What will be done": "this proposal does not duplicate the watchdog run, it changes poll-heartbeat.sh's own stdout-echo step ... to surface that same run's output instead of a static string." There is no reading of "surface that same run's output" that is satisfiable from inside the frozen write set alone — either the write set is wrong (must include hooks/poll-rearm.sh) or the "same run, not duplicated" claim is wrong (a second run is unavoidable).

### Expected
The proposal should either (a) add `on-the-record/hooks/poll-rearm.sh` to its write set so `poll_rearm_arm_if_due` can be given a capture-and-return path back to its callers, or (b) drop the "same run, not duplicated" claim and accept/describe the double-invocation cost of a second foreground watchdog call issued independently by `poll-heartbeat.sh`. As written, the frozen two-file write set is insufficient for the mechanism the proposal describes.

### Proposal text updated in response
canonical: docs/issue-922/proposals/poll-heartbeat-capture-hop.md, mechanism paragraph, read after this edit.
The paragraph was rewritten so `poll-heartbeat.sh`'s due branch no longer calls `poll_rearm_arm_if_due`; it inlines the same `poll-due` check and, on a due tick, itself runs the watchdog CLI in the foreground. `poll-rearm.sh` and its two other callers are left as reference-only, unedited. This is proposal wording, not a code change.

## before-landing — stance 0: assume the gate just touched is bypassable; find the bypass

Verdict: FINDING — the rich per-tick report only surfaces on poll-heartbeat.sh's stdout when this script itself wins the shared atomic poll-due TTL race against directive.sh/stop-poll-rearm.sh; when either turn-driven hook wins instead (the common case, since they fire on every user turn vs. this script's 60s cadence), the same watchdog run happens via the unchanged nohup-background path in poll-rearm.sh, whose report lands only in poll-watchdog.log, and poll-heartbeat.sh's tick prints the bare "poll tick: skipped (within TTL)" with no report content at all.
Kind: composition
Seed: on-the-record/monitors/poll-heartbeat.sh, on-the-record/monitors/test_poll_heartbeat.py (diff), on-the-record/hooks/poll-rearm.sh (unchanged sibling caller of the same TTL gate)
cap_seconds: 120
tier: size:medium
diff_stat_lines: 128
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:15:00Z

### Reproduce
```
T=/tmp/claude-1000/hunt/race
rm -rf "$T"; mkdir -p "$T/checkout" "$T/home"
cat > "$T/checkout/spawn.py" <<'PYEOF'
import sys
if sys.argv[1] == "poll-due":
    sys.exit(0)
elif sys.argv[1] == "watchdog":
    print("[poll-report] roster: 1 entry")
    print("issue-999/implementation: STALLED (watcher-dead)")
    print("[resume] issue-999/implementation: respawned watcher")
    sys.exit(0)
PYEOF
export HOME="$T/home"
export TOKENMAXXXER_CHECKOUT="$T/checkout"

# turn-driven hook wins the TTL race first (unchanged poll-rearm.sh path)
source on-the-record/hooks/poll-rearm.sh
poll_rearm_arm_if_due "$T/checkout"
sleep 1

echo "--- poll-watchdog.log ---"
cat "$HOME/.claude/tokenmaxxxer/poll-watchdog.log"

# now the Monitor heartbeat's own poll-due call on the same window: not due
cat > "$T/checkout/spawn.py" <<'PYEOF'
import sys
if sys.argv[1] == "poll-due":
    sys.exit(1)
elif sys.argv[1] == "watchdog":
    print("SHOULD NOT RUN")
    sys.exit(0)
PYEOF

echo "--- poll-heartbeat.sh stdout on the SAME due window ---"
TOKENMAXXXER_CHECKOUT="$T/checkout" POLL_HEARTBEAT_MAX_TICKS=1 POLL_HEARTBEAT_SLEEP_SECONDS=0 \
  bash on-the-record/monitors/poll-heartbeat.sh
```

### Observed
```
--- poll-watchdog.log ---
[poll-report] roster: 1 entry
issue-999/implementation: STALLED (watcher-dead)
[resume] issue-999/implementation: respawned watcher
--- poll-heartbeat.sh stdout on the SAME due window ---
poll tick: skipped (within TTL)
```
Monitor's stdout for that tick carries none of the STALLED/watcher-dead/[resume] content — it is only in the log file.

### Expected
Per the proposal's stated goal ("Monitor's per-tick stdout carries a rich user-facing report instead of a bare line... every due tick"), a due tick's watchdog output should be visible on Monitor stdout regardless of which of the three callers (directive.sh, stop-poll-rearm.sh, poll-heartbeat.sh) actually won the shared TTL race and ran the watchdog. As implemented, the capture-hop only fires when poll-heartbeat.sh itself is the winner, which is the minority case in an active session where user turns (driving the other two callers) vastly outnumber 60s heartbeat ticks — so the feature's own acceptance goal is satisfied only intermittently, and most due ticks still silently degrade to the pre-#922 "skipped/no report" behavior on the Monitor channel.
