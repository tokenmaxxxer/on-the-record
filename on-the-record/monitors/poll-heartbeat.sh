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

# issue #1245: attachment gate. The Monitor must not register at all (no
# alive marker, no tick loop, no state/log files) for a session whose
# target repo is not an on-the-record board (no docs/specs/approvers.md)
# -- the operator's widened #1219 requirement. Checked before the alive
# marker write below, which is the earliest registration artifact.
if [ ! -f "$(pwd -P)/docs/specs/approvers.md" ]; then
  echo "poll tick: skipped (target repo is not an on-the-record board)"
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
    diff_output="$(POLL_HEARTBEAT_TEXT="${printed_text}" python3 - "${CHECKOUT}/runs/poll_heartbeat_last_state.json" "$(date +%s)" <<'PY'
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
# issue #1239: [returned-pr] joins the always-emit set — the #680 spawn
# gate's undisposed-PR list must survive delta suppression every tick, not
# just when it changes, so neglect stays visible (northpole req#1).
ALWAYS_RE = re.compile(
    r"^\[(resume|orphaned|watchdog-crash|returned-pr)\]|STALLED|CRASHED|COMPLETED|watcher-dead",
    re.IGNORECASE,
)

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
        key = "__fixed__"
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
for key in order:
    line = curr[key]
    if first_tick or prev_lines.get(key) != line or ALWAYS_RE.search(line):
        to_emit.append(line)

emitted_now = False
if to_emit:
    sys.stdout.write("\n".join(to_emit) + "\n")
    emitted_now = True
else:
    last_emit_epoch = int(prev.get("last_emit_epoch", 0) or 0)
    if now - last_emit_epoch >= 1800:
        healthy = sum(1 for k in curr if "#" not in k and not k.startswith("__fixed__"))
        sys.stdout.write(
            f"[heartbeat] monitoring active, {healthy} session(s) tracked, no changes\n"
        )
        emitted_now = True

new_state = {"lines": curr, "last_emit_epoch": now if emitted_now else prev.get("last_emit_epoch", 0)}
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
      mkdir -p "${HOME}/.claude/tokenmaxxxer" 2>/dev/null
      printf '[poll-due crashed, rc=%s] %s\n' "${due_rc}" "${due_out}" \
        >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>/dev/null || true
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
