
## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: on-the-record/hooks/deviation-log-guard.sh (CLAUDE_ROLE-unset early-exit removed), on-the-record/hooks/role-deviation-directive.sh (new), on-the-record/hooks/session-role-bind.sh
cap_seconds: 120
tier: default
diff_stat_lines: ~5 files touched (per proposal context)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:15:00Z

Confirmed by direct execution that deviation-log-guard.sh no longer reads
CLAUDE_ROLE at all — enforcement is keyed purely off the git branch name
(`issue-<n>/<role>` regex) and transcript scan, independent of the env var.
Ran the guard directly with CLAUDE_ROLE set/unset/reset with a transcript
containing a recognized-deviation marker and no matching deviation-log
diff/commit: it blocks (additionalContext) in both cases, confirming the
env-var-manipulation bypass the old early-exit permitted is closed. Also
checked hooks.json's Stop registration (no matcher restricting to
non-role sessions) and role-deviation-directive.sh's own CLAUDE_ROLE gate
(only gates the reminder text injection, not enforcement, so unsetting
CLAUDE_ROLE mid-session only silences the nudge, not the Stop-time check).

Looked for a role-session-specific silent no-op via detached HEAD /
worktree branch-name mismatch (spawn.py does a plain branch checkout, no
worktree, so this path isn't reachable) and via the git-diff-vs-staged
blind spot (`git diff` without `--cached` misses index-only additions) —
the latter is real but pre-existing (same code path serves orchestrator
sessions already) and produces a false *block*, not a silent bypass, so
it doesn't fit this stance. No role-session-specific bypass reproduced
within the cap.
