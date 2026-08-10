---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

## Request

The respawn cap (`RESPAWN_MAX_ATTEMPTS`, from #675) currently counts every
automatic continuation the same way, whether or not the session actually
advanced the work. Make it count only *no-progress* respawns: reset the
counter when measurable progress happened since the previous respawn (a new
commit sha on the branch, or a change to any file under
`docs/issue-<n>/**`). `refused`/`waiting-on-human` stay excluded from
auto-continuation entirely, as today. Decide, but do not necessarily build,
whether an absolute total-respawn ceiling is also warranted as a backstop.

## Constraints

- `refused`/`waiting-on-human` must never auto-continue — unchanged from
  today's structural exclusion.
- Progress detection must read observable repo state (commit sha,
  board-file content), never the spawned session's own self-report of
  having "made progress."
- Cap-reached behavior must keep posting the durable issue comment via
  `_post_crash_comment()`.
- No new dependency, no new environment variable, no schema/migration.

## Rationale

Two progress signals are named in the issue: commit sha and board-record
delta. The survey found both measured today by existing primitives
(`_git_head`/`_is_new_commit` and `board_snapshot`) already used elsewhere
in `spawn.py`'s classify/reconcile pipeline — no new instrumentation is
needed, only wiring a stored "fingerprint" into `_respawn_or_cap()`.

Alternative considered and rejected: deriving progress from the *outcome
string* the most recent session ended with (e.g. treat `classify()`'s
`progressed` verdict as "reset the counter") instead of an explicit
before/after fingerprint diff. Rejected because outcome strings describe
one session's own end state, and are already consumed once to decide
*whether* to respawn at all; they answer "did this last attempt look done,"
not "did overall state advance across the *sequence* of respawns," which is
what the counter tracks. A session that ends `crashed` after having pushed
a real commit earlier in the same attempt is exactly the case the issue
wants credited, and no single-session outcome string carries that.

On the absolute-ceiling question: this proposal adopts one. A counter that
only tracks no-progress *streaks* has no protection left against a session
that keeps making trivial, real progress forever (a genuine but
economically pointless commit or board touch every attempt) — the issue's
own "Still broken / out of scope" section names exactly this risk and asks
phase 1 to decide it. The alternative — no absolute ceiling, rely solely on
the no-progress streak — was rejected because it removes the only cost
backstop #675's original cap provided, trading an unconditional total limit
for one that a manufactured-progress pattern can defeat indefinitely. The
ceiling is set high enough to not interfere with the streak-reset's stated
purpose (a task genuinely advancing every single respawn) while still
bounding total token cost for a single roster key.

## What will be done

- Add a fingerprint helper in `spawn.py` that reads, for a given
  workspace: the current git HEAD sha (`_git_head`) and a stable hash of
  `board_snapshot()`'s output (sorted-dict hash, so two identical snapshots
  hash equal regardless of dict ordering).
- Extend the `RESPAWN_STATE` entry per key from `{"attempts": N}` to also
  carry the fingerprint recorded at the *previous* respawn attempt (e.g.
  `{"attempts": N, "fingerprint": {"head": ..., "board": ...}}`).
- In `_respawn_or_cap()`, before the existing `attempts >=
  RESPAWN_MAX_ATTEMPTS` check: compute the current fingerprint from `work`;
  compare it against `state[key]["fingerprint"]` (absent on first respawn,
  treated as "no prior fingerprint" — never itself progress or no-progress,
  just nothing to diff against, so the first respawn starts the streak at
  1 as today). If either component differs, treat this as progress: reset
  the no-progress streak to 0 before incrementing (so this attempt becomes
  streak 1, not streak N+1). If both are unchanged, increment the streak as
  today.
- Add a second constant, `RESPAWN_ABSOLUTE_MAX`, checked independently of
  the no-progress streak against a new `state[key]["total_attempts"]`
  counter that increments on every respawn regardless of progress. Reaching
  either cap triggers the existing `_post_crash_comment()` path (same
  comment mechanism, distinguishable by trigger string/body text for which
  cap fired).
- Store the fingerprint taken *after* a successful respawn is issued (i.e.
  the state the next call should diff against), so the comparison always
  measures "since the last time we respawned," matching the issue's wording
  exactly.
- Extend `test_spawn.py`'s `AutoRespawnClaim`/`SelfTriggeredRespawn`
  (and/or a new test class) with: a respawn preceded by a new commit sha
  resets the no-progress streak; a respawn preceded by a changed
  `docs/issue-<n>/**` file resets it too; consecutive no-progress respawns
  still hit `RESPAWN_MAX_ATTEMPTS`; the new `RESPAWN_ABSOLUTE_MAX` cap
  fires even when the no-progress streak keeps resetting; `refused`/
  `waiting-on-human` never reach `_respawn_or_cap()` at all (regression
  guard on the existing exclusion).

## Accumulation

The two new constants (`RESPAWN_MAX_ATTEMPTS`, unchanged, and the new
`RESPAWN_ABSOLUTE_MAX`) and the `RESPAWN_STATE` per-key shape
(`attempts`/`fingerprint`/`total_attempts`) are each defined exactly once
in `spawn.py` and read by the single shared `_respawn_or_cap()` function —
this change adds fields to that one already-shared structure, it does not
add a new per-caller inline `subprocess`/`gh` call or a new repeated
file/list entry. If a future issue needs a third progress signal (e.g. a
test-count delta), it extends the same one fingerprint helper and the same
one state shape; it does not add a new standalone respawn path. Nothing
here scales linearly with issue count, role count, or roster size — the
state dict is already keyed per roster `key` today, and this proposal adds
two more per-key fields to an existing per-key entry, not a new per-key
file.

## Out of scope

- Orchestrator-side blocking or scheduling changes (#645 territory, per the
  issue text).
- Changing what counts as `refused`/`waiting-on-human` or how those
  outcomes are classified.
- Any change to `_post_crash_comment()`'s idempotency/marker mechanism
  beyond what is needed to report which cap fired.
- Retroactively re-deriving progress for respawns that already happened
  before this change ships — the streak starts fresh from this change's
  first call per key.

## How you'll know it worked

`python3 -m pytest test_spawn.py -k "RespawnOrCap or SelfTriggeredRespawn or
ProgressAware"` passes, including the new cases above. Manual trace: a key
with `attempts == RESPAWN_MAX_ATTEMPTS - 1` whose workspace has a new
commit sha since the last respawn is respawned again with its no-progress
streak reset to 1 rather than capped; a key with unchanged HEAD and
unchanged `docs/issue-<n>/**` content across `RESPAWN_MAX_ATTEMPTS`
consecutive respawns still hits the cap and posts the durable comment.
