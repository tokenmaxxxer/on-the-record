---
proposal: docs/issue-1292/proposals/poll-heartbeat-non-git-demotion.md
---

# Hunt record — poll-heartbeat-non-git-demotion

## after-proposal — stance 1: is_git/is_board demotion in poll-heartbeat.sh silently misroutes or leaves dead/inert state

Verdict: NO FINDING
Seed: git diff on-the-record/monitors/poll-heartbeat.sh (issue #1292: exit-1 non-git refusal replaced with is_git/is_board computation folded into the #1282 sweep-exclusion path)
cap_seconds: unknown (not specified by dispatcher)
tier: default
diff_stat_lines: ~20 (poll-heartbeat.sh) + 3 new tests in tests/test_spawn.py
started_at: 2026-08-14T00:00:00Z
ended_at: 2026-08-14T00:20:00Z

Checked: exit-code semantics for the Monitor tool caller (script always exits 0 via
the tick loop regardless, unaffected either way); is_git/is_board are computed in
the shell but never exported/passed to the `python3 spawn.py ...` subprocess calls
that follow, so they are provably inert in poll-heartbeat.sh itself. Verified that
`spawn._board_wide_sweep_all` (spawn.py:2659) independently derives board status
from `(repo / "docs/specs/approvers.md").exists()` per target repo, which already
handles a non-git arm-root correctly (no such marker present) without needing the
shell-side is_git/is_board at all. Ran the actual script end-to-end against a
non-git cwd (`bash poll-heartbeat.sh` with POLL_HEARTBEAT_MAX_TICKS=1 in a fresh
non-git dir): rc=0, no `[monitor-arm-refused]` in stdout/stderr, alive marker
written under the workspace-keyed hash — matches the new tests' expectations.
Checked `_repo_identity` (spawn.py:3619) and confirmed it degrades gracefully
(falls back to dir basename) for a non-git cwd, so no `gh`/`git` subprocess call
in the sweep path crashes on a non-git root. No reproducible wrong output found;
the docstring at spawn.py:2671 ("arm-root's non-git validation was already
finished at the CLI entry point (#1275)") is now stale prose since #1292 removed
that CLI-level validation, but this is a comment inaccuracy with no observable
behavioral consequence I could reproduce, so it does not qualify as a finding.
