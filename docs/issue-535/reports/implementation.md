---
code_under_review: pending
loop_state: landed
---

# Implementation record — issue #535

## Summary of work

Applying the approved phase-1 proposal
(docs/issue-535/proposals/2026-08-09-turn-budget-rules.md): add
turn-budget rules to on-the-record/commands/run.md and
on-the-record/hooks/directive.sh per the proposal's "What will be
done" section.

## Why

Long foreground tool-call chains (merges, verification loops) block the
harness's queued user input until the turn ends. The orchestration
contract currently encourages this shape; this change adds explicit
turn-budget rules so operations expected to exceed ~30s go to
background and turns close as soon as remaining work is armed.

## Upstream / basis

Based on: docs/issue-535/proposals/2026-08-09-turn-budget-rules.md

## What did not work

None.

## Doc placement

- on-the-record/commands/run.md — new turn-budget-rules section
  (contract text, per doctrine ladder: contract/handbook surface).
- on-the-record/hooks/directive.sh — compressed reminder paragraph in
  the injected directive block.

## Open findings

None.

## Verification

- `grep -n "턴 예산 규칙\|TURN-BUDGET RULES" on-the-record/commands/run.md
  on-the-record/hooks/directive.sh` — all three rules present in both
  files (run.md:416 new section + 551 watchdog cross-reference;
  directive.sh:113 compressed paragraph).
- Grep sweep of both changed files for remaining foreground-blocking
  instructions beyond the existing bounded watch call: none found — the
  only bounded-wait pattern left is the pre-existing `spawn.py watch
  --stall-timeout` (directive.sh 74-90), which the new rules generalize,
  not replace, per the proposal's constraint.
- `python3 -m pytest on-the-record/hooks/` — 62 passed, no regression.

## Resolution path

Not applicable — no open findings.
