# Scout brief — issue #600 (close-the-turn-on-decision-wait)

Mode: internal sweep (non-product deliverable — the "best of own kind" is
this repo's existing Stop/PreToolUse enforcement hooks, not an external
market). Scouted in place of a web sweep because the artifact under design
*is* a hook in `on-the-record/hooks/`; the strongest comparables already
live there. Stages used: 1 (sweep only; no deepening needed — the four
hits below converge on one shape, so judge point 1 already saturated).

## Must-bes (what every comparable enforcement hook here does)
- Fails to a stated side (open or closed), explicitly commented, never
  implicit (`decision-queue-stopgate.sh`, `retry-loop-bound.sh`,
  `report-framing-check.sh`).
- Kill switch via `ORCHESTRATE_OFF` and `CLAUDE_ROLE` gating, checked
  first, before any payload parsing.
- Reads the live reply/state fresh each turn — no persisted judgment
  carried across turns for the semantic check itself (only
  `retry-loop-bound.sh` persists state, and only a *counter*, never a
  verdict).
- Ships as a single self-contained `python3 -c` block inside the `.sh`,
  zero external imports — matches the zero-install constraint already
  binding this issue.

## Performance axes (where they compete / how they differ)
1. **Detection surface**: state-only (`decision-queue-stopgate.sh` reads
   `spawn.py flows --json`, never looks at the reply text) vs. text-only
   (`report-framing-check.sh` regexes `last_assistant_message`, never
   looks at external state) vs. counted-repetition (`retry-loop-bound.sh`
   keys on a `(tool, target)` signature, blind to both state and text).
2. **Gaming resistance**: `retry-loop-bound.sh` is hardest to game — it
   counts actual repeated tool calls, a physical fact, not a phrasing
   choice. `report-framing-check.sh` is easiest to game — reflows a
   sentence to add the four framing words and passes without doing the
   thing. Pure phrasing-blocklist checks are the weakest axis on this
   spectrum.
3. **Escalation shape**: two-tier soft→hard (`decision-queue-stopgate.sh`:
   `additionalContext` at 1h, `block` at 4h) vs. single-tier hard-after-N
   (`retry-loop-bound.sh`: `allow`+context at K, `deny` at 2K) vs.
   single-tier soft-only (`report-framing-check.sh`: never blocks, only
   nudges).

## Adopt / skip
- **Adopt**: `decision-queue-stopgate.sh`'s existing `decision_queue`
  read is *exactly* condition (a) of this issue's required check
  ("non-empty decision queue holding the turn") — extend that file
  rather than invent a second source of the same fact.
- **Adopt**: `retry-loop-bound.sh`'s two-tier allow-with-context /
  deny-outright shape as the gaming-resistance model — condition (b)
  ("waiting-declaration reply with no closed turn") is a text-phrasing
  signal, structurally as gameable as `report-framing-check.sh`'s, so it
  should never gate alone; it must always be conjoined with (a)'s
  state fact, which is not gameable by rephrasing.
- **Skip**: a brand-new persisted-state hook. No comparable in this repo
  invents fresh state to catch a one-turn pattern; the fact needed
  (decision_queue non-empty) is already computed and read fresh by
  `spawn.py flows --json` every turn.

## Gap line
The current state (survey below) already has condition (a) — a live,
non-empty `decision_queue` read, every Stop turn, via
`decision-queue-stopgate.sh`. It has **no** condition (b) — no read of
`last_assistant_message` for a waiting-declaration/no-turn-close pattern,
and no run.md sentence naming this exact failure mode. Both are the gap
this issue closes.

Sources (internal, no web fetch — see rationale above):
- on-the-record/hooks/decision-queue-stopgate.sh
- on-the-record/hooks/retry-loop-bound.sh
- on-the-record/hooks/report-framing-check.sh
- on-the-record/hooks/directive.sh (lines ~60-92, bounded-wait pattern)
- on-the-record/commands/run.md, "턴 예산 규칙 (#535)" section
