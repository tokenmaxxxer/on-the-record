---
status: proposed
files:
  - docs/issue-927/reports/defect-verification.md
---

# Proposal — issue #927 defect-verification, step 1

## Intent

Verify, by direct reproduction against current `spawn.py`, the root
cause the issue names: the auto-armed detached `--follow` watcher
dies on stall/wall-clock (not session-end, not crash) with no
self-heal, and its printed re-arm instruction is orphaned because
auto-arm's stdout/stderr go to a file nothing reads for content. No
fix — that is issue-927 step 2 (implementation), gated on this
record.

## Constraints

- No coding/qa/review record exists for issue-927; this survey
  reproduces the issue's own diagnosis directly against `spawn.py`,
  citing file:line and command output for every claim, rather than
  re-litigating a prior role's verdict that does not exist.
- No fix, no test additions — those belong to step 2.
- Cite `gh issue view 927` as canonical evidence for the reported
  symptom; do not re-derive the observed production incident (workers
  dying mid-session, PRs orphaned) — pin only what is reproducible by
  reading/grepping the current tree.

## What will be done

Write
docs/issue-927/reports/defect-verification/current-state.md (already
committed alongside this proposal, phase-1 survey home), pinning:

1. All three non-session-end `_watch` exit paths (wall-clock cap at
   spawn.py:3494-3497, crash/pid-loss at spawn.py:3548-3550, follow-stall
   at spawn.py:3553-3556) are plain `return`s inside the `while True:`
   loop with no re-arm loop, and `_watch`/the `watch` subcommand's
   argument parser carry no flag distinguishing an auto-armed call from
   an interactive one.
2. Auto-arm (spawn.py:5085-5093) spawns the identical interactive
   `watch --follow` argv, so the three return paths execute the same
   way regardless of which caller armed the watcher.
3. `watcher_log` (spawn.py:5085, receiving auto-arm's stdout/stderr) has
   exactly one other reference in the file (spawn.py:2115-2122), which
   reads only its mtime for a staleness signal — never its text — so
   the "재무장하라" messages are orphaned as the issue claims.
4. The crash path emits a stderr line and a process exit code, but no
   durable event write, so an "ended without session-end" fact does
   not reach any log a downstream orchestrator could read after the
   detached process exits.
5. No test in `tests/test_spawn.py` (or elsewhere in `tests/`) drives
   the cumulative `stall_limit_s` boundary, observes a real auto-arm
   subprocess surviving it, or asserts a subsequent real `session-end`
   delivery — the issue's acceptance-gate live-fire test is genuinely
   absent.

On phase-2 approval, docs/issue-927/reports/defect-verification.md
(the role's own contract-mandated record — findings, severity,
`loop_state`) is written per `verify:finding-record` /
`verify:severity-classification`, restating this survey's confirmed
mechanism as a formal finding addressed to `coding`/`implementation`,
with severity assigned by the deterministic band lookup.

## Out of scope

- Any change to `spawn.py` (the `--self-heal` mode split, the
  self-heal loop itself, or the crash-path event write) — issue-927
  step 2, implementation role.
- Designing or writing the live-fire regression test the issue's
  Acceptance section requires — step 2's job, not this survey's.
- Re-running the actual production incident the user reports (3
  watcher deaths in one day, at least one orphaned PR) — this survey
  reproduces the code-level mechanism, not that specific historical
  session.

## How you'll know it worked

docs/issue-927/reports/defect-verification/current-state.md pins the
exact line ranges of all three lethal return paths, the auto-arm
call site, the single (mtime-only) reader of `watcher_log`, the
absent crash-path event write, and the absent live-fire test — each
with a file:line citation or code-fenced command output — confirming
the issue's diagnosis holds against the current codebase before any
fix is designed.

## Scout

Skip: investigative reproduction/pinning task with no product-facing
design decision open — the issue asks for its own root-cause
diagnosis to be verified against current code, not for a design
direction to be chosen among external products; there is no external
field to scout.

## What did not work

The first current-state-survey draft tripped `record-claim-guard.sh`'s
gates on its own text: a bare "line 5085/5087" count reference (issue
#333's bare-count-claim check) and several status/defect-claim
sentences whose nearest `canonical:` tag sat more than 3 lines above
them (issue #793's canonical-citation check). Each was rephrased —
either merged into an adjacent `canonical:`-tagged sentence or given
its own citation — with no claim altered and no gate bypassed.
