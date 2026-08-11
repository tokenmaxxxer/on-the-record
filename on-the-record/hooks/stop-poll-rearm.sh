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
if [ -n "$CHECKOUT" ]; then
  poll_rearm_arm_if_due "${CHECKOUT}" || true
fi

trap - EXIT
exit 0
