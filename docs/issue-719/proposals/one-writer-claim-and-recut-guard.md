---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

files:
- spawn.py
- test_spawn.py

## Request

Field logs show role sessions for the same (issue, role) colliding on the
shared remote branch `issue-<n>/<role>`: non-fast-forward push rejections
(issue-289) and "No commits between main and branch" PR-create failures
(issue-272/295/319). #719 asks for a survey of spawn.py's branch cut/push/
re-cut path plus a one-writer claim (branch-scoped, stale-claim expiry,
never deadlocking an abandoned branch) and a re-cut guard, following the
issue's Acceptance.

## Constraints

- Never deadlock a legitimately abandoned branch — an expired/stale claim
  must be reclaimable (issue's own requirement, and matches the existing
  `_acquire_spawn_claim` stale-PID-cleanup behavior).
- Empty state must be byte-identical to today: no prior claim → spawn
  proceeds unchanged.
- Re-cut must never silently drop a running session's commits; a
  fully-absorbed (already-merged) branch must still be re-cuttable.
- No new dependency, no new environment variable, no schema/migration —
  this is a concurrency-control fix inside `spawn.py`'s existing claim
  primitive.

## Rationale

The survey (`docs/issue-719/reports/implementation/survey.md`) found that
issue-223's claim (merged 2026-08-03, before the field logs) already
serializes entry into `checkout_issue_branch()`, so it already prevents a
second live session from re-cutting a branch out from under a first live
session — the re-cut path itself is not the field-log mechanism. The
actual gap is a release-time race: `_release_spawn_claim()` fires at
spawn.py:4715, right after `proc.wait()`, but the git-mutating operations
the field logs are about — `git push` and `gh pr create` inside
`ensure_pushed()` — run afterward, at spawn.py:4745, unprotected by any
claim. A respawn that acquires the claim in that window can push/PR-create
against the same branch concurrently with the first session's own
still-running `ensure_pushed()`, producing exactly the non-fast-forward
and no-commits signatures quoted in the issue.

Considered and rejected: **remote-side claim** (a `refs/claims/issue-<n>/
<role>` ref or similar, checked cross-host). This would also close a
true cross-host collision window, but the survey found no field-log
evidence that cross-host spawning (rather than a same-host respawn racing
the first session's tail) is what produced the quoted signatures — the
release-before-push race inside one host's respawn loop already
reproduces every quoted symptom on its own. Adding a remote-visible
primitive and a network round-trip to every spawn for an unconfirmed
scenario is scope beyond what the field logs establish; it is deferred to
a follow-up issue if cross-host collision is separately confirmed.

Also considered and rejected: **`git push --force-with-lease` as the
concurrency mechanism**, letting rejections signal the collision and
having the loser retry. This is what `ensure_pushed()` already does today
(a plain `git push`, spawn.py:4192) — it is the status quo that produces
the field-log failures, not a fix for them.

## What will be done

1. Widen `_spawn_one()`'s claim-held window so `_release_spawn_claim()`
   runs only after `ensure_pushed()` completes, not right after
   `proc.wait()`. Concretely: move the `_release_spawn_claim(cwd,
   os.getpid())` call (currently spawn.py:4715) to after the
   `push_result = ensure_pushed(cwd, issue, role)` call (currently
   spawn.py:4745), keeping everything currently between those two points
   (roster removal, the settings-tempfile `finally`, uncommitted-work
   detection, `_git_head`) running exactly as today, still inside the
   claim. `roster_remove()` stays where it is — the claim, not the
   roster, is the concurrency primitive being widened.
2. Ensure the claim is still released on every exit path out of
   `_spawn_one()` between claim-acquire and the new release point
   (including any early-return/exception path already present), so a
   crash cannot leave a claim wedged — this is what the existing
   `_alive(pid)` stale-check already covers for the case where release
   never runs at all (process dies holding the claim); widening the held
   window does not change that guarantee, it only moves the release call
   later on the already-guaranteed paths, i.e. it is additive to the
   existing crash-safety, not a new crash-safety property.
3. Add a re-cut guard to `checkout_issue_branch()`'s fully-absorbed check
   (spawn.py:4122-4144): after `_fetch_or_halt()` has updated
   `origin/<branch>`, before deciding to re-cut, also read `rev-list
   --count base..origin/<branch>` (remote ahead-of-base count) alongside
   the existing local `base..branch` count. Re-cut only when **both** are
   zero. If the local count is zero but the remote count is not (local
   ref stale relative to a branch some other workspace already advanced),
   fast-forward/re-point the local branch to `origin/<branch>` instead of
   resetting to `base` — the branch is not actually fully absorbed, only
   locally stale, and re-cutting from `base` in that state is exactly the
   "re-cut drops a running session's commits" failure mode the issue asks
   to guard against, just triggered from staleness rather than from a
   second concurrent live session.
4. Unit tests in `test_spawn.py`, following the issue's own Acceptance
   check/empty-state pairs:
   - one-writer claim: a second `_acquire_spawn_claim()` call for a live
     (issue,role) is refused while the first claim's PID is alive; once
     the held PID is not alive (stale), the claim is reclaimable. (Much of
     this already has coverage from issue-223; this proposal's tests
     target specifically the *widened* window — i.e. a claim acquired at
     `_spawn_one()` entry is still held through a fake/mocked
     `ensure_pushed()` call, and only released after it returns.)
   - empty state: no prior claim file → `_acquire_spawn_claim()` returns
     `None` unchanged (already the case; a regression test pins it).
   - re-cut guard: fixture where local `base..branch` is 0 but
     `base..origin/branch` is not 0 → `checkout_issue_branch()` does not
     reset to `base` (no commit loss), it tracks `origin/branch` instead.
   - empty state: local and remote both 0 (truly fully-absorbed/merged)
     → re-cut proceeds exactly as today, asserted unchanged.

## Out of scope

- A remote/cross-host claim primitive (Alternative B in the survey) —
  deferred pending confirmation that cross-host spawning, not same-host
  respawn timing, is actually occurring in the field.
- Any change to `_acquire_spawn_claim()`'s TOCTOU-safe file mechanics
  (link-based create, tempfile write) — that machinery already works and
  is untouched; only the call sites that acquire/release it move.
- Any change to the watchdog/roster (`roster_register`/`roster_remove`/
  `_alive`) liveness machinery — reused as-is.
- issue-319's "8 sequential respawns, all failed-no-commit" pattern beyond
  what the re-cut guard and widened claim window address; if that
  specific log turns out to have a distinct root cause (e.g. a respawn cap
  or fingerprinting issue in `_respawn_or_cap`), that is a separate
  investigation, not bundled here — the survey did not find evidence
  tying it to the branch/claim/re-cut path this issue names.

## Accumulation

This touches `spawn.py`'s existing inline `subprocess`/`gh` call sites
inside `checkout_issue_branch()` and `ensure_pushed()` rather than adding
new ones — it adds one more `git rev-list --count` read (remote ahead
count) next to the existing local one, reusing the same `git(*a)` closure
pattern already in both functions. If this pattern (one more ahead-count
read feeding one more branch decision) recurs N more times across future
issues, the right move is to factor `checkout_issue_branch()`'s local/
remote ahead-count pair into a small named helper (e.g.
`_branch_ahead_counts(cwd, base, branch)` returning `(local_ahead,
remote_ahead)`) so each new caller reads one helper instead of
hand-rolling another `rev-list --count` pair. Not bundled into this
proposal: today it is exactly one call site being extended, not yet a
repeated pattern across the file.

## How you'll know it worked

- `test_spawn.py`'s new/updated tests pass, covering: claim held through
  `ensure_pushed()`; empty-state claim-acquire unchanged; re-cut guard
  refuses to drop commits when local is stale but remote is not; re-cut
  proceeds unchanged when both are truly 0.
- Full existing `test_spawn.py` suite still passes (no regression to the
  issue-223 claim mechanics or the existing re-cut fast path).
- Manually traceable: the field-log failure shape (non-fast-forward push,
  no-commits PR-create) requires a claim-window gap or a stale local
  ref to occur; both are closed by this change, and the fixtures added in
  step 4 directly reproduce and then refute each shape.
