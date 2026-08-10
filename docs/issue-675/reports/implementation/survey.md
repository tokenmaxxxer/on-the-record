Scout skip record: this is a pure mechanism-extension bugfix inside `spawn.py`'s
existing classify/respawn pipeline — no product-shaped surface, no external
category to benchmark against. Skip condition: "the change is a pure bugfix"
(scout-directive). No scout brief written.

## Current state (spawn.py)

- `classify(rc, result, delta, blocked)` (spawn.py:1497-1520): names one of
  `errored` / `progressed` / `waiting-on-human` / `refused` / `silent-failure`.
  `silent-failure` is the fallback: exit 0, no board delta, nothing blocked,
  no `permission_denials`. This is exactly the "causeless incomplete stop"
  shape the issue describes — a session that talked and stopped.
- `fail_closed_downgrade()` (spawn.py:1571-1621) runs after `classify()` and
  can *upgrade* a `silent-failure` to `progressed` (issue #484) when git/PR
  state shows real delivery (`already_delivered` or `new_commit +
  push_succeeded`), or downgrade it to `uncommitted-work` /
  `push-rejected` via the two `elif` branches at spawn.py:4526-4531. A
  `silent-failure` that survives both of these has, by construction: no new
  commit, no dirty tree that got flagged as `uncommitted-work`, no
  `push-rejected`, and no open/merged PR on the branch. That is the "no PR,
  no refusal record, no waiting-on-human marker" case the issue names.
- `RESPAWN_MAX_ATTEMPTS = 2` (spawn.py:2397) is a single shared cap, keyed by
  roster `key`, spent atomically via `.respawn-claim-{ts}` files
  (O_CREAT|O_EXCL) in `_respawn_or_cap()` (spawn.py:2547-2607). Both existing
  triggers funnel into this one function:
  - watchdog `crashed` path: `_auto_respawn_check()` (spawn.py:2610-2645),
    gated by `session_end_verdict() == "crashed"`.
  - self-trigger path: `_self_trigger_respawn()` (spawn.py:2651-2671), gated
    by `outcome in _ABANDONED_WORK_OUTCOMES` where
    `_ABANDONED_WORK_OUTCOMES = ("uncommitted-work", "failed-no-commit")`
    (spawn.py:2648).
  `_self_trigger_respawn()`'s own docstring (spawn.py:2662-2665) states the
  current deliberate exclusion: "`refused`/`waiting-on-human`/그냥
  `silent-failure`는 사람이 봐야 하거나 정당한 무변화이지 이 결함의 모양이
  아니라서 여기서 건드리지 않는다" — i.e. plain `silent-failure` was
  explicitly scoped OUT of issue #247's self-trigger. Issue #675 asks to
  reopen exactly that exclusion, narrowed to the causeless subset.
- `_self_trigger_respawn()` is called once per bounded self-spawn, right
  after `session-end` is appended and the durable comment posted
  (spawn.py:4632-4633), inside the child branch of `_spawn_one()`
  (`bounded and issue is not None`, spawn.py:4605).
- `failed-no-commit` (`fail_closed_downgrade`, spawn.py:1621) is a
  distinct outcome from `silent-failure`: it fires when `classify()` said
  `progressed` (board delta happened) but git shows no new commit — this
  outcome is already a member of `_ABANDONED_WORK_OUTCOMES`, so it is
  already auto-continued today.
- `refused` and `waiting-on-human` are never touched by
  `_self_trigger_respawn()` and must stay that way — the issue's acceptance
  criteria explicitly requires the refusal/human-gate distinction be
  preserved, not collapsed.
- Cap-reached behavior: `_post_crash_comment()` (spawn.py:2415-2434) posts
  the durable "respawn cap reached" issue comment regardless of which
  `trigger` string called `_respawn_or_cap()` — this already generalizes
  across triggers, so no change is needed there; a new trigger value only
  needs to be a distinct string for the log line at spawn.py:2605 and the
  comment body's `trigger` param.

## Write set implied for phase 2

- `spawn.py`: extend `_ABANDONED_WORK_OUTCOMES` (or add an equivalent
  explicit check next to it) to include the causeless `silent-failure`
  case, and pass a distinct `trigger` string
  (e.g. `"self-triggered-causeless"`) through `_self_trigger_respawn()` so
  cap-comments/log lines can tell it apart from `uncommitted-work`.
- `test_spawn.py`: extend `Classify` (spawn.py:938) and
  `SelfTriggeredRespawn` (spawn.py:3997) with cases for: `silent-failure`
  routed to respawn, `refused` and `waiting-on-human` still excluded.

## Alternatives visible from this survey (for the proposal's Rationale)

1. Add `"silent-failure"` directly to `_ABANDONED_WORK_OUTCOMES`'s tuple.
2. Introduce a separate constant/function (e.g.
   `_CAUSELESS_INCOMPLETE_OUTCOMES` or a `_is_causeless(outcome, ...)`
   predicate) instead of overloading `_ABANDONED_WORK_OUTCOMES`, since the
   two failure shapes ("dirty tree left behind" vs "talked and stopped with
   nothing to show") are semantically distinct even though both end up
   auto-continued.
3. Add a goal-check re-arm mechanism in `reconcile()` instead of extending
   the self-trigger outcome set — `reconcile()` already emits
   `next_action: respawn` for its own divergence set (spawn.py:1624-1692)
   but `drive()` explicitly refuses to act on it (spawn.py:3268); wiring
   `drive()` to act would be a second, independent trigger path parallel to
   `_self_trigger_respawn()`.

These are evaluated in the proposal's `## Rationale`.
