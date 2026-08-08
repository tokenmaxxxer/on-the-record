# Survey — issue-533 (phase 1)

## The collision, precisely

`WORKSPACE_INDEX` (`spawn.py:1992`, `runs/workspaces.json`) is one JSON dict
keyed only by `issue-<n>/<role>`:

- `_workspace_index_put` (`spawn.py:2416-2426`) writes
  `d[f"issue-{issue}/{role}"] = entry`.
- `_lookup_roster_entry` (`spawn.py:2489-2499`) reads either that exact key
  (role given) or scans for `startswith(f"issue-{issue}/")` (role omitted).

Neither carries which target repo the entry belongs to. Two different repos
spawning the same `issue-<n>/<role>` (e.g. `user-discovery-rulebook`
issue-19/implementation and `requirements-engineering-rulebook`
issue-19/implementation) collide on the same dict key; the second `put`
silently clobbers the first's `{work, log, watcher_pid}` entry.

`ROSTER` (`runs/active.json`, `spawn.py:1670`, written by `roster_register`)
is a **separate** file/mechanism from `WORKSPACE_INDEX`. The issue body and
its acceptance checks name only `_workspace_index_put`/`_lookup_roster_entry`
— `ROSTER` is out of scope for this fix (noted so scope doesn't creep at
build time).

## `-C`/cwd is not threaded into `watch` at all

`main()`'s `watch` dispatch (`spawn.py:3079-3084`):

```python
if a.role == "watch":
    ...
    return _watch(a.issue, a.watch_role, a.stall_timeout, follow=a.follow)
```

`a.cwd` (the `-C` flag, `spawn.py:3004`) is parsed but never passed to
`_watch`. Confirms the issue body's observation literally: `-C` does not
scope the lookup — because nothing downstream of `main()`'s `watch` branch
ever receives it. `_watch_all` (`spawn.py:2597`) has no cwd/repo parameter
either, but it's a deliberate everything-multiplexer (`watch --all`) — it
iterates the whole index by design, so it isn't the misrouting site; `watch
--issue N -C repoA` (single-entry lookup) is.

## Where entries get written (the `put` call sites)

Both live in `_spawn_one`, gated on `bounded and issue is not None`
(`spawn.py:3736-3741`, `spawn.py:3780-3781`):

```python
roster_key = f"issue-{issue}/{role}" if issue is not None else f"adhoc/{role}/{os.getpid()}"
...
if bounded and issue is not None:
    _workspace_index_put(issue, role, str(cwd), str(log_path))
    ...
    _workspace_index_put(issue, role, str(cwd), str(log_path), watcher_pid=wproc.pid)
```

`cwd` here is the *target repo's checkout* (the worktree `spawn.py` just
created/reused for this spawn, resolved earlier in the same function from
`a.cwd`/`--issue` branch handling) — i.e. exactly the value needed to derive
a repo identity, already in scope at both call sites, no plumbing needed to
reach it.

Both call sites pass `work=str(cwd)` as the third positional arg to
`_workspace_index_put`. `_lookup_roster_entry`'s callers (`_watch`,
`spawn.py:2506`) only have `idx` + `issue` + `role` in scope today — a repo
identity has to be threaded in from `main()`'s `a.cwd`.

## `_repo_slug`/`_repo_name` exist but are network calls

`spawn.py:1029-1038`:

```python
def _repo_slug(root: Path) -> str | None:
    r = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner",
                        "-q", ".nameWithOwner"], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None
```

Used today only for GitHub-API-adjacent work (ledger comments, PR lookups)
where a `gh` round-trip is already happening anyway. Calling this on every
`_workspace_index_put`/`_lookup_roster_entry` (hot path: every spawn, every
`watch` invocation) would add a network call plus `gh` dependency to a
purely local bookkeeping operation, and would silently degrade to `None`
offline — bad fit for a key component that must be stable and always
present.

`_origin_pr_prefix` (`spawn.py:2392-2400`) is the existing *local*-only
pattern: `git -C <cwd> remote get-url origin`, parsed with a regex, no
network round-trip (`git remote get-url` reads local config only). This is
the shape already used elsewhere in the file for "identify which repo we're
in without hitting the network."

## Existing repo-scoping precedent: `spawn.py:3350-3389` (worktree naming)

The worktree-provisioning code already derives a repo identity from
`git remote get-url origin`, normalizes scheme (ssh→https), and uses
`repo_name` (basename of `owner/repo`) to build the workspace directory
name and to guard against "wrong repo re-used this workspace path"
(`spawn.py:3378-3380`, hard `sys.exit` on origin mismatch — an existing
precedent for "collision must be a loud failure, not silent overwrite").
This is the closest in-repo precedent for both halves of the fix: repo
identity derivation, and hard-erroring on an unexpected collision.

## Test fixture shape that constrains the key-format change

`test_spawn.py:6180-6330` (`WatchAll`/watchdog workspace-index tests) call
`_workspace_index_put(issue, role, work, log, ...)` with `work` as a bare
string (`"work"`, `"log"`) or a plain (non-git) `tempfile` dir, then read
back via a literal key string `f"issue-{n}/{role}"` — e.g.
`spawn._workspace_index_load()["issue-488/implementation"]`
(`test_spawn.py:6186`). None of these fixtures are git repos, so a repo
identity derived from `git remote get-url origin` resolves to nothing for
all of them — the fix needs a defined fallback for "not a git repo /
no origin remote" that these ~15 existing call sites can still exercise
predictably (and whose assertions will need the key literal updated to
match, since the fix changes the on-disk key format for every entry, not
only colliding ones).

## Acceptance requirements recap (from issue #533)

1. `python3 -m pytest` unit covering `_workspace_index_put`/
   `_lookup_roster_entry` collision case: two concurrent spawns on
   different repos, same issue+role, keep distinct roster entries.
2. `spawn.py watch --issue <n> -C <repoA>` never returns events from
   repoB's session (lookup scoped by repo).
3. Full gate/test suite passes.
4. Empty state: if migrating existing `workspaces.json` entries is
   ambiguous, the proposal must state the manual reconcile procedure
   explicitly — `runs/workspaces.json` is a live, gitignored,
   machine-local runtime file (not checked in), so "migration" here means
   an in-process upgrade of whatever's on disk on next load/write, not a
   one-time repo-wide data migration script.

## Alternatives visible in the current code

- **A: derive repo identity via `_repo_slug`/`gh repo view` (network).**
  Rejected in the survey above already — adds a network dependency and
  `gh` round-trip to a hot, purely-local bookkeeping path, and degrades to
  `None` offline, which would make the new key component unstable exactly
  when it matters (a stale/offline checkout is also when collisions are
  likeliest to go unnoticed).
- **B: derive repo identity locally from `git remote get-url origin`**
  (mirrors `_origin_pr_prefix`/the worktree-naming code at
  `spawn.py:3350-3389`), falling back to the resolved directory's basename
  when there's no git repo/no origin (matches the issue body's own
  suggested key shape: "repo-root-basename-or-remote-slug").
- **C: require callers to pass an explicit repo identity string** (no
  derivation at all, caller's responsibility). Rejected: every current
  call site already has `cwd`/`work` in scope and nothing else identifying
  "which repo" more directly; pushing derivation to callers would just
  duplicate the same `git remote get-url` logic at each call site instead
  of once.
