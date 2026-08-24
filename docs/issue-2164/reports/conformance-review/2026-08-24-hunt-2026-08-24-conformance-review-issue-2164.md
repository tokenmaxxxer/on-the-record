# hunt record — proposal docs/issue-2164/proposals/2026-08-24-conformance-review-issue-2164.md

proposal: docs/issue-2164/proposals/2026-08-24-conformance-review-issue-2164.md

## after-proposal dispatch — attempted, could not complete

Tier: size:docs-only (every touched path under `docs/`), cap 60s, one
stance (stance 0, `.warrant-hunt.count` absent so index 0 mod 5): assume
the gate just touched is bypassable — find the bypass. Intended target:
whether this session's `pretooluse-dispatcher.sh` approval-gate hook's
crash-and-deny behavior (a `gh --json state_reason` field the installed
`gh` CLI doesn't recognize) is itself bypassable for a write that should
have been gated.

Three dispatch attempts this session, each error text encountered live:

canonical: attempt 1's tool-call result, quoted verbatim on the next line
1. `subagent_type: warrant-hunter` — "Agent type 'warrant-hunter' not
   found" (the correct name in this environment is
   `warrant:warrant-hunter`, namespaced).

canonical: attempt 2's tool-call result, quoted verbatim on the next line
2. `subagent_type: warrant:warrant-hunter` — `hunt-guard.sh` returned "a
   hunter has been running for 7s; one at a time."

canonical: attempt 3's tool-call result, quoted verbatim on the next line
3. Same, after a wait — `hunt-guard.sh` returned "...running for 40s..."
   then "...running for 60s..." on a third retry, past this tier's own
   60s cap with no completion.

canonical: `ListAgents` output this session (no matching hunter process
listed) plus the fact that attempt 1 never returned a `task_id` — no
independent hunter process is visible, and `TaskStop` has nothing valid
to target. This reads as a stale lock left by attempt 1's error, not a
real hunter still working: `hunt-guard.sh`'s lock-acquire most likely
runs before the `subagent_type` name is validated, so an invalid-name
error still left the lock held with nothing to release it.

Given contract v3 s22 (headless/single-shot: never end a turn having
delegated work not consumed within the same turn) outranks the warrant
directive's hunter-dispatch mandate, and repeated dispatch was not
converging, this session stopped retrying rather than loop indefinitely.
No hunter finding was produced for this transition. This gap is named
in the phase-1 proposal's Constraints section rather than left silent.
