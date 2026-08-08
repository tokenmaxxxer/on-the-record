---
code_under_review: HEAD
loop_state: landed
---

Subject: issue-533

## What was done

Implemented the fix approved in `docs/issue-533/proposals/2026-08-09-repo-scoped-workspace-index-keys.md`:

- `spawn.py`: added `_repo_identity(cwd)` — a local-only (no network) repo
  identity derivation, `git remote get-url origin` parsed for the short
  repo name, falling back to `Path(cwd).resolve().name` when there's no
  origin remote or `git` fails.
- `_workspace_index_put`: key now `f"{_repo_identity(work)}/issue-{issue}/{role}"`
  instead of `f"issue-{issue}/{role}"`. Same-key-different-`work` now
  raises `RuntimeError` unconditionally (including before `watcher_pid` is
  set — closes the pre-registration race the after-proposal warrant hunt
  found) instead of silently overwriting.
- `_workspace_index_load`: migrates any legacy bare-format key
  (`issue-<n>/<role>`) to the new repo-scoped format on load, persisting
  the migration; idempotent; raises the same collision error if migration
  would collide with an existing new-format entry.
- `_lookup_roster_entry`: new optional `repo` param — scopes the lookup to
  one repo's entries when given; falls back to the prior all-repo suffix
  match when omitted (unchanged default behavior for callers that don't
  pass one).
- `main()`'s `watch` dispatch and `_watch`: thread `a.cwd` through as
  `repo=_repo_identity(a.cwd)`, so `spawn.py watch --issue N -C repoA`
  only ever returns repoA's entry.
- Two same-file fixes discovered while implementing, both inside
  `spawn.py` (already in the frozen write set) and necessary for the
  keying change not to silently break existing WORKSPACE_INDEX consumers
  that were not named in the proposal's "What will be done" bullet list:
  - `watchdog_check_one` (signal 5, dead/missing watcher check) looked up
    `_workspace_index_load().get(key)` where `key` is the ROSTER-format
    bare key — now builds the repo-scoped key from the roster entry's
    `work` field before the lookup.
  - `_roster_reconcile_unreported` matched keys with `^issue-(\d+)/` —
    updated to `(?:^|/)issue-(\d+)/` so repo-scoped keys still match.
  - `_watch`'s follow-loop crash check looked up `_roster_load().get(key)`
    with the now-repo-scoped `key` against ROSTER's still-bare-keyed
    store — now strips the repo prefix back off before that lookup.
- `test_spawn.py`: updated the existing round-trip key-format assertions
  (`WatcherAutoArm`, `WatchAll` classes) to the new `<repo>/issue-<n>/<role>`
  shape; added a new `RepoScopedWorkspaceIndex` test class covering: two
  repos/same issue+role keep distinct entries, same-key different-work
  collision raises (with and without `watcher_pid` set), same-key
  same-work is a normal update, `_lookup_roster_entry` scoped by `repo`
  ignores the other repo, `spawn.py watch --issue N -C repoA` end-to-end
  never returns repoB's entry, and legacy-key migration on load
  (idempotent) — reproduce: `python3 -m pytest test_spawn.py -k
  RepoScopedWorkspaceIndex -q`. Also added `WORKSPACE_INDEX` test
  isolation (temp-file override) to two `_spawn_one(bounded=True)`
  integration tests
  (`SelfTriggeredRespawn::test_spawn_one_call_site_fires_after_own_session_end_event`,
  `SpawnOneIssueRoleClaim::test_fork_child_rewrites_claim_pid_before_setsid`)
  that previously wrote to the real `runs/workspaces.json` and only
  worked by accident because same-key overwrites were silent before this
  fix — the new hard-error surfaced that missing isolation as a genuine
  test-fixture gap.

## Why

Per the proposal's Rationale: local-only repo identity (mirroring the
existing `_origin_pr_prefix` pattern) avoids adding a network dependency
to a hot path (`_workspace_index_put` fires on every spawn, `_watch` on
every CLI watch call), and deriving identity from `work`/`cwd` (already in
scope everywhere) avoids a call-site signature change at ~15+ existing
call sites.

## Upstream basis

docs/issue-533/proposals/2026-08-09-repo-scoped-workspace-index-keys.md

## What did not work

- Initial new-test collision fixture used `str(self.repo_a) + "-other"` as
  the "different work, same key" case — that changes the resolved
  directory's basename too, so `_repo_identity` derived a *different* key
  entirely (no collision, test asserted nothing). Fixed by using
  `str(self.repo_a) + "/"` (same git repo, same origin, same resolved
  identity, different literal `work` string) — genuinely exercises the
  same-key-different-work path.
- Two pre-existing `_spawn_one(bounded=True)` integration tests
  (`SelfTriggeredRespawn`, `SpawnOneIssueRoleClaim`) started raising the
  new collision `RuntimeError` on a full-suite run — they never isolated
  `WORKSPACE_INDEX` to a temp file, so repeated runs against the same
  literal `work` tempdir basename ("work") kept colliding against
  leftover entries in the real `runs/workspaces.json` from earlier runs.
  This was previously invisible because same-key overwrites were silent;
  fixed by adding the same `WORKSPACE_INDEX` temp-file override pattern
  already used by other test classes in this file.

## Doc placement

No new env var, dependency, migration, or public wire-format change —
nothing to place under handbooks/decisions/reports per the doctrine
ladder beyond this record itself.

## Hunt

After-proposal hunt (stance 0, recorded in
`docs/reports/2026-08-09-hunt-repo-scoped-workspace-index-keys.md`) found
the pre-watcher-pid collision race; addressed above (unconditional
collision check, not gated on `watcher_pid`/liveness).

closed_checks:
- full pytest suite, code_sha 6f7815932dc19fcc0f3b230ba4e9ac6a11271ab3 —
  reproduce: `python3 -m pytest test_spawn.py -q`; the only failure is
  pre-existing and unrelated
  (`WatcherAutoArm::test_watchdog_flags_pid_reused_by_unrelated_process`),
  confirmed failing identically on the unmodified baseline via `git
  stash` before this change.

## Open findings

None outstanding.
