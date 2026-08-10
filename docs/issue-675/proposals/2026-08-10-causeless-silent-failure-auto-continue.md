---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

## Request

A spawned role session is a single-shot headless turn. When the model ends
its turn early with no board delta, nothing blocking, and no permission
denial, `classify()` names it `silent-failure` — and today that outcome is
explicitly excluded from the self-trigger respawn path
(`_self_trigger_respawn()`, spawn.py:2648-2671), so nothing continues it; a
human has to notice and manually respawn. `refused` (gate denied a write) and
`waiting-on-human` (blocked on a real gate) are legitimate stops and must
stay excluded. The ask is to auto-continue the causeless case — no PR, no
refusal record, no waiting-on-human marker — under the existing attempt cap
(`RESPAWN_MAX_ATTEMPTS = 2`), while still never touching `refused` or
`waiting-on-human`.

## Constraints

- Never auto-continue `refused` or `waiting-on-human` — the issue's
  acceptance criteria states this distinction must stay enforced in
  `classify()`/`_respawn_or_cap()` "or an equivalent named mechanism, not
  prose."
- Reuse the existing shared cap and claim machinery
  (`RESPAWN_MAX_ATTEMPTS`, `_respawn_or_cap()`'s atomic
  `.respawn-claim-{ts}` file) — the issue asks to extend the
  respawn-eligible outcome set, not build a second respawn pipeline.
- Cap-reached behavior must still post the durable issue comment
  (`_post_crash_comment()`, spawn.py:2415-2434) — already generalized across
  `trigger` values, so this falls out for free as long as the new path calls
  `_respawn_or_cap()` with a `trigger` string of its own.
- Only a `silent-failure` that has already survived
  `fail_closed_downgrade()`'s upgrade/downgrade checks counts as causeless —
  a `silent-failure` that git evidence shows was actually delivered is
  already upgraded to `progressed` before `_self_trigger_respawn()` ever
  sees it (spawn.py:4526-4568), so no new "is it really causeless" check is
  needed on top of that existing pipeline.

## Rationale

Chosen: add `"silent-failure"` to `_ABANDONED_WORK_OUTCOMES`
(spawn.py:2648), and pass a distinct `trigger` string
(`"self-triggered-causeless"`) through `_self_trigger_respawn()` so
logs/cap-comments can tell this path apart from the existing
`uncommitted-work` self-trigger.

Rejected alternative: introduce a separate constant/predicate (e.g.
`_CAUSELESS_INCOMPLETE_OUTCOMES` or `_is_causeless()`) instead of extending
`_ABANDONED_WORK_OUTCOMES` in place. Rejected because
`_ABANDONED_WORK_OUTCOMES` already means exactly "self-trigger set that
routes into `_respawn_or_cap()`" — a second parallel set with the same
shape and the same consumer (`_self_trigger_respawn()`'s single `if outcome
not in ... : return`) would only fork one membership check into two without
changing behavior; the `trigger` string parameter already gives the two
failure shapes (dirty tree vs. talked-and-stopped) distinct identity in the
log/comment record, which is the same distinguishing power a second
constant would buy, without the extra indirection.

Rejected alternative: wire `drive()` to act on `reconcile()`'s
`next_action: respawn` divergence (spawn.py:1624-1692, 3268) instead of
extending `_self_trigger_respawn()`. Rejected because that is a second,
independent trigger path parallel to the existing self-trigger/watchdog
pair, competing for the same `RESPAWN_MAX_ATTEMPTS` budget through a
different code path — the issue's acceptance criteria asks for the
respawn-eligible outcome set to be extended (or an equivalent re-arm
mechanism), and extending the set that `_self_trigger_respawn()` already
checks satisfies that with less new surface than standing up a second
consumer of `_respawn_or_cap()`.

## What will be done

- In `spawn.py`, change `_ABANDONED_WORK_OUTCOMES` (spawn.py:2648) to
  `("uncommitted-work", "failed-no-commit", "silent-failure")`.
- In `_self_trigger_respawn()` (spawn.py:2651-2671), pass a `trigger` value
  that distinguishes the causeless case from the existing dirty-tree case —
  `"self-triggered-causeless"` when `outcome == "silent-failure"`,
  `"self-triggered-abandoned"` otherwise (current value, unchanged) — so
  `_respawn_or_cap()`'s log line (spawn.py:2605) and
  `_post_crash_comment()`'s body still show which failure shape triggered
  the respawn once the cap is hit.
- Update the docstring at spawn.py:2662-2665 (currently states plain
  `silent-failure` is out of scope) to reflect the narrowed exclusion: only
  `refused`/`waiting-on-human` stay excluded now.
- In `test_spawn.py`, extend `Classify` (spawn.py:938) and
  `SelfTriggeredRespawn` (spawn.py:3997) with cases: `silent-failure`
  routes to `_respawn_or_cap()` with the new trigger string; `refused` and
  `waiting-on-human` still return without calling it.

## Accumulation

This adds one more member to `_ABANDONED_WORK_OUTCOMES` and one more
`trigger` string literal next to the two that already exist
(`"watchdog-observed-crashed"`, `"self-triggered-abandoned"`). If future
issues keep widening the causeless-continuation set outcome-by-outcome
(e.g. `push-rejected` later, per the Out-of-scope note below), the tuple
and the `trigger`-string `if/else` in `_self_trigger_respawn()` stay a
short, flat list/branch — no shared helper is warranted below roughly 4-5
members, since each member is one outcome name plus one distinguishing
string, not repeated logic. If a fourth or fifth outcome is added, the
`if/else` chain should become a `dict[outcome] -> trigger` lookup at that
point rather than nesting further `elif` branches; this proposal's two-way
branch does not yet cross that threshold.

## Out of scope

- Any change to `classify()`'s own outcome-naming logic — it already names
  `silent-failure` correctly; this proposal only changes what happens after
  the name is assigned.
- The watchdog `crashed` path (`_auto_respawn_check()`) — unaffected, keeps
  its own `session_end_verdict() == "crashed"` gate.
- `push-rejected` — has a real commit and a concrete, actionable reason
  (host push failure) already surfaced to the operator
  (spawn.py:4530-4531); not the "no PR, no refusal record, no
  waiting-on-human marker, and nothing to point at" shape this issue names.
  Left for a future issue if the same causeless-continuation logic should
  extend to it.
- Orchestrator-side blocking on long-running sessions (#645).
- Any goal-check re-arm mechanism in `reconcile()`/`drive()` — the rejected
  alternative above.

## How you'll know it worked

check: `test_spawn.py::Classify` and `test_spawn.py::SelfTriggeredRespawn`
gain passing cases for `silent-failure` (respawns, distinct trigger string)
and `refused`/`waiting-on-human` (still excluded) — run via
`python3 -m pytest test_spawn.py -k "Classify or SelfTriggeredRespawn"`.
empty state: not applicable — this is a pure code-path extension with no
corpus/empty-state distinction.
provenance: executed-unit — the new/extended test cases are run directly
against `_self_trigger_respawn()` and `classify()`, not through a live
spawned session.
