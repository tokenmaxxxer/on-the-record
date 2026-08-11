---
name: survey
subject: issue-773
---

# Current-state survey — issue-773

Scout skip: pure bugfix on an internal TOCTOU race — no product-facing
design decision, no external exemplar applies. Skip condition: "spec
leaves no design decision open" does not literally apply (there is a
lock-strategy choice), but the choice is an internal concurrency-control
mechanism, not a product surface — scouting best-in-class products has
no purchase here. Treated as pure-bugfix-adjacent; skip recorded per
scout-directive.

## Write set (frozen candidates)

- `spawn.py` — `rulebook_checkout()` (spawn.py:207-251), the sole
  populator of `runs/rulebooks/<mkt>`.
- `tests/test_spawn.py` — new test class for concurrent
  `rulebook_checkout()` calls.

No `.env.example`, no dependency manifest, no migration: the fix is
pure stdlib (`os`, `tempfile`, `fcntl`/`os.link`, already imported in
spawn.py at line 23 `import fcntl`).

## The race, traced

`rulebook_checkout(role, spec)` (spawn.py:207):

1. Line 234: `d = ROOT / "runs" / "rulebooks" / mkt` — path is fixed by
   marketplace name; every same-role spawn computes the identical `d`.
2. Line 235: `if _mkt(d).exists():` — exists-check #1. All concurrent
   spawns for a cold cache see `False` here (no lock guards this read).
3. Line 243: `d.parent.mkdir(parents=True, exist_ok=True)` — harmless,
   idempotent.
4. Line 245: `git clone -q https://github.com/{repo}.git {d}` — every
   spawn that passed step 2 races to clone into the SAME final path
   `d`. `git clone` refuses when the target exists and is non-empty,
   so all but the first clone to reach `mkdir`/write fail with "target
   path already exists and is not empty" — this is the loss pattern
   the issue reports from its reproduction batch (see the issue #773
   body for the reproduction's exact count).
5. Line 247: `if not _mkt(d).exists(): sys.exit(...)` — the losing
   clones hard-exit the whole `on-the-record` spawn process; nothing
   downstream runs for that role's session.

Classic check-then-act TOCTOU: the exists-check (step 2) and the
clone-into-final-path (step 4) are not atomic with respect to other
processes, and no interprocess exclusion exists between them.

`_RULEBOOK_CACHE` (module-level dict, line 204) only dedupes calls
*within one process* — it is empty at process start and gives zero
protection across the separately-spawned `on-the-record` processes
that raced in the reproduction (each parallel `architecture` spawn is
a separate OS process, each running its own fresh `spawn.py`).

## TTL freshness path (#285), must be preserved unchanged

Once `_mkt(d).exists()` is `True` (warm cache, the common case after
the first successful clone), the current code takes a *different*
branch entirely (spawn.py:235-241): `_migrate_legacy_ttl_marker`, then
`_pull_is_fresh(d)` gates whether `git pull` runs, then
`_mark_pulled(d)`. This path does zero clones and must stay byte-for-byte
identical for the "single spawn with a warm cache" acceptance case —
i.e. any lock added around clone-population must not force a lock
acquisition (or any other new syscall) onto the already-warm path,
or must make that acquisition so cheap/uncontended it doesn't change
observable behavior (no new `git` invocation, same TTL skip decision).

## Existing staleness/reclaim pattern to mirror (spawn-claim, #223)

`_acquire_spawn_claim` / `_release_spawn_claim` (spawn.py:4317-4405)
already solve a structurally identical problem — exclusive access to a
shared resource keyed by path, with crash-safe reclaim — for spawn
claims:

- Atomic creation via write-to-tempfile-then-`os.link()` (not
  `O_CREAT|O_EXCL` directly), because `open` + separate write leaves a
  window where a concurrent reader sees a just-created-but-empty file
  and misjudges it corrupt/stale (documented TOCTOU at spawn.py:4332-4337,
  found by hunt).
- Staleness reclaim via `_alive(pid)` (spawn.py:1785, `os.kill(pid, 0)`)
  — a lock/claim file records the holder's pid; a holder whose pid is
  no longer alive is treated as stale and reclaimed, not honored
  indefinitely.
- Release only unlinks if the current pid still owns the claim
  (spawn.py:4391-4404) — avoids releasing a claim some other process
  already reclaimed after this one went stale.

This pattern is the direct analogue the issue's fix direction points
at ("matching the existing spawn-claim staleness pattern") and is the
natural template for a per-rulebook lock: same directory
(`runs/rulebooks/`), same crash-safety requirement (a spawn can be
killed mid-clone), same reclaim mechanism (pid liveness), same
atomic-creation technique (tempfile + `os.link`).

## Alternatives considered (survey-level, expanded in proposal Rationale)

1. **`fcntl.flock` on a per-rulebook lock file, held for the clone
   duration.** `fcntl` is already imported (line 23) and already used
   for the roster lock (spawn.py:1732-1739, `ROSTER.with_name(...
   ".lock")` + `flock(LOCK_EX)` / `flock(LOCK_UN)`). Blocking flock
   naturally serializes concurrent clones into "one clones, the rest
   wait then reuse" — matches the issue's "share the one clone or wait
   for it" language directly, and reuses an in-file precedent instead
   of adding a new mechanism.
2. **Clone-to-temp-dir then atomic `os.rename`** (issue's other named
   direction) — clone into a per-attempt tmp dir
   (`runs/rulebooks/.tmp-<mkt>-<pid>-<rand>`), then `os.rename()` the
   tmp dir onto the final `d` only if `d` still doesn't exist,
   otherwise discard the tmp clone and reuse the winner's `d`. Avoids
   ever holding a lock across the slow network clone, but wastes
   network/CPU on every loser's full clone (a fresh rulebook clone,
   not a small file — CLONE_TIMEOUT=180s budget for a reason) and
   needs its own race check at the rename step (`os.rename` onto an
   existing non-empty dir raises `OSError` on POSIX, so the loser still
   needs a "does `d` now exist" check after losing the rename, not
   just before).
3. **Do nothing / catch-and-retry the "already exists" error in the
   caller.** Rejected outright: doesn't fix the underlying race, only
   papers over one observed symptom string; a retry would just re-race
   against a slower-finishing winner and could still lose if the winner
   hasn't finished writing objects yet when the loser's `_mkt(d).exists()`
   retry-check fires (marketplace.json may exist mid-clone before
   `git clone` finishes checkout, giving a partially-written directory).

Proposal will pick between (1) and (2) and give the rejection reason
for the other, since the issue accepts either ("a per-rulebook file
lock ... or clone into a temp dir then atomic rename").

## Acceptance mapping

- "unit test simulates N concurrent rulebook-cache populations for one
  role and asserts exactly one clone occurs (or all serialize) with no
  'already exists / not empty' failure" → new test in
  `tests/test_spawn.py`, driving `rulebook_checkout()` from multiple
  threads/processes against a `subprocess.run` mock that counts clone
  invocations and simulates the real "second clone into non-empty dir
  fails" behavior.
- "a stale lock is reclaimable" → test writes a lock/claim file
  stamped with a dead pid, asserts `rulebook_checkout()` still succeeds
  without hanging.
- "a single spawn with a warm cache skips cloning unchanged
  (byte-identical to today)" → existing warm-cache branch
  (spawn.py:235-241) untouched in the diff; a test locks in that no
  new `git` subprocess call happens on that path.
