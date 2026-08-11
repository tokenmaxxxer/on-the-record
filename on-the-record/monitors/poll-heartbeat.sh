#!/usr/bin/env bash
# issue #835 phase 2: plugin Monitor heartbeat. Auto-started by Claude Code
# for a user-scope plugin install (monitors.json, when: "always") — no
# `/loop`, no manual setup. Loops `sleep 60` and calls the EXISTING
# poll_rearm_arm_if_due() (on-the-record/hooks/poll-rearm.sh) that
# directive.sh (UserPromptSubmit) and stop-poll-rearm.sh (Stop) already
# call — this is a THIRD caller of the same poll_due() TTL gate
# (spawn.py:1953-1978), not a new polling engine; that gate's own
# lock-protected TTL check is what de-dups this tick against the two
# turn-driven hooks, so no separate coordination code is added here.
#
# Hard boundary (docs/specs/platform-capabilities.md, "Claude Code plugin
# Monitors"): this process is SESSION-BOUND — it runs only for the
# lifetime of the session that started it and does not survive that
# session's death or reboot. On a host where the Monitor tool is
# unavailable, the platform never invokes this script at all; the
# existing turn-driven hooks are untouched and keep polling as before.
#
# Kill switch: ORCHESTRATE_OFF=1 (same convention as poll-rearm.sh's
# other two callers).
#
# Test hooks: POLL_HEARTBEAT_MAX_TICKS=<n> bounds the loop to n iterations
# so the test suite can exercise it without a backgrounded process running
# forever; POLL_HEARTBEAT_SLEEP_SECONDS=<n> overrides the 60s cadence so
# the bounded run also completes quickly. Both unset in production — the
# loop then runs a real 60s cadence for the session's lifetime as
# designed.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=../hooks/poll-rearm.sh
source "${SCRIPT_DIR}/../hooks/poll-rearm.sh"

CHECKOUT="$(poll_rearm_resolve_checkout "${BASH_SOURCE[0]}" || true)"
if [ -z "${CHECKOUT}" ]; then
  echo "poll tick: skipped (checkout not resolvable)"
  exit 0
fi

tick=0
max_ticks="${POLL_HEARTBEAT_MAX_TICKS:-0}"
sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-60}"
while true; do
  sleep "${sleep_seconds}"
  if poll_rearm_arm_if_due "${CHECKOUT}"; then
    echo "poll tick: due, watchdog armed"
  else
    echo "poll tick: skipped (within TTL)"
  fi
  tick=$((tick + 1))
  if [ "${max_ticks}" != "0" ] && [ "${tick}" -ge "${max_ticks}" ]; then
    break
  fi
done
