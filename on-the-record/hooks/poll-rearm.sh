#!/usr/bin/env bash
# Shared poll/watchdog arming step (issue #801 phase 2, candidate 4 of
# docs/issue-801/proposals/technical-feasibility.md): factored out of
# directive.sh so the SAME poll-due + background-watchdog trip can be
# called from more than one hook event, not duplicated per-caller.
#
# Called from UserPromptSubmit (directive.sh, turn start) AND from Stop
# (stop-poll-rearm.sh, turn end) — arming at both boundaries of a turn
# narrows the quiet gap between "user stops typing" and "watchdog last
# ran" versus arming on turn-start alone, but this is still a TURN-DRIVEN
# best-effort loop: it requires the orchestrator session's own process to
# be alive and a hook to actually fire. It does NOT survive the session's
# own death — that remains the hard, externally-blocked boundary recorded
# in docs/issue-801/proposals/technical-feasibility.md (no plugin-shipped
# settings.json permissions key exists to self-grant a session-independent
# wake; see that file's "Hard boundary" section). Kill switch:
# ORCHESTRATE_OFF=1 (checked by callers before sourcing this).
#
# Usage: source this file, then call `poll_rearm_resolve_checkout` and
# `poll_rearm_arm_if_due "$CHECKOUT"`.
set -uo pipefail

# Resolve the on-the-record checkout (spawn.py lives at the repo root,
# OUTSIDE the plugin subtree — a cache install copies only orchestrate/, so
# a plugin-root/../.. guess points at nothing there). Order: dev override,
# plugin-root ancestors, the marketplace clone, else self-clone (preferring
# an existing new-path checkout, falling back to a still-present old-path
# checkout before re-cloning). Shared verbatim between directive.sh and
# stop-poll-rearm.sh so the two hook events resolve the same checkout.
poll_rearm_resolve_checkout() {
  local hook_script_path="${1:?poll_rearm_resolve_checkout requires the caller script path}"
  if [ -n "${TOKENMAXXXER_CHECKOUT:-}" ] && [ -f "${TOKENMAXXXER_CHECKOUT}/spawn.py" ]; then
    printf '%s' "${TOKENMAXXXER_CHECKOUT}"; return 0
  fi
  local d probe
  d="$(cd "$(dirname "${hook_script_path}")" && pwd -P)"
  probe="$d"
  for _ in 1 2 3 4; do
    probe="$(dirname "$probe")"
    if [ -f "$probe/spawn.py" ]; then printf '%s' "$probe"; return 0; fi
  done
  local mk="$HOME/.claude/plugins/marketplaces/tokenmaxxxer"
  if [ -f "$mk/spawn.py" ]; then printf '%s' "$mk"; return 0; fi
  local own="$HOME/.claude/tokenmaxxxer/on-the-record"
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  local old="$HOME/.claude/tokenmaxxxer/muster"
  if [ -f "$old/spawn.py" ]; then printf '%s' "$old"; return 0; fi
  mkdir -p "$(dirname "$own")" 2>/dev/null
  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}

poll_rearm_arm_if_due() {
  local checkout="${1:?poll_rearm_arm_if_due requires the resolved checkout path}"
  local due_out due_rc
  # issue #910 finding #3: "not due" (clean non-zero exit) and "poll-due
  # crashed" (unhandled exception on corrupt state/bad JSON) previously both
  # discarded stdout+stderr and returned 1 identically. Capture stderr and
  # log it on a crash so a persistent failure doesn't read as a healthy
  # quiet period.
  due_out="$(python3 "${checkout}/spawn.py" poll-due 2>&1 >/dev/null)"
  due_rc=$?
  if [ "$due_rc" -eq 0 ]; then
    mkdir -p "${HOME}/.claude/tokenmaxxxer" 2>/dev/null
    nohup python3 "${checkout}/spawn.py" watchdog --auto-respawn \
      >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>&1 &
    disown 2>/dev/null || true
    return 0
  fi
  if [ -n "$due_out" ]; then
    mkdir -p "${HOME}/.claude/tokenmaxxxer" 2>/dev/null
    printf '[poll-due crashed, rc=%s] %s\n' "$due_rc" "$due_out" \
      >>"${HOME}/.claude/tokenmaxxxer/poll-watchdog.log" 2>/dev/null || true
  fi
  return 1
}
