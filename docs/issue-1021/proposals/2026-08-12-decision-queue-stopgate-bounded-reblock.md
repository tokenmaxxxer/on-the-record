---
status: proposed
files:
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/test_decision_queue_stopgate.py
  - docs/issue-1021/reports/implementation.md
---

## Request

`decision-queue-stopgate.sh` blocks Stop on every turn once a
decision-queue item ages past 4h, even though an aged item is by
definition waiting on the operator and the session cannot resolve it —
observed live as dozens of consecutive blocked Stops each producing
only a short "in progress" reply, an unbounded token-burning loop. The
hook never reads the official Stop-hook payload's `stop_hook_active`
field (true when the current turn was already forced by a prior Stop
block), which exists precisely to prevent this class of loop. Fix:
honor `stop_hook_active` (never re-block when true — degrade to
advisory), and block at most once per queue-content snapshot (re-block
only when the queue's contents change, not merely because age ticked
up). The 1h-4h advisory tier is unchanged.

## Constraints

- Scout skip: pure bugfix, per `docs/issue-1021/reports/implementation/survey.md`.
- Advisory tier (`1 <= age_hours < 4`) behavior is unchanged — the issue
  states this explicitly.
- `stop_hook_active=true` must never produce `decision: "block"` from
  this hook, on any tier.
- The "block once per snapshot" latch must key off queue *contents*
  (which issue/PR items are 4h-or-older), not `age_hours`, since
  `age_hours` changes every turn even when the queue is otherwise
  identical.
- `on-the-record/hooks/test_decision_queue_stopgate.py` gains exactly
  the three cases the issue's Acceptance section names:
  `stop_hook_active=true` -> no block; same queue snapshot twice ->
  second Stop not blocked; queue content change -> may block once more.
- No new dependency, no new required env var.

## Rationale

Considered keying the "already blocked" latch on a hash of the *entire*
`decision_queue` payload (including `age_hours`) instead of just the
4h-or-older items' issue/PR identities. Rejected: `age_hours` is a
float that increases every single turn by construction, so any hash
including it would never repeat and the latch would never suppress a
re-block — this is the same bug restated, not a fix. Keying on the
identity of the items that are actually in the blocking tier (their
issue/PR pairs) is the only choice that satisfies the issue's stated
acceptance case "same queue snapshot twice -> second Stop not blocked".

Considered a purely stateless fix: dropping the persisted latch
entirely and relying only on `stop_hook_active` to prevent repeats
(since a blocked Stop forces exactly one more turn, and that next
turn's payload should carry `stop_hook_active=true`). Rejected: nothing
in this hook or its test harness proves Claude Code always sets
`stop_hook_active` on the immediately-following turn for every runtime
this hook executes under, and the issue's own acceptance list names a
distinct "same queue snapshot twice" case independent of
`stop_hook_active` — the two mechanisms are asked for as separate,
overlapping safeguards, not one standing in for the other. The existing
waiting-declaration branch a few lines above already proves the
persisted-latch pattern works and is cheap; reusing its shape (rather
than trusting `stop_hook_active` alone) also degrades gracefully if a
given host ever omits the field.

## What will be done

1. In `decision-queue-stopgate.sh`'s `CHECK` Python body: read
   `stop_hook_active = bool(stdin_payload.get("stop_hook_active"))`
   alongside the existing `last_msg`/`session_id` reads.
2. Add a second persisted latch, mirroring `_state_path()` /
   `_load_blocked()` / `_save_blocked()`'s shape but keyed under a
   distinct field name (e.g. `"tier2_last_blocked_ids"`) in the same
   per-session JSON file, storing the sorted list of
   `(issue, pr)` identities for items with `age_hours >= 4` at the time
   of the last block.
3. Replace the current unconditional "4h-and-older items always block"
   branch with: compute the current 4h-and-older items' identities;
   if `stop_hook_active` is true, or the identities match the persisted
   last-blocked set, skip the block and instead emit the same
   `additionalContext` advisory shape the 1h-4h branch already uses
   (naming the aged items) so the operator still sees them; otherwise
   emit `decision: "block"` as today and persist the new identity set.
4. Leave the 1h-4h advisory branch and the waiting-declaration branch
   untouched.
5. Add the three named test cases to
   `on-the-record/hooks/test_decision_queue_stopgate.py`, extending the
   existing `_run()` helper with a `stop_hook_active` parameter wired
   into the JSON payload the same way `last_assistant_message` already
   is.
6. Write `docs/issue-1021/reports/implementation.md` at the start of
   phase 2, per the record-shape directive.

## Out of scope

- Any change to the 1h-4h advisory tier's trigger condition or wording
  beyond reusing its existing output shape for the degraded case.
- Any change to the waiting-declaration branch (issues #600/#692) or its
  own separate latch.
- Changing how `flows --json`/`decision_queue` is computed upstream.

## How you'll know it worked

- `python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py`
  passes, including the three new cases named in the issue's Acceptance
  section.
- A Stop with `stop_hook_active=true` and a 4h+ item never returns
  `decision: "block"`.
- Two consecutive Stops against an unchanged 4h+ queue block only on the
  first; a Stop after the queue's aged-item identities change may block
  again.
