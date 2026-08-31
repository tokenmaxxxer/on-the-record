#!/usr/bin/env bash
# SessionStart: refresh the installed checkout. Nothing else does — the
# measured trap: `claude plugin update` reads only the version string and
# reports "already latest" forever. Quiet; offline failure is fine.
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 0; fi' EXIT
set -uo pipefail
case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac
# Resolve the on-the-record checkout (spawn.py lives at the repo root,
# OUTSIDE the plugin subtree — a cache install copies only orchestrate/, so
# the old plugin-root/../.. guess pointed at nothing there). Order: dev
# override, plugin-root ancestors, the marketplace clone, own clone, else
# self-clone. issue #2908: the retired `muster` name (#83) dropped from
# this order -- see poll-rearm.sh's poll_rearm_resolve_checkout for the
# rationale; the two must keep resolving identically.
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
  mkdir -p "$(dirname "$own")" 2>/dev/null
  git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own" 2>/dev/null
  if [ -f "$own/spawn.py" ]; then printf '%s' "$own"; return 0; fi
  return 1
}
CHECKOUT="$(_checkout_resolve || true)"
if [ -n "$CHECKOUT" ]; then
  # issue #2749: this used to `git pull --ff-only` unconditionally here.
  # `pull` = fetch + merge into the working tree, and the working tree is
  # what every hook in this checkout executes from — so that merge, not
  # the GitHub merge, was the moment code changed underneath whichever
  # sessions were live (issue #2670's finding, reflog-confirmed: repeated
  # fast-forwards this hook fired with no actor choosing the moment,
  # while sessions were running). `git fetch` alone only updates
  # refs/objects, never the working tree, so it stays unconditional and
  # safe here; advancing the working tree is now a deliberate act —
  # `spawn.py self-update`, which refuses while any session is live (the
  # same "zero sessions running at pull time" discipline #2670 ran by
  # hand). issue #910 finding #4's bar still holds either way: the
  # outcome is always recorded to `.pull-check`, never silently dropped —
  # mirror the `.shallow-check` marker pattern below.
  fetch_err="$(git -C "$CHECKOUT" fetch -q 2>&1)"
  if [ $? -ne 0 ]; then
    printf 'pull=failed:fetch:%s\n' "$(printf '%s' "$fetch_err" | tr '\n' ' ' | head -c 500)" \
      > "$CHECKOUT/.pull-check" 2>/dev/null || true
  else
    behind_err="$(git -C "$CHECKOUT" rev-list --count 'HEAD..@{u}' 2>&1)"
    if [ $? -ne 0 ]; then
      printf 'pull=unknown:%s\n' "$(printf '%s' "$behind_err" | tr '\n' ' ' | head -c 200)" \
        > "$CHECKOUT/.pull-check" 2>/dev/null || true
    elif [ "$behind_err" = "0" ]; then
      printf 'pull=ok\n' > "$CHECKOUT/.pull-check" 2>/dev/null || true
    else
      printf 'pull=deferred:%s-behind-origin\n' "$behind_err" \
        > "$CHECKOUT/.pull-check" 2>/dev/null || true
      # issue #2908: the fetch above already computed this count -- this
      # is not a new check, only a new place its result goes. Previously
      # only `.pull-check` recorded it, and nothing ever read that file:
      # the hooks running THIS session could be current while the engine
      # they call (spawn.py etc. at CHECKOUT) sat arbitrarily far behind,
      # with no signal either had drifted from the other. `spawn.py
      # self-update` (issue #2749) clears this the moment zero sessions
      # are live; until then, print it to this hook's own stdout so a
      # SessionStart context surfaces the skew every session it persists,
      # instead of only to a file no reader consumes.
      printf '[self-update] engine checkout %s commits behind origin/main (%s) -- hooks may be current while the engine they call is not; clears automatically once no spawned sessions are live\n' \
        "$behind_err" "$CHECKOUT"
    fi
  fi
fi
# #412: a self-clone (or any pre-existing checkout) can be shallow — a
# shallow checkout silently breaks history-dependent checks (log/blame
# ranges truncate at the shallow boundary). Detect it and attempt to
# unshallow; record the outcome either way so a still-shallow checkout is
# at least visible, not silent.
if [ -n "$CHECKOUT" ]; then
  marker="$CHECKOUT/.shallow-check"
  if [ "$(git -C "$CHECKOUT" rev-parse --is-shallow-repository 2>/dev/null)" = "true" ]; then
    if git -C "$CHECKOUT" fetch -q --unshallow 2>/dev/null; then
      printf 'shallow=true unshallow=ok\n' > "$marker" 2>/dev/null || true
    else
      printf 'shallow=true unshallow=failed\n' > "$marker" 2>/dev/null || true
    fi
  else
    printf 'shallow=false\n' > "$marker" 2>/dev/null || true
  fi
fi
trap - EXIT
exit 0
