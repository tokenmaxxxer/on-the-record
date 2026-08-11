#!/usr/bin/env bash
# PreToolUse (Bash): recut a mid-run session's own branch when a concurrent
# merge absorbed it out from under the session — issue #784.
#
# Extends #732's absorbed-branch detection (spawn.py:checkout_issue_branch,
# now factored into the shared `_recut_absorbed_branch` helper) to a case
# #732 could not cover: #732's recut runs only once, at spawn time, inside
# `checkout_issue_branch()`. A session that is already running never calls
# that function again. If an orchestrator merges+deletes that session's
# phase-1 PR branch while the session is still alive, the branch is
# absorbed into base out from under it, and the session's own next
# `git commit`/`gh pr create` is the first place absorption would surface
# — today, as a silent "No commits between main and issue-<n>/<role>" at
# PR-create time.
#
# Interposition point (after-proposal warrant hunt correction,
# docs/issue-784/reports/implementation/2026-08-11-hunt-absorbed-branch-mid-run-recut.md):
# the first draft of the approved proposal named spawn.py's
# `_PROGRESS_BASH_PREFIXES` match inside the orchestrator's own
# `for line in proc.stdout:` transcript scan as the recheck's trigger. The
# hunt found that site only logs, asynchronously, from the PARENT process
# reading the child session's streamed NDJSON — it cannot block or precede
# the child's own tool execution, so a recut attached there would race
# with (and could lose to) the very `git commit`/`gh pr create` it needs
# to precede. This hook instead runs the same synchronous, in-process
# `PreToolUse` mechanism `contract-guard.sh` already uses to gate `gh pr
# merge` before it executes — it runs inside the session's own process,
# before the matched Bash command runs, against the session's own cwd.
#
# Detection reuses `_recut_absorbed_branch()` (spawn.py, factored out of
# `checkout_issue_branch()` by this same change) via a small CLI subcommand
# (`spawn.py recut-if-absorbed -C <cwd>`) — pure local-git-state, no
# roster read, no cross-process/cross-host lookup (proposal constraint).
# Untracked/uncommitted work is preserved the same way #732 already does
# (stash-push, recut, stash-pop, leftover-stash recovery) — never silently
# dropped.
#
# Zero-install shape: this hook ships with the plugin like
# contract-guard.sh, but its detection logic lives in spawn.py, which is
# only present in the on-the-record repo's own self-hosted checkout (see
# spawn.py's `self_hosted_hooks()` — `${CLAUDE_PLUGIN_ROOT}` resolves to
# `<cwd>/on-the-record` there, so spawn.py sits one directory up). In an
# arbitrary consumer repo spawn.py is absent — this hook then no-ops
# (fail-open), matching contract-guard.sh's own posture for lookups it
# cannot perform (a wrong-allow here is cheap: the matched command simply
# runs and, if actually absorbed, still fails exactly as it does today —
# this hook only ever adds a recut, it never denies).
set -uo pipefail

case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac
payload="$(cat 2>/dev/null || true)"
command -v python3 >/dev/null 2>&1 || { echo "[$(basename "${BASH_SOURCE[0]}")] skipping: python3 not found (fail-open)" >&2; exit 0; }
command -v git >/dev/null 2>&1 || { echo "[$(basename "${BASH_SOURCE[0]}")] skipping: git not found (fail-open)" >&2; exit 0; }

spawn_py="${CLAUDE_PLUGIN_ROOT:-}/../spawn.py"
[ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$spawn_py" ] || exit 0

IFS='' read -r -d '' EXTRACT <<'PY' || true
import json, os, re, sys

try:
    e = json.loads(os.environ.get("ABRG_PAYLOAD", ""))
except ValueError:
    sys.exit(0)
if not isinstance(e, dict) or (e.get("tool_name") or "") != "Bash":
    sys.exit(0)
ti = e.get("tool_input") or {}
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)

# Same commit/PR-open prefixes spawn.py already tracks for progress
# logging (`_PROGRESS_BASH_PREFIXES`, spawn.py:2251) — the two that can
# actually surface "No commits between main and issue-<n>/<role>".
# `re.search` (not an anchored `startswith`) so a compound command like
# `cd <dir> && git commit -m x` still matches (before-landing hunt,
# stance 2: an anchored startswith silently missed exactly that shape and
# let the guard go silent on the one command form sessions actually use
# when they need to act on a path other than their own cwd).
if not (re.search(r"(?:^|&&)\s*git\s+commit\b", cmd)
        or re.search(r"\bgh\s+pr\s+create\b", cmd)):
    sys.exit(0)

# A leading `cd <path> &&` targets a different directory than the hook
# process's own cwd — resolve it the same way contract-guard.sh does,
# instead of assuming the session's Bash tool never wraps a `cd`.
cd_m = re.match(r"^\s*cd\s+(\S+)\s*&&", cmd)
print(cd_m.group(1) if cd_m else os.getcwd())
PY

target_cwd="$(ABRG_PAYLOAD="$payload" python3 -c "$EXTRACT")"
[ -n "$target_cwd" ] || exit 0

out="$(python3 "$spawn_py" recut-if-absorbed -C "$target_cwd" 2>&1)"
rc=$?
if [ $rc -ne 0 ]; then
    # Recut attempted and failed — reported, never silently swallowed, but
    # never denies: the matched command still runs and fails exactly as it
    # would have without this hook (fail-open, same posture as
    # contract-guard.sh's lookup failures).
    printf 'absorbed-branch-recut-guard: recut failed, letting the command run unchanged: %s\n' "$out" >&2
fi
exit 0
