# Survey — issue #1021

Scout skip condition: pure bugfix. The issue names the exact fix
direction (honor `stop_hook_active`; block at most once per queue
content snapshot; advisory tier unchanged) against one existing file,
`on-the-record/hooks/decision-queue-stopgate.sh`, with acceptance cases
already named against the existing test file
`on-the-record/hooks/test_decision_queue_stopgate.py`. No product-facing
or design decision is open — this scouts nothing and the sweep protocol
is skipped per the scout-directive's mandatory skip record.

## Current state

canonical: on-the-record/hooks/decision-queue-stopgate.sh (read in full
this session)

`on-the-record/hooks/decision-queue-stopgate.sh` (single file, bash
wrapper around a heredoc Python `CHECK` block) already implements:

- role/orchestrate-off/checkout-resolve early exits.
- a `flows --json` fetch for `decision_queue`.
- a waiting-declaration turn-occupancy branch (issue #600/#692) with its
  own one-shot-per-run latch, persisted via
  `OTR_DECISION_QUEUE_STOPGATE_STATE_DIR` + `_state_path()` /
  `_load_blocked()` / `_save_blocked()`, keyed on `session_id`, storing
  `{"waiting_declaration_blocked": bool}` at
  `<state_dir>/<safe_session_id>.json`, atomic write via `.tmp` +
  `os.replace`, fail-open on any `OSError`/`ValueError`.
- the age-tier block/advisory logic this issue targets: an item with
  `age_hours >= 4` goes into a list that always triggers
  `decision: "block"` on every Stop, with no per-run memory — this is
  the reported unbounded loop. An item with `age_hours` between 1 and 4
  goes into a separate list that emits a non-blocking
  `hookSpecificOutput.additionalContext` advisory, already correct and
  explicitly out of scope per the issue ("Advisory tier unchanged").

derived: `grep -n "STOPGATE_STDIN_JSON\|stdin_payload.get" on-the-record/hooks/decision-queue-stopgate.sh`
```
$ grep -n "STOPGATE_STDIN_JSON\|stdin_payload.get" on-the-record/hooks/decision-queue-stopgate.sh
STOPGATE_STDIN_JSON="$payload" STOPGATE_STATE_DIR="$STOPGATE_STATE_DIR" python3 -c "$CHECK"
last_msg = stdin_payload.get("last_assistant_message") or ""
session_id = stdin_payload.get("session_id")
```

Two gaps against the issue's fix direction:

1. `stdin_payload` is read only for `last_assistant_message` and
   `session_id` (see derived grep above) — the official Stop-hook
   payload's `stop_hook_active` boolean is never read by this script.
2. The 4h-and-older block branch has no persisted "already blocked for
   this queue snapshot" state, unlike the waiting-declaration branch a
   few lines above it in the same file, which already has that shape
   (latch keyed on session, reset condition, atomic save/load) — the
   pattern to mirror, not invent fresh.

## Write set implied

- `on-the-record/hooks/decision-queue-stopgate.sh` — read
  `stop_hook_active` from `stdin_payload`; when true, never emit
  `decision: "block"` from the 4h-and-older branch (degrade to the same
  `additionalContext` advisory shape the 1h-4h branch already uses, so
  the operator still sees the aged-item names); add a persisted
  per-session "last-blocked queue snapshot" latch for the 4h-and-older
  branch, keyed the same way the existing waiting-declaration latch is
  keyed (`_state_path()`/session_id), storing a stable identity of the
  aged items (issue/pr pairs) rather than their age_hours values — age
  ticks every turn even when the queue's contents have not changed, and
  the issue's second acceptance case is exactly "same queue snapshot
  twice -> second Stop not blocked".
- `on-the-record/hooks/test_decision_queue_stopgate.py` — the cases the
  issue's Acceptance section names verbatim: `stop_hook_active=true` ->
  no block; same queue snapshot twice -> second Stop not blocked; queue
  content change -> may block once more.
- a phase-2 implementation record, written at the start of phase 2 at
  this issue's standard report path.

No new dependency, no new env var beyond a state-dir override mirroring
the existing `OTR_DECISION_QUEUE_STOPGATE_STATE_DIR` (already declared,
reused, not new).
