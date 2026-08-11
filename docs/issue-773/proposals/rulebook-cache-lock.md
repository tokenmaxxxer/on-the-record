---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

## Request

Concurrent spawns of the same role each try to populate the shared
rulebook cache directory `runs/rulebooks/<role>` by cloning into it
directly; the exists-check and the clone are not atomic, so parallel
same-role spawns race and all but the winner die with "target path
already exists and is not empty" (reproduced 2026-08-11 with a batch
of parallel `architecture` spawns). Make same-role concurrent
cache-population collision-free, preserving the existing #285 TTL-skip
behavior on a warm cache, with stale-lock reclaim matching the
existing spawn-claim pid-liveness pattern.

## Constraints

- Fix must live inside `rulebook_checkout()` (spawn.py:207-251) — no
  change to its call sites or return contract (still returns the
  `Path` to use).
- The warm-cache path (spawn.py:235-241, `_pull_is_fresh` gate) must
  stay behaviorally identical: no new `git` subprocess call, same TTL
  decision, for the "single spawn, warm cache" case.
- A crashed spawn must not permanently wedge future spawns — reclaim
  must be pid-liveness based, mirroring `_acquire_spawn_claim`/`_alive`
  (spawn.py:4321-4366, 1785-1790), not a bare timeout that could
  reclaim a live-but-slow clone.
- No new dependency; `fcntl` is already imported (spawn.py:23) and
  already used for `ROSTER`'s lock (spawn.py:1732-1739).

## Rationale

Two directions were viable (both named in the issue): a blocking
`flock` held across the clone, or clone-to-temp-then-atomic-rename.

**Chosen: per-rulebook `flock`.** A lock file at
`runs/rulebooks/<mkt>.lock` is opened/created, then `fcntl.flock(f,
LOCK_EX)` is acquired before the exists-check, held through the clone,
and released after. Losers block on the OS-level lock instead of
racing `git clone`; when the winner releases, losers re-check
`_mkt(d).exists()` (now true) and skip straight to the warm-cache
branch. This directly matches the issue's "share the one clone or wait
for it" framing, and it reuses the exact mechanism (`fcntl.flock`) the
repo already applies to `ROSTER` for the same shared-mutable-directory
problem, rather than introducing a second concurrency idiom
(temp-clone-then-rename) alongside it.

**Rejected: clone-to-temp-dir then atomic rename.** This avoids
holding a lock across the (up to `CLONE_TIMEOUT=180s`) network clone,
which is a real advantage — but every losing spawn still pays the full
network/CPU cost of a complete rulebook clone before discovering it
lost the rename, and the rename step itself needs its own
existence race-check (`os.rename` onto an existing non-empty directory
raises on POSIX, so a loser must re-check `_mkt(d).exists()` after a
failed rename and fall through to reuse the winner's dir — functionally
converging back to a wait-for-winner path, just implemented with wasted
work instead of a wait). Rejected because it burns bandwidth/CPU N-1
times over on every cold-cache race for no behavioral benefit over
`flock`, and this repo has no existing precedent for the
temp-then-rename idiom to build on, whereas the `flock` idiom is
already established and already crash-safety-reviewed in this file for
`ROSTER`.

Stale-lock reclaim is layered on top of the `flock` regardless of which
direction was chosen (a plain `flock` alone cannot go stale — the
kernel releases it automatically if the holder process dies — so the
`_acquire_spawn_claim`-style pid-liveness reclaim is for a *secondary*
in-progress marker written into the lock file, used only to produce a
clear diagnostic/timeout bound rather than to actually gate correctness;
kernel `flock` release-on-crash already gives correctness for free,
which is why `flock` was preferred over a hand-rolled pid-file claim
for the primary exclusion mechanism).

## What will be done

1. Add `_rulebook_lock_path(d: Path) -> Path`: returns
   `d.parent / (d.name + ".lock")`, i.e. `runs/rulebooks/<mkt>.lock`,
   sibling to the clone dir (not inside it — keeps `git status
   --porcelain` clean inside the clone, same reasoning already applied
   to TTL markers per #296).
2. In `rulebook_checkout()`, before the existing `if _mkt(d).exists():`
   check (spawn.py:235): open (creating if absent) the lock file, then
   `fcntl.flock(lock_fd, fcntl.LOCK_EX)` — blocking acquire, no
   timeout (a stuck acquire means another process is still cloning;
   the OS releases the lock automatically if that process dies, so
   there is no dedicated stale-lock code path to write for the flock
   itself — this is the concrete form of the reclaim guarantee named
   in Rationale).
3. Inside the locked section, re-run the existing exists-check
   (`_mkt(d).exists()`) and branch exactly as today: warm →
   migrate/TTL/pull path unchanged; cold → `mkdir` + `git clone` +
   post-clone existence check, unchanged apart from now running inside
   the lock.
4. Release the lock (`fcntl.flock(lock_fd, fcntl.LOCK_UN)`) and close
   the fd in a `finally`, so a clone failure (the existing `sys.exit`
   on line 247-248) still releases before the process exits — matters
   for tests that run this in-process without a real process exit.
5. `tests/test_spawn.py`: new test class exercising
   `rulebook_checkout()` under simulated concurrency — spawn N threads
   calling it against a mocked `subprocess.run` for `git clone` that
   (a) fails if invoked while the target dir is non-empty (reproducing
   today's collision) and (b) creates `marketplace.json` under `d` on
   success — and assert exactly one real clone subprocess call
   happened and all N threads returned the same `Path` with no
   exception. A second test proves the reclaim guarantee by killing the
   holding process mid-clone via a real subprocess and asserting a
   subsequent call still succeeds (the OS releases a dead process's
   flock automatically — no pid marker needed for the primary lock). A
   third test asserts the warm-cache path issues zero `git` subprocess
   calls (only the existing `_pull_is_fresh` gate decides), unchanged
   from today.

## Out of scope

- `ensure_rulebook()` (spawn.py:296) and its `claude -p --settings`
  warm-up dance — it calls `rulebook_dir()`, not `rulebook_checkout()`,
  and doesn't clone; untouched.
- Locking anything other than the clone-population section — pull
  (`_pull_is_fresh` / `git pull`) on the warm path stays unlocked, same
  as today (a concurrent pull race is a different, much smaller
  problem the issue does not report or ask for).
- Cross-machine locking (`flock` is local-filesystem only) — spawns in
  this repo's usage always share one filesystem (northpole orchestrator
  runs same-host); out of scope per the issue's reproduction scenario.

## Accumulation

The change adds one lock/unlock pair around one existing call site
(`rulebook_checkout()`), not a per-role or per-marketplace repeated
inline block — there is exactly one clone-population path in this
file, so this does not accumulate as more roles or marketplaces are
added; every role's checkout already funnels through this single
function, and the lock path is derived (`_rulebook_lock_path(d)`) from
`d`, not hand-written per caller. If a second cache-populating call
site were ever added elsewhere in the codebase, it would need to reuse
`_rulebook_lock_path`/the same lock discipline rather than re-implement
its own — that reuse obligation is the guard against this becoming N
inline copies; today N=1 call site exists, so no extraction beyond the
one new helper is warranted yet.

## How you'll know it worked

- New `tests/test_spawn.py` concurrent-population test passes and,
  without the fix (reverting to a pre-lock version of
  `rulebook_checkout`), reproduces the collision (fails).
- Warm-cache regression test shows zero new `git` subprocess
  invocations, confirming byte-identical behavior for that path.
- `python3 -m pytest tests/test_spawn.py -q` run clean.
