---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

## Request

`runs/workspaces.json` (`WORKSPACE_INDEX`) keys entries by `issue-<n>/<role>`
only, with no target-repo component. Two different repos spawning the same
issue number and role collide on the same key — the later spawn silently
overwrites the earlier repo's entry, and every index-driven mechanism
(`watch`, the auto-armed watcher, watchdog, stall comments, crash respawn)
then silently tracks the wrong repo's session. `spawn.py watch --issue N -C
repoA` doesn't currently scope by `-C` at all. Fix: key the roster by
repo identity + issue + role, scope lookups by that identity, migrate
existing entries, and hard-error on an unexpected same-key overwrite while
the existing entry looks live.

## Constraints

- `runs/workspaces.json` is gitignored and machine-local (confirmed:
  `.gitignore:1` → `runs/`) — it is a live runtime cache, not checked-in
  data, so "migration" means an in-process upgrade on next load/write, not
  a one-time repo-wide script.
- `ROSTER` (`runs/active.json`, `roster_register`) is a separate mechanism
  from `WORKSPACE_INDEX` and is not named by the issue's acceptance
  checks — out of scope here.
- `_workspace_index_put`'s existing positional signature
  `(issue, role, work, log, watcher_pid=None)` is called from two sites in
  `_spawn_one` (`spawn.py:3741`, `spawn.py:3780`) and from ~15 test call
  sites (`test_spawn.py:6183-6330`) that pass bare/non-git `work` strings —
  the fix must not require a new required parameter at every call site,
  since `work`/`cwd` (already passed everywhere) is sufficient to derive
  repo identity locally.
- No network calls on the hot path: `_repo_slug`/`_repo_name`
  (`spawn.py:1029-1038`) shell out to `gh repo view` — unsuitable for a key
  component computed on every spawn and every `watch` call (adds latency,
  a `gh` dependency, and degrades to `None` offline).
- `watch`'s `-C`/`a.cwd` is parsed by `argparse` but never passed into
  `_watch`/`_lookup_roster_entry` today (`spawn.py:3079-3084`) — confirmed
  in the survey, not assumed.

## Rationale

Considered deriving repo identity via `_repo_slug` (`gh repo view --json
nameWithOwner`), the function already used elsewhere in `spawn.py` for
repo-scoped ledger/PR lookups. Rejected for this specific use: it's a
network round-trip via `gh`, and `_workspace_index_put`/
`_lookup_roster_entry` fire on every spawn and every `watch` call — turning
a purely local bookkeeping operation into one that can hang or silently
degrade to `None` when offline or rate-limited, which is exactly the
condition (a flaky/offline environment) under which a stale collision is
most likely to go unnoticed. The repo's own worktree-provisioning code
(`spawn.py:3350-3389`) already solves an adjacent problem — "which repo is
this checkout for" — purely locally via `git remote get-url origin` (no
network call; reads local git config) plus a hard `sys.exit` on mismatch.
Chosen instead: reuse that same local-only pattern
(`_origin_pr_prefix`-style, `spawn.py:2392-2400`, already does exactly this
parsing for a different field) to derive a repo identity, with a
basename-of-directory fallback when there's no git repo or no origin
remote (matches the issue body's own suggested key shape:
"repo-root-basename-or-remote-slug") — covering the existing non-git test
fixtures deterministically, with no network dependency anywhere in the
fix.

Also considered adding a required `repo` parameter to
`_workspace_index_put`/`_lookup_roster_entry` instead of deriving it from
`work`/`cwd`. Rejected: every current call site already has `work`/`cwd` in
scope and nothing else identifying "which repo" more directly — an explicit
parameter would just push the same `git remote get-url` call out to each
of the ~15+ call sites (production and test) instead of computing it once
inside the two functions that actually need it, and would force a
call-site signature change everywhere `_workspace_index_put` is invoked
today, including all existing test fixtures, for no behavioral benefit.

## What will be done

- `spawn.py`: add `_repo_identity(cwd) -> str`, following
  `_origin_pr_prefix`'s local-only shape: `git -C cwd remote get-url
  origin`, parse the `owner/repo` slug with the same regex pattern, return
  just the short repo name (no owner, no slashes — keeps composite keys
  free of embedded `/` ambiguity and human-legible in `cat
  runs/workspaces.json`, matching `_repo_name`'s existing "owner stripped"
  convention). When there's no origin remote or the `git` call fails
  (non-git tempdir, detached checkout), fall back to
  `Path(cwd).resolve().name` — always succeeds, purely local, no network.
- `_workspace_index_put(issue, role, work, log, watcher_pid=None)`: key
  becomes `f"{_repo_identity(work)}/issue-{issue}/{role}"` instead of
  `f"issue-{issue}/{role}"`. Before writing, if the computed key already
  exists in the loaded index with a **different** `work` value, and the
  existing entry's `watcher_pid` is present and `_alive(watcher_pid)` is
  true (the index's own existing liveness signal — the same one `watchdog`
  already trusts for watcher-dead/watcher-missing checks), raise
  `RuntimeError` instead of overwriting — a same-key overwrite while a
  watcher is verifiably alive means either a real repo-identity collision
  (two different repos resolved to the same fallback basename) or a bug,
  and both must fail loudly per the issue's acceptance requirement, not
  clobber the live entry. Same-key writes where `work` is unchanged (the
  existing two-call pattern in `_spawn_one`: register, then re-register
  with `watcher_pid` added) remain a normal update, not a collision.
- `_workspace_index_load()`: after parsing JSON, migrate any key not
  already in `<repo>/issue-<n>/<role>` shape (i.e. matching the legacy
  bare `issue-<n>/<role>` pattern) by computing
  `_repo_identity(entry["work"])` for that entry's stored `work` path and
  rewriting the key under the new format; if the migrated key would
  collide with an existing new-format key, apply the same live-collision
  hard-error as `_put`. Persist the migrated dict back to
  `WORKSPACE_INDEX` immediately (self-healing on first load post-upgrade,
  idempotent — a second load of an already-migrated file is a no-op).
  Empty-state answer to the issue's acceptance requirement #4: this
  migration path is never ambiguous — `_repo_identity` always resolves via
  its basename fallback even if the `work` directory no longer exists on
  disk (it's a pure string operation once `git remote` fails) — so no
  manual reconcile procedure is needed; if an operator wants a clean slate
  regardless, deleting `runs/workspaces.json` is always safe (it's a
  regenerated runtime cache, confirmed gitignored).
- `_lookup_roster_entry(idx, issue, role, repo=None)`: new optional `repo`
  param. When `repo` is given, look up by the exact composite key (role
  given) or filter `startswith(f"{repo}/issue-{issue}/")` (role omitted) —
  scoping the lookup to one repo, closing the `-C`-does-nothing gap. When
  `repo` is omitted (unchanged default), fall back to matching by suffix
  across all repos (`key.endswith(f"/issue-{issue}/{role}")` or
  `"/issue-{issue}/" in key`), preserving today's cross-repo-visible
  behavior for callers that don't pass `-C`, including the existing
  multi-match `sys.exit` disambiguation message when more than one repo
  has a matching entry.
- `main()`'s `watch` dispatch and `_watch`: thread `a.cwd` through —
  `_watch(issue, role, stall_timeout, follow, repo=_repo_identity(a.cwd))`
  — so `spawn.py watch --issue N -C repoA` only ever returns repoA's
  entry, satisfying acceptance check #2 directly. `watch --all`
  (`_watch_all`) is intentionally unscoped (it multiplexes every entry by
  design) and is unchanged.
- `test_spawn.py`: update the ~15 existing `_workspace_index_put`/
  `_workspace_index_load()[...]` round-trip assertions
  (`test_spawn.py:6183-6330` and similar) to the new key format (these
  tests use non-git `work` values, so their keys become
  `f"{Path(work).resolve().name}/issue-<n>/<role>"` via the basename
  fallback — mechanical, same round-trip shape, different literal). Add
  new tests: (a) two `_workspace_index_put` calls with different `work`
  paths pointing at two distinct fake git repos (different `origin`
  remotes) but the same issue+role keep two distinct index entries; (b)
  same scenario but same-key/different-`work` collision with a live
  `watcher_pid` raises `RuntimeError`; (c) `_lookup_roster_entry` with
  `repo=` set only returns that repo's entry when two repos share an
  issue+role; (d) a legacy bare-format entry migrates correctly on next
  `_workspace_index_load()` call.

## Out of scope

- `ROSTER`/`runs/active.json` and `roster_register`/`roster_kill` — a
  separate keying mechanism, not named by this issue's acceptance checks.
- Any change to `watch --all`'s multiplexing behavior.
- A `gh`-API-backed (`owner/repo`) identity instead of the local
  short-name — considered and rejected in Rationale.
- Any repo-wide/checked-in data migration tooling — `workspaces.json` is a
  gitignored runtime cache; the fix's in-process migration on load covers
  the only case that exists.

## How you'll know it worked

- New unit test: two `_workspace_index_put` calls for different repos
  (different `git remote get-url origin`), same issue number and role,
  produce two distinct entries in `_workspace_index_load()` — directly
  covers acceptance check #1.
- New unit test: `_lookup_roster_entry(idx, issue, role, repo="repoA")`
  never returns repoB's entry when both exist for the same issue+role —
  covers acceptance check #2 at the function level; a `main()`-level test
  exercises `spawn.py watch --issue n -C <repoA path>` end-to-end against
  a fabricated two-repo index.
- `python3 -m pytest` (full suite) exits 0 — acceptance check #3.
- Collision hard-error test: same key, different `work`, live
  `watcher_pid` → `_workspace_index_put` raises instead of silently
  overwriting.
