---
code_under_review:
  - gates/patrol_promote.py
  - gates/test_patrol_promote.py
type: feature
breaking: false
# canonical: acceptance: python3 -m pytest gates/test_patrol_promote.py -q — result: UNMEASURED-with-reason: no acceptance-commands.md row on record for this target
verdict: pass
loop_state: landed
---

## Summary of work

Built C2 (checkbox tick -> real per-finding issue promotion) per issue
#1589, on top of landed #1591 (contract), #1592 (C1 board), #1593
(judge transport). New module gates/patrol_promote.py: `detect_ticks`
(transition-only tick detection from a stored prior board body vs the
freshly-fetched one), `build_finding_issue_body` (structured body:
fingerprint, rule/baseline ID, file:line@SHA, severity, evidence,
proposed direction, anti-loop marker), `find_existing_promotion`
(fingerprint search before create — idempotence), `rate_cap_ok` (2/hr,
10 open, independent checks per role), `move_ticked_line` (board line
moves to Approved / In Progress on promotion, or stays Pending+ticked
with a "queued: rate cap" suffix on deferral — never dropped), and
`run_patrol_promote` (the imperative shell: ETag-conditional board
read via patrol_board.find_board_issue, one board edit per run,
restart-durable state under .git/patrol-promote/). See
docs/issue-1589/proposals/2026-08-15-patrol-board-c2-promotion.md for
the frozen write set and design rationale (chosen: stored-prior-body
diff over marker-only re-derivation).

## Why

issue #1589 is the final stage of the patrol program: without it, a
human ticking a board checkbox has no effect — findings stay inert.

## Upstream / basis

docs/issue-1589/proposals/2026-08-15-patrol-board-c2-promotion.md

## What did not work

None — no discarded approach during this build; the design chosen in
the proposal (stored prior-body diff) matched the implementation
without rework.

## Test-tier gap

canonical: this session's own `ls .on-the-record/test-tiers.json` shell
call run this turn — no such file exists in this repo. Per the
test-tier directive, this is recorded rather than silently absorbed.
Ran the targeted suite directly instead of a full-repo run.

acceptance: python3 -m pytest gates/test_patrol_promote.py -q — result: UNMEASURED-with-reason: no acceptance-commands.md row on record for this target
```
$ python3 -m pytest gates/test_patrol_promote.py -q
14 passed in 0.84s
```

acceptance: python3 -m pytest gates/test_patrol_board.py gates/test_patrol_trigger.py gates/test_patrol_queue.py -q — result: UNMEASURED-with-reason: no acceptance-commands.md row on record for this target
```
$ python3 -m pytest gates/test_patrol_board.py gates/test_patrol_trigger.py gates/test_patrol_queue.py -q
20 passed in 0.85s
```

## Doc-placement ladder

- No env var / config key / new dependency / migration / setup step
  introduced -> no handbook entry needed.
- No library-or-alternative choice beyond the tick-detection design
  already recorded in docs/issue-1589/proposals/2026-08-15-patrol-board-c2-promotion.md's
  Rationale -> no separate docs/issue-1589/decisions/ entry.
- No benchmark/investigation numbers produced -> no docs/issue-1589/reports/
  entry beyond this record itself.

## Open findings

None.

## Next steps

None — record is terminal (`landed`).

## Resolution path

N/A — no open finding.
