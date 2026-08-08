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

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — `_roster_reconcile_unreported()` builds its "already commented" marker from the now-repo-prefixed workspace-index key, but `_post_session_end_comment()` still posts the marker with the bare `issue-<n>/<role>` key, so the marker never matches and every normal session-end is reported as unreported forever.
Kind: silent-failure
Seed: docs/issue-533/proposals/2026-08-09-repo-scoped-workspace-index-keys.md; spawn.py `_repo_identity`, `_workspace_index_load`/`_workspace_index_put` (spawn.py:2525-2589), `_roster_reconcile_unreported` (spawn.py:1972-2013), `_post_session_end_comment` callers (spawn.py:1954, 4324)
cap_seconds: 180
tier: default
diff_stat_lines: 321 insertions (spawn.py/test_spawn.py/docs/issue-533/reports/implementation.md)
started_at: 2026-08-09T05:40:47+09:00
ended_at: 2026-08-09T06:05:00+09:00

### Reproduce
```
python3 - <<'PYEOF'
MARKER = "[watch] {key}: session-end:"
# actual posted marker uses the bare roster key (spawn.py:1954, :3930, :4324
# -> _post_session_end_comment)
posted = MARKER.format(key="issue-533/dev")
# _roster_reconcile_unreported (spawn.py:1999) builds its lookup marker from
# the workspace-index key, which _workspace_index_put (spawn.py:2578) now
# writes with a repo-identity prefix
looked_up = MARKER.format(key="on-the-record/issue-533/dev")
print("posted comment contains:", posted)
print("marker reconcile searches for:", looked_up)
print("match:", looked_up in posted)
PYEOF
```
Also: `RosterReconcileUnreported` in test_spawn.py (test_spawn.py:4729-4780) still mocks
`spawn._workspace_index_load` to return bare keys like `"issue-534/coding"`, the
pre-#533 shape — that mock hides the break because it never exercises the
prefixed-key shape `_workspace_index_put` now actually produces.

### Observed
```
posted comment contains: [watch] issue-533/dev: session-end:
marker reconcile searches for: [watch] on-the-record/issue-533/dev: session-end:
match: False
```
`_roster_reconcile_unreported` (spawn.py:1999) computes
`marker = _SESSION_END_COMMENT_MARKER.format(key=key)` where `key` is a
workspace-index key from `_workspace_index_load()` — after this diff always
`<repo-identity>/issue-<n>/<role>`. It then checks `marker in c.get("body", "")`
for GitHub comments. Since the actual posted comment always uses the bare
`issue-<n>/<role>` marker (spawn.py:1954 `_post_session_end_comment(ROOT, issue_n, key, work, ...)`
with `key` from the bare-keyed roster dict, and spawn.py:4324 with `roster_key`
built at spawn.py:3930 as `f"issue-{issue}/{role}"`), the substring check
always fails post-#533, so `reconcile --unreported` will report every
already-acknowledged, normal-verdict session as "미보고" on every single run,
indefinitely.

### Expected
`_roster_reconcile_unreported` should derive the bare `issue-<n>/<role>`
portion of the workspace-index key (the same way `watchdog_check_one` already
does at spawn.py:2766 via `re.search(r"issue-\d+/[^/]+$", key)`) before
formatting `_SESSION_END_COMMENT_MARKER`, so the marker it searches for
actually matches what gets posted.
