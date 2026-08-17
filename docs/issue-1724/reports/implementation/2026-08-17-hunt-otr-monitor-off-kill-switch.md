---
proposal: docs/issue-1724/proposals/otr-monitor-off-kill-switch.md
---

# Hunt record — otr-monitor-off-kill-switch

## after-proposal — stance 1: probe the PLAN's OTR_MONITOR_OFF test additions for a masking/composition defect in _run_heartbeat's env-dict construction

Verdict: FINDING — the planned second new test ("ORCHESTRATE_OFF=1 alone, OTR_MONITOR_OFF unset, still stops the monitor") passes identically whether ORCHESTRATE_OFF's own check works or is completely deleted, because `_run_heartbeat` (test_poll_heartbeat.py) builds `env = dict(os.environ)` and never clears/normalizes `OTR_MONITOR_OFF` the way it unconditionally normalizes `POLL_HEARTBEAT_SLEEP_SECONDS`/`POLL_HEARTBEAT_MAX_TICKS`/`CLAUDE_ROLE` for every call — so an ambient `OTR_MONITOR_OFF=1` (which this very proposal tells operators to set in `.claude/settings.local.json`'s `env` block, i.e. exactly the kind of shell that runs this repo's own test suite) silently masks a regression in the sibling switch the test claims to pin.
Kind: composition
Seed: docs/issue-1724/proposals/otr-monitor-off-kill-switch.md ("Accumulation" section: planned second test "asserting ORCHESTRATE_OFF=1 alone (with OTR_MONITOR_OFF unset) still stops the monitor exactly as it does today"); on-the-record/monitors/test_poll_heartbeat.py `_run_heartbeat` (lines 72-83)
cap_seconds: unspecified
tier: default
diff_stat_lines: 0 (docs-only phase-1; probing the not-yet-written phase-2 plan)
started_at: 2026-08-17T00:00:00Z
ended_at: 2026-08-17T00:20:00Z

### Reproduce
```
WORK=/tmp/otr1724repro
cp on-the-record/monitors/poll-heartbeat.sh "$WORK/poll-heartbeat.sh"
# apply the proposal's exact planned insertion after the ORCHESTRATE_OFF case (line 44):
#   case "${OTR_MONITOR_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
mkdir -p "$WORK/checkout"; cat > "$WORK/checkout/spawn.py" <<'PY'
#!/usr/bin/env python3
import os, sys
marker = os.environ["FAKE_SPAWN_MARKER"]
if sys.argv[1:2] == ["poll-due"]:
    sys.exit(0 if os.environ.get("FAKE_POLL_DUE") == "1" else 1)
if sys.argv[1:2] == ["watchdog"]:
    open(marker, "a").write("watchdog-ran\n"); sys.exit(0)
sys.exit(0)
PY

# Scenario A: ORCHESTRATE_OFF case intact.
env -i PATH="$PATH" HOME="$WORK/home" TOKENMAXXXER_CHECKOUT="$WORK/checkout" \
  FAKE_SPAWN_MARKER="$WORK/marker.log" POLL_HEARTBEAT_MAX_TICKS=1 POLL_HEARTBEAT_SLEEP_SECONDS=0 \
  FAKE_POLL_DUE=1 ORCHESTRATE_OFF=1 OTR_MONITOR_OFF=1 bash "$WORK/poll-heartbeat.sh"
# rc=0, empty stdout, marker not written

# Scenario B: delete the ORCHESTRATE_OFF case line entirely (simulate a future
# regression that breaks it), ambient OTR_MONITOR_OFF=1 still set:
sed -i '' 's/^case "\${ORCHESTRATE_OFF:-}".*$/# BROKEN/' "$WORK/poll-heartbeat.sh"
env -i PATH="$PATH" HOME="$WORK/home" TOKENMAXXXER_CHECKOUT="$WORK/checkout" \
  FAKE_SPAWN_MARKER="$WORK/marker.log" POLL_HEARTBEAT_MAX_TICKS=1 POLL_HEARTBEAT_SLEEP_SECONDS=0 \
  FAKE_POLL_DUE=1 ORCHESTRATE_OFF=1 OTR_MONITOR_OFF=1 bash "$WORK/poll-heartbeat.sh"
# rc=0, empty stdout, marker not written -- IDENTICAL to Scenario A
```

### Observed
Both scenarios produce `rc=0`, empty stdout, and no watchdog marker written —
completely indistinguishable, even though Scenario B has no working
ORCHESTRATE_OFF check at all. The planned test's env_extra dict for this case
(`{"FAKE_POLL_DUE": "1", "HOME": ..., "ORCHESTRATE_OFF": "1"}`, deliberately
omitting `OTR_MONITOR_OFF` so it stays "unset") does not actually guarantee
`OTR_MONITOR_OFF` is unset in the subprocess — `_run_heartbeat` inherits the
full ambient `os.environ` and only overrides
`TOKENMAXXXER_CHECKOUT`/`FAKE_SPAWN_MARKER`/`POLL_HEARTBEAT_MAX_TICKS`/
`POLL_HEARTBEAT_SLEEP_SECONDS`/(via `env.pop`)`CLAUDE_ROLE`. Confirmed live in
this very session's shell: `env | grep POLL_HEARTBEAT_SLEEP_SECONDS` already
returns `POLL_HEARTBEAT_SLEEP_SECONDS=3600`, proving this exact ambient-env
propagation channel (a developer's Claude Code session env, the very thing
this proposal tells operators to set `OTR_MONITOR_OFF` in) is real and already
in effect for the sibling knob today.

### Expected
`_run_heartbeat` should unconditionally normalize `OTR_MONITOR_OFF` (e.g.
`env["OTR_MONITOR_OFF"] = env_extra.get("OTR_MONITOR_OFF", "")`, mirroring how
it already unconditionally sets `POLL_HEARTBEAT_SLEEP_SECONDS`/
`POLL_HEARTBEAT_MAX_TICKS` and pops `CLAUDE_ROLE`) so every test's "unset"
claim is actually enforced rather than inherited from whatever the invoking
shell happens to carry — otherwise the "ORCHESTRATE_OFF alone still works"
test (and every other non-kill-switch test) can silently pass on any
contributor machine that followed this proposal's own documented setup,
proving nothing about the code it claims to pin.
