#!/usr/bin/env bash
# SessionStart hook (issue #3231): pull the skill-repository fetch that used
# to happen only inside a real `--skills` spawn forward to session start
# instead. Without this, a plugin-only install (no manual clone, per
# docs/handbooks/setup.md's old -- and wrong -- "no automatic clone" claim)
# would let a consumer session spawn `--skills` and find nothing, because
# nothing had ever triggered `_skill_repo_managed_root()`'s clone before
# that first real spawn attempted it. Tier: on-first-need-with-notice --
# `spawn.py ensure-skills` (skills.py:ensure_skill_corpus_cli) does the
# fetch automatically but always prints what it did to stderr; nothing here
# writes silently.
#
# Quiet, fail-open, non-blocking: any failure here (offline, no CHECKOUT
# resolvable yet, clone timeout) degrades to "the next real --skills spawn
# tries again", never to a session that won't start.
trap 'exit 0' EXIT
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
case "${MUSTER_SKILL_BOOTSTRAP:-}" in ""|1|true|yes|on) ;; *) trap - EXIT; exit 0 ;; esac

# Same checkout-resolution order as self-update.sh (issue #2908 kept the two
# in sync) -- dev override, plugin-root ancestors, marketplace clone, own
# clone. Unlike self-update.sh this hook never self-clones on-the-record:
# self-update.sh already owns that job and runs first in hooks.json: if it
# hasn't produced a usable checkout, there is nothing for this hook to
# bootstrap skills into yet, and it degrades quietly.
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
  return 1
}

CHECKOUT="$(_checkout_resolve || true)"
if [ -n "$CHECKOUT" ] && command -v python3 >/dev/null 2>&1; then
  python3 "$CHECKOUT/spawn.py" ensure-skills 2>&1 || true
fi

trap - EXIT
exit 0
