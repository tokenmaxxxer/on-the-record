Scout skip record: this is a pure mechanism-extension bugfix inside `spawn.py`'s
existing respawn pipeline — no product-shaped surface, no external category to
benchmark against. Skip condition: "the change is a pure bugfix" (scout-directive).
No scout brief written.

## Current state (spawn.py)

- `RESPAWN_MAX_ATTEMPTS = 2` (spawn.py:2397) is a single shared cap, keyed by
  roster `key`, spent atomically via `.respawn-claim-{ts}` files
  (O_CREAT|O_EXCL) inside `_respawn_or_cap()` (spawn.py:2547-2607). The
  counter is `state[key]["attempts"]`, incremented unconditionally on every
  successful claim (spawn.py:2600-2604) and persisted via
  `_respawn_state_save()` to `RESPAWN_STATE` (`runs/respawn_state.json`,
  spawn.py:2396, saved at spawn.py:2409-2411). Nothing currently
  distinguishes a respawn that followed genuine progress from one that
  followed a no-op session — this is exactly the gap issue #678 names.
- Both existing triggers funnel into `_respawn_or_cap()`:
  - watchdog `crashed` path: `_auto_respawn_check()` (spawn.py:2610-2645).
  - self-trigger path: `_self_trigger_respawn()` (spawn.py:2651-2671), gated
    by `outcome in _ABANDONED_WORK_OUTCOMES` where
    `_ABANDONED_WORK_OUTCOMES = ("uncommitted-work", "failed-no-commit",
    "silent-failure")` (spawn.py:2648, extended by issue #675).
  - `refused`/`waiting-on-human` never reach either trigger function today —
    `_self_trigger_respawn()`'s own docstring (spawn.py:2662-2665) already
    states this exclusion is deliberate, and it must stay untouched by this
    issue (acceptance criteria: "`refused`/`waiting-on-human` never
    continue").
- Progress-measurement primitives already exist and are reused elsewhere in
  the same file, so no new instrumentation is needed to detect the two
  progress signals the issue names:
  - commit sha: `_git_head(cwd)` (spawn.py:1437-1442) returns current HEAD
    sha (or `None` for a commit-less repo); `_is_new_commit(cwd, before,
    after)` (spawn.py:1445-1464) already answers "did `after` land a real
    new commit on top of `before`" (ancestor-checked, not just `!=`) and is
    already called at spawn.py:4591 with `before_head`/`after_head` captured
    around a session run.
  - board-record delta: `board_snapshot(cwd)` (spawn.py:1467-1484) returns
    a `{relative_path: sha256(content)}` mapping for every file under
    `docs/issue-*/**` — already the primitive `reconcile()`/`classify()` use
    to detect "the board moved" (§6 of the contract, per the docstring).
    Two snapshots taken before and after a respawn interval can be compared
    dict-for-dict (or via a single hash of the sorted dict) to answer "did
    any board file change."
  - Both primitives take a `cwd`/`work` string identical to what
    `_respawn_or_cap()` already receives as its `work` parameter — no new
    parameter threading needed to reach them.
- `_respawn_or_cap()` currently has no "before" state to diff against on
  entry — it is called once per crash/self-trigger observation and reads
  `attempts` directly from `state[key]`. To detect progress *since the
  previous respawn*, the previous respawn's fingerprint (HEAD sha plus
  board-snapshot hash) must be persisted alongside `attempts` in
  `RESPAWN_STATE`, then compared against the *current* fingerprint (read
  fresh from `work` at call time) on each new call. `state[key]` is a dict
  already (`{"attempts": N}` — spawn.py:2603), so this is an additive key,
  not a shape change.
- Cap-reached behavior (`_post_crash_comment()`, spawn.py:2414-2439) fires
  when `attempts` reaches `RESPAWN_MAX_ATTEMPTS` (spawn.py:2585) and is
  unconditional on the `trigger` string — no change needed there beyond the
  counter it reads staying named `attempts`.
- No absolute total-respawn ceiling exists anywhere in the current code —
  `RESPAWN_MAX_ATTEMPTS` is the only cap, and per the issue it becomes
  strictly a *no-progress-streak* cap under this change. The issue's "Still
  broken / out of scope" section asks the proposal to decide, not build,
  whether a second absolute ceiling (independent of progress) is warranted
  as a token-cost backstop against a session that manufactures meaningless
  commits or board churn to keep resetting the counter forever.

## Write set implied for phase 2

- `spawn.py`: a fingerprint helper (HEAD sha plus board-snapshot hash)
  computed at each `_respawn_or_cap()` call; counter-reset logic comparing
  it against the fingerprint stored alongside `attempts` in
  `RESPAWN_STATE`; if the proposal adopts an absolute ceiling, a second
  constant and check.
- `test_spawn.py`: new cases per the issue's acceptance criteria — a
  respawn preceded by a new commit sha resets the counter; consecutive
  no-progress respawns still hit `RESPAWN_MAX_ATTEMPTS`; `refused` and
  `waiting-on-human` never continue (already true structurally — a
  regression-guard case, not new behavior).

## Alternatives visible from this survey (for the proposal's Rationale)

1. Store only the git HEAD sha as the progress fingerprint, ignore
   board-record deltas — simpler, but misses non-code progress the issue
   explicitly names (board-record delta as a first-class progress signal
   equal to commit sha), so a docs-only advancing session would wrongly be
   treated as no-progress.
2. Store only a board-snapshot hash, ignore commit sha — misses the
   opposite case: a session that commits and pushes real code but touches
   no `docs/issue-*/` file in that particular respawn interval (e.g. a
   pure-code follow-up commit after the board was already updated earlier).
3. Combine both signals as the survey concludes: fingerprint equals (HEAD
   sha, board-snapshot hash); progress is either component changing since
   the fingerprint stored at the previous respawn. This matches the issue
   text exactly ("new commit sha on the branch, or a board-record delta")
   and reuses existing primitives with no new instrumentation.
4. Re-derive progress from `session_end_verdict()`/`classify()` outcome
   strings (e.g. treat `progressed` as progress) instead of a fresh
   fingerprint diff — rejected because those outcomes describe the *most
   recent single session's* end state and are already consumed to decide
   *whether* to respawn at all (crashed/uncommitted-work/etc.); they don't
   answer "did state move since the last respawn attempt," a multi-attempt
   comparison `_respawn_or_cap()` doesn't currently do at all.
