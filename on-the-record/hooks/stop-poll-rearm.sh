#!/usr/bin/env bash
# Stop: turn-END re-arm of the poll/watchdog trip (issue #801 phase 2,
# candidate 4 of docs/issue-801/proposals/technical-feasibility.md).
#
# directive.sh already arms poll-due/watchdog on UserPromptSubmit
# (turn-START). This hook arms the SAME check again right as the turn
# ends, before the session goes idle waiting on the next user message —
# so the last-armed watchdog process is as fresh as possible going into
# a quiet gap, without the user ever typing /loop. It is a turn-driven,
# best-effort widening of the existing mechanism, not a new one: the
# poll-due 60s TTL (spawn.py POLL_INTERVAL_SEC) means a Stop-hook trip
# inside the same window as the last UserPromptSubmit trip is a no-op —
# by design, this is exactly what keeps two hook events from double-
# spawning a watchdog per turn.
#
# HARD BOUNDARY (do not overclaim): this still requires the orchestrator
# session's own process to be alive for the Stop hook to fire at all. It
# does NOT survive the session's own death, and it does NOT create any
# OS-level scheduled-execution primitive (cron/launchd/systemd timer) —
# both are the externally-blocked condition recorded in
# docs/issue-801/proposals/technical-feasibility.md's "Hard boundary"
# section: a plugin-shipped settings.json has no permissions key to grant
# a session-independent wake, so true install-only self-wake past a dead
# session remains unreachable from this repo alone.
#
# Kill switch: ORCHESTRATE_OFF=1.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
# A spawned role session is never the orchestrator, even if the plugin leaks in.
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }

. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/poll-rearm.sh"
CHECKOUT="$(poll_rearm_resolve_checkout "${BASH_SOURCE[0]}" || true)"

# issue #1497 req 3: same staleness check and once-per-episode re-arm
# directive as directive.sh's UserPromptSubmit copy -- duplicated
# verbatim here (this hook does not source directive.sh) so the Stop
# boundary also surfaces a dead Monitor, not only turn-start. Shares the
# same stamp/state file paths and de-dup key, so a stamp already fresh
# or an episode already notified by directive.sh this turn stays quiet
# here too.
_monitor_liveness_check_and_notify() {
  local checkout="$1"
  local stamp="${checkout}/runs/poll_heartbeat_alive.json"
  local state="${checkout}/runs/poll_heartbeat_staleness_state.json"
  local threshold="${MONITOR_LIVENESS_STALE_SECONDS:-180}"
  python3 - "$stamp" "$state" "$threshold" "$checkout" <<'PY' 2>/dev/null || true
import json
import os
import sys
import time

stamp_path, state_path, threshold, checkout = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
now = time.time()

last_tick = None
try:
    with open(stamp_path) as f:
        last_tick = json.load(f).get("last_tick")
except (OSError, ValueError):
    last_tick = None

stale = last_tick is None or (now - float(last_tick)) >= threshold

state = {}
try:
    with open(state_path) as f:
        state = json.load(f)
except (OSError, ValueError):
    state = {}

if not stale:
    if state.get("notified_episode") is not None:
        try:
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            with open(state_path, "w") as f:
                json.dump({}, f)
        except OSError:
            pass
    sys.exit(0)

episode_key = "missing" if last_tick is None else str(last_tick)
if state.get("notified_episode") == episode_key:
    sys.exit(0)

try:
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w") as f:
        json.dump({"notified_episode": episode_key}, f)
except OSError:
    pass

since_label = (
    time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(float(last_tick)))
    if last_tick is not None
    else "unknown (no tick ever recorded this checkout)"
)
print(
    f"[orchestrate][MONITOR-DEAD] poll-heartbeat monitor dead since {since_label} "
    "-- ACTION REQUIRED before anything else this turn: re-arm it via the Monitor "
    f"tool with persistent: true (command: {checkout}/on-the-record/monitors/"
    "poll-heartbeat.sh) -- a re-arm without persistent: true dies again in 5 "
    "minutes, the Monitor tool's own default timeout_ms"
)
PY
}

# Issue #2140 (#2101 mechanism 4): external dead-man check. The watch
# layer's own death must be observable from OUTSIDE it — this Stop hook
# is that outside caller. Cheap (one bounded python invocation reading a
# single marker file's mtime), advisory-only (spawn.py deadman-check
# never blocks or kills anything; its stdout is the advisory, surfaced
# in the Stop hook output), and recorded in the fires-log like the
# other observation hooks. Any failure mode (timeout, missing python,
# import error) is swallowed — watch-class machinery never blocks Stop.
_deadman_check() {
  local checkout="$1"
  { printf '%s Stop stop-poll-rearm.sh deadman-check\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      >>"$(pwd -P)/.orchestrate-hook-fires.log"; } 2>/dev/null || true
  timeout 20 python3 "${checkout}/spawn.py" deadman-check 2>/dev/null || true
}

if [ -n "$CHECKOUT" ]; then
  _monitor_liveness_check_and_notify "${CHECKOUT}"
  _deadman_check "${CHECKOUT}"
  poll_rearm_arm_if_due "${CHECKOUT}" || true
fi

trap - EXIT
exit 0
