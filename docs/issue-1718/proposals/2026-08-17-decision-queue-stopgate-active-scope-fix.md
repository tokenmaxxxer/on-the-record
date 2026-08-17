---
status: proposed
files:
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/test_decision_queue_stopgate.py
  - docs/issue-1718/reports/implementation.md
---

## Request

`on-the-record/hooks/decision-queue-stopgate.sh` still emits Stop
`additionalContext`/`decision: "block"` on turns the harness itself
already forced (`stop_hook_active: true`) — issue #1021 only wired that
field into two of the hook's branches (the waiting-declaration block and
the tier2 age >= 4h block), not the tier1 advisory branch or tier2's own
advisory-degrade path. The harness treats any Stop `additionalContext`
as inject-and-resume, so each of those emissions re-triggers another
Stop, looping until the harness's consecutive-block cap ends the turn
(observed: 9 forced turns per reply). Separately, `decision_queue` items
surface regardless of whether *this* checkout ever spawned the work
behind them — issue #1712's items were spawned from a different
operator's checkout, so this checkout nags about a decision it never
owned. Fix both directly in the hook: a guard that makes any
`stop_hook_active` turn emit nothing at all, and a filter that drops
queue items this checkout has no local spawn record for.

## Constraints

- Scout skip: pure bugfix, per
  `docs/issue-1718/reports/implementation/survey.md`.
- `stop_hook_active: true` must produce zero stdout from this hook on
  every branch — waiting-declaration, tier1, tier2 — not just suppress
  `decision: "block"` while still emitting advisory
  `additionalContext`, since the issue's own diagnosis is that the
  advisory emissions are exactly what loops the turn.
- When `stop_hook_active` is false, the hook still emits at most once
  per user turn (unchanged from current behavior): tier1 advisory,
  tier2 block, or the waiting-declaration block.
- The checkout-scope filter must use data the hook already has access
  to — `flows --json`'s existing `sessions` (active roster) and
  `ledger` (runs ledger) arrays, per the survey — no new `spawn.py` or
  `gates/flows.py` surface, no new subprocess call.
- Empty queue, role sessions (`CLAUDE_ROLE`/role-bind snapshot), and
  `ORCHESTRATE_OFF=1` behave exactly as before (issue's own "empty
  state" acceptance line) — neither change touches those early exits.
- No new dependency, no new required env var.
- `on-the-record/hooks/test_decision_queue_stopgate.py` gains cases for
  both acceptance checks the issue names.

## Rationale

Considered filtering `decision_queue` upstream, in `gates/flows.py`'s
`_own_item()` (gates/flows.py:358-367), instead of in the hook. Rejected:
`_own_item()`'s "can't observe -> can't deny ownership -> show it"
default is deliberate for issue #1035's purpose — same-checkout,
concurrent-session scoping for the board/`flows` CLI output, a shared
read-only data contract (`flows-schema.md`) other consumers (the
repo-status-board, `spawn.py flows`'s human-readable output) also read.
Narrowing that default would change what those other consumers see, for
a bug the issue scopes explicitly to
`on-the-record/hooks/decision-queue-stopgate.sh`. The hook already
receives everything it needs (`sessions`, `ledger`) on the same payload,
so filtering there is strictly smaller and matches "keep the fix
minimal — one guard plus one filter — no new abstractions."

Considered keeping tier2's existing `stop_hook_active or <latch match>`
advisory-degrade (on-the-record/hooks/decision-queue-stopgate.sh:265)
as-is and only adding the missing check to the tier1 branch, reasoning
that an advisory-only payload is lower-risk than a block. Rejected: the
issue's acceptance text is explicit — "the hook emits nothing at all ...
regardless of queue age" — and the transcript evidence it cites is
exactly the tier2 advisory-degrade path looping via
`additionalContext`, not a `decision: "block"` path. A per-branch patch
would leave the reported failure mode live in the one branch most
implicated by the evidence.

## What will be done

1. In `decision-queue-stopgate.sh`'s `CHECK` Python body, immediately
   after `stop_hook_active = bool(stdin_payload.get("stop_hook_active"))`
   (on-the-record/hooks/decision-queue-stopgate.sh:72): add
   `if stop_hook_active: sys.exit(0)`. Placed before the role-identity
   resolution and before the `flows`/`decision_queue` parsing, so every
   later branch — waiting-declaration, tier1, tier2 — is unreachable on
   such a turn; nothing is written to stdout.
2. Right after the existing `decision_queue` empty check
   (on-the-record/hooks/decision-queue-stopgate.sh:104-106): build a set
   of issue numbers from `flows.get("sessions")` and `flows.get("ledger")`
   (each entry's `"issue"` field), filter `queue` down to items whose
   `"issue"` is in that set, and re-check emptiness (`sys.exit(0)` if the
   filtered queue is empty). Every later reference to `queue` (the
   waiting-declaration item list, the tier1/tier2 partition loop) then
   operates on the filtered list without further changes.
3. Update `on-the-record/hooks/test_decision_queue_stopgate.py`:
   - extend the shared `_run()` test helper with a
     `spawn_record_issues` parameter that injects a matching `sessions`
     entry into the fake `flows --json` payload for every issue already
     present in the test's `decision_queue` by default (so the existing
     tier/latch/role/waiting-declaration tests, which are not about
     this filter, keep passing unchanged) — and lets a test pass `[]` or
     an explicit subset to exercise the filter itself.
   - replace `t_stop_hook_active_never_blocks_tier2` (asserts the old
     advisory-degrade shape, now gone) with a case asserting empty
     stdout for `stop_hook_active=True` against a tier2 item.
   - add cases: `stop_hook_active=True` emits nothing across tier1,
     tier2, and the waiting-declaration pattern; `stop_hook_active=True`
     emits nothing even when a same-content tier2 latch was primed by a
     prior non-active turn; a queue item with no matching `sessions` or
     `ledger` entry is silently skipped (empty stdout); a queue item
     whose only local record is in `ledger` (not `sessions`) still
     surfaces; a mixed queue surfaces only the item with a local record.
4. Write `docs/issue-1718/reports/implementation.md` at the start of
   phase 2, per the record-shape directive.

## Out of scope

- Any change to `gates/flows.py`, `spawn.py`, or the `flows --json`
  schema — the filter reads existing fields only.
- Any change to the 1h/4h age thresholds, the waiting-declaration
  pattern/latch semantics, or the tier2 content-latch mechanism beyond
  making them all unreachable on a `stop_hook_active` turn.
- Repo-scoping or cross-repo issue-number collisions in `sessions`
  (which is not currently repo-filtered) — out of scope for this
  checkout-scope fix; the issue's own acceptance text frames the gap as
  checkout-level, not repo-level.

## How you'll know it worked

- `python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py`
  passes, including the new cases for both acceptance checks.
- A Stop payload with `stop_hook_active: true` and any non-empty
  `decision_queue` (any age, any branch) produces empty stdout and exit
  code 0.
- A `decision_queue` item whose issue has no entry in `flows`'s
  `sessions` or `ledger` never appears in this hook's output, silently.
