---
proposal: docs/issue-533/proposals/2026-08-09-repo-scoped-workspace-index-keys.md
---

# Hunt record — repo-scoped-workspace-index-keys

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the proposed hard-error-on-live-collision guard has a race window: `_spawn_one` calls `_workspace_index_put` first with `watcher_pid=None` (spawn.py:3741), and only a fork later re-calls it with `watcher_pid` set (spawn.py:3780). During that window the collision check ("existing entry's watcher_pid is present and `_alive(watcher_pid)` is true") cannot fire, because the very entry that would need protecting has no `watcher_pid` yet — so a second, genuinely different repo that happens to resolve to the same `_repo_identity` (e.g. two non-git/detached tempdir checkouts sharing a directory basename, which the proposal itself names as a real fallback path) can silently clobber the first repo's freshly-registered entry with zero error, exactly the original bug the proposal sets out to fix.
Kind: composition
Seed: docs/issue-533/proposals/2026-08-09-repo-scoped-workspace-index-keys.md (planned _workspace_index_put/_lookup_roster_entry collision-detection design); grounded against current spawn.py:2416-2426 (_workspace_index_put) and spawn.py:3741,3780 (_spawn_one's two-call registration pattern: first call with watcher_pid=None, later call with watcher_pid=wproc.pid)
cap_seconds: 60
tier: default (docs-only)
diff_stat_lines: docs-only, 3 new files (survey.md, scout-brief.md, proposal)
started_at: 2026-08-09T04:36:15+09:00
ended_at: 2026-08-09T04:38:30+09:00

### Reproduce
Trace through spawn.py:3735-3781 and the proposal's "What will be done" section for `_workspace_index_put`'s collision check:
1. Repo A spawns issue N role R from a tempdir whose basename fallback resolves to `_repo_identity == "work"` (no git origin remote — the proposal's own documented fallback case). `_spawn_one` calls `_workspace_index_put(issue, role, str(cwd_A), str(log_path))` — no `watcher_pid` arg, so per the plan the stored entry has no `watcher_pid` key yet.
2. Before Repo A's fork completes and re-registers with `watcher_pid=wproc.pid` (spawn.py:3780), Repo B — a distinct git checkout that also has no origin remote and whose directory also happens to be named `work` (or any other collision producing the same `_repo_identity`) — spawns the same issue N role R and calls `_workspace_index_put(issue, role, str(cwd_B), str(log_path))`.
3. Per the proposal's own collision rule ("if the computed key already exists ... and the existing entry's watcher_pid is present and `_alive(watcher_pid)` is true ... raise RuntimeError"), the check evaluates `entry.get("watcher_pid")` on Repo A's entry, which is absent — the condition is false, so the write falls through to a normal overwrite.

### Observed
Under the proposed design, Repo B's write silently replaces Repo A's `work`/`log` under the identical composite key with no error and no log — indistinguishable from success, even though the two entries belong to different repos/processes.

### Expected
The collision guard should also fire (or the race should be closed by some other means, e.g. checking `work != existing["work"]` regardless of `watcher_pid` presence, or registering with a placeholder liveness marker atomically) when an entry exists under the same key with a *different* `work` value but no `watcher_pid` recorded yet — the absence of `watcher_pid` should not be treated as "not live," since the entry was created by a process that is, in fact, still alive and mid-registration.
