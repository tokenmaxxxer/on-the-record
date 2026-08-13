# Product priority ordering: poll-heartbeat noise vs. watch coverage

## Poll-heartbeat Monitor noise vs. watch coverage (issue #1117)

Operator-stated ordering, highest priority first:

1. **Watch-coverage inviolable (#90)** — any due tick whose captured
   watchdog output differs from the last emitted tick MUST emit. No
   coverage regression, ever, for any noise-reduction reason.
2. **Delta-suppression noise reduction (#1117)** — an unchanged due tick
   suppresses its Monitor-surfaced stdout (log append is unaffected).
   This is the mechanism that may trade off against noise, never #1.
3. **Full off via `ORCHESTRATE_OFF=1` (last resort only)** — the kill
   switch that disables the heartbeat loop entirely; used only when 1
   and 2 together are insufficient.

Source: issue #1117 (2026-08-13 orchestrator session), Requirements
section — quoted verbatim as "watch-coverage inviolable (#90 — changed
output must always pass) > delta-suppression noise reduction > full off
via ORCHESTRATE_OFF=1 (last resort only)".

Proposal: docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md
