#!/usr/bin/env bash
# SessionStart: tell the role session how it talks to the user and where its
# output goes. This is the informing half of core — board-gate.sh is the
# enforcing half; the two must describe the same rules (contract v3 s10).
#
# Injected only for a spawned session (TOKENMAXXXER_SPAWNED or CLAUDE_SKILL
# set, issue #327): a session on-the-record did not spawn is not a role
# session, and the orchestrator's or user's own session needs no
# behavioral directive. Kill switch: CORE_OFF=1.
#
# Anti-bloat criterion for this heredoc's own growth: mirror a contract rule
# here only once a gate has been observed repeatedly catching a session on
# it — an anticipated-but-unobserved friction point is not, by itself,
# grounds for a new bullet (issue-122).
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
. "${CLAUDE_PLUGIN_ROOT_CORE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}/hooks/lib/gate-lib.sh" || { echo "directive.sh: cannot source gate-lib.sh" >&2; exit 2; }
set -uo pipefail

gate_kill_switch_active "${CORE_OFF:-}" || { trap - EXIT; exit 0; }

skill="${CLAUDE_SKILL:-}"
# Presence test (issue #327, per on-the-record #2538): OR of
# TOKENMAXXXER_SPAWNED and skill, not the new var alone — no SessionStart
# snapshot exists in core to fall back to, so unsetting only one of the
# two spawner-set vars must not silently skip the directive. The skill
# NAME (used below to render the invariants block) still comes only from
# CLAUDE_SKILL — that part is value-dependent, not presence.
[ -n "${TOKENMAXXXER_SPAWNED:-}${skill}" ] || { trap - EXIT; exit 0; }

# Precondition probe (contract v3 s10): the target must be a git repo with
# a GitHub-reachable remote, and gh must be authenticated — issues, PRs,
# and reviews are GitHub objects, and this protocol cannot run without
# them. The probe only informs; the gates deny. Best-effort and cheap:
# each check degrades to a report line, never an error.
missing=""
root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
if [ -z "$root" ] || ! git -C "$root" rev-parse --git-dir >/dev/null 2>&1; then
  missing="${missing}
- Not a git repository. The human must init and publish it before any role can work."
else
  if ! git -C "$root" remote get-url origin >/dev/null 2>&1; then
    missing="${missing}
- No git remote 'origin'. The human must publish this repository first, e.g.:
    gh repo create <owner>/<name> --private --source \"$root\" --push"
  fi
fi
if command -v gh >/dev/null 2>&1; then
  # gh auth status is a network call (~4s measured, issue-269). Cache the
  # outcome under the temp dir, keyed by repo root, for CORE_AUTH_PROBE_TTL
  # seconds (default 300; 0 disables caching). A cached FAILURE is never
  # served: a broken auth must never hide behind a stale success, so only
  # a passing probe is worth caching, and every miss re-probes for real.
  auth_probe_ttl="${CORE_AUTH_PROBE_TTL:-300}"
  auth_ok=1
  if [ "$auth_probe_ttl" != "0" ]; then
    cache_key=$(printf '%s' "$root" | cksum | cut -d' ' -f1)
    cache_file="${TMPDIR:-/tmp}/core-auth-probe-${cache_key}.cache"
    now=$(date +%s)
    cached_at=""
    if [ -f "$cache_file" ]; then
      read -r cached_at < "$cache_file" 2>/dev/null || cached_at=""
    fi
    if [ -n "$cached_at" ] && [ "$cached_at" -le "$now" ] 2>/dev/null && [ $((now - cached_at)) -lt "$auth_probe_ttl" ]; then
      auth_ok=0
    else
      if gh auth status >/dev/null 2>&1; then
        auth_ok=0
        printf '%s\n' "$now" > "$cache_file" 2>/dev/null
      else
        auth_ok=1
        rm -f "$cache_file" 2>/dev/null
      fi
    fi
  else
    gh auth status >/dev/null 2>&1 && auth_ok=0 || auth_ok=1
  fi
  [ "$auth_ok" = 0 ] || missing="${missing}
- gh is not authenticated. The human must run: gh auth login"
else
  missing="${missing}
- gh CLI is not installed. The human must install it (https://cli.github.com) and run gh auth login."
fi

if [ -n "$missing" ]; then
  cat <<EOF
[core] PRECONDITIONS NOT MET for role '${skill}' (contract v3 s10):
${missing}

Until every item above is resolved: do NOT start work, do NOT improvise a
local substitute for issues, PRs, or approvals (a local approval artifact
is forgeable by definition), and do NOT create files. State plainly to the
user what is missing and how to fix it (the commands above), then stop.
The gates will refuse board and execution writes regardless.
EOF
  trap - EXIT
  exit 0
fi

if [ "${CORE_BUILD_NOW:-}" = "1" ]; then
  DFILE="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}/directive/session-protocol-build-now.md"
  cat <<EOF
[core] Interaction protocol for role ${skill} (role-handoff contract v3), build-now (single-phase). INVARIANTS:
- Requirements are user-authored GitHub ISSUES; your issue is assigned in the spawning prompt — never pick or file one. No issue named: ask and stop.
- ALL output returns as a PULL REQUEST from branch issue-<n>/${skill}; never push main. The board is what is MERGED to main, not open PRs.
- Build-now (s19a): CORE_BUILD_NOW=1 is set — skip the proposal round, deliver directly: build on issue-<n>/${skill}, commit code and your record, open one PR. The two-phase default, checkpoint mode, and Approve-signal mechanics do not apply this run; never grant yourself this bypass.
- Layout: code src/, tests test/, docs/ six buckets; your record is docs/issue-<n>/reports/${skill}.md, and you write only your own record area. docs/issue-<n> commits use git commit -m with a Subject: issue-<n> trailer; git add new files explicitly first.
- A session that stages a change to any docs/specs/* file also regenerates docs/specs/reconciled-index.md (python3 gates/spec_index.py --update) in the same commit, where the repo ships that generator.
- This build-now PR is the delivery PR: it must carry Closes/Fixes/Resolves #<issue> (issue complete) or Advances/Part of #<issue> (intentionally partial) — never neither.
- Verification is verify-at-landing: a deliverable is work plus EXECUTED acceptance evidence — command and output in your record. Do not author persistent test files by default. Never omit SKIPPED lines; a hand-typed pass count must equal the pasted summary count.
EOF
else
  DFILE="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)}/directive/session-protocol.md"
  cat <<EOF
[core] Interaction protocol for role ${skill} (role-handoff contract v3). INVARIANTS:
- Requirements are user-authored GitHub ISSUES; your issue is assigned in the spawning prompt — never pick or file one. No issue named: ask and stop.
- ALL output returns as a PULL REQUEST from branch issue-<n>/${skill}; never push main. The board is what is MERGED to main, not open PRs.
- Two phases (s19): phase 1 commits survey + proposal, opens the PR; phase 2 (work + record) opens only on a human Approve — a PR review Approve from a different approvers.md account, or an issue comment whose entire body is exactly APPROVE issue-<n>/<role>. String equality only; never approve or merge yourself. Default (two-session): stop after the phase-1 PR. Checkpoint (single-session): only when the spawning prompt declared it — run the declared await-approval wait, then continue in-session.
- Build-now bypass (s19a): when the environment carries CORE_BUILD_NOW=1, set by the spawner, never by you — skip the proposal round and deliver directly.
- Layout: code src/, tests test/, docs/ six buckets; your record is docs/issue-<n>/reports/${skill}.md, and you write only your own record area. docs/issue-<n> commits use git commit -m with a Subject: issue-<n> trailer; git add new files explicitly first.
- A session that stages a change to any docs/specs/* file also regenerates docs/specs/reconciled-index.md (python3 gates/spec_index.py --update) in the same commit, where the repo ships that generator.
- PR trailer phase split: a phase-1 proposal PR references its issue as a plain #<issue>; Closes/Fixes/Resolves #<issue> is forbidden until the phase-2 delivery PR, which must carry it.
- Verification is verify-at-landing: a deliverable is work plus EXECUTED acceptance evidence — command and output in your record. Do not author persistent test files by default. Never omit SKIPPED lines; a hand-typed pass count must equal the pasted summary count.
EOF
fi

# issue-299: this used to end with "Read ${DFILE} NOW, before any work" —
# on-the-record #2204 measured that exact imperative-Read shape costing a
# real tool round-trip (~46s) every session, on the on-the-record side; the
# session that verified #2204's own fix hit the same shape live right here,
# in this file, because #2204's remedy never reached core. Deliver the full
# protocol's content directly instead, the same way #2204 rode it in via
# --append-system-prompt: cat it into this hook's own stdout so it lands in
# context with no Read call needed. The file carries no per-session
# substitution — role appears only as the literal placeholder <role>, the
# same convention issue-<n> above already uses — so this block renders
# byte-identical every session regardless of role, keeping it a stable
# prefix for prompt caching across spawns; only the INVARIANTS block above
# (rendered with the real ${skill}) varies per session.
if [ -r "$DFILE" ]; then
  echo
  echo "[core] Full protocol (session-protocol.md), delivered inline, no Read needed:"
  echo
  cat "$DFILE"
else
  cat <<EOF

[core] session-protocol.md is missing or unreadable at: $DFILE
The full protocol (record required fields, loop_state vocabulary per kind,
operational-surface commit rule, headless delegation rule) could not be
delivered this session. The INVARIANTS above still apply; ask a human to
restore the file at that path before relying on anything not listed above.
EOF
fi

trap - EXIT
exit 0
