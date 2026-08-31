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
        sleep 1
        continue
      fi
      _status="$(_alive_stamp_lock_owner_status "${_lockfile}")"
      case "${_status}" in
        dead)
          # silent-failure-audit (issue #2919): logged, not just broken --
          # a stale lock silently cleared reads identically to "no
          # contention happened" otherwise, hiding a prior writer's crash.
          _poll_watchdog_log_append "$(printf '[alive-stamp-lock] stale lockfile %s (owner pid %s confirmed dead) reclaimed after %ss wait' "${_lockfile}" "$(cat "${_lockfile}" 2>/dev/null)" "${_tries}")"
          rm -f "${_lockfile}" 2>/dev/null || true
          _forming_tries=0
          ;;
        forming)
          _forming_tries=$((_forming_tries + 1))
          if [ "${_forming_tries}" -ge "${_forming_grace}" ]; then
            _poll_watchdog_log_append "$(printf '[alive-stamp-lock] stale lockfile %s (no owner pid recorded after %ss wait) reclaimed' "${_lockfile}" "${_tries}")"
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
      sleep 1
    done
    # only reachable once the noclobber write above has ATOMICALLY
    # created the lockfile with our own pid already inside it -- there
    # is no separate publish-identity step left to race, and no
    # reclaimed-stale-lock path falls through into the critical section
    # unprotected.
    printf '{"last_tick": %s}' "$(date +%s)" >"${_alive_stamp_path}.tmp" 2>/dev/null \
      && mv -f "${_alive_stamp_path}.tmp" "${_alive_stamp_path}" 2>/dev/null
    rm -f "${_lockfile}" 2>/dev/null || true
  fi
}

tick=0
# issue #1598 (patrol wiring E2): patrol_tick is its OWN counter,
# independent of `tick` above — the validity consult flagged reusing
# `tick`'s counting assumptions, and the proposal (PR #1600) requires the
# promote-poll cadence to be separate state so a future change to `tick`'s
# semantics cannot silently retime patrol promotion.
patrol_tick=0
patrol_every_n="${POLL_HEARTBEAT_PATROL_EVERY_N:-5}"
# issue #2919: `read -a` on empty stdin leaves the array name completely
# UNDEFINED under bash 3.2 (not defined-and-empty), and even a literal
# `ARR=()` expands as "unbound variable" under `set -u` pre-bash-4.4 --
# both a failed role_data() query and a genuinely-empty roster produce
# the same empty stdin here, so the rc is captured separately to tell
# them apart (must-not: don't make those two conditions indistinguishable
# — precedent controller #521/#523 for the unguarded-expansion class).
_patrol_skills_query_failed=0
_patrol_skills_query_out="$(python3 -c "
import sys
sys.path.insert(0, '${CHECKOUT}')
import spawn
print(' '.join(sorted(spawn.role_data())))
" 2>&1)"
_patrol_skills_query_rc=$?
if [ "${_patrol_skills_query_rc}" -eq 0 ]; then
  IFS=' ' read -r -a POLL_HEARTBEAT_PATROL_SKILLS <<<"${_patrol_skills_query_out}"
else
  POLL_HEARTBEAT_PATROL_SKILLS=()
  _patrol_skills_query_failed=1
  _poll_watchdog_log_append "$(printf '[patrol-skills query failed, rc=%s] %s' "${_patrol_skills_query_rc}" "${_patrol_skills_query_out}")"
fi
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
  # used to launch one `python3 .../gates/patrol_promote.py` subprocess
  # per configured role (POLL_HEARTBEAT_PATROL_ROLES) with no existence
  # check, and python3 itself failed to open the momentarily-missing
  # script file (errno 2, "No such file or directory") once per role --
  # a 43-role crash burst for one transient condition. Reuse the same
  # existence signal poll_rearm_resolve_checkout already trusts
  # (spawn.py present at CHECKOUT) and skip the WHOLE tick -- due-check
  # and patrol both -- with one advisory line, instead of letting every
  # subprocess below fail independently.
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
  else
    if [ -n "${due_out}" ]; then
      _poll_watchdog_log_append "$(printf '[poll-due crashed, rc=%s] %s' "${due_rc}" "${due_out}")"
    fi
    # issue #1220: non-due ticks are now fully silent (no "skipped (within
    # TTL)" line) — delta-only emission means a normal within-TTL tick
    # produces zero Monitor-visible output, not a constant per-minute echo.
  fi
  # issue #1598 (patrol wiring E2): patrol promotion rides this SAME loop
  # at a reduced, independently-counted cadence — unconditional, outside
  # the due_rc-gated branch above and outside its delta-suppression state
  # file, so a patrol-due tick always prints its own trace line regardless
  # of whether this tick was also heartbeat-due (warrant hunt finding,
  # hunt-patrol-heartbeat-wiring.md: poll-due's TTL is shared with the
  # turn-driven directive.sh hook, so a patrol-due tick is routinely
  # non-due — folding patrol emission into the due-gated report would
  # silently drop promotion trace lines on exactly those ticks).
  # issue #2163: checking every configured role here every patrol_every_n
  # ticks is uncapped BY DESIGN, and deliberately not
  # gates/patrol_wiring.py's MAX_ROLES_PER_MERGE=3 — that cap protects a
  # different, expensive call (spawn.judge_cmd's Haiku-prefiltered judge
  # run at the merge seam); this loop's per-role call
  # (gates/patrol_promote.py) is a cheap board-state read/tick-detect
  # that only reaches a `gh` write when a checkbox was actually ticked,
  # so sweeping all configured roles on a slow, fixed cadence costs one
  # cheap read per role rather than one judge run per role. The two caps
  # are not the same code path and must not be unified.
  patrol_tick=$((patrol_tick + 1))
  if [ "${patrol_every_n}" != "0" ] && [ "$((patrol_tick % patrol_every_n))" -eq 0 ]; then
    if [ -e "${CHECKOUT}/.on-the-record/patrol-disabled" ]; then
      printf '[patrol-poll] disabled, skipped\n'
    else
      _patrol_checked=0
      _patrol_promotions=0
      _patrol_crashed=0
      if [ "${_patrol_skills_query_failed}" -eq 1 ]; then
        # issue #2919: the roster query crashed at Monitor startup, so
        # this loop has nothing to iterate all session long -- say so on
        # every patrol-due tick rather than reading as an indistinguishable
        # quiet "no skills configured" tick (must-not in #2919).
        printf '[patrol-poll] skills query failed at startup, patrol skipped this tick\n'
      fi
      # issue #2919: bash 3.2 (unlike 4.4+) treats even a genuinely-empty
      # declared array as unbound under `set -u` when expanded plainly --
      # confirmed live under bash 3.2.57. The `${arr[@]+"${arr[@]}"}`
      # idiom expands to nothing (zero loop iterations, no error) whether
      # the array is unset, empty, or populated, on both bash 3.2 and 5.x.
      for _patrol_skill in "${POLL_HEARTBEAT_PATROL_SKILLS[@]+"${POLL_HEARTBEAT_PATROL_SKILLS[@]}"}"; do
        _patrol_out="$(python3 "${CHECKOUT}/gates/patrol_promote.py" run "${CHECKOUT}" "${_patrol_skill}" 2>&1)"
        _patrol_rc=$?
        _patrol_checked=$((_patrol_checked + 1))
        if [ "${_patrol_rc}" -ne 0 ]; then
          # warrant hunt finding (hunt-patrol-heartbeat-wiring.md): a
          # per-role patrol_promote.py crash must not vanish silently —
          # logged the same way the existing due_rc-crash path already
          # logs (_poll_watchdog_log_append), plus a Monitor-visible
          # trace line so the failing role is identifiable per tick.
          _poll_watchdog_log_append "$(printf '[patrol-poll crashed, role=%s, rc=%s] %s' "${_patrol_skill}" "${_patrol_rc}" "${_patrol_out}")"
          printf '[patrol-poll] %s: crashed (rc=%s)\n' "${_patrol_skill}" "${_patrol_rc}"
          _patrol_crashed=1
        elif [ -n "${_patrol_out}" ]; then
          _patrol_count="$(printf '%s' "${_patrol_out}" | python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.read())
except (ValueError, TypeError):
    d = {}
print(len(d.get("promotions", [])) if isinstance(d, dict) else 0)
' 2>/dev/null || printf '0')"
          if [ -n "${_patrol_count}" ] && [ "${_patrol_count}" != "0" ]; then
            _patrol_promotions=$((_patrol_promotions + _patrol_count))
            printf '[patrol-poll] %s: %s promotion(s)\n' "${_patrol_skill}" "${_patrol_count}"
          fi
        fi
      done
      # issue #1722: the summary line only fires when there's something to
      # act on (a promotion or a crash) — a quiet tick still runs the
      # patrol and logs it, it just stops waking the Monitor session with
      # a "0 promotion(s)" no-op every patrol_every_n ticks.
      if [ "${_patrol_promotions}" != "0" ] || [ "${_patrol_crashed}" = "1" ]; then
        printf '[patrol-poll] checked %s role(s), %s promotion(s)\n' "${_patrol_checked}" "${_patrol_promotions}"
      fi
    fi
  fi
  tick=$((tick + 1))
  if [ "${max_ticks}" != "0" ] && [ "${tick}" -ge "${max_ticks}" ]; then
    break
  fi
done
