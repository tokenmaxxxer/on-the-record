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

# issue #1275: arm-time root validation — a monitor/watchdog armed with
# root = a non-git parent directory (e.g. a session cwd outside any
# checkout) has spawn_coverage._list_open_issues run `gh issue list`
# there, failing "not a git repository" on EVERY tick forever instead of
# refusing once, clearly, at arm time. `root` here is always `pwd -P`
# (neither poll_rearm_arm_if_due's nohup watchdog launch nor
# poll-heartbeat.sh's due-tick watchdog call ever pass -C, so both
# default to the calling process's cwd — spawn.py's own `-C` argparse
# default). Two checks, in order, first failure wins:
#   1. is `root` a git repository at all;
#   2. is it registered as an on-the-record board — `docs/specs/approvers.md`
#      present (the same board marker `spawn.py init` writes).
# On failure: print one explicit `[monitor-arm-refused]` line naming the
# root and the failed check, and return 1 BEFORE touching anything else
# (no poll-due call, no nohup watchdog, no registration artifact of any
# kind) — the caller must treat a non-zero return as "did not arm".
poll_rearm_validate_root() {
  local root="${1:?poll_rearm_validate_root requires a root path}"
  if ! git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf '[monitor-arm-refused] root=%s check=git-repo: not a git repository — refusing to arm\n' "$root" >&2
    return 1
  fi
  if [ ! -f "$root/docs/specs/approvers.md" ]; then
    printf '[monitor-arm-refused] root=%s check=board-registration: docs/specs/approvers.md missing — refusing to arm\n' "$root" >&2
    return 1
  fi
  return 0
}

poll_rearm_arm_if_due() {
  local checkout="${1:?poll_rearm_arm_if_due requires the resolved checkout path}"
  local root
  root="$(pwd -P)"
  if ! poll_rearm_validate_root "$root"; then
    return 1
  fi
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
