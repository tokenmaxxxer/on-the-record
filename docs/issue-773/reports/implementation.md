---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal
(docs/issue-773/proposals/rulebook-cache-lock.md):

- Added `_rulebook_lock_path(d)` and `_locked_rulebook_dir(d)`
  (spawn.py, right after `_RULEBOOK_CACHE`) — a per-rulebook
  `fcntl.flock` context manager reusing the exact idiom `ROSTER` already
  uses (spawn.py:1732-1739). A dead holder's `flock` is released by the
  kernel automatically, so there is no separate stale-lock reclaim code
  path — matching the proposal's chosen mechanism.
- Wrapped the exists-check-through-clone body of `rulebook_checkout()`
  (spawn.py:207-251) in `_locked_rulebook_dir(d)`. Warm-cache branch
  (TTL-skip) logic is byte-identical, now inside the lock.
- Wrapped the identical hand-written clone race in `core_root()`
  (spawn.py:3227-3265) the same way. Made `_locked_rulebook_dir` itself
  fall back to lock-free execution when the lock file's parent can't be
  created/opened (read-only-root edge case), so `core_root()`'s
  existing halt-on-missing-core behavior for that edge case is
  preserved.
- Added test classes RulebookCacheLock and CoreRootCacheLock to
  tests/test_spawn.py, covering: concurrent-population serializing to
  one clone, stale-lock reclaim via a real killed subprocess, and
  warm-cache issuing zero git calls (for both `rulebook_checkout()` and
  `core_root()`).
  derived: `python3 -m pytest tests/test_spawn.py -q -k "RulebookCacheLock or CoreRootCacheLock"`
  ```
  .....
  5 passed, 401 deselected in 0.31s
  ```

## Why

Basis: docs/issue-773/proposals/rulebook-cache-lock.md (approved
phase-1 proposal), itself based on
docs/issue-749/reports/conformance-review.md rank 1 and the collision
issue #773 describes when reproducing a parallel same-role spawn batch.

## What did not work

- First cut of the `core_root()` change moved its `d.parent.mkdir(...)`
  unconditionally out of the function's original `try/except OSError`
  block. An existing test using a non-writable root
  (`test_core_dir_resolves_or_halts`) then failed with an uncaught
  `PermissionError` instead of the expected `SystemExit` — the original
  code swallowed that `OSError` and fell through to the halt message.
  Fixed by re-wrapping the mkdir in `try/except OSError: pass` and
  making `_locked_rulebook_dir` itself catch `OSError` on its own
  mkdir/open and degrade to running `populate` without a lock in that
  case (the subsequent clone attempt fails for the same underlying
  reason and still reaches the existing halt path).

## Open findings

None.

## Next steps

None — landed.

## Resolution path

N/A — no open findings.

## Doc placement

- No new env var, config key, dependency, or migration introduced —
  nothing new for docs/handbooks/.
- No public signature or wire format changed (`rulebook_checkout()` and
  `core_root()` keep their existing return contracts, per the
  proposal's Constraints) — nothing new for docs/issue-773/decisions/.
- Full-suite pass count is the benchmark number this change produces;
  recorded below under Acceptance verification.

## Acceptance verification

checked: concurrent same-role rulebook-cache populations do not collide
— result: verified
  derived: `python3 -m pytest tests/test_spawn.py -q -k "RulebookCacheLock or CoreRootCacheLock"`
  ```
  .....
  5 passed, 401 deselected in 0.31s
  ```

checked: full test_spawn.py suite passes clean
  derived: `python3 -m pytest tests/test_spawn.py -q`
  ```
  ........................................................................ [ 17%]
  ........................................................................ [ 35%]
  ........................................................................ [ 53%]
  ........................................................................ [ 70%]
  ........................................................................ [ 88%]
  ..............................................                           [100%]
  406 passed in 33.63s
  ```
