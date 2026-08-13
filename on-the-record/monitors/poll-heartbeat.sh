#!/usr/bin/env bash
# issue #835 phase 2: plugin Monitor heartbeat. Auto-started by Claude Code
# for a user-scope plugin install (monitors.json, when: "always") — no
# `/loop`, no manual setup. Loops `sleep 60` and, on a due tick, calls the
# SAME `python3 spawn.py poll-due` atomic TTL-check-and-stamp that
# poll_rearm_arm_if_due() (on-the-record/hooks/poll-rearm.sh) uses —
# this is a THIRD caller of the same poll_due() TTL gate
# (spawn.py:1976-1999), not a new polling engine; that gate's own
# lock-protected TTL check is what de-dups this tick against the two
# turn-driven hooks (directive.sh, stop-poll-rearm.sh), which keep
# calling poll_rearm_arm_if_due() unchanged.
#
# issue #922 phase 2: the due branch no longer launches the watchdog
# detached (nohup ... &) and echoes a static "poll tick: due, watchdog
# armed" line. Instead it runs `spawn.py watchdog --auto-respawn` in the
# FOREGROUND, capturing its combined stdout+stderr, and echoes that
# captured text verbatim as this tick's own stdout — so the Monitor
# notification channel surfaces roster_watchdog()'s already-computed
# rich per-session report (health, STALLED/watcher-dead, [resume],
# [poll-report]) every due tick instead of a bare line
# (docs/issue-922/proposals/poll-heartbeat-capture-hop.md). This is a
# single watchdog invocation per due tick, not two: poll-rearm.sh and
# its other two callers are untouched.
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

# issue #947: monitor-unavailable degradation notice. Plugin Monitors run
# only in interactive CLI sessions (docs/specs/platform-capabilities.md);
# directive.sh (UserPromptSubmit) infers whether THIS session's own
# Monitor ever started by checking this marker's mtime against its own
# recorded session-start time, so a workspace-scoped touch here is enough
# -- no session_id is available to a Monitor command (unlike a hook, it
# carries no documented stdin JSON contract, and blocking on one here
# would risk hanging this loop forever). Written before the sleep loop
# so it reflects "the monitor process launched", not "a tick completed".
mkdir -p "$(pwd -P)/.orchestrate-monitor-alive" 2>/dev/null && \
  touch "$(pwd -P)/.orchestrate-monitor-alive/alive" 2>/dev/null || true

tick=0
max_ticks="${POLL_HEARTBEAT_MAX_TICKS:-0}"
sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-60}"
while true; do
  sleep "${sleep_seconds}"
  due_out="$(python3 "${CHECKOUT}/spawn.py" poll-due 2>&1 >/dev/null)"
  due_rc=$?
  if [ "${due_rc}" -eq 0 ]; then
    report="$(python3 "${CHECKOUT}/spawn.py" watchdog --auto-respawn 2>&1)"
    watchdog_rc=$?
    mkdir -p "${HOME}/.claude/tokenmaxxxer" 2>/dev/null
    printf '%s\n' "${report}" >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>/dev/null || true
    if [ -n "${report}" ]; then
      printed_text="${report}"
    else
      printed_text="poll tick: due, watchdog ran (rc=${watchdog_rc}, no output)"
    fi
    # issue #1117: hash the exact text this tick would print (not `report`
    # alone — two empty-report ticks with different watchdog_rc values
    # would otherwise hash identically, silently suppressing a
    # watchdog-crash signal change and violating #90 watch-coverage).
    # Persisted as a plain sibling file next to the poll TTL stamp
    # (runs/poll_state.json) rather than inside that fcntl-locked file —
    # see docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md.
    hash_state_file="${CHECKOUT}/runs/poll_heartbeat_last_hash"
    new_hash="$(printf '%s' "${printed_text}" | sha256sum | cut -d' ' -f1)"
    prev_hash=""
    if [ -f "${hash_state_file}" ]; then
      prev_hash="$(cat "${hash_state_file}" 2>/dev/null || true)"
    fi
    if [ "${new_hash}" != "${prev_hash}" ]; then
      printf '%s\n' "${printed_text}"
      mkdir -p "${CHECKOUT}/runs" 2>/dev/null
      printf '%s' "${new_hash}" >"${hash_state_file}" 2>/dev/null || true
    fi
  else
    if [ -n "${due_out}" ]; then
      mkdir -p "${HOME}/.claude/tokenmaxxxer" 2>/dev/null
      printf '[poll-due crashed, rc=%s] %s\n' "${due_rc}" "${due_out}" \
        >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>/dev/null || true
    fi
    echo "poll tick: skipped (within TTL)"
  fi
  tick=$((tick + 1))
  if [ "${max_ticks}" != "0" ] && [ "${tick}" -ge "${max_ticks}" ]; then
    break
  fi
done
