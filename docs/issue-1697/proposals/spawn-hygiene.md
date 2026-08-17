---
files:
  - gates/spawn_on_pr.py
  - tests/test_spawn_on_pr.py
---

## Request

#1697: spawn-on-pr observer spawns (execution-observation,
conformance-review) should (a) resolve their branch base from live
origin/main at spawn time instead of relying only on whatever a later,
per-session fetch happens to see, and (b) skip (with a logged board
note) when the subject's own PR is already merged or its issue is
closed at spawn time. A second live reproduction (issue-1696) extends
(b): also defer while the subject's own implementation session is still
running, since that is exactly the in-flight-fix window that produces
the stale-base revert class this issue exists to close.

## Constraints

- Stay inside `gates/spawn_on_pr.py` — do not touch `spawn.py`'s
  `checkout_issue_branch`/`_spawn_one` git-cut mechanics (out of this
  issue's write set; contract, `spawn.py` mutation control lives
  elsewhere).
- No network calls inside unit tests — fixtures use local git repos and
  monkeypatched `gh`-backed helpers, matching the existing
  `tests/test_spawn_on_pr.py` style.
- Preserve existing behavior for open, unmerged subjects (issue's own
  stated "empty state").

## Rationale

Considered adding the live-fetch step only inside
`spawn.checkout_issue_branch()` (it already fetches fresh before
computing `_base()`). Rejected: that fetch fires *after* `_spawn_one`
has already committed to spawning and after `issue_workspace()` has
cloned — it can't be unit-tested with a bare-git moved-main fixture at
the spawn_on_pr decision layer, and doing nothing upstream means a
subject already merged/closed still burns a spawn before the later
fetch ever runs. Anchoring the fetch+base resolution and the
merged/closed/active-session checks inside `spawn_on_pr.py` itself keeps
the decision and its test at the same layer, and composes with the
existing `missing_verification`/`spawn_missing_for_pr` structure instead
of adding a second code path.

## What will be done

- `resolve_live_base(root)`: fetches `origin` and returns the resolved
  base ref's current sha (using `spawn._base`), so the spawn decision
  point has an explicit, testable anchor to live origin/main; called
  once per `spawn_missing_for_pr` tick and logged. `None` on fetch
  failure (fail-open — no behavior change on network blips).
- `_pr_state_for_branch(root, branch, pr_index)`: like the existing
  `_pr_number_for_branch`, but returns the PR's state string
  (`"OPEN"`/`"MERGED"`/`None`) instead of just its number, reusing the
  same `pr_index` bulk-index-first / per-branch-fallback shape.
  `missing_verification` skips (and `ledger_write`s + prints) a subject
  whose PR state is `"MERGED"`.
- `_implementation_session_active(root, subject)`: checks
  `spawn._roster_load()` for a `<subject>/implementation` entry whose
  pid is alive (`spawn._alive`). `missing_verification` skips (and
  `ledger_write`s + prints) a subject with an active implementation
  session — this is the second-reproduction defer condition.
- Issue-closed skip is already implemented (`_issue_is_open`) — no
  change needed there beyond keeping it wired the same way.
- Unit tests for all three: a moved-main fixture (bare `origin` +
  clone, advance origin after clone, assert `resolve_live_base` returns
  the *new* sha), a merged-PR skip test, an active-session skip test,
  and a regression test that open/unmerged/idle subjects still spawn
  exactly as before.

## Accumulation

`resolve_live_base` adds one more small `subprocess.run(["git", ...])`
helper alongside the several already in `gates/spawn_on_pr.py` and
`spawn.py` (`_pr_number_for_branch`, `_base`, `bootstrap_fetch_and_record_sha`,
etc.). If this "fetch + resolve a ref" pattern repeats N more times
across the codebase, the right move is consolidating onto the single
existing `spawn._base`/`bootstrap_fetch_and_record_sha` pair rather than
growing a third near-duplicate — this proposal keeps `resolve_live_base`
as a thin wrapper calling `spawn._base` for exactly that reason, so
there is nothing further here to consolidate.

## Out of scope

- Item (c) from the issue body — record PRs rebasing/merging main before
  opening — is not in the verbatim acceptance checks and is not
  addressed here.
- Changing `spawn.checkout_issue_branch()`'s own fetch/base logic.
- The `SPAWN_CAP`/park/backoff machinery — untouched.

## How you'll know it worked

- `python3 -m pytest tests/test_spawn_on_pr.py` passes, including new
  tests: moved-main fixture for `resolve_live_base`, merged-PR skip,
  active-implementation-session skip, and unchanged behavior for open/
  idle subjects.
