#!/usr/bin/env bash
# issue #835 phase 2: plugin Monitor heartbeat. Auto-started by Claude Code
# for a user-scope plugin install (monitors.json, when: "always") — no
# `/loop`, no manual setup. Loops `sleep 120` (env-overridable via
# POLL_HEARTBEAT_SLEEP_SECONDS) and, on a due tick, calls the
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
# other two callers). issue #1724: OTR_MONITOR_OFF=1 is the monitor-only
# counterpart — it stops only this script, leaving every other hook
# (directive.sh, stop-poll-rearm.sh, poll-rearm.sh, the commit-time gate
# hooks) unaffected.
#
# Test hooks: POLL_HEARTBEAT_MAX_TICKS=<n> bounds the loop to n iterations
# so the test suite can exercise it without a backgrounded process running
# forever; POLL_HEARTBEAT_SLEEP_SECONDS=<n> overrides the 120s default
# cadence so the bounded run also completes quickly. Both unset in
# production — the loop then runs the real 120s cadence for the
# session's lifetime as designed.
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
case "${OTR_MONITOR_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=../hooks/poll-rearm.sh
source "${SCRIPT_DIR}/../hooks/poll-rearm.sh"

CHECKOUT="$(poll_rearm_resolve_checkout "${BASH_SOURCE[0]}" || true)"
if [ -z "${CHECKOUT}" ]; then
  echo "poll tick: skipped (checkout not resolvable)"
  exit 0
fi

# issue #1292: demoted from #1275's hard `exit 1` to the same
# sweep-exclusion/dormancy path #1282 built for the non-board case below
# — a non-git arm-root can never be a board, so it is simply excluded
# from `_board_wide_sweep_all`'s arm-root inclusion (spawn.py), exactly
# like a non-board git root. The tick loop always runs; roster-derived
# board targets (#1276) still get swept every tick even when the
# arm-root itself is a non-git parent folder. No `[monitor-arm-refused]`
# error, no exit-1 "script failed" notification for this case.
if git -C "$(pwd -P)" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  is_git=1
else
  is_git=0
fi

# issue #1245/#1280: attachment gate, demoted from a full exit to a
# sweep-exclusion. A non-board arm-root (no docs/specs/approvers.md) no
# longer kills the whole Monitor process -- plugin Monitors are armed
# once at session start and cannot be re-armed, so exiting here
# permanently defeats idle watch for the rest of the session, including
# roster-derived watch (#1276) over board repos the session spawns into
# later. `is_board` only gates `_board_wide_sweep_all`'s arm-root
# inclusion (spawn.py); the tick loop below always runs. A non-git root
# (#1292) is forced to `is_board=0` regardless of what a stray
# `docs/specs/approvers.md` file might say — it can never be a board.
if [ "${is_git}" -eq 1 ] && [ -f "$(pwd -P)/docs/specs/approvers.md" ]; then
  is_board=1
else
  is_board=0
fi

# issue #947/#1280: monitor-unavailable degradation notice. Plugin
# Monitors run only in interactive CLI sessions
# (docs/specs/platform-capabilities.md); directive.sh (UserPromptSubmit)
# infers whether THIS session's own Monitor ever started by checking
# this marker's mtime against its own recorded session-start time.
# Relocated out of the target repo (workspace-keyed under
# ~/.claude/tokenmaxxxer/, hashed by resolved arm-root path) so #1245's
# "no registration artifacts in a non-board repo" holds even now that
# the loop always arms there -- no session_id is available to a Monitor
# command (unlike a hook, it carries no documented stdin JSON contract,
# and blocking on one here would risk hanging this loop forever).
# Written before the sleep loop so it reflects "the monitor process
# launched", not "a tick completed". directive.sh computes the identical
# hash from its own `pwd -P` at hook-fire time -- same cwd, no shared
# state file, no IPC.
_alive_dir="$(PWD_P="$(pwd -P)" python3 -c '
import hashlib, os
root = os.environ.get("PWD_P", "")
h = hashlib.sha256(root.encode("utf-8", "surrogatepass")).hexdigest()[:24]
print(os.path.join(os.path.expanduser("~/.claude/tokenmaxxxer/monitor-alive"), h))
' 2>/dev/null)"
if [ -n "${_alive_dir}" ]; then
  mkdir -p "${_alive_dir}" 2>/dev/null && \
    touch "${_alive_dir}/alive" 2>/dev/null || true
fi

# issue #1465: GC stale monitor-alive marker dirs on heartbeat startup,
# and report (never delete) legacy .orchestrate-monitor-alive/ dirs in
# consumer repos. Non-fatal — `|| true` so a GC failure can never take
# down the tick loop below (observe-only machinery must never die on
# cleanup errors).
python3 "${SCRIPT_DIR}/../../spawn.py" gc-monitor-alive >/dev/null 2>&1 || true

# issue #1466: poll-watchdog.log gets an ISO-8601 tick-header line per
# appended tick and single-generation size-based rotation (to `.1`), both
# non-fatal to this loop. Confirmed (docs/issue-1466/reports/implementation/survey.md
# "Existing-parser check") no existing tool parses this log's current
# format before adding the header/rotation. Threshold overridable for
# tests via POLL_WATCHDOG_LOG_MAX_BYTES; unset in production (default
# 5MB). This only touches the on-disk log -- the Monitor stdout paths
# below (printed_text/diff_output) are untouched.
POLL_WATCHDOG_LOG_MAX_BYTES="${POLL_WATCHDOG_LOG_MAX_BYTES:-5242880}"

_poll_watchdog_log_append() {
  local log_path="${HOME}/.claude/tokenmaxxxer/poll-watchdog.log"
  local body="$1"
  mkdir -p "${HOME}/.claude/tokenmaxxxer" 2>/dev/null || true
  local size
  size="$(wc -c <"${log_path}" 2>/dev/null || echo 0)"
  size="${size//[[:space:]]/}"
  if [ -n "${size}" ] && [ "${size}" -gt "${POLL_WATCHDOG_LOG_MAX_BYTES}" ] 2>/dev/null; then
    mv -f "${log_path}" "${log_path}.1" 2>/dev/null || true
  fi
  local header
  header="[tick] $(date +'%Y-%m-%dT%H:%M:%S%z')"
  { printf '%s\n' "${header}"; printf '%s\n' "${body}"; } >>"${log_path}" 2>/dev/null || true
}

# issue #1497 req 2: a liveness stamp, owned solely by this tick loop and
# written on EVERY iteration regardless of the due/not-due outcome below —
# so staleness reflects the loop's own wake cadence, not the shared
# poll_due() TTL race (survey's "Death-vs-TTL-quiet mechanics": that race
# already has three callers and cannot itself disambiguate "the Monitor
# ticked" from "a hook ticked"). flock-guarded like poll_due()
# (spawn.py:2356-2381) rather than an unlocked write, per the same
# established atomic-file-state convention. Separate from
# poll_heartbeat_last_state.json (the #1220 delta-suppression state) and
# from the workspace-keyed one-shot alive marker (#1280) — neither can
# stand in for this without reintroducing the disambiguation gap.
_alive_stamp_path="${CHECKOUT}/runs/poll_heartbeat_alive.json"
_alive_stamp_write() {
  mkdir -p "${CHECKOUT}/runs" 2>/dev/null || true
  (
    flock -x 200
    printf '{"last_tick": %s}' "$(date +%s)" >"${_alive_stamp_path}.tmp" 2>/dev/null \
      && mv -f "${_alive_stamp_path}.tmp" "${_alive_stamp_path}" 2>/dev/null
  ) 200>"${_alive_stamp_path}.lock"
}

tick=0
max_ticks="${POLL_HEARTBEAT_MAX_TICKS:-0}"
sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"
while true; do
  sleep "${sleep_seconds}"
  _alive_stamp_write
  # issue #2163: CHECKOUT is resolved ONCE, above, at Monitor-session
  # startup -- it is never re-resolved per tick. A mid-session
  # `claude plugin marketplace update` (stale-directory cleanup +
  # re-clone) removes and recreates that same directory tree while this
  # loop is sleeping between ticks; a tick landing inside that window
  # used to launch each `python3 .../spawn.py` subprocess below with no
  # existence check, and python3 itself failed to open the momentarily-
  # missing script file (errno 2, "No such file or directory") once per
  # subprocess -- a multi-subprocess crash burst for one transient
  # condition. Reuse the same existence signal poll_rearm_resolve_checkout
  # already trusts (spawn.py present at CHECKOUT) and skip the WHOLE tick
  # with one advisory line, instead of letting every subprocess below
  # fail independently.
  if [ ! -f "${CHECKOUT}/spawn.py" ]; then
    printf '[poll-heartbeat] checkout unavailable at %s (mid-update?), skipping tick\n' "${CHECKOUT}"
    tick=$((tick + 1))
    if [ "${max_ticks}" != "0" ] && [ "${tick}" -ge "${max_ticks}" ]; then
      break
    fi
    continue
  fi
  due_out="$(python3 "${CHECKOUT}/spawn.py" poll-due 2>&1 >/dev/null)"
  due_rc=$?
  if [ "${due_rc}" -eq 0 ]; then
    report="$(python3 "${CHECKOUT}/spawn.py" watchdog --auto-respawn 2>&1)"
    watchdog_rc=$?
    _poll_watchdog_log_append "${report}"
    if [ -n "${report}" ]; then
      printed_text="${report}"
    else
      printed_text="poll tick: due, watchdog ran (rc=${watchdog_rc}, no output)"
    fi
    # issue #1274: roster_watchdog()'s contract (spawn.py) makes its exit
    # code the ANOMALY COUNT (0=clean, N=N anomalies) — never a crash
    # flag. A non-zero rc alone is routine anomaly reporting (the
    # per-entry lines above already carry it); labeling it
    # [watchdog-crash] fires a false alarm on every tick with even one
    # benign anomaly. A real crash is only rc>=128 (the shell's
    # signal-death encoding, e.g. SIGKILL=137) or the reserved
    # WATCHDOG_CRASH_SENTINEL (spawn.py, currently 97) that spawn.py's
    # watchdog CLI branch exits on an unhandled internal exception —
    # append a recognizable marker line so the line-keyed diff below (an
    # always-emit "crash" category, issue #1220 req #3) never suppresses
    # it even if two consecutive crash ticks carry the same rc.
    if [ "${watchdog_rc}" -ge 128 ] || [ "${watchdog_rc}" -eq 97 ]; then
      printed_text="$(printf '%s\n[watchdog-crash] watchdog exited rc=%s' "${printed_text}" "${watchdog_rc}")"
    fi
    # issue #1220: replaced #1117's whole-text SHA-256 suppression with a
    # line-keyed diff against the previous tick's state — unchanged lines
    # print nothing, changed/new lines print just their delta, and a
    # fixed always-emit category (crash/dead/orphaned/resume) prints
    # every tick regardless of diff. Persisted as JSON at
    # runs/poll_heartbeat_last_state.json, the #1117 sibling-file
    # convention's successor (docs/issue-1220/proposals/delta-only-monitor-emission.md).
    # Also emits a bounded ~30min aliveness heartbeat when a due tick would
    # otherwise be fully suppressed for that long, so the Monitor channel
    # never goes silent past a bound (issue req #1220).
    # issue #2266 (fix for #1719's landmine, made worse by #2181): the
    # delta-diff logic used to live inline as a `python3 - <<'PY' ... PY`
    # heredoc inside this $( ) capture -- bash 3.2 miscounts quote nesting
    # through a heredoc body while scanning for the enclosing $( )'s own
    # closing paren, so any edit that changed the heredoc body's total
    # apostrophe count could flip `bash -n` from clean to a syntax error.
    # Extracted to on-the-record/monitors/poll_heartbeat_delta.py so no
    # bash version has to tokenize Python source through a quoted
    # delimiter at all -- removes the landmine structurally instead of
    # re-balancing the apostrophe count.
    diff_output="$(POLL_HEARTBEAT_TEXT="${printed_text}" python3 "${SCRIPT_DIR}/poll_heartbeat_delta.py" "${CHECKOUT}/runs/poll_heartbeat_last_state.json" "$(date +%s)")"
    if [ -n "${diff_output}" ]; then
      printf '%s\n' "${diff_output}"
    fi
  else
    if [ -n "${due_out}" ]; then
      _poll_watchdog_log_append "$(printf '[poll-due crashed, rc=%s] %s' "${due_rc}" "${due_out}")"
    fi
    # issue #1220: non-due ticks are now fully silent (no "skipped (within
    # TTL)" line) — delta-only emission means a normal within-TTL tick
    # produces zero Monitor-visible output, not a constant per-minute echo.
  fi
  tick=$((tick + 1))
  if [ "${max_ticks}" != "0" ] && [ "${tick}" -ge "${max_ticks}" ]; then
    break
  fi
done
