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
# issue #1598 (patrol wiring E2): patrol_tick is its OWN counter,
# independent of `tick` above — the validity consult flagged reusing
# `tick`'s counting assumptions, and the proposal (PR #1600) requires the
# promote-poll cadence to be separate state so a future change to `tick`'s
# semantics cannot silently retime patrol promotion.
patrol_tick=0
patrol_every_n="${POLL_HEARTBEAT_PATROL_EVERY_N:-5}"
IFS=' ' read -r -a POLL_HEARTBEAT_PATROL_ROLES <<<"$(python3 -c "
import sys
sys.path.insert(0, '${CHECKOUT}')
import spawn
print(' '.join(spawn.ROLES))
" 2>/dev/null)"
max_ticks="${POLL_HEARTBEAT_MAX_TICKS:-0}"
sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"
while true; do
  sleep "${sleep_seconds}"
  _alive_stamp_write
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
    # issue #1719 (macOS stock bash 3.2 landmine): editing the comments in
    # this heredoc body can flip `bash -n`/execution to "unexpected EOF
    # while looking for matching \`\"'" even though the delimiter is
    # quoted (<<'PY', fully literal per POSIX) -- bash 3.2 appears to
    # miscount quote nesting through the body while scanning for this
    # $(...)'s own closing paren. Empirically, changing the total count of
    # apostrophes in this heredoc (not their content) is what flips it;
    # if an edit here breaks parsing, try adjusting an apostrophe count
    # before suspecting anything else.
    diff_output="$(POLL_HEARTBEAT_TEXT="${printed_text}" python3 - "${CHECKOUT}/runs/poll_heartbeat_last_state.json" "$(date +%s)" <<'PY'
import hashlib
import json
import os
import re
import sys

state_path, now_s = sys.argv[1], sys.argv[2]
now = int(now_s)
text = os.environ.get("POLL_HEARTBEAT_TEXT", "")
lines = text.split("\n") if text else []

TAG_RE = re.compile(r"^\[(poll-report|watchdog|health|reconcile|orphaned|resume|watchdog-crash|returned-pr)\]\s*([^:]+):")
ENTRY_RE = re.compile(r"^([\w./-]+/[\w./-]+):\s")
BULLET_RE = re.compile(r"^\s+-\s")
# issue #1719: [returned-pr] no longer joins the always-emit set —
# it is compared below with its age= token stripped instead, so an
# unchanged set doesn't re-announce every tick (supersedes #1239 req 2).
# issue #2133: [awaiting-approval] joins the always-emit set — the healthy
# approval pause must reach the Monitor relay every tick (the remaining-time
# token changes anyway, but the always-emit membership is the contract).
ALWAYS_RE = re.compile(
    r"^\[(resume|orphaned|watchdog-crash|awaiting-approval)\]|STALLED|CRASHED|COMPLETED|watcher-dead",
    re.IGNORECASE,
)
AGE_STRIP_RE = re.compile(r"age=[^ ]+")
# issue #1719: two watchdogs contending for the cross-workspace board-sweep
# lock make this line alternate between a real sweep result and this skip
# text tick to tick; treat the skip text as no-change (never emitted, prior
# sweep state kept) instead of flapping the delta state.
BOARD_SWEEP_LOCK_SKIP_RE = re.compile(
    r"^\[watchdog\] board-sweep:.*건너뜀 \(다른 워크스페이스가 스윕 중\)"
)
# issue #1734: lines matching none of TAG_RE/ENTRY_RE/BULLET_RE used to
# share one fixed placeholder key literal, disambiguated only by an
# appearance-order ordinal -- inserting or dropping one such line shifted
# every following line onto a different ordinal and the delta comparison
# then compared it against a different lines previous text, emitting
# unchanged content as "changed". FIXED_TAG_RE derives a content-carried
# key instead: a broader bracket-tag prefix (not just TAG_REs enumerated
# set) plus a hash of the full line, so a key travels with its own
# content and position no longer matters.
FIXED_TAG_RE = re.compile(r"^\[([^\]]+)\]\s*([^:]+):")

curr = {}
order = []
last_key = None
bullet_ordinal = 0
for line in lines:
    m = TAG_RE.match(line)
    if m:
        key = f"{m.group(1)}:{m.group(2)}"
        last_key = key
        bullet_ordinal = 0
    elif ENTRY_RE.match(line):
        key = f"entry:{ENTRY_RE.match(line).group(1)}"
        last_key = key
        bullet_ordinal = 0
    elif BULLET_RE.match(line) and last_key is not None:
        key = f"{last_key}#{bullet_ordinal}"
        bullet_ordinal += 1
    else:
        line_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()[:12]
        fm = FIXED_TAG_RE.match(line)
        if fm:
            key = f"fixed:{fm.group(1)}:{fm.group(2).strip()}:{line_hash}"
        else:
            key = f"fixed:hash:{line_hash}"
    if key in curr:
        # collision within one tick's text (e.g. two genuinely singleton
        # lines) — keep both by disambiguating with an ordinal so neither
        # is silently dropped.
        n = 1
        while f"{key}~{n}" in curr:
            n += 1
        key = f"{key}~{n}"
    curr[key] = line
    order.append(key)

prev = {"lines": {}, "last_emit_epoch": 0}
if os.path.exists(state_path):
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            prev.update(loaded)
    except (OSError, ValueError):
        pass
prev_lines = prev.get("lines", {})
first_tick = not os.path.exists(state_path)

to_emit = []
new_lines = {}
for key in order:
    line = curr[key]
    if BOARD_SWEEP_LOCK_SKIP_RE.search(line):
        # lock-contention skip is not a real state change: carry the
        # previously known board-sweep line forward (or, if none was ever
        # recorded, fall back to the skip text itself) and never emit it.
        new_lines[key] = prev_lines.get(key, line)
        continue
    new_lines[key] = line
    if key.startswith("returned-pr:"):
        prev_line = prev_lines.get(key)
        changed = prev_line is None or (
            AGE_STRIP_RE.sub("age=", prev_line) != AGE_STRIP_RE.sub("age=", line)
        )
    else:
        changed = prev_lines.get(key) != line
    if first_tick or changed or ALWAYS_RE.search(line):
        to_emit.append(line)

emitted_now = False
if to_emit:
    sys.stdout.write("\n".join(to_emit) + "\n")
    emitted_now = True
else:
    last_emit_epoch = int(prev.get("last_emit_epoch", 0) or 0)
    if now - last_emit_epoch >= 1800:
        # issue #1732: the periodic no-op liveness line is dropped --
        # liveness is already covered by the alive marker
        # (poll-heartbeat.sh:105-114). Only the undisposed-PR set #1719
        # req#1 attached to this bound stays visible, and only when
        # non-empty; an empty result leaves emitted_now False so
        # last_emit_epoch (line 343) stays untouched.
        returned_pr_lines = [curr[k] for k in order if k.startswith("returned-pr:")]
        if returned_pr_lines:
            sys.stdout.write("\n".join(returned_pr_lines) + "\n")
            emitted_now = True

new_state = {"lines": new_lines, "last_emit_epoch": now if emitted_now else prev.get("last_emit_epoch", 0)}
os.makedirs(os.path.dirname(state_path), exist_ok=True)
with open(state_path, "w", encoding="utf-8") as f:
    json.dump(new_state, f)
PY
)"
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
  patrol_tick=$((patrol_tick + 1))
  if [ "${patrol_every_n}" != "0" ] && [ "$((patrol_tick % patrol_every_n))" -eq 0 ]; then
    if [ -e "${CHECKOUT}/.on-the-record/patrol-disabled" ]; then
      printf '[patrol-poll] disabled, skipped\n'
    else
      _patrol_checked=0
      _patrol_promotions=0
      _patrol_crashed=0
      for _patrol_role in "${POLL_HEARTBEAT_PATROL_ROLES[@]}"; do
        _patrol_out="$(python3 "${CHECKOUT}/gates/patrol_promote.py" run "${CHECKOUT}" "${_patrol_role}" 2>&1)"
        _patrol_rc=$?
        _patrol_checked=$((_patrol_checked + 1))
        if [ "${_patrol_rc}" -ne 0 ]; then
          # warrant hunt finding (hunt-patrol-heartbeat-wiring.md): a
          # per-role patrol_promote.py crash must not vanish silently —
          # logged the same way the existing due_rc-crash path already
          # logs (_poll_watchdog_log_append), plus a Monitor-visible
          # trace line so the failing role is identifiable per tick.
          _poll_watchdog_log_append "$(printf '[patrol-poll crashed, role=%s, rc=%s] %s' "${_patrol_role}" "${_patrol_rc}" "${_patrol_out}")"
          printf '[patrol-poll] %s: crashed (rc=%s)\n' "${_patrol_role}" "${_patrol_rc}"
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
            printf '[patrol-poll] %s: %s promotion(s)\n' "${_patrol_role}" "${_patrol_count}"
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
