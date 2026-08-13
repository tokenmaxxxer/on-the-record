---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - gates/test_poll_heartbeat_delta.py
  - docs/issue-1117/decisions/priorities.md
type: feature
breaking: false
# canonical: python3 gates/test_poll_heartbeat_delta.py and python3 on-the-record/monitors/test_poll_heartbeat.py, executed live this turn (see Verification run below)
verdict: pass
loop_state: landed
---

# issue-1117 phase-2: poll-heartbeat delta-suppression — implementation record

## What was done

Implemented the approved proposal
(docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md), landed
in commit d3db195:

- `on-the-record/monitors/poll-heartbeat.sh`'s due-tick branch now builds
  the exact text the tick would print (`report` when non-empty, else the
  existing rc-embedding fallback line), hashes that combined text with
  `sha256sum`, and compares it against a hash persisted in a plain
  sibling file (`${CHECKOUT}/runs/poll_heartbeat_last_hash`) next to the
  poll TTL stamp (`runs/poll_state.json`). Unchanged hash → no
  printf/echo for that tick (poll-watchdog.log append is unaffected).
  Changed or absent hash → prints as before and updates the state file.
  Not-due, poll-due-crash, and the `ORCHESTRATE_OFF` kill switch are
  untouched — the hash logic only wraps the due-tick captured-report
  branch.
- Added `gates/test_poll_heartbeat_delta.py`, driving
  `on-the-record/monitors/poll-heartbeat.sh` via
  `POLL_HEARTBEAT_MAX_TICKS`/`POLL_HEARTBEAT_SLEEP_SECONDS`, covering:
  identical-tick suppression, changed-tick emission,
  change-after-suppression emission, and fresh-state first-tick
  emission (the issue's four named Acceptance cases).
- Recorded the operator's priority ordering (watch-coverage inviolable
  #90 > delta-suppression noise reduction > `ORCHESTRATE_OFF=1` last
  resort) as a structured entry — see Rationale for deviations below for
  its actual landed path.

## Why

Suppress Monitor-surfaced stdout for a due tick whose captured watchdog
report is byte-identical to the previously emitted tick, eliminating the
"대기중입니다" waiting-turn interject loop and Monitor noise reported by
the operator on 2026-08-13, while any changed output must still emit
(#90 watch-coverage inviolable).

## Upstream basis

docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md (approved
via issue comment "APPROVE issue-1117/implementation").

## Rationale for deviations

canonical: PreToolUse:Write hook refusal received in this session while attempting to write the literal path the proposal named — the hook's own stderr, quoted verbatim below.

The approved proposal's write set named a path under a "product" prefix
(not reachable from this working tree — never created) for the
structured priority-ordering entry. That path is refused at write time
by `board-gate.sh` (contract v3 s10): the prefix is neither the docs
top-level README, one of the six standing buckets (`_assets, decisions,
handbooks, proposals, reports, specs`), nor a per-issue tree
(`docs/issue-<n>/`). Actual refusal text received:

```
board-gate: docs/product/priorities.md is neither docs/README.md, one of
the six standing buckets (_assets, decisions, handbooks, proposals,
reports, specs), nor an issue tree (docs/issue-<n>/). (contract v3 s10)
```

The proposal's own layout constraint (mirroring contract v3 s10) was
never actually satisfiable at the literal path the issue named — this
surfaced only at write time, not during proposal drafting. Landed the
same structured content instead at `docs/issue-1117/decisions/priorities.md`
(committed in d3db195), using the `decisions/` standing bucket under this
issue's own tree, the closest fit for a durable priority-ordering
record. The content and three-tier structure are unchanged from what the
proposal specified; only the file's location moved to a layout-legal
path.

## What did not work

- Attempted to write the proposal-specified "product" prefix path (and
  `mkdir -p` of that directory); both refused by `board-gate.sh`'s
  layout check (contract v3 s10; refusal text quoted above). Replaced
  with `docs/issue-1117/decisions/priorities.md` (see Rationale for
  deviations above).

## Verification run

canonical: python3 gates/test_poll_heartbeat_delta.py and python3 on-the-record/monitors/test_poll_heartbeat.py, executed live in this session against the committed code at d3db195; combined pasted output below.

```
$ python3 gates/test_poll_heartbeat_delta.py
ok  t_change_after_suppression_emits
ok  t_changed_tick_emits
ok  t_fresh_state_first_tick_always_emits
ok  t_identical_second_tick_suppressed

4/4 passed

$ python3 on-the-record/monitors/test_poll_heartbeat.py
ok  t_heartbeat_arms_watchdog_when_due
ok  t_heartbeat_respects_kill_switch
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller

5/5 passed
```

canonical: git show d3db195 -- on-the-record/monitors/poll-heartbeat.sh — the diff hunk in the committed change touches only the due-tick captured-report branch; the not-due, poll-due-crash, and `ORCHESTRATE_OFF` branches carry no diff hunks.

## Open findings

None.

## Doc placement

- [x] `docs/issue-1117/decisions/priorities.md` — operator priority
  ordering, structured entry (moved from the proposal's stated
  product-prefix path; see Rationale for deviations).
