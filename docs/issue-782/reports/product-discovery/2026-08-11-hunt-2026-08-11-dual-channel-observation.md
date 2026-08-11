---
proposal: docs/issue-782/proposals/2026-08-11-dual-channel-observation.md
---

# Hunt record — dual-channel-observation

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — the completion-detection dedup key `(issue, role, "session-end")` has no session/attempt identifier, so a genuinely distinct completion from a respawned session for the same issue+role collides with a prior session-end stamp inside the 15-min TTL and is wrongly suppressed (false-negative, not double-action, but the ledger key "colliding across genuinely different events" as the stance asks).
Kind: design-error
Seed: docs/specs/dual-channel-observation.md section 2 ("Dedup key: (issue, role, pr_number) if a PR exists, else (issue, role, "session-end")"); same key repeated in docs/issue-782/proposals/2026-08-11-dual-channel-observation.md lines 56-57.
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: 507
started_at: 2026-08-11T16:38:20+09:00
ended_at: 2026-08-11T16:42:00+09:00

### Reproduce (paper scenario, per instructions — design not yet code)

1. t=0:00 — Role R (issue N) session #1 ends without opening a PR (e.g.
   hit max-turns with no work to show). Completion-detection lane fires:
   dedup key = (N, R, "session-end"); ledger stamps it at t=0:00, reports
   "session ended, no PR" to the orchestrator.
2. t=0:01 — Health-repair or orchestrator respawns role R for the same
   issue N (a fresh session #2, distinct process/session id, per the
   design's own "crash→respawn" health-repair mapping in section 3).
3. t=0:10 (still inside the 15-min TTL from step 1) — Session #2
   legitimately finishes: this time it *did* open real work and reaches
   its own, entirely distinct session-end (or even opens no PR again but
   for a different, unrelated reason). Its dedup key is computed the
   same way: (N, R, "session-end") — identical to step 1's key, because
   the key has no session/attempt/pid component, only issue+role.
4. Per spec step 2 of the ledger algorithm ("If the ledger has that key
   stamped within a bounded TTL... skip: the other channel already
   reported/acted on this"), session #2's genuine, distinct completion
   is treated as a duplicate of session #1's and is silently dropped —
   even though it is a different session with a different outcome.

### Observed (as designed on paper)

The spec's own worked examples in section 2 only walk through the
same-PR case (watch vs. poll both observing the *same* PR) and never
consider two different sessions of the same role reusing the
"session-end" sentinel. Nothing in the key definition or the TTL logic
distinguishes session #1's end from session #2's end; both hash to
(N, R, "session-end").

### Expected

The dedup key for the completion-detection lane should include a
per-session/per-attempt discriminator (e.g. session id, spawn timestamp,
or a monotonic respawn counter) when no PR exists, so that two distinct
sessions of the same role — which the design's own health-repair lane
explicitly anticipates via `respawn` — don't collide on the sentinel key
and have a real completion silently suppressed.

## before-landing

docs-only, no before-landing dispatch — every touched path in this transition's diff is under docs/.
