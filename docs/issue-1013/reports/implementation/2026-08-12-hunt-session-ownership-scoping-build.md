---
proposal: docs/issue-1013/proposals/session-ownership-scoping-build.md
---

# Hunt record — session-ownership-scoping-build

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — the proposal's frontmatter write set (`spawn.py`, `tests/test_spawn.py`) omits `docs/issue-1013/reports/implementation.md`, a file the proposal's own "What will be done" section commits the build to writing ("`docs/issue-1013/reports/implementation.md` recording the build").
Kind: design-error
Seed: docs/issue-1013/proposals/session-ownership-scoping-build.md (new, untracked)
cap_seconds: 120
tier: default
diff_stat_lines: new file, 130 lines
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
grep -n '^files:' -A3 docs/issue-1013/proposals/session-ownership-scoping-build.md
grep -n 'reports/implementation.md' docs/issue-1013/proposals/session-ownership-scoping-build.md
```

### Observed
The frontmatter lists only:
```
files:
  - spawn.py
  - tests/test_spawn.py
```
but the "What will be done" section's last bullet reads: "`docs/issue-1013/reports/implementation.md` recording the build." No hook in `on-the-record/hooks/` actually cross-checks a Write/Edit tool call's path against the proposal's declared `files:` frontmatter list (confirmed by grepping all hooks for any parse of a proposal's `files:` key against tool_input paths — none exists; `approval-gate.sh` only checks a fixed `docs/issue-<n>/reports/<role>.md` pattern independent of any proposal's declared write set). So the mechanical gate happens to admit the report write anyway, but the proposal's own accounting of its write set is internally inconsistent: it authorizes and later performs a write to a path it never declared as in-scope.

### Expected
The `files:` frontmatter should list every path the proposal's own body commits to writing, including `docs/issue-1013/reports/implementation.md`, so the declared write set actually matches the work the proposal authorizes.

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — orphan roster entries (session_id absent) are treated as "own" by *every* caller in `_undispositioned_role_prs`, so any session — regardless of its own ORCHESTRATOR_SESSION_ID — silently skips the PR gate for undisposed branches whose roster entry never got session-tagged, defeating block C whenever tagging is incomplete (the default state, since nothing in the repo sets ORCHESTRATOR_SESSION_ID except spawn.py itself/opt-in callers).
Kind: composition
Seed: spawn.py `_roster_own()` (new helper) and its use at `_undispositioned_role_prs()` line ~1176 (`own_branches = {key for key in _roster_own(_roster_load(), all_scope=False)}`)
cap_seconds: 120
tier: size:21-200
diff_stat_lines: spawn.py +62/-5, tests/test_spawn.py +158
started_at: 2026-08-12T13:20:30+09:00
ended_at: 2026-08-12T13:23:40+09:00

### Reproduce
```
python3 -c "
import os, sys
sys.path.insert(0, '.')
import spawn

# Caller B has a real, distinct session id set (a normal legit orchestrator, not hostile).
os.environ['ORCHESTRATOR_SESSION_ID'] = 'sessB'

# Roster contains an orphan entry (no session_id) that actually belongs to a
# different, concurrently-running session/orchestrator invocation that never got
# ORCHESTRATOR_SESSION_ID tagged (the default today: nothing else in the repo sets
# this env var, so every pre-existing/legacy/adhoc roster entry is an orphan).
roster = {
    'issue-9999/other-role': {'session_id': None, 'issue': 9999, 'role': 'other-role'},
}

own_scope = spawn._roster_own(roster, all_scope=False)
print('BYPASS: orphan entry treated as own by sessB ->', 'issue-9999/other-role' in own_scope)
"
```
grep confirms no other file sets ORCHESTRATOR_SESSION_ID: `grep -rln ORCHESTRATOR_SESSION_ID --include=*.py --include=*.sh .` returns only spawn.py and tests/test_spawn.py — so in ordinary operation (no wrapper sets the env var) every roster entry is an orphan, and `_roster_own(d, all_scope=False)` is then the identity function for *all* callers, including the PR gate in `_undispositioned_role_prs`.

### Observed
`BYPASS: orphan entry treated as own by sessB -> True` — the orphan branch `issue-9999/other-role`, which is not actually caller B's, ends up in `own_branches` and is therefore excluded from `_undispositioned_role_prs`'s blockers list (line 1181: `if pr.get("headRefName") in own_branches: continue`) for caller B, even though the entry may belong to a different concurrently-running session.

### Expected
Block C is meant to keep blocking on *other* sessions' undisposed role PRs; the same orphan-inclusion policy that is correct for `roster_watchdog` (observation-loss avoidance: keep unowned/legacy entries visible to *someone*) is reused verbatim as the gate's ownership test, where its effect is the opposite of intended — it lets *every* session, not just the true owner, treat an unattributed branch as "mine, don't block me." Since session-id tagging is opt-in and nothing currently sets ORCHESTRATOR_SESSION_ID outside spawn.py's own optional callers, this makes the PR gate's new scoping a no-op (full bypass) in the common case rather than a scoped exclusion of the caller's own PRs only.
