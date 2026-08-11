# Issue #692 — Phase 1 Survey (implementation)

## Write surface

`on-the-record/hooks/decision-queue-stopgate.sh` — the waiting-declaration
guard is the `_WAITING_RE.search(last_msg) and not _ARM_RE.search(last_msg)`
branch (added #600, PR #622, commit 27df97f). It runs on every `Stop`
event, reading `last_assistant_message` fresh from the hook's own stdin
payload each invocation — the hook process is spawned per Stop, so it
has no built-in memory across turns.

## What the guard does today

1. Loads `decision_queue` from `spawn.py flows --json`.
2. If the last assistant message matches a waiting pattern
   (`대기 중`, `기다리는 중`, `waiting for`, `standing by`) and does NOT
   match a background-arm marker (`background`, `observation`, 백그라운드,
   옵저베이션), it emits `{"decision": "block", "reason": "..."}` and
   exits 0. The reason text quotes run.md rule 4 but does not restate
   the queue items themselves.
3. Otherwise falls through to the pre-existing age-tier logic (#466/#374,
   not at fault per the issue).

## Why it loops (confirmed by reading the branch)

A blocked Stop forces one more assistant turn. If the only actionable
work left is an operator decision, the model's honest next reply is
again a bare waiting statement — which re-matches `_WAITING_RE` and
re-blocks. Nothing in the branch remembers that it already fired once,
and the reason text does not hand the model a concrete escape shape (a
one-shot relay + close), only a citation to a rule. Both of those are
exactly what #692 asks to fix.

## Existing bounded-loop pattern in this repo: `retry-loop-bound.sh`

`on-the-record/hooks/retry-loop-bound.sh` (issue #507) already solves
"stop this exact class of repeated event after N times" for
`PreToolUse`/`PostToolUse` pairs:

- Keys a per-session JSON state file on `payload["session_id"]`
  (`${OTR_RETRY_BOUND_STATE_DIR:-$TMPDIR/otr-retry-bound}/<session_id>.json`),
  written atomically via `os.replace` over a `.tmp` file.
- `pre` mode reads the counter for a signature and changes behavior
  once a threshold is crossed (K: inject corrective context and allow;
  2K: deny outright for the rest of the session).
- Fails open on any parse/session_id-missing error — the hook only adds
  behavior on top of existing gates, never replaces them.

`decision-queue-stopgate.sh` is a single-event (`Stop`) hook, not a
pre/post pair, so it needs only the state-read-and-bump half of that
pattern, applied once per waiting-declaration block: on the block, if
this session has already blocked once, allow instead (state already
served its purpose — the queue is either now closed, or the operator
still owns it and forcing more turns does not help).

## Confirmed: `session_id` is already delivered to Stop hooks

`retry-loop-bound.sh` reads `payload.get("session_id")` from its own
stdin payload without any special wiring — this is the standard Claude
Code hook payload field, present on `Stop` events the same as on
`PreToolUse`/`PostToolUse`. `decision-queue-stopgate.sh` already reads
`stdin_payload` (parsed from `STOPGATE_STDIN_JSON`) for
`last_assistant_message`; `session_id` is available on the same object
with no new plumbing.

## Test harness gap

`on-the-record/hooks/test_decision_queue_stopgate.py`'s `_run()` helper
only sends `{"last_assistant_message": ...}` as stdin — no `session_id`.
Adding the bound requires the helper to accept and forward a
`session_id`, and to point `OTR`-style state at a temp dir per test (the
same isolation `retry-loop-bound`'s own tests use), or two test
invocations in the same test process would collide on a stray real
`$TMPDIR/otr-*-bound` state file across test runs.

## Alternatives considered while surveying

- **In-process counter (no state file):** rejected — each Stop hook
  invocation is a fresh `bash`/`python3` process (confirmed: the file
  has no daemon, no long-lived state); an in-memory counter cannot
  survive across invocations at all, so it is not actually an
  alternative, just a description of the current (broken) behavior.
- **Reuse `retry-loop-bound.sh`'s own state file/dir instead of a new
  one:** rejected — its signature is `(tool_name, target)` keyed off
  `PreToolUse` tool_input shape, which does not exist on a `Stop`
  payload; the state file also lives per-session already, but mixing
  key spaces from two different hooks in one file risks a collision if
  either hook's signature format ever changes independently. A
  sibling state dir following the same pattern (`os.replace`-atomic,
  session-keyed, `OTR_*_STATE_DIR` env override) keeps the two hooks
  decoupled while reusing the proven shape.
