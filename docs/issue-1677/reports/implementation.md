---
code_under_review:
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/test_directive_content.py
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# Implementation record — issue #1677 phase 2

## What was done

canonical: on-the-record/hooks/directive.sh (this branch, working tree)

Added three obligation blocks to the co-injected orchestrate directive (`on-the-record/hooks/directive.sh`), mirroring the existing `#1024`/`#310`/`#1651`/`#1658` block style (heading naming the issue, prose describing the obligation, the gate module path):

1. `VERDICT-ASYMMETRY AT MERGE (issue #1669)` — before merging on a reviewer verdict, run `gates/verdict_gate.py` `classify(verdict, merge_gate_result, tests_pass)`: CHANGES always respawns; MERGE merges only on `ALLOW_MERGE`; every other case is HOLD (never merge on the LLM verdict alone); a correct MERGE blocked by a flaky deterministic gate surfaces as HOLD, not auto-reject.
2. `STALE-REVERT AT MERGE (issue #1664)` — the same pre-merge step also runs `gates/stale_revert_guard.py`, REFUSING a PR whose merge would drop content base HEAD gained after the PR's merge-base (automates the PR#1662/#1675 manual catch).
3. `ASSUMPTION-LEDGER INVENTED-CONFIRM AT INTAKE (issue #1665)` — before spawning a design-bearing issue, surface `gates/assumption_ledger.py` `invented_assumptions()` for human confirmation; an unconfirmed `invented:` item blocks the spawn; `assumptions-skip: mechanical` issues proceed unchanged.

Extended `on-the-record/hooks/test_directive_content.py` with one presence test per obligation (heading + gate module path + a key phrase each) plus widened the existing ordering test to also assert all three new blocks land after the `#1024` block and before the closing `Full procedure` line. No PreToolUse hook conversion — directive-driven only, per the issue's explicit scope note (hard-hook hardening is a later follow-up).

## Why

canonical: gh issue view 1677 (issue body, `## Problem`/`## What to build`)

The three judgment gate modules (`verdict_gate.py`, `stale_revert_guard.py`, `assumption_ledger.py`) landed module-only in prior issues (#1669/#1664/#1665) but were never invoked from the orchestrator's actual decision path — proven live twice (PR #1662, PR #1675 stale-reverts the orchestrator had to catch manually). Wiring them into `directive.sh`, the same enforcement layer `#1024`/`#310`/`#1651`/`#1658` already use, activates them without introducing a new enforcement mechanism.

## Upstream

canonical: gh issue view 1677 (issue body); gates/verdict_gate.py, gates/stale_revert_guard.py, gates/assumption_ledger.py (pre-existing modules from issues #1669/#1664/#1665)

- Basis: docs/issue-1677 (this issue); pre-existing `gates/verdict_gate.py` (#1669), `gates/stale_revert_guard.py` (#1664), `gates/assumption_ledger.py` (#1665) — none modified, only referenced by name from `directive.sh`.
- Mirrors: `on-the-record/hooks/directive.sh`'s existing `#1651`/`#1658` block shape; `on-the-record/hooks/test_directive_content.py`'s existing presence/ordering test shape.

## What did not work

None — the directive-block-plus-test approach mirrored the existing `#1651`/`#1658` pattern exactly and needed no rework.

## Acceptance verification

canonical: on-the-record/hooks/directive.sh, on-the-record/hooks/test_directive_content.py (this branch)

- check: directive.sh contains the three obligations, each naming its gate module; test asserts their presence alongside `#1024`/`#310`/`#1651` blocks — result: met.

```
$ python3 -m pytest on-the-record/hooks/test_directive_content.py -q
9 passed in 0.89s
```

canonical: gates/verdict_gate.py:49-61 (`classify()`, executed live below)
- check: live — MERGE-verdict PR failing verdict_gate is HELD, not merged — result: met.

```
$ python3 -c "
import sys; sys.path.insert(0,'gates'); import verdict_gate
print(verdict_gate.classify('MERGE', {'allowed': False, 'reasons': ['check failed']}, True))
print(verdict_gate.classify('MERGE', {'allowed': True, 'reasons': []}, False))
print(verdict_gate.classify('MERGE', {'allowed': True, 'reasons': []}, True))
"
HOLD
HOLD
ALLOW_MERGE
```

canonical: gates/stale_revert_guard.py:83-116 (`classify()`), executed live against a reconstructed git repo below
- check: live — a stale-revert PR (PR#1675 reconstruction: a branch deleting a just-landed module's content) is REFUSED — result: met. Reconstructed with a real git repo: `mergebase` tags the fork point, `basehead` adds a line simulating a just-landed module, `prbranch` forks from `mergebase` and independently edits the same region (dropping the landed line on merge).

```
$ python3 gates/stale_revert_guard.py check "$TMP" basehead mergebase prbranch
거절: stale revert 발견
  - f.py: 병합이 merge-base 이후 추가된 내용과 충돌함(오래된(stale) merge-base)
exit:1
```

canonical: gates/assumption_ledger.py:94-115 (`invented_assumptions()`, `check_issue_body()`, executed live below)
- check: live — a design-bearing issue with an unconfirmed `invented:` assumption is not spawned until confirmed — result: met.

```
$ python3 -c "
import sys; sys.path.insert(0,'gates'); import assumption_ledger as al
print(al.invented_assumptions('## Assumptions\n- invented: the API rate limit is 100 req/min\n'))
print(al.check_issue_body(0, 'assumptions-skip: mechanical\n'))
"
['the API rate limit is 100 req/min']
[]
```

- empty state: a clean MERGE-verdict PR passing all deterministic gates still merges byte-identical; a mechanical issue (`assumptions-skip: mechanical`) spawns unchanged — result: met (shown by the `ALLOW_MERGE` and empty-errors-list lines above; `directive.sh`'s existing #1024/#310/#1651/#1658 text and behavior are untouched — only new blocks were appended).

## Test-tier note (issue #1518)

derived: `.on-the-record/test-tiers.json`

This branch's diff matches `on-the-record/hooks/*.sh` and `on-the-record/hooks/test_*.py` in `trigger_change_classes`, so both tiers were run, not just `fast`:

```
$ python3 -m pytest -q -m "not slow"
2149 passed, 20 xfailed, 1 xpassed in 23.57s

$ python3 -m pytest -q -m slow
100 passed, 2 xfailed in 500.27s (0:08:20)
```

## Open findings

None.
