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
# armed" line. Instead it runs `spawn.py watchdog` in the
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
# session's lifetime as designed. issue #2977: POLL_HEARTBEAT_ALIVE_LOCK_RETRY_SLEEP=<n>
# overrides the alive-stamp-lock acquire loop's own per-iteration sleep
# (default 1s) and POLL_HEARTBEAT_RECLAIM_LOG_WINDOW=<n> overrides the
# dead/forming reclaim-log collapse window (default 5s) — both let tests
# exercise heavy lock contention without waiting out real time. Unset in
# production.
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
# issue #3293: OWNER TOKEN. Every session's heartbeat used to have a
# byte-identical command line and share one workspace-keyed alive marker,
# so nothing told this session's heartbeat apart from a neighbour's. Both
# consequences were observed on 2026-09-03: a session tidying what it
# reasonably read as duplicate heartbeats killed another session's with a
# `pkill -f` pattern that cannot be narrowed, and an orchestrator wanting
# to stop only its own had no way to name it.
#
# The token is this process's pid plus its start tick -- the pid-reuse-proof
# pairing `roster.py::_paired_liveness()` already trusts, since the OS will
# not hand out that combination twice. Exported so children see it, and
# echoed once so an operator can match a heartbeat to the session that
# armed it.
if [ -z "${OTR_MONITOR_OWNER:-}" ]; then
  OTR_MONITOR_OWNER="$(python3 -c '
import sys
pid = sys.argv[1]
try:
    with open("/proc/%s/stat" % pid, "r", encoding="utf-8") as f:
        raw = f.read()
    start = raw[raw.rfind(")") + 2:].split()[19]
except (OSError, IndexError, ValueError):
    # No /proc (macOS). `ps -o lstart=` answers on both platforms, and
    # without it the token degraded to "nostat", which monitor_ownership
    # then accepted on the pid alone -- reopening the pid-reuse hole the
    # token exists to close.
    import subprocess
    try:
        out = subprocess.run(["ps", "-p", pid, "-o", "lstart="],
                             capture_output=True, text=True, timeout=5)
        start = out.stdout.strip().replace(" ", "_") or "nostat"
    except Exception:
        start = "nostat"
print("%s.%s" % (pid, start))
' "$$" 2>/dev/null)"
  [ -n "${OTR_MONITOR_OWNER}" ] || OTR_MONITOR_OWNER="$$.unknown"
fi
export OTR_MONITOR_OWNER
# Recorded, not printed. Startup stdout is the Monitor's event stream and
# several tests pin it to empty at arm time; an owner line there would be a
# per-session banner in a channel reserved for things worth waking for. The
# token is still discoverable two ways that do not cost a wake:
# `spawn.py monitor-list`, and this log.
OTR_MONITOR_OWNER_NOTE="[poll-heartbeat] owner=${OTR_MONITOR_OWNER} pid=$$ -- stop only this one: python3 ${CHECKOUT}/spawn.py monitor-stop --owner ${OTR_MONITOR_OWNER}"

_alive_dir="$(PWD_P="$(pwd -P)" python3 -c '
import hashlib, os
root = os.environ.get("PWD_P", "")
h = hashlib.sha256(root.encode("utf-8", "surrogatepass")).hexdigest()[:24]
print(os.path.join(os.path.expanduser("~/.claude/tokenmaxxxer/monitor-alive"), h))
' 2>/dev/null)"
if [ -n "${_alive_dir}" ]; then
  mkdir -p "${_alive_dir}" 2>/dev/null && \
    touch "${_alive_dir}/alive" 2>/dev/null || true
  # issue #3293: an owner-scoped marker alongside the shared one. The
  # shared `alive` stays exactly as it was -- directive.sh's degradation
  # check reads it and is not in this change's scope -- but a per-owner
  # file lets a session prove which heartbeat is its own.
  if [ -n "${OTR_MONITOR_OWNER:-}" ]; then
    printf '%s\n' "$$" > "${_alive_dir}/owner-${OTR_MONITOR_OWNER}" 2>/dev/null || true
  fi
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

# issue #2977: a contended alive-stamp-lock can drive the `dead`/`forming`
# reclaim branches inside _alive_stamp_write's acquire loop into a
# per-iteration log stream (up to ~1/s per contending process, more in
# aggregate across concurrently contending processes) -- enough to push
# the Monitor past its own output limit and silence every other signal it
# would otherwise surface. This does NOT apply to the max-age
# force-reclaim valve (the safety-valve line, logged directly via
# _poll_watchdog_log_append, unchanged, never routed through here) or to
# the release-skipped path -- neither repeats per-iteration inside a
# single wait, so neither is the flood source this bounds.
#
# _reclaim_log_bounded logs the first collapsible reclaim event in a
# window immediately, then folds further events in the same window into
# a counter instead of logging each one -- bounding total output -- and
# flushes that counter into the NEXT emitted line once the window
# elapses, so every event is still reflected in a count, never silently
# dropped (docs/issue-2977: "still reports that the events occurred and
# how many"). _reclaim_log_flush emits any remainder that never hit a
# window boundary, called once the lock is finally acquired, so a run
# that ends mid-window still reports its count rather than dropping it.
#
# State (_reclaim_collapsed_count / _reclaim_last_logged_ts /
# _reclaim_log_window) lives in the caller's (_alive_stamp_write's)
# `local`s -- bash's dynamic scoping makes them visible here because
# these are only ever called from inside that function's call stack, not
# invoked standalone. POLL_HEARTBEAT_RECLAIM_LOG_WINDOW overrides the
# window (seconds) for tests; POLL_HEARTBEAT_ALIVE_LOCK_RETRY_SLEEP
# (used at the acquire loop's own retry sleeps below) overrides the
# per-iteration delay for the same reason -- both unset in production.
_reclaim_log_bounded() {
  local _msg="$1"
  local _window="${_reclaim_log_window:-5}"
  local _now
  _now="$(date +%s)"
  _reclaim_collapsed_count=$((_reclaim_collapsed_count + 1))
  if [ "${_reclaim_last_logged_ts}" -eq 0 ] || [ "$((_now - _reclaim_last_logged_ts))" -ge "${_window}" ]; then
    _poll_watchdog_log_append "$(printf '%s (bounded: %s reclaim event(s) counted in this window)' "${_msg}" "${_reclaim_collapsed_count}")"
    _reclaim_last_logged_ts="${_now}"
    _reclaim_collapsed_count=0
  fi
}

_reclaim_log_flush() {
  local _lockfile_for_msg="$1"
  if [ "${_reclaim_collapsed_count}" -gt 0 ]; then
    _poll_watchdog_log_append "$(printf '[alive-stamp-lock] %s further reclaim event(s) on lockfile %s occurred while waiting (window not yet elapsed at acquisition; reporting count now)' "${_reclaim_collapsed_count}" "${_lockfile_for_msg}")"
    _reclaim_collapsed_count=0
  fi
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
# issue #2919: flock ships with util-linux and is absent on macOS by
# default (and this script must not require consumers to install it or a
# newer bash). Detected once here, not per tick, so the hot loop below
# pays no extra cost on the common Linux/flock host. When flock is
# missing, _alive_stamp_write falls back to an mkdir-based mutex — mkdir
# is atomic on every POSIX filesystem, so this still serialises
# concurrent writers to the same stamp file instead of silently letting
# the write race (the earlier behaviour: the flock subshell errored to
# stderr and the write still happened, unserialised, while the tick kept
# reporting success).
if command -v flock >/dev/null 2>&1; then
  _alive_stamp_has_flock=1
else
  _alive_stamp_has_flock=0
fi

# issue #2919 follow-up (adversarial review of the original mkdir-mutex
# fix, docs/issue-2919/reports/adversarial-review-a4f05242.md "Open
# findings"): a live but merely SLOW holder was being evicted by the
# 20-failed-retries-then-force-break threshold below, because that
# threshold inferred staleness purely from elapsed wait time -- it never
# checked whether the holder was actually still running. Sprouted out
# (refactoring-legacy-seam-selection rule 1: single, clearly-localized
# behavioral change -> Sprout Method) so the liveness decision is
# independently testable without exercising the full acquire/release
# sequence. Liveness is ESTABLISHED via the recorded owner PID (`kill -0`,
# same-host signal-0 existence probe), never inferred from a retry count.
# Echoes exactly one of:
#   alive   - the lockfile names a PID and that process still exists --
#             the caller must keep waiting, no matter how many retries
#             have elapsed. This is the fix: a slow-but-alive holder is
#             never reported stale.
#   dead    - the lockfile names a PID and `kill -0` confirms it no
#             longer exists -- safe to reclaim now, established rather
#             than assumed.
#   forming - the lockfile exists but has no readable owner PID in it
#             yet. issue #2919 follow-up (adversarial-review-95d4569a
#             point 1): under the prior two-step "mkdir dir, then
#             separately printf a pid file inside it" acquire sequence
#             this was the NORMAL window every acquire passed through,
#             wide enough that a host-load pause of the acquiring
#             shell between the two separate commands (live-reproduced
#             at >3s) got a still-alive holder evicted. Acquisition
#             below now creates the lockfile and writes the owner pid
#             in one shell redirection (`_alive_stamp_write`'s
#             noclobber write), so this status is reachable only via a
#             write that crashed between opening the file and writing
#             its content -- exceptional, not the common case -- and
#             the short grace period below exists for that residual,
#             not for ordinary acquisition.
_alive_stamp_lock_owner_status() {
  local _lockfile="$1"
  local _owner_pid
  _owner_pid="$(cat "${_lockfile}" 2>/dev/null)"
  if [ -z "${_owner_pid}" ]; then
    printf 'forming'
    return 0
  fi
  if kill -0 "${_owner_pid}" 2>/dev/null; then
    printf 'alive'
  else
    printf 'dead'
  fi
}

_alive_stamp_write() {
  mkdir -p "${CHECKOUT}/runs" 2>/dev/null || true
  if [ "${_alive_stamp_has_flock}" -eq 1 ]; then
    (
      flock -x 200
      printf '{"last_tick": %s}' "$(date +%s)" >"${_alive_stamp_path}.tmp" 2>/dev/null \
        && mv -f "${_alive_stamp_path}.tmp" "${_alive_stamp_path}" 2>/dev/null
    ) 200>"${_alive_stamp_path}.lock"
  else
    local _lockfile="${_alive_stamp_path}.lockfile"
    local _tries=0
    local _forming_tries=0
    # issue #2977: see _reclaim_log_bounded/_reclaim_log_flush above --
    # these locals are the shared state those functions read/write via
    # bash's dynamic scoping, and the retry-sleep override lets tests
    # exercise many iterations without waiting out real 1s sleeps.
    local _reclaim_log_window="${POLL_HEARTBEAT_RECLAIM_LOG_WINDOW:-5}"
    local _reclaim_collapsed_count=0
    local _reclaim_last_logged_ts=0
    local _alive_stamp_lock_retry_sleep="${POLL_HEARTBEAT_ALIVE_LOCK_RETRY_SLEEP:-1}"
    # issue #2919 follow-up (adversarial-review-95d4569a point 1, "the
    # forming boundary"): the prior design split acquisition into two
    # separate top-level commands -- `mkdir "${_lockdir}"` to claim the
    # lock, then a later `printf ... >"${_owner_pid_file}"` to publish
    # who claimed it. Nothing stopped the acquiring shell from being
    # descheduled by the OS between those two commands, and a
    # contending waiter reading the lockdir in that gap saw "claimed,
    # but nobody says by whom" -- indistinguishable from a holder that
    # crashed before ever recording its pid. Live-reproduced: a holder
    # sleeping 5s between its own mkdir and its own pid write got
    # reclaimed by a waiter at the 3s mark, and then the original
    # holder's now-orphaned pid write failed silently and it fell
    # through into the stamp write with no lock held -- the same
    # unprotected-concurrent-write shape PR #2923 was meant to close.
    #
    # Fix: collapse "claim" and "publish identity" into ONE shell
    # command. `set -o noclobber` makes `printf '%s' "$$" >file` open
    # the file with O_EXCL -- atomic exclusive-create at the kernel
    # level, the same guarantee `mkdir` gave for a directory -- and
    # that same command's own printf writes our pid through the
    # already-open fd before control returns to this loop. There is no
    # bash-level command boundary between "the lockfile exists" and
    # "the lockfile names its owner" for a scheduler pause to land in,
    # because there is only one command; a waiter can no longer catch
    # this holder's lockfile in a claimed-but-anonymous state as a
    # result of ITS shell being paused between two separate steps.
    #
    # This does not claim a literal zero-width window: the open() and
    # the write() that follows it inside the same command are still two
    # kernel calls, and a reader could in principle observe the file
    # between them. That residual is not the bug this issue reports --
    # it cannot be widened by host load or scheduling the way a gap
    # between two top-level shell commands could, because no other
    # command from this script runs in between to be delayed. The
    # `forming` grace below stays as a defensive backstop for exactly
    # that residual (or a write killed mid-syscall), not as the primary
    # mechanism -- see the status echoed by _alive_stamp_lock_owner_status
    # above.
    local _forming_grace=3
    # issue #2919 follow-up (adversarial-review-95d4569a point 2): `kill
    # -0` cannot tell a genuinely live holder from an unreaped zombie --
    # a crashed process whose exit status its parent has not yet
    # collected still answers `kill -0` as if it existed. Who reaps a
    # crashed poll-heartbeat.sh, and how promptly, is a Claude Code
    # plugin Monitor platform behaviour with no repo-visible spawn/reap
    # code (docs/specs/platform-capabilities.md) -- this repository
    # cannot establish it, so "a crashed holder's lock always recovers"
    # is NOT a guarantee this fix can make solely from pid liveness. If
    # the real owner is a zombie the platform never reaps, `_status`
    # would read "alive" forever and a waiter would block forever.
    # ${_alive_stamp_lock_max_age} is a second, independent recovery
    # path that does not trust pid liveness at all: once a waiter has
    # been trying to acquire this lock longer than this many seconds,
    # it force-reclaims regardless of what the liveness check says. The
    # default (60s) is chosen with deliberate margin above the longest
    # legitimate hold this fix's own verification demonstrated (a 25s
    # slow-but-alive holder, adversarial-review-95d4569a point 1) and
    # well inside the 120s tick cadence, so a zombie-shadowed lock costs
    # at most about one tick's worth of delay rather than an unbounded
    # wait -- it does not make the zombie case impossible, it bounds
    # its cost. This IS a deliberate, honestly-stated trade: if a holder
    # is still genuinely alive and legitimately working past 60s (not
    # demonstrated as realistic for this small a write, but not provable
    # impossible either), the valve force-reclaims it anyway and a second
    # writer proceeds concurrently -- the exact unprotected-write failure
    # shape this issue exists to close, deliberately reintroduced for
    # holds beyond 60s in exchange for guaranteeing forward progress
    # against a hold that never legitimately ends (the zombie case). No
    # mechanism in this repo can distinguish "genuinely still working"
    # from "zombie that will never be reaped" from the outside, so this
    # is the honest floor, not an unqualified "never deadlocks" claim.
    # POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE overrides it for tests.
    local _alive_stamp_lock_max_age="${POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE:-60}"
    local _wait_started
    _wait_started="$(date +%s)"
    local _status
    local _owner_pid_at_release
    while ! ( set -o noclobber; printf '%s' "$$" >"${_lockfile}" ) 2>/dev/null; do
      _tries=$((_tries + 1))
      if [ "$(($(date +%s) - _wait_started))" -ge "${_alive_stamp_lock_max_age}" ]; then
        # silent-failure-audit (issue #2919): logged, not just broken --
        # this is a deliberate override of the liveness check, not a
        # normal reclaim, and must say so rather than read identically
        # to the `dead` branch below.
        _poll_watchdog_log_append "$(printf '[alive-stamp-lock] lockfile %s exceeded max wait %ss (owner pid %s) -- force-reclaimed independent of liveness check (zombie/reap-uncertainty safety valve, not a normal stale-lock reclaim)' "${_lockfile}" "${_alive_stamp_lock_max_age}" "$(cat "${_lockfile}" 2>/dev/null)")"
        rm -f "${_lockfile}" 2>/dev/null || true
        _forming_tries=0
        _wait_started="$(date +%s)"
        sleep "${_alive_stamp_lock_retry_sleep}"
        continue
      fi
      _status="$(_alive_stamp_lock_owner_status "${_lockfile}")"
      case "${_status}" in
        dead)
          # silent-failure-audit (issue #2919): logged, not just broken --
          # a stale lock silently cleared reads identically to "no
          # contention happened" otherwise, hiding a prior writer's crash.
          # issue #2977: routed through _reclaim_log_bounded, not logged
          # directly -- a contended lock cycling through repeatedly
          # re-created dead owners must not turn this into a
          # per-iteration stream (the defect this issue reports); the
          # bound still reports every event's occurrence and count.
          _reclaim_log_bounded "$(printf '[alive-stamp-lock] stale lockfile %s (owner pid %s confirmed dead) reclaimed after %ss wait' "${_lockfile}" "$(cat "${_lockfile}" 2>/dev/null)" "${_tries}")"
          rm -f "${_lockfile}" 2>/dev/null || true
          _forming_tries=0
          ;;
        forming)
          _forming_tries=$((_forming_tries + 1))
          if [ "${_forming_tries}" -ge "${_forming_grace}" ]; then
            # issue #2977: same bounding as the `dead` branch above.
            _reclaim_log_bounded "$(printf '[alive-stamp-lock] stale lockfile %s (no owner pid recorded after %ss wait) reclaimed' "${_lockfile}" "${_tries}")"
            rm -f "${_lockfile}" 2>/dev/null || true
            _forming_tries=0
          fi
          ;;
        alive)
          # never evict a live holder, no matter how many retries elapse
          # -- this is the defect fix itself (adversarial review point
          # 10): the prior threshold broke a merely-slow, still-running
          # holder's lock and let a second writer enter concurrently.
          _forming_tries=0
          ;;
      esac
      sleep "${_alive_stamp_lock_retry_sleep}"
    done
    # issue #2977: report any dead/forming reclaims that occurred but
    # never hit a window boundary while waiting -- the lock is acquired
    # now, so this is the last chance to reflect their count rather than
    # dropping it silently.
    _reclaim_log_flush "${_lockfile}"
    # only reachable once the noclobber write above has ATOMICALLY
    # created the lockfile with our own pid already inside it -- there
    # is no separate publish-identity step left to race, and no
    # reclaimed-stale-lock path falls through into the critical section
    # unprotected.
    printf '{"last_tick": %s}' "$(date +%s)" >"${_alive_stamp_path}.tmp" 2>/dev/null \
      && mv -f "${_alive_stamp_path}.tmp" "${_alive_stamp_path}" 2>/dev/null
    # issue #2919 follow-up (adversarial-review-67ff85fb finding 1): the
    # max-age valve above can force-reclaim THIS holder's own lockfile
    # while this holder is still genuinely alive and mid-write (the
    # valve's own disclosed trade-off, documented above). When that
    # happens, a later contender re-acquires the lockfile with ITS OWN
    # pid before this holder ever reaches here -- an unconditional
    # `rm -f` at that point deletes THAT holder's live lock, not this
    # holder's already-gone slot, letting a further contender in
    # alongside it (live-reproduced: adversarial-review-67ff85fb,
    # PRE_RELEASE_OWNER_CHECK instrumentation showed worker A remove
    # worker B's active lockfile, worker D then entering alongside
    # still-active B). Mirrors the acquire-side fix above
    # (adversarial-review-95d4569a point 1): re-verify ownership
    # immediately before acting, never remove on the strength of "I
    # created this file at some point in the past."
    #
    # Residual: the `cat` (read) below and the `rm -f` (remove) are
    # still two separate commands, so a scheduler pause between them is
    # not literally impossible -- if THIS holder's own eviction by the
    # max-age valve lands in that exact gap (after the read confirms
    # ownership but before the rm executes), the same failure shape
    # could in principle reappear. That window is now bounded by two
    # adjacent syscalls rather than this holder's entire remaining
    # hold-plus-write duration (previously reachable any time up to
    # several seconds under load, per the max-age valve's own stated
    # >60s trade-off) -- narrower by orders of magnitude, not proven
    # zero, the same honesty standard the noclobber acquire fix above
    # applies to its own open()/write() gap.
    _owner_pid_at_release="$(cat "${_lockfile}" 2>/dev/null)"
    if [ "${_owner_pid_at_release}" = "$$" ]; then
      rm -f "${_lockfile}" 2>/dev/null || true
    else
      # silent-failure-audit (issue #2919): logged, not silently
      # skipped -- this release is a deliberate no-op because the
      # lockfile now belongs to a different, active holder, not an
      # error, but it must not read identically to an ordinary quiet
      # release.
      _poll_watchdog_log_append "$(printf '[alive-stamp-lock] release skipped: lockfile %s no longer names this holder (pid %s) -- current owner %s (this holder was likely force-reclaimed by the max-age valve while still alive; removing would delete a live holder'"'"'s lock)' "${_lockfile}" "$$" "${_owner_pid_at_release:-<empty>}")"
    fi
  fi
}

# issue #3293: record the owner token now that the log helper exists.
_poll_watchdog_log_append "${OTR_MONITOR_OWNER_NOTE}"

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
    report="$(python3 "${CHECKOUT}/spawn.py" watchdog 2>&1)"
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
    elif [ "${watchdog_rc}" -eq 95 ]; then
      # issue #3120 layer 1: WATCHDOG_STALE_CODE_SENTINEL (spawn.py,
      # currently 95) — watchdog_freshness_check (watchdog.py) detected
      # that the checkout HEAD moved out from under this tick (a git
      # pull, a `claude plugin marketplace update`, or an ordinary
      # merge). This is neither the crash case above nor routine
      # silence; give it its own tellable-apart label instead of letting
      # it fall through unclassified — that is exactly how issue #3120
      # went unnoticed until a live capture caught it.
      printed_text="$(printf '%s\n[watchdog-stale-code] watchdog exited rc=%s (checkout HEAD changed — restarting)' "${printed_text}" "${watchdog_rc}")"
    fi
    # issue #1220: replaced #1117's whole-text SHA-256 suppression with a
    # line-keyed diff against the previous tick's state — unchanged lines
    # print nothing, changed/new lines print just their delta, and a
    # fixed always-emit category (crash/dead/orphaned/resume) prints
    # every tick regardless of diff. Persisted as JSON at
    # runs/poll_heartbeat_last_state.json, the #1117 sibling-file
    # convention's successor (docs/issue-1220/proposals/delta-only-monitor-emission.md).
    # issue #1732 removed the #1220-era unconditional ~30min "monitoring
    # active, no changes" backstop outright (content-free, exactly what
    # #2913/issue #2915 forbid reintroducing). issue #2915 round 2 adds a
    # narrower, content-CARRYING replacement in poll_heartbeat_delta.py's
    # own 1800s-bound branch: a non-empty tracked roster that stays fully
    # suppressed for 1800s now re-emits each entry's real current state
    # under a `[monitor-heartbeat]` tag (not a static phrase). A genuinely
    # empty roster (nothing tracked) stays exactly as silent past the
    # bound as #1732 left it — see poll_heartbeat_delta.py and
    # docs/handbooks/monitor-liveness.md's "Issue #2915" section for the
    # measured before/after.
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
    if [ "${watchdog_rc}" -eq 95 ]; then
      # issue #3120 layer 2: self-heal instead of leaving the tick loop
      # running indefinitely against a checkout the freshness check has
      # already decided is stale, with nothing to restart it (the
      # "재기동 필요" sentinel used to be delivered and then ignored).
      # `exec` replaces this process's OWN image in the SAME pid — a
      # live probe against this session's own real platform Monitor
      # process (docs/issue-3120/reports/.../record.md "What was done")
      # confirmed its stdout/stderr are fds inherited from its parent
      # (sockets, not files the platform re-opens by path), and `exec`
      # never touches open file descriptors — so a downstream reader of
      # this process's output sees no gap across the restart, and
      # startup_head gets re-captured fresh in the new image. Guard on
      # the exec TARGET's own presence first: measured directly (not
      # assumed) that `exec` into a file that is momentarily absent
      # (mid checkout-update) kills the process outright — bash reports
      # "No such file or directory" and exits 127, the whole loop gone,
      # never reaching another tick. This reuses the same
      # "checkout mid-update" signal the loop's own spawn.py-presence
      # guard above already trusts (issue #2163), applied to the actual
      # exec target rather than exec'ing into nothing.
      _exec_target="${CHECKOUT}/on-the-record/monitors/poll-heartbeat.sh"
      if [ -f "${_exec_target}" ]; then
        printf '[poll-heartbeat] stale code (rc=95) -- restarting via exec %s\n' "${_exec_target}"
        exec bash "${_exec_target}"
      else
        printf '[poll-heartbeat] stale code (rc=95) but restart target unavailable at %s (mid-update?) -- skipping restart this tick\n' "${_exec_target}"
      fi
    fi
  else
    if [ -n "${due_out}" ]; then
      _poll_watchdog_log_append "$(printf '[poll-due crashed, rc=%s] %s' "${due_rc}" "${due_out}")"
    fi
    # issue #1220: non-due ticks carry no watchdog output — the sibling
    # session that claimed this window runs the sweep.
    # issue #3293: but the tick must still WAKE. A session whose window a
    # sibling claimed used to produce nothing at all, so "wake every 120
    # seconds" quietly depended on winning a race against every other
    # session sharing this checkout. `tick-payload` is the read-only half:
    # no lock, no ledger write, no gh call, so running it in every session
    # every tick leaves poll-due's single-writer protection untouched.
    payload="$(python3 "${CHECKOUT}/spawn.py" tick-payload 2>/dev/null)"
    # Printed straight through, not via poll_heartbeat_delta.py: the
    # payload is exempt from that filter by design, and routing it there
    # would also have this branch write the shared last-state file that the
    # due branch owns.
    if [ -n "${payload}" ]; then
      printf '%s\n' "${payload}"
    fi
  fi
  tick=$((tick + 1))
  if [ "${max_ticks}" != "0" ] && [ "${tick}" -ge "${max_ticks}" ]; then
    break
  fi
done
