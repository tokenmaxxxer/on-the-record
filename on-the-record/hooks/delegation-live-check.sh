#!/usr/bin/env bash
# Stop: live wiring for issue #3061's standing-delegation checker (issue
# #3229). #3061 shipped `delegation_state.py`'s scope-manifest lookup and
# an after-the-fact `audit()` over finished session logs, but nothing
# that ran while a turn was still happening -- PR #3220's tenth
# verification named that gap: a delegated operator whose next action IS
# covered by a manifest still gets asked about it in the moment, and only
# a later `--audit` run shows the stop was avoidable. This hook is the
# live counterpart: at the exact moment the orchestrator stops to ask,
# it re-derives the intended action the same way #3061's own audit()
# does (from tool_use events, never from the question's prose) and, only
# on a covered action with a clean episode, refuses the stop.
#
# The seam was established experimentally before this hook was written,
# not assumed from documentation (docs/issue-3229's record has the
# captured payloads and the block/additionalContext/exit-2 comparison
# against the real `claude` binary): a Stop hook CAN refuse the stop and
# force the turn to continue via `{"decision": "block", "reason": ...}`
# on stdout -- the same mechanism skill-verdict-guard.sh's own "hard"
# violations already use (that file's own comment elsewhere calls
# additionalContext "not decision:'block'"; live behavior showed both
# actually force a same-turn continuation, and this hook's record says
# so plainly rather than picking whichever the comment implied). This is
# genuine enforcement, not a same-turn correction or an after-the-fact
# record -- named accurately because the alternative (calling a weaker
# mechanism by a stronger name) is the exact failure mode issue #3229
# exists to avoid.
#
# Fail-closed toward NOT suppressing, the opposite trap direction from
# stop-gate.sh/skill-verdict-guard.sh's own house style: those hooks'
# ENFORCED invariant is the safe default, so THEIR trap remaps a crash to
# exit 2 (block, force a retry) on purpose. This hook's enforced action
# (decision:"block") is the DANGEROUS one -- it is what could suppress a
# genuine question -- so a crash here must never be reinterpreted as
# "block" the way copying that same trap verbatim would (silent-failure
# audit, docs/issue-3229's record: this was caught and fixed before
# landing, not a hypothetical). `delegation_state.live_stop_decision()`
# already catches every exception internally and returns suppress=False
# (see that function's own docstring), so this trap is defense-in-depth
# for a crash OUTSIDE python entirely (e.g. this script's own shell
# syntax) -- exit 0 either way: a hook that cannot run is a hook that
# does not fire, same direction as "no grant recorded".
#
# Kill switches: ORCHESTRATE_OFF=1 (matches every other on-the-record
# hook). A spawned session (TOKENMAXXXER_SPAWNED set) is never the
# orchestrator asking the operator a question -- it is doing headless,
# already-authorized work (see docs/handbooks/completion-and-landing.md)
# -- so it is skipped the same way stop-poll-rearm.sh/stop-gate.sh skip
# themselves for a spawned session.
#
# issue #1725 Stop-hook contract: `stop_hook_active` means this fire is
# already a forced continuation from a PRIOR Stop hook's block (possibly
# this one's own, possibly another Stop hook's, e.g. skill-verdict-guard.sh)
# -- checked FIRST, before any other work, so a retry turn this hook
# itself forced can never re-suppress and loop.
trap 'rc=$?; if [ "$rc" != 0 ]; then exit 0; fi' EXIT
set -uo pipefail

payload="$(cat 2>/dev/null || true)"
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/hook-fires.sh"
hook_fires_record "Stop delegation-live-check.sh" "$payload"

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
[ -z "${TOKENMAXXXER_SPAWNED:-}" ] || { trap - EXIT; exit 0; }

command -v python3 >/dev/null 2>&1 || exit 2

# Resolve the on-the-record checkout (spawn.py/delegation_state.py/
# trajectory_analyzer.py live at its root) the same way stop-poll-rearm.sh
# / directive.sh already do, so this hook works from any cwd inside a
# checkout, not only the checkout root.
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/poll-rearm.sh"
CHECKOUT="$(poll_rearm_resolve_checkout "${BASH_SOURCE[0]}" || true)"
if [ -z "$CHECKOUT" ] || [ ! -f "$CHECKOUT/delegation_state.py" ]; then
    # No delegation_state.py reachable -- this consumer checkout doesn't
    # carry issue #3061's module at all. Nothing to check against, so
    # nothing fires; the same silent, cheap no-op as "no grant recorded".
    trap - EXIT
    exit 0
fi

CHECK=""
IFS='' read -r -d '' CHECK <<'PY' || true
import json, os, sys

sys.path.insert(0, os.environ["DLC_CHECKOUT"])
import delegation_state as ds

try:
    payload = json.loads(os.environ.get("DLC_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(payload, dict):
    sys.exit(0)

# issue #1725: a forced-retry turn (this hook's own suppression, or any
# other Stop hook's) must emit nothing at all -- checked first.
if payload.get("stop_hook_active"):
    sys.exit(0)

repo = payload.get("cwd") or os.environ.get("DLC_CHECKOUT")
decision = ds.live_stop_decision(payload, repo)

if decision.get("reason"):
    sys.stderr.write(decision["reason"] + "\n")

if decision.get("suppress") and decision.get("hook_output"):
    sys.stdout.write(json.dumps(decision["hook_output"]))

sys.exit(0)
PY

[ -n "$CHECK" ] || { echo "delegation-live-check: heredoc assignment produced no program (disk full / temp file unavailable?) -- bailing, not enforcing this turn" >&2; exit 1; }

DLC_PAYLOAD="$payload" DLC_CHECKOUT="$CHECKOUT" python3 -c "$CHECK"
rc=$?
trap - EXIT
exit "$rc"
