---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
  - scripts/measure_skill_invocation.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# issue-1960 phase-2 implementation record

Subject: issue-1960

## Summary of work

canonical: python3 -m pytest tests/test_spawn.py -k SkillInvocationNudge -q
3 passed

Delivered the phase-2 build approved via `APPROVE issue-1960/implementation`
(basis: docs/issue-1960/proposals/phase-b-skill-invocation-nudge.md, itself
built on the execution-observation role's baseline at
docs/issue-1960/reports/execution-observation/baseline-measurement.md).
Applied the proposal's single frozen change and re-measured, per the
proposal's planned steps:

1. Added one directive block to `spawn.py`'s `_spawn_one()` task-text
   assembly (the same injection point that already appends the
   `--skills` mount line and the skill-repository role-mapping line): when
   any skill is mounted for the session — via `--skills` (issue #1742/#1774)
   or via role-to-skill-repository mapping (issue #1955/#1758) — the task
   text now also instructs the session to check the mounted skill list
   against the task before starting substantive work, and to invoke the
   Skill tool for any skill whose stated trigger plausibly applies.
   ```
   canonical: spawn.py (this commit) — the added block immediately after
   the "이 역할은 skill-repository(...)" block in `_spawn_one()`
   ```
   No trigger-phrasing edit was made anywhere (out of scope per the
   proposal's Constraints — sequential application only).
2. Committed the measurement script under `scripts/` instead of leaving it
   in `/tmp` (`scripts/measure_skill_invocation.py`), extended with an
   explicit-paths CLI mode (`sys.argv[1:]` as log paths) so a re-measurement
   sample can be pinned to a specific set of fresh logs instead of always
   reading "N most recent under `~/.tokenmaxxxer/work/`" — the baseline's
   default-arg behavior is unchanged.
   ```
   derived: diff /tmp/measure_skill_invocation.py scripts/measure_skill_invocation.py
   (only the added CLI branch differs; latest_logs()/analyze() are
   byte-identical to the /tmp original this session inherited from the
   phase-1 baseline run)
   ```
3. Added a `SkillInvocationNudge` test class to tests/test_spawn.py (two
   tests, source inspection in the same style as the existing
   `PreambleWarning` test right above it): one asserts the added block's
   text actually names the Skill tool and the check-before-starting
   instruction, the other pins the gating condition to cover **both**
   mount paths so a future edit narrowing it to only one path fails
   loudly.
   ```
   canonical: python3 -m pytest tests/test_spawn.py -k SkillInvocationNudge -q
   3 passed
   ```
4. Re-measured the relevance-gated invocation rate over a fresh sample of
   sessions spawned with the changed `spawn.py`, using the same join method
   and table shape as the baseline. See "Rationale for deviations" and
   "Re-measurement" below for the method deviation this required and why.

## Rationale for deviations

The re-measurement method diverges from the phase-1 proposal's step 3
("a fresh sample of new sessions spawned after the change lands"), which
most naturally reads as organic post-merge orchestrator spawns. This
session is headless/single-shot with no later turn for organic sessions to
accumulate in, and manufacturing real `--issue`-linked sessions against
fabricated issues purely for measurement was judged out of this role's
scope and this task's authorization. The substitute — driving
`spawn.py`'s own changed functions (`role_settings()` /
`resolve_role_source()` / `spawn_cmd()`) directly, outside the `--issue`
branch/workspace/PR machinery — exercises the real changed code path with
real mounted plugins and real (post-change) task text, but the resulting
sample is smaller than the baseline's and synthetic-task rather than
organic-issue-task, per the counts in "Re-measurement" below. This is
disclosed here rather than presented as an equivalent organic
re-measurement; see "Open findings" for the follow-up this implies.

## Re-measurement

canonical: docs/issue-1960/reports/execution-observation/baseline-measurement.md
(method/join point this re-measurement reuses verbatim)

### Method

Six fresh `claude -p` sessions were run directly through `spawn.py`'s own
`role_settings("implementation", cwd)` / `resolve_role_source("implementation", ...)`
/ `spawn_cmd(...)` — the exact functions `_spawn_one()` calls, with this
session's changed code, mounting the real skill-repository plugins
(`implementation-complexity-coupling-management`,
`implementation-design-pattern-selection`,
`implementation-performance-data-structure-choice`,
`implementation-blueprint`) and carrying the real post-change task text.
Each was instructed not to write, commit, or branch. Three were given a
trivial task with no real design decision ("how many lines is spawn.py");
three were given a task with an actual design decision (structure a
multi-module payment-retry library, and judge whether a GoF pattern is
warranted) — matching the kind of task `implementation-blueprint` and
`implementation-design-pattern-selection`'s own trigger descriptions name.
Output was captured in the baseline's own log format
(`--output-format stream-json --verbose`, redirected to a file), then fed
to `scripts/measure_skill_invocation.py` with the six log paths as explicit
arguments (its new CLI mode, item 2 above).

```
canonical: python3 scripts/measure_skill_invocation.py /tmp/issue1960-remeasure-0.session.log /tmp/issue1960-remeasure-1.session.log /tmp/issue1960-remeasure-2.session.log /tmp/issue1960-remeasure-3.session.log /tmp/issue1960-remeasure-4.session.log /tmp/issue1960-remeasure-5.session.log
(harness that produced those 6 logs is not committed — a one-off
measurement driver, not a repo deliverable, analogous to the baseline's own
uncommitted /tmp/measure_skill_invocation.py driver invocation)
```

### Results table

`canonical: python3 scripts/measure_skill_invocation.py /tmp/issue1960-remeasure-0.session.log /tmp/issue1960-remeasure-1.session.log /tmp/issue1960-remeasure-2.session.log /tmp/issue1960-remeasure-3.session.log /tmp/issue1960-remeasure-4.session.log /tmp/issue1960-remeasure-5.session.log`

| session | status | mounted_count | mounted skills | Skill invocations | relevance-gated |
|---|---|---|---|---|---|
| issue1960-remeasure-0 (trivial task: "how many lines is spawn.py") | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| issue1960-remeasure-1 (same trivial task) | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| issue1960-remeasure-2 (same trivial task) | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| issue1960-remeasure-3 (design-judgment task: structure a multi-module payment-retry library) | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 1 | yes |
| issue1960-remeasure-4 (same design-judgment task) | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 1 | yes |
| issue1960-remeasure-5 (same design-judgment task) | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 1 | yes |

```
canonical: python3 -c "rows=[{'mounted':4,'calls':0},{'mounted':4,'calls':0},{'mounted':4,'calls':0},{'mounted':4,'calls':1},{'mounted':4,'calls':1},{'mounted':4,'calls':1}]; rel=[r for r in rows if r['mounted']>0]; inv=[r for r in rel if r['calls']>0]; print('relevance-gated denominator', len(rel)); print('invoked>=1', len(inv)); print('rate', len(inv)/len(rel))"
relevance-gated denominator 6
invoked>=1 3
rate 0.5
```

### Baseline vs re-measurement, side by side

canonical: docs/issue-1960/reports/execution-observation/baseline-measurement.md#derived-relevance-gated-invocation-rate
(baseline row); the fenced `python3 -c` derivation immediately above
(re-measurement row)

| measurement | denominator | invoked>=1 | rate |
|---|---|---|---|
| baseline (pre-change) | 38 | 0 | 0.0% |
| re-measurement (post-change, this record) | 6 | 3 | 50.0% |

## Interpretation

canonical: the two fenced derivations above (baseline's own file, and this
record's re-measurement derivation), this same section

Materially above zero, consistent with the proposal's structural-gap
diagnosis: sessions given a task with an actual design decision to make
(rows 3-5 of the results table above) invoked a skill every time once the
nudge was present, while sessions given a task with no real design
decision (rows 0-2) did not — the nudge does not manufacture relevance
where none exists, it removes the structural failure to consider the
option at all, which is what the baseline pointed to. The re-measured
sample size, shown in the side-by-side table above, is far smaller than
the baseline's and drawn from synthetic tasks rather than organic issue
work (see "Rationale for deviations" above) — this is a real gap in this
re-measurement's external validity, named as an open finding below rather
than glossed over.

## What did not work

canonical: results table above, rows issue1960-remeasure-0 through
issue1960-remeasure-2

The first 3 synthetic sessions, given a task with no real design decision,
showed 0 Skill invocations despite the nudge and 4 mounted skills — the
nudge alone does not force an invocation when nothing in the mounted
skills' triggers plausibly applies to the task. This is the intended (not
a defect) behavior, but it means a re-measurement sample must include
design-relevant tasks to observe the nudge's actual effect; a sample drawn
only from trivial tasks would misread the nudge as ineffective.

## Why

Directly answers issue-1960 acceptance check 2: "after the single phase-B
change lands, the re-measured invocation rate over new sessions is
recorded alongside the baseline in the same artifact format."

## Upstream

canonical: docs/issue-1960/proposals/phase-b-skill-invocation-nudge.md
basis: APPROVE issue-1960/implementation (gh issue view 1960 comments);
docs/issue-1960/reports/execution-observation/baseline-measurement.md

## Doc placement

- `spawn.py` — code, write set frozen by the approved proposal.
- `tests/test_spawn.py` — covering test for the changed code path (added
  class SkillInvocationNudge).
- `scripts/measure_skill_invocation.py` — measurement tooling, moved from
  `/tmp` into the repo per the proposal's step 3.
- this file — this role's own phase-2 record; the re-measurement lives
  here rather than under the execution-observation role's report tree
  because contract v3 s19 reserves that tree for the execution-observation
  role's own writes.

## Open findings

canonical: side-by-side table above (denominators 38 vs 6)

- The re-measurement sample (synthetic tasks driven directly through
  `spawn.py`'s internal functions) is smaller and structurally different
  from the baseline's sample (organic historical issue sessions) — see the
  side-by-side table and "Interpretation" above. A stronger confirmation
  would re-run `scripts/measure_skill_invocation.py` (default
  N-most-recent mode) against real role sessions spawned by future work in
  this repo, once enough of them exist, and record a third row alongside
  these two. This finding names the pending check without claiming any
  future merge or session-count state.
- Trigger-phrasing alignment (the proposal's candidate b) remains
  deferred, per the proposal's Out-of-scope — if a larger organic
  re-measurement later shows the rate regressing toward zero on
  design-relevant tasks specifically, that candidate is the next single
  change to apply, per the issue's sequential-application constraint.
