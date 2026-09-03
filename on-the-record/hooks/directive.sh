#!/usr/bin/env bash
# UserPromptSubmit: the orchestration directive, injected EVERY prompt —
# the coding-rulebook pattern (terse/freelunch/scout): steering must be
# freshly read to steer, and a session-start-only injection drifts out of
# a long context. Installing this plugin IS the opt-in. Kill switch:
# ORCHESTRATE_OFF=1
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

# issue #2028: append-only fire counter -- the #2016 survey left "how
# often does Stop/UserPromptSubmit actually fire per session" an
# unmeasured open finding. One line per firing, written before any
# kill-switch/spawned-session short-circuit below so the count reflects every real
# trip of this hook, not just the ones that go on to do work. Lives under
# the session workspace (the target repo this hook fires in, same
# per-workspace convention GREETED_MARKER below already uses), never the
# shared on-the-record checkout. Best-effort: a write failure here must
# never turn into a directive failure.
#
# issue #2348: sharded per session (hook-fires.sh's hook_fires_record())
# instead of one shared append-only path -- same conflict-elimination
# shape issue #2333 shipped for consult-log.md. Stdin is captured HERE,
# once, before the counter write, so the payload can be reused below for
# the monitor-notice check without a second read (stdin can only be
# consumed once).
_HOOK_PAYLOAD="$(cat 2>/dev/null || true)"
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/hook-fires.sh"
hook_fires_record "UserPromptSubmit directive.sh" "$_HOOK_PAYLOAD"

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
# A spawned session is never the orchestrator, even if the plugin leaks in.
[ -z "${TOKENMAXXXER_SPAWNED:-}" ] || { trap - EXIT; exit 0; }

# issue #947 (northpole req#7): monitor-unavailable degradation notice.
# Plugin Monitors (idle self-wake) run only in interactive CLI sessions
# (docs/specs/platform-capabilities.md); in IDE-extension sessions the
# Monitor never starts and idle self-wake silently degrades to
# turn-driven-only. poll-heartbeat.sh touches a workspace-scoped alive
# marker before its sleep loop; this hook reads its OWN session_id from
# the UserPromptSubmit JSON payload (same contract retry-loop-bound.sh /
# approval-gate.sh already read), records this session's first-seen
# timestamp on first observation, and — past a grace window — checks
# whether the alive marker's mtime is at or after that timestamp. An
# mtime from before this session began cannot be this session's own
# monitor (warrant-hunt finding,
# docs/issue-947/reports/implementation/2026-08-12-hunt-monitor-unavailable-notice.md:
# a session-agnostic marker check would let a live CLI session's marker
# "prove" a later, monitor-less IDE session's monitor is alive). Fails
# open (no notice, no crash) on any missing payload/session_id/parse
# error, matching every other on-the-record hook's stdin-JSON handling.
_MONITOR_NOTICE_PAYLOAD="$_HOOK_PAYLOAD"
if [ -n "$_MONITOR_NOTICE_PAYLOAD" ] && command -v python3 >/dev/null 2>&1; then
  OTR_MN_PAYLOAD="$_MONITOR_NOTICE_PAYLOAD" \
  OTR_MN_ROOT="$(pwd -P)" \
  OTR_MN_GRACE="${MONITOR_NOTICE_GRACE_SECONDS:-600}" \
    python3 - <<'PY' || true
import hashlib
import json
import os
import sys
import time

payload_raw = os.environ.get("OTR_MN_PAYLOAD", "")
# issue #1280: the heartbeat's alive marker moved out of the target repo
# to a workspace-keyed path under ~/.claude/tokenmaxxxer/monitor-alive/,
# hashed by the resolved arm-root path (same formula poll-heartbeat.sh
# uses) -- both sides compute the identical key from their own `pwd -P`
# with no shared state file and no IPC, and it never collides across
# concurrent sessions rooted in different repos.
_otr_mn_root = os.environ.get("OTR_MN_ROOT", "")
marker_dir = (
    os.path.join(
        os.path.expanduser("~/.claude/tokenmaxxxer/monitor-alive"),
        hashlib.sha256(_otr_mn_root.encode("utf-8", "surrogatepass")).hexdigest()[:24],
    )
    if _otr_mn_root
    else ""
)
try:
    grace = int(os.environ.get("OTR_MN_GRACE", "600"))
except ValueError:
    grace = 600

try:
    payload = json.loads(payload_raw)
except ValueError:
    sys.exit(0)
if not isinstance(payload, dict):
    sys.exit(0)
session_id = payload.get("session_id")
if not isinstance(session_id, str) or not session_id or not marker_dir:
    sys.exit(0)
# Hash rather than char-substitute: a substitution sanitizer (e.g.
# re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)) maps distinct ids like
# "sess/a" and "sess?a" to the identical "sess_a", letting one session's
# start/notified bookkeeping silently answer for a different session
# (warrant-hunt finding,
# docs/issue-947/reports/implementation/2026-08-12-hunt-monitor-unavailable-notice-before-landing.md).
# A hash keeps distinct ids collision-free regardless of their characters.
safe_session = hashlib.sha256(session_id.encode("utf-8", "surrogatepass")).hexdigest()[:24]

os.makedirs(marker_dir, exist_ok=True)
start_path = os.path.join(marker_dir, ".session-" + safe_session + "-start")
notified_path = os.path.join(marker_dir, ".session-" + safe_session + "-notified")
alive_path = os.path.join(marker_dir, "alive")

now = time.time()
if not os.path.exists(start_path):
    with open(start_path, "w") as f:
        f.write(str(now))
    sys.exit(0)  # first observation this session: nothing to check yet

if os.path.exists(notified_path):
    sys.exit(0)  # already notified this session, never repeat

try:
    with open(start_path) as f:
        start = float(f.read().strip())
except (OSError, ValueError):
    sys.exit(0)

if (now - start) < grace:
    sys.exit(0)  # still inside the grace window

alive = os.path.exists(alive_path) and os.path.getmtime(alive_path) >= start
if alive:
    # issue #3120: a stale-notice write by an earlier, monitor-late
    # session in this workspace was never cleared once the monitor came
    # up -- grep -rn 'orchestrate-wake-notice' found only the write below
    # and the directive text pointing at it, no unlink on any path. This
    # branch is reachable only when alive is True, so a genuinely absent
    # monitor still falls through to the write unchanged. Best-effort
    # like every other marker touch in this hook: a removal failure must
    # never turn into a directive failure, and a notice that was already
    # absent (FileNotFoundError, an OSError subclass) is not a failure.
    notice_path = os.path.join(_otr_mn_root, ".orchestrate-wake-notice")
    try:
        os.remove(notice_path)
    except OSError:
        pass
    sys.exit(0)

with open(notified_path, "w") as f:
    f.write(str(now))

# issue #2102 (byte-stability): the degradation notice is NEVER printed
# into the per-turn injection -- it was the sole measured variance source
# poisoning prompt-cache reuse (issue #2102 baseline: 5/6 captures
# hash-identical, this line the only diff). It lands once per session in
# a workspace file instead; the always-on index below carries a stable
# pointer line, and directive/monitor-mode.md documents the contract.
notice_path = os.path.join(_otr_mn_root, ".orchestrate-wake-notice")
try:
    with open(notice_path, "w") as f:
        f.write(
            "[orchestrate] idle self-wake is unavailable in this session "
            "(plugin Monitors run only in interactive CLI sessions -- "
            "docs/decisions/2026-08-12-monitor-cli-only-fallback.md); "
            "turn-driven wake via the UserPromptSubmit/Stop poll hooks is "
            "the active mode.\n"
        )
except OSError:
    pass
PY
fi

# Shared checkout resolution + poll-due/watchdog arming (issue #801):
# factored into poll-rearm.sh so UserPromptSubmit (here) and Stop
# (stop-poll-rearm.sh) trip the exact same logic, not two forks of it.
# shellcheck source=./poll-rearm.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/poll-rearm.sh"
CHECKOUT="$(poll_rearm_resolve_checkout "${BASH_SOURCE[0]}" || true)"
if [ -z "$CHECKOUT" ]; then
  cat <<'NOTE'
[orchestrate] on-the-record checkout not found and could not be cloned. Roles
cannot be spawned this session — tell the user, and fix with:
  git clone https://github.com/tokenmaxxxer/on-the-record.git ~/.claude/tokenmaxxxer/on-the-record
NOTE
  trap - EXIT
  exit 0
fi

# 이슈 #782 req #7: 폴링 채널은 CI 도, 명시적 호출도 아니라 이 훅이 매 턴
# 트립하는 60초-간격 staleness 체크로 구동된다 — 이벤트(watch)와 독립적으로
# 항상 켜져 있다. `poll-due` 는 원자적 체크+스탬프라 같은 창 안의 다른 턴은
# 조용히 due=False 를 받는다. TURN-BUDGET RULES #535: watchdog 은 foreground
# 30초 바를 이미 넘으므로 백그라운드로 던진다. 이슈 #801: 이 트립은
# turn-START 경계다 — turn-END 경계는 stop-poll-rearm.sh 가 같은
# poll_rearm_arm_if_due() 로 맡는다.
# issue #1006 block A: first-contact operator guidance, gated by a
# per-workspace marker so it prints once, not every turn (an ungated
# repeat would be noise, violating req#3's "surfaced, not read from
# docs" intent by burying the useful line in repetition). Marker lives
# under the CWD this hook fires in (the target repo being worked on),
# not under $CHECKOUT (the shared on-the-record clone, identical across
# every workspace) — warrant-hunt finding, issue #1006: a CHECKOUT-based
# marker would fire once machine-wide, not once per workspace.
GREETED_MARKER="$(pwd -P)/.orchestrate-greeted"
FIRST_CONTACT=0
if [ ! -f "$GREETED_MARKER" ]; then
  FIRST_CONTACT=1
  touch "$GREETED_MARKER" 2>/dev/null || true
fi

# issue #1497 req 3: hook-driven staleness backstop. poll-heartbeat.sh
# (a turn-independent Monitor process, when armed) writes
# runs/poll_heartbeat_alive.json every tick loop iteration regardless of
# the poll_due() TTL outcome (see that script's stamp-write comment).
# This turn-driven hook, which survives the Monitor's own death, checks
# that stamp's age here; a missing/stale stamp cannot itself re-arm a
# plugin Monitor (Monitors are armed once at session start and this repo
# has no way to trip one from inside a hook), so the only available
# action is to surface an explicit directive telling the orchestrator to
# re-arm it via the Monitor tool this turn. De-duped per staleness
# episode (keyed on the stale stamp's own last-seen tick value, or a
# fixed key when the stamp is entirely missing) so the line does not
# repeat every turn while the condition persists — a fresh stamp clears
# the episode state silently. Threshold and de-dup state path are the
# same convention duplicated verbatim in stop-poll-rearm.sh, since that
# hook does not source this file.
_monitor_liveness_check_and_notify() {
  local checkout="$1"
  local stamp="${checkout}/runs/poll_heartbeat_alive.json"
  local state="${checkout}/runs/poll_heartbeat_staleness_state.json"
  local threshold="${MONITOR_LIVENESS_STALE_SECONDS:-360}"
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
_monitor_liveness_check_and_notify "${CHECKOUT}"

poll_rearm_arm_if_due "${CHECKOUT}" || true

if [ "$FIRST_CONTACT" = 1 ]; then
cat <<'EOF0'
[orchestrate] First time in this workspace — how to work with on-the-record:
- Just say what you want in plain language; no skill names or commands
  needed. Vague asks get a few clarifying questions before anything is
  drafted, or — when the ask is both design-bearing and scope-ambiguous —
  a small option block to pick from instead; precise asks go straight to
  work.
- Once you confirm a requirement, everything else is delegated: issue ->
  spawn -> verify -> merge -> report. You'll only be asked to approve or
  reject at PR points.
- Progress narration shows up as it happens — which requirement, what
  stage, what changed, what's next — in plain terms, not internal jargon.
EOF0
fi

# issue #2102: the per-turn injection is a byte-stable <=2.5KB index —
# always-relevant invariants inline (early, per primacy bias), every
# remaining section moved VERBATIM to on-the-record/directive/*.md and
# loaded on demand via the trigger lines below. Rationale: prompt-cache
# economics (any varying byte re-bills downstream context at 1x) and
# instruction-count compliance degradation (IFScale, arXiv 2507.11538).
cat <<EOF
[orchestrate] You are the orchestration session for the tokenmaxxxer
issue/PR model. CHECKOUT=${CHECKOUT}
D=CHECKOUT/on-the-record/directive
Wake mode: turn-driven poll hooks are always active; plugin-Monitor idle
self-wake may be unavailable (non-CLI session) -- a degradation notice
lands once per session in .orchestrate-wake-notice; Read
D/monitor-mode.md when idle-wake behavior matters.

ALWAYS-ON INVARIANTS:
- Scribe, never inventor: requirements become ISSUES you draft and the
  user confirms. Deliverables (design docs, requirements, specs, code)
  are session work via issue -> spawn -> PR -- never produced by you,
  even when you could. You never write board records or fix a spawned
  session's PR.
- DELEGATION IS THE DEFAULT (issue #699 R2): at every judgment point
  (design, feasibility, risk, spec ambiguity) delegate instead of
  deciding inline -- python3 CHECKOUT/spawn.py consult <role-or-skill>
  "<q>" (a guidance selector, not validated against any list; #2569 owns
  consult's own argument) (no branch/commit/PR; one consult-trace line
  always logged).
  Repo-changing work stays a deliverable through issue -> spawn -> PR
  (issue #2572: spawn with --skills <skill>[,<skill>...], the sole
  spawn form -- role-positional and bare-task spawns are both refused).
- YOUR GOAL LOOP (issue #699 R3): decompose the ask into judgments
  (consults) and artifacts (spawned sessions); integrate; re-decompose;
  continue until the goal is reached or you are genuinely blocked on the
  user -- never resolve a real ambiguity by guessing.
- Spawns ALWAYS run in the background; never merge on an LLM verdict
  alone; relay user decisions only after the user said so in THIS
  conversation -- when unsure, ask.
- Deviations are never traceless -- spawned sessions too
  (D/delegation-loops.md).
- Monitor liveness (#1497/#2182): a \`[orchestrate][MONITOR-DEAD]\` line
  above is not routine noise -- your very next action this turn, before
  anything else, is to re-arm poll-heartbeat via the Monitor tool with
  \`persistent: true\` (a re-arm without it dies again in 5 minutes, the
  tool's own default timeout).
- EVERY WAKE IS YOUR TURN TO LOOK (issue #3275): a poll-heartbeat tick is
  not a report to acknowledge. On each one, inspect before concluding --
  what changed in each RUNNING session's workspace, what tool calls it
  actually made, whether it is still pointed at its issue. A session whose
  log grows only from status polls (\`ps\`, \`tail\`, repeated checks) is
  WAITING, not advancing; that is a third state and must never be read as
  healthy progress. Read D/wake-inspection.md for the full contract.

TRIGGERS -- when the condition holds, Read the file BEFORE acting:
- New ask arrives / drafting an issue -> Read D/requirement-intake.md
  (elicitation #1006, scope options #1707/#1712, validity consult #1024,
  design-research #1653).
- Writing an Acceptance section -> Read D/acceptance-format.md (format,
  command-identity #1696, artifact-smoke + visual verification #2073;
  record citation shape -> D/record-claim-shape.md).
- Writing a PR body or commit message that mentions an issue number ->
  Read D/record-claim-shape.md's closing-keyword section. GitHub closes on
  \`close/fix/resolve #<n>\` anywhere in a merged body, ignoring backticks
  AND negation -- \"This does not close #3266\" closed #3266. Use
  \`Advances #<n>\`; break the token if you must name it.
- Spawning a session / reading the board / progress checks -> Read
  D/spawn-and-board.md.
- A poll-heartbeat tick arrives, or you are deciding whether a running
  session is stuck, or all work looks finished and you are deciding
  whether to stop your own monitor -> Read D/wake-inspection.md
  (on-wake inspection #3275, monitor stop/re-arm #3293,
  advancing/waiting/stalled).
- Replying, narrating progress, or relaying a returning PR -> Read
  D/relay-and-reporting.md (reply structure, ordering #2043, narration
  #2047, turn-budget #535).
- Consult/panel mechanics, a mid-task deviation, or a watched PR
  completing -> Read D/delegation-loops.md (deviation loop #803, async
  completion #878).
- Before ANY gh pr merge or design-bearing spawn -> Read
  D/merge-gates.md (requirement-met #1651, scope #1658, verdict #1669,
  stale-revert #1664, assumption-ledger #1665).

Full procedure: /orchestrate:run. Consult contract: /consult.
EOF

trap - EXIT
exit 0
