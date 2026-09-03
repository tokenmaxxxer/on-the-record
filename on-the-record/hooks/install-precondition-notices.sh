#!/usr/bin/env bash
# SessionStart hook (issue #3231): the "stays manual, but with a better
# error" tier for the two preconditions that genuinely cannot be removed
# by the plugin (git identity is the operator's own choice to make; a
# target repo's docs/specs/approvers.md board file is per-repo state the
# plugin has no authority to invent) -- only a *notice*, printed once at
# session start instead of surfacing deep inside a spawned session's `git
# commit` or `require_board()` exit. Never mutates global git config,
# never writes into the target repo. Read-only checks only, same class of
# operation scripts/preflight/consumer_preconditions.py already performs.
trap 'exit 0' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac

if command -v git >/dev/null 2>&1; then
  name="$(git config --get user.name 2>/dev/null || true)"
  email="$(git config --get user.email 2>/dev/null || true)"
  if [ -z "$name" ] || [ -z "$email" ]; then
    printf '[install-check] git identity not configured (user.name=%s user.email=%s) -- board.py commits during `spawn.py init --push` will fail until you run:\n  git config --global user.name "<name>"\n  git config --global user.email "<email>"\n' \
      "${name:-<unset>}" "${email:-<unset>}"
  fi
fi

# `docs/specs/approvers.md` is target-repo state -- only worth checking when
# the current session's cwd actually looks like a git checkout (this hook
# also fires for orchestrator sessions with no target repo open yet).
if [ -d ".git" ] && [ ! -f "docs/specs/approvers.md" ]; then
  printf '[install-check] this repo has no docs/specs/approvers.md yet -- every spawn is refused until one exists; create it with:\n  python3 <on-the-record checkout>/spawn.py init -C .\n'
fi

trap - EXIT
exit 0
