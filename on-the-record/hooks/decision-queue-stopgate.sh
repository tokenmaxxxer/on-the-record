#!/usr/bin/env bash
# Stop: surface aged decision_queue items so an operator decision does not
# sit unread across an unlimited number of new orchestrator turns.
# Issue #466 (class-B row from the #464 ADR), carrying the #374 proposal's
# design (docs/issue-374/proposals/2026-08-07-decision-queue-stop-hook-nudge.md)
# into this issue's acceptance-named file.
#
# Two age tiers, read fresh every turn from `spawn.py flows --json`'s
# decision_queue (already-correct data, per #374's survey — nothing new is
# computed here):
#   age_hours >= 1 -> additionalContext reminder, non-blocking.
#   age_hours >= 4 -> decision:"block", forcing one more turn.
# Below tier 1, or an empty queue -> silent (exit 0, no output).
#
# Resolves the on-the-record checkout the same way directive.sh does.
# Kill switches: ORCHESTRATE_OFF=1, CLAUDE_ROLE set (spawned role session).
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
payload="$(cat 2>/dev/null || true)"

_checkout_resolve() {
  if [ -n "${TOKENMAXXXER_CHECKOUT:-}" ] && [ -f "${TOKENMAXXXER_CHECKOUT}/spawn.py" ]; then
    printf '%s' "${TOKENMAXXXER_CHECKOUT}"; return 0
  fi
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  probe="$d"
  for _ in 1 2 3 4; do
    probe="$(dirname "$probe")"
    if [ -f "$probe/spawn.py" ]; then printf '%s' "$probe"; return 0; fi
  done
  mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer"
  if [ -f "$mk/spawn.py" ]; then printf '%s' "$mk"; return 0; fi
  own="$HOME/.claude/tokenmaxxxer/on-the-record"
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  old="$HOME/.claude/tokenmaxxxer/muster"
  if [ -f "$old/spawn.py" ]; then printf '%s' "$old"; return 0; fi
  mkdir -p "$(dirname "$own")" 2>/dev/null
  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
[ -n "$CHECKOUT" ] || { trap - EXIT; exit 0; }

command -v python3 >/dev/null 2>&1 || exit 2

REPO="$(pwd -P)"
FLOWS_JSON="$(python3 "$CHECKOUT/spawn.py" flows --json -C "$REPO" 2>/dev/null || true)"
[ -n "$FLOWS_JSON" ] || { trap - EXIT; exit 0; }

IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, re, sys

try:
    flows = json.loads(os.environ.get("STOPGATE_FLOWS_JSON", ""))
except ValueError:
    sys.exit(0)
if not isinstance(flows, dict):
    sys.exit(0)

queue = flows.get("decision_queue")
if not isinstance(queue, list) or not queue:
    sys.exit(0)


def _name(item):
    issue = item.get("issue")
    pr = item.get("pr")
    age = item.get("age_hours")
    parts = []
    if issue is not None:
        parts.append(f"#{issue}")
    if pr is not None:
        parts.append(f"PR#{pr}")
    label = "/".join(parts) if parts else "(unnamed)"
    return f"{label} ({age:.1f}h)"


# Issue #600: waiting-declaration turn-holding. A non-empty queue (any
# age -- the incident item was age_hours=0.3, below tier 1) combined with
# a reply that declares it is waiting but shows no sign of closing the
# turn (no background-arm marker) is the turn-occupancy violation run.md
# rule 4 (#535 section) forbids. Independent of, and fires before, the
# age-tier logic below.
try:
    stdin_payload = json.loads(os.environ.get("STOPGATE_STDIN_JSON", ""))
except ValueError:
    stdin_payload = {}
last_msg = ""
session_id = None
if isinstance(stdin_payload, dict):
    last_msg = stdin_payload.get("last_assistant_message") or ""
    session_id = stdin_payload.get("session_id")
if not isinstance(last_msg, str):
    last_msg = ""
if not isinstance(session_id, str) or not session_id:
    session_id = None

_WAITING_RE = re.compile(
    r"대기\s*중|기다리는\s*중|waiting for|standing by", re.IGNORECASE
)
_ARM_RE = re.compile(
    r"background|observation|백그라운드|옵저베이션", re.IGNORECASE
)

# Issue #692: bound the waiting-declaration block to at most one fire per
# consecutive run in a session -- a blocked Stop forces another turn, and
# when the only remaining work is an operator decision, the natural next
# reply is another bare waiting declaration, which blocked again on every
# repeat (six in a row in the reported incident). State follows
# retry-loop-bound.sh's persistence shape (own sibling state dir, atomic
# os.replace, silent fail-open) but is NOT the same file/key schema --
# retry-loop-bound keys on a PreToolUse (tool, target) signature that a
# Stop event's payload has no equivalent for.
_STATE_DIR = os.environ.get("STOPGATE_STATE_DIR", "")


def _state_path():
    if not _STATE_DIR or not session_id:
        return None
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
    return os.path.join(_STATE_DIR, safe + ".json")


def _load_blocked():
    path = _state_path()
    if not path:
        return False
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return bool(data.get("waiting_declaration_blocked"))
    except (OSError, ValueError):
        pass
    return False


def _save_blocked(blocked):
    path = _state_path()
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"waiting_declaration_blocked": blocked}, f)
        os.replace(tmp, path)
    except OSError:
        pass


if _WAITING_RE.search(last_msg) and not _ARM_RE.search(last_msg):
    if not _load_blocked():
        names = ", ".join(_name(i) for i in queue if isinstance(i, dict))
        out = {
            "decision": "block",
            "reason": (
                "decision-queue-stopgate: waiting-declaration reply over "
                "a non-empty decision queue with no background-arm "
                "marker -- this is turn-occupancy, not a closed turn. "
                "run.md #535 규칙 4 (\"남은 작업이 사람의 결정뿐이면 그 "
                "자리에서 턴을 닫는다\") requires closing the turn instead "
                "of repeating a waiting status line. Decision-queue items: "
                + names + ". One-shot escape: in your next message, relay "
                "these items by name once (issue/PR coordinates above), "
                "then close the turn -- do not send another bare waiting "
                "declaration; this block will not repeat this run."
            ),
        }
        _save_blocked(True)
        sys.stdout.write(json.dumps(out))
        sys.exit(0)
    # Already blocked once this run of consecutive waiting declarations --
    # fall through to the age-tier logic below instead of blocking again.
else:
    # Non-waiting-declaration Stop (arm marker present, or no waiting
    # pattern at all): reset the latch so a later, unrelated stall in the
    # same session is still caught.
    _save_blocked(False)

tier1, tier2 = [], []
for item in queue:
    if not isinstance(item, dict):
        continue
    age = item.get("age_hours")
    if not isinstance(age, (int, float)):
        continue
    if age >= 4:
        tier2.append(item)
    elif age >= 1:
        tier1.append(item)

if not tier1 and not tier2:
    sys.exit(0)

if tier2:
    names = ", ".join(_name(i) for i in tier2)
    out = {
        "decision": "block",
        "reason": (
            "decision-queue-stopgate: decision-queue items have aged "
            "past 4h with no operator decision: " + names + ". "
            "Address the queue (approve, defer explicitly, or state why "
            "not yet) before continuing new work."
        ),
    }
    sys.stdout.write(json.dumps(out))
    sys.exit(0)

names = ", ".join(_name(i) for i in tier1)
out = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": (
            "decision-queue-stopgate: decision-queue items waiting on an "
            "operator decision: " + names + "."
        ),
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
PY

STOPGATE_STATE_DIR="${OTR_DECISION_QUEUE_STOPGATE_STATE_DIR:-${TMPDIR:-/tmp}/otr-decision-queue-stopgate}"

STOPGATE_FLOWS_JSON="$FLOWS_JSON" STOPGATE_STDIN_JSON="$payload" STOPGATE_STATE_DIR="$STOPGATE_STATE_DIR" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
