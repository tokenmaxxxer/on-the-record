# issue-1507 current-state survey (implementation, phase 1)

derived: `grep -n "_fetch_or_halt\|_BOOTSTRAP" spawn.py | head -20`

Write surfaces this session expects to touch (reqs 1-2 only; req 3 deferred
per issue body's explicit ordering):

- `spawn.py` — bootstrap fetch path. `_fetch_or_halt()` (spawn.py:6381+)
  already does `git fetch -q origin` and caches per-work_dir in
  `_FETCHED_THIS_SPAWN`, called from `checkout_issue_branch()`
  (spawn.py:6676+) before any branch-verification logic runs. It does not
  use `--prune`, and does not record/expose the fetched origin/main sha
  anywhere — nothing downstream (a record-authoring session) can cite it.
- `tests/test_spawn.py` — has an existing real-git-fixture test class
  (`WorkspaceSyncFailClosed`, line ~1153) that clones a local `origin` repo
  into `work` and drives `checkout_issue_branch()` against it — this is the
  established pattern for a "deliberately stale clone" fixture (see
  `test_checkout_tracks_origin_only_branch`, line ~1282, which advances
  `origin` after the initial clone).
- `gates/repo_scope.py` — issue #415's existing mechanism. `check_repo_scope()`
  gates capability/contract absence claims on having a scope phrase nearby
  (`_SCOPE_PHRASES`, line 49: `as of <sha>`, `in <repo>`, `checked <path>`,
  etc). No freshness/fetch-timestamp component exists yet. The module's own
  docstring (line 9-14) states it only checks phrase *presence*, not truth.
- `gates/test_repo_scope.py` — did not exist before this session (`find
  gates -iname "*repo_scope*"` -> only `repo_scope.py`, verified before the
  first commit). Acceptance names this exact path as the extension site.

Alternatives considered (feeds proposal Rationale):
- A brand-new module for the freshness check vs. extending
  `gates/repo_scope.py` in place — issue body explicitly mandates reuse
  ("extend it... rather than inventing a parallel field"), so a new module
  was never a live option; not restated as an alternative in the proposal.
- Storing the bootstrap fetch record as a file on disk vs. an in-process
  `dict` keyed by resolved work_dir — considered file-based (durable across
  process restarts) but rejected: `checkout_issue_branch()` and any
  same-process caller (the spawned role session's own tooling) share one
  process lifetime; `_FETCHED_THIS_SPAWN` already uses the identical
  in-process dict pattern one function above it, so a file would be a second
  mechanism for the same one-spawn-one-process lifetime the codebase already
  established.
