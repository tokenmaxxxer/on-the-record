---
code_under_review:
  - scripts/skill_outcome_contrast.py
  - gates/test_skill_outcome_contrast.py
loop_state: landed
type: feature
breaking: false
verdict: pass
---

Subject: issue-1992

## What was done

Added `scripts/skill_outcome_contrast.py`: an outcome-contrast script that
groups session logs into two groups (reflected/not-reflected when a scope-A
reflection artifact -- `measure_skill_reflection.py` JSONL output -- is
supplied via `--reflection-artifact=`, else falling back to
invoked/not-invoked from `measure_skill_invocation.py`'s live invocation
labels) and contrasts three outcome proxies read directly from each
session's raw log text: `review_rounds` (git-push cycle count),
`gate_refusals` (PreToolUse `hook error` block count), and
`acceptance_failure_rate` (fraction of sessions with any acceptance/test
failure marker). Below `MIN_GROUP_N = 3` sessions in either group the report
says "underpowered" and emits no comparison numbers. Every report, powered
or not, carries an explicit correlation-only selection-bias caveat line
naming role/difficulty confounds and disclaiming causal claims. Added
`gates/test_skill_outcome_contrast.py`, six test functions covering: bias
caveat always present, underpowered guard, full-group table rendering,
raw-text metric extraction, reflection-label majority derivation,
invocation fallback when no artifact is given.
derived: `grep -c '^def test_' gates/test_skill_outcome_contrast.py` -> 6

## Why

Issue #1992 (scope B, run alongside scope A per the consult ordering)
requirement: a correlation-only outcome-contrast artifact over accumulated
session history, contrasting review-round counts / gate-refusal counts /
acceptance-failure rates between skill-reflected and non-reflected (or
invoked/not-invoked) sessions, with the bias caveat stated in the artifact
itself. validity-consult: docs/reports/consult-log.md 2026-08-22
requirements-engineering (S2 correlation-only, confounds named).

Reflection labels come from `measure_skill_reflection.py`'s judge panel,
which shells out to `spawn.py consult` per lens per skill per session --
too costly to invoke live across dozens of today's sessions inside one
build turn. The script accepts a pre-computed reflection artifact (JSONL
of `reflect_session()` output, scope A's own artifact) as its preferred
grouping input, and falls back to the cheap, purely local invocation labels
otherwise -- this keeps the acceptance's "run live" requirement satisfiable
without an unbounded LLM-judging fan-out hidden inside a single script
invocation.

## Upstream basis

- scripts/measure_skill_invocation.py (invocation labels, live-parsed)
- scripts/measure_skill_reflection.py (reflection artifact schema)

## Acceptance verification

checked: `python3 scripts/skill_outcome_contrast.py` over today's real
session logs under `~/.tokenmaxxxer/work/` — result: pass
canonical: python3 scripts/skill_outcome_contrast.py — executed live this
session (2026-08-22) against the 57 today-dated `*.session.20260822*.log`
files under `~/.tokenmaxxxer/work/` discovered by `today_logs()`; output:

```
# Skill outcome-contrast (invocation-based grouping)

| group | n | review_rounds mean | gate_refusals mean | acceptance_failure_rate |
|---|---|---|---|---|
| invoked | 3 | 2.67 | 4.00 | 1.00 |
| not-invoked | 54 | 3.04 | 11.09 | 1.00 |

CAVEAT (correlation-only): role and task-difficulty are uncontrolled confounds -- sessions were not randomly assigned to skill-invoked vs not-invoked (or reflected vs not-reflected). Any gap between groups may reflect who/what tends to invoke or reflect skills, not an effect of the skill itself. No causal claims.
```

The output shows the group table (n, per-group metric means) and the
explicit bias-caveat line, satisfying the acceptance check. The `invoked`
group happened to clear `MIN_GROUP_N=3` today so the underpowered path did
not fire live; the underpowered guard itself is covered by the committed
test suite (`gates/test_skill_outcome_contrast.py`, functions
`test_underpowered_below_min_n_emits_no_comparison_numbers` and
`test_bias_caveat_always_present_underpowered`).

acceptance: `python3 -m pytest -q gates/test_skill_outcome_contrast.py -o addopts=''` — result: pass
canonical: python3 -m pytest -q gates/test_skill_outcome_contrast.py -o
addopts='' — executed live this session (2026-08-22); output:

```
......                                                                   [100%]
6 passed in 0.07s
```

## What did not work

None.

## Open findings

None.
