---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - on-the-record/commands/run.md
---

## Request

Session outcomes (normal completion, PR opened, or no PR) currently reach
the orchestrator only through the orchestrator's own in-conversation
re-arm/watch loop — LLM state that a context compaction or restart drops.
Make the outcome recoverable from persistent state instead: post a durable
issue comment on session-end/PR-open, and add a reconcile sweep that lists
sessions whose outcome was never acknowledged, callable at any wake-up
(including after compaction).

## Constraints

- Reuse the existing idempotent marker-comment pattern
  (`_issue_comments()`, spawn.py:1070) — no duplicate comments across
  repeated watchdog ticks.
- Reuse `_pr_open_or_merged_for_branch()` (spawn.py:1049) as the PR-open
  signal; do not invent a second PR-state check.
- Do not change `_auto_respawn_check()`'s documented contract
  (spawn.py:2313-2318: "respawn 여부만 판단한다") — respawn-decision and
  outcome-reporting are different concerns and must not be fused into one
  function whose docstring says otherwise.
- New sweep must reuse `roster_reconcile()`'s existing CLI verb
  (`spawn.py reconcile`) rather than adding a parallel command surface.
- Tests must follow the existing no-live-`gh` convention (monkeypatch
  `spawn._issue_comments`, assert marker presence / call count).

## Rationale

Two placements were viable for the new outcome-comment logic:
(1) extend `_auto_respawn_check()` to also branch on `normal`/`in-progress`
verdicts, or (2) add a new sibling function called from
`roster_watchdog()` alongside `_auto_respawn_check()`.

(1) was rejected: `_auto_respawn_check()`'s own docstring
(spawn.py:2313-2318) states its contract is deciding respawn, and it
already special-cases `stalled` only because that comment is a *side
effect of the respawn decision itself* ("재스폰하지 않는 것과 아무도
모르게 재스폰하지 않는 것은 다르다" — the comment justifies *not*
respawning). A `normal`/PR-opened comment is not a respawn-adjacent
side effect at all — it fires precisely when respawn is irrelevant. Folding
it into `_auto_respawn_check()` would silently broaden a function whose
name and docstring promise a narrower job, which is exactly the kind of
undocumented scope creep this repo's own doctrine ladder rules exist to
prevent (decisions belong in a decision, not buried in an unrelated
diff). Chosen: (2) — a new function, `_post_session_end_comment()`,
called from `roster_watchdog()` right after `_auto_respawn_check()`,
keeping the two concerns (respawn-decision vs. outcome-durability)
separately named, separately testable, and independently
disable-able.

A third question, surfaced by the after-proposal warrant hunt
(docs/reports/2026-08-09-hunt-session-end-durability.md): calling the new
comment poster only from `roster_watchdog()`'s dead-entry scan cannot work
for `verdict == "normal"` at all — `_spawn_one()` (spawn.py:3988) calls
`roster_remove()` synchronously right after `proc.wait()`, the same race
`_self_trigger_respawn()`'s docstring (spawn.py:2360-2367) already
documents: no later watchdog tick can ever see a dead-but-registered entry
for a normally-ended session, since the roster entry is already gone by
the time any tick runs. The alternative of leaving the comment call in
`roster_watchdog()` only and relying on `--unreported` to catch what it
misses was rejected: `--unreported` would then report every normal
session-end as permanently unacknowledged, not as a rare recovery case,
defeating its own purpose. Chosen instead: follow
`_self_trigger_respawn()`'s own precedent — call the new
`_post_session_end_comment()` self-triggered, from inside `_spawn_one()`
itself right after the session-end event is written (before/alongside
`roster_remove()`), not from the watchdog tick. `roster_watchdog()`'s
`--unreported` sweep then exists purely as the recovery path for what the
self-trigger itself misses (process killed before reaching that line,
orchestrator died mid-call) — the actual scenario the issue describes, not
the common path.

For the reconcile sweep, the alternative of a brand-new top-level CLI verb
(`spawn.py unreported`) was considered and rejected in favor of a
`--unreported` flag on the existing `spawn.py reconcile` verb
(`roster_reconcile()`, spawn.py:1964) — the existing verb already means
"go find state the orchestrator should react to"; a second verb with
near-identical semantics would fragment the sweep entry point the issue
explicitly asks for ("a single call the orchestrator can run at any
wake-up").

## What will be done

- `spawn.py`:
  - Add `_SESSION_END_COMMENT_MARKER` templates (normal-no-PR and
    PR-opened variants), following `_STALL_COMMENT_MARKER`'s pattern.
  - Add `_post_session_end_comment(root, issue, key, work, log)`:
    computes `verdict` via `session_end_verdict()`, resolves PR state via
    `_pr_open_or_merged_for_branch()`, and posts (idempotently, via
    `_issue_comments()`) `[watch] {key}: session-end: PR <url> opened` or
    `[watch] {key}: session-end: no PR` for `verdict in ("normal",)`.
    `in-progress`/`stalled`/`crashed` stay out of this function's scope
    (crashed/stalled already get their own comments elsewhere).
  - Call `_post_session_end_comment()` self-triggered from `_spawn_one()`
    (spawn.py:~3988) right after the session-end event is recorded and
    before/alongside `roster_remove()` — following
    `_self_trigger_respawn()`'s existing precedent for the same
    dead-entry-invisible-to-watchdog race. Also call it from
    `roster_watchdog()` (spawn.py:~1940-1948) as a best-effort catch for
    any dead-but-registered entry a watchdog tick does still observe
    (e.g. non-self-triggered paths); primary coverage is the self-trigger,
    not the tick.
  - Add `--unreported` flag to the `spawn.py reconcile` CLI verb
    (`roster_reconcile()`, spawn.py:1964): when set, scan the roster (or
    completed-session records under the events log) for entries with
    `verdict == "normal"` and no matching `_SESSION_END_COMMENT_MARKER`
    in the issue's comments — i.e., sessions that ended, may have opened a
    PR, and were never durably reported. Print each as a line the
    orchestrator can act on; this the "empties after acknowledgment"
    fixture the issue's acceptance criterion names (acknowledgment =
    presence of the marker comment).
  - PR-open detection signal: `_pr_open_or_merged_for_branch()`
    (spawn.py:1049, already hardened by #484 to use open-or-merged, not
    `--state all`). Failure mode (per issue's "empty state" acceptance
    line): if the `gh pr list` call itself fails (network/auth), the
    comment falls back to the no-PR wording with a `(pr-check-failed)`
    suffix rather than silently omitting the comment or crashing the
    watchdog tick — the session-end fact is always reported even when the
    PR sub-check is unreliable.
- `test_spawn.py`: unit tests for `_post_session_end_comment()` (marker
  idempotency, PR-url interpolation, pr-check-failed fallback) and for
  `roster_reconcile(unreported=True)` (synthetic ended-session-with-open-PR
  fixture appears before acknowledgment, disappears after a matching
  marker comment is injected into the mocked comment list).
- `on-the-record/commands/run.md`: add one contract line under session
  start / post-compaction recovery — first act is `spawn.py reconcile
  --unreported` (not resuming from conversation memory).

## Accumulation

`_post_session_end_comment()` adds one more inline `subprocess.run(["gh", ...])`
site to `spawn.py`, alongside the existing `_post_stall_comment`/
`_post_crash_comment`/`_post_stranded_push_comment` family it follows the
pattern of. If N more outcome-comment variants show up later (e.g. a
`waiting-on-human` comment), the right move is the same one this family
already avoids taking today: consolidate the shared
read-marker/post-if-absent skeleton into one small helper
(`_post_marker_comment(root, issue, marker, body_fn)`) that the per-verdict
functions call, rather than adding a fourth/fifth copy of the
read-then-check block. This proposal does not do that consolidation now —
three near-identical call sites (crash/stall/session-end) is still within
the pattern's existing shape, and a fourth (stranded-push, which already
exists) has not triggered it either; a fifth new variant should.

## Out of scope

- Issue #533 (roster key collision) — not present in this checkout, no
  code dependency found.
- Changing `_auto_respawn_check()`'s respawn decisions themselves.
- A new durable transport beyond GitHub issue comments (e.g. a database,
  webhook) — issue comments are the existing durable substrate
  (`_issue_comments()`) and the issue's own fix direction names comments
  explicitly.
- Rewriting `spawn.py watch --all` (#488) or the registration-race fix
  (#484) — both stay as-is; this proposal only adds the missing comment
  and sweep.

## How you'll know it worked

- `python3 -m pytest test_spawn.py -k session_end_comment` and `-k
  unreported` pass, covering: marker posted once for a normal/PR-opened
  session-end; sweep lists an ended-session-with-open-PR fixture and
  empties after the marker comment exists.
- `python3 -m pytest` (full suite) passes.
- Manual trace: `spawn.py reconcile --unreported` against a roster with a
  synthetic `normal`-verdict, unmarked entry prints that entry; re-running
  after injecting the marker comment prints nothing for it.
