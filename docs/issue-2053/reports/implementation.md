---
subject: issue-2053
code_under_review:
  - tests/test_perf_budget_issue_2053.py
loop_state: committing
type: implementation
breaking: false
verdict: pass
---

# Record: per-occurrence performance budget guard (skill-verdict-guard,
BM25 cross-family scoring, report-framing-check extension)

## What was done

Measured the per-occurrence standalone cost of the three new
engagement/matching/reporting stages named in the issue, using the
#2016 survey's method (standalone, outside the Claude Code harness,
file-based stdin payloads — never a `gh pr`/`git commit` literal inline
in a Bash command string), and added `tests/test_perf_budget_issue_2053.py`
codifying the stated budgets as a regression test: `<200ms` standalone
for `skill-verdict-guard.sh` and for `_bm25_cross_family_scores()`
(spawn.py), plus a static check that none of the three stages shells
out to `gh`/network at all — the `skill_judge` consult stays the only
permitted network call, and only at spawn (`_skill_judge_consult()`),
never inside these per-occurrence stages.

No stage exceeded its budget, so no short-circuit/caching fix was
needed for this delivery (see Measurement below).

## Why

Operator direction 2026-08-23 (issue body) asked for a measured budget
guard so the #2039/#2040/#2044/#2043/#2047 additions don't regress
per-session performance.
canonical: `docs/issue-2016/reports/performance-engineering/survey.md`
(this session's own read) — phase 1 measured the pre-existing hook/gate
layer's per-call overhead as the recurring cost bucket this issue asks
to guard the new stages against. The issue's own Acceptance freezes the
method (#2016's file-based-payload approach) and the budget numbers
(`<200ms` each, consult-only network), so this delivery's job is to
measure against that frozen bar and, only if over, fix in the same
delivery.

## Basis

Upstream: `docs/issue-2016/reports/performance-engineering.md` (method
precedent), `docs/issue-2016/reports/performance-engineering/survey.md`
(file-based-payload method statement), issue #2053 body (frozen
Acceptance). `validity-consult-skip: trivial` on the issue plus this
session's own spawn-time `skill_judge` consult (`docs/issue-2053/reports/consult-log.md`)
authorize single-phase (no separate phase-1 proposal) — `CORE_BUILD_NOW=1`
was set in this session's environment by the spawner, invoking contract
v3 s19a's build-now bypass.

## Measurement

Method: standalone (subprocess/import calls outside the Claude Code
harness), 5 reps per stage, file-based stdin payloads written to disk
first and read back (no gate-triggering literal ever appears inline in
a shell command string) — same posture as
`docs/issue-2016/reports/performance-engineering.md`'s own before/after
runs.

canonical: `python3 -m pytest -q tests/test_perf_budget_issue_2053.py`
acceptance: `python3 -m pytest -q tests/test_perf_budget_issue_2053.py` — result: 6 passed

Standalone reps captured while authoring the test
(/tmp/otr-bench-2053/run_bench.py, same fixtures as the committed
test, 5 reps each):

canonical: `python3 /tmp/otr-bench-2053/run_bench.py`
acceptance: `python3 /tmp/otr-bench-2053/run_bench.py` — result: skill-verdict-guard.sh mean=0.0383s max=0.0411s; report-framing-check.sh mean=0.0288s max=0.0360s; bm25_cross_family_scores mean=0.0091s max=0.0096s

| stage | mean | max | budget |
|---|---|---|---|
| `skill-verdict-guard.sh` (Stop, record-write) | 0.0383s | 0.0411s | <0.200s |
| `report-framing-check.sh` skills-utilization extension (Stop) | 0.0288s | 0.0360s | <0.200s |
| `_bm25_cross_family_scores()` (spawn, four-surface scoring) | 0.0091s | 0.0096s | <0.200s |

All three stages land well under the 200ms budget standalone — no
short-circuit/caching fix was required in this delivery.

Network-call check: `skill-verdict-guard.sh` and `report-framing-check.sh`
carry no `gh`/`curl`/`wget` token (both do local git/file-read work
only); `_bm25_cross_family_scores()` carries no `subprocess` call (pure
in-process tokenize/score over already-read `SKILL.md` text). The one
network-capable call among these three stages' call graph is
`_cross_family_skill_matches_with_consult()`'s optional
`_skill_judge_consult()` step, which fires once per spawn (not
per-occurrence of the scoring stage itself) — matching the issue's
"only permitted network call ... never per-tool-call" requirement.
This is also visible in this session's own live spawn-time
bootstrap_timing line (captured while running the pre-existing
slow-tier spawn tests below), which reports cross_family=13.678 /
cross_family=10.888 — that combined figure is the BM25 scan (~9ms per
the standalone measurement above) plus the optional skill_judge consult
network round trip inside the same wrapped block, not the BM25 scan
alone; the issue does not budget the consult call's own latency, only
that it stays the sole and spawn-only network call, which the test
asserts mechanically.

canonical: `python3 -m pytest -q tests/test_perf_budget_issue_2053.py`
acceptance: `python3 -m pytest -q tests/test_perf_budget_issue_2053.py` — result: 6 passed (includes the 3 network-call assertions above)

## Test suite

canonical: `python3 -m pytest -q -m "not slow"`
acceptance: `python3 -m pytest -q -m "not slow"` — result: 2586 passed, 19 xfailed, 2 xpassed in 41.06s

canonical: `python3 -m pytest -q -m slow`
acceptance: `python3 -m pytest -q -m slow` — result: 109 passed, 1 xfailed, 1 xpassed, 2 failed in 264.08s

The 2 failures (test_spawn_directive_assembly.py
SinglePhaseSignal.test_without_flag_is_byte_identical_to_today,
test_spawn_gate_wiring.py
Ledger.test_toolchain_cache_env_redirected_into_workspace) are
pre-existing and unrelated to this delivery's diff — this delivery's
only change is the new, independent tests/test_perf_budget_issue_2053.py
file (no edit to spawn.py, any on-the-record/hooks/*.sh, or any other
existing test); re-running just those two tests in isolation reproduces
the same failures with no diff applied, and both trace to this
sandbox's own environment (no origin/main remote to diff against, no
live gh auth for the gh read-cost assertion), not to any behavior this
delivery touched.

canonical: this session's own isolated re-run of the same two failing
node IDs, with no diff applied beyond the committed
tests/test_perf_budget_issue_2053.py addition
acceptance: python3 -m pytest -q tests/test_spawn_directive_assembly.py tests/test_spawn_gate_wiring.py -k "test_without_flag_is_byte_identical_to_today or test_toolchain_cache_env_redirected_into_workspace" — result: 2 failed in 100.59s, both on origin/main-diff / gh sandbox-environment errors visible in captured stderr (fatal: ambiguous argument 'origin/main...HEAD', gh 조회 실패), independent of this delivery's one-file diff

## What did not work

None — the measurement ran cleanly on the first attempt and no stage
exceeded budget, so there was no fix path to iterate on. (The 2
pre-existing slow-suite failures above are a sandbox-environment gap,
not a fix this delivery's write set covers — see Open findings.)

## Rationale for deviations

None — this delivery followed the issue's own frozen Acceptance and
method exactly (measure against the #2016 method/budgets; single-phase
via the operator-set `CORE_BUILD_NOW=1` bypass, as the issue text
itself states "Tags justify single-phase").

## skill-verdict lines

skill-verdict: implementation-complexity-coupling-management — not-applicable: no class/module coupling or import-direction decision was made in this delivery — it is a measurement + regression-test addition, not a restructuring.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-style pattern indirection was introduced or reconsidered; the test file is a flat set of measurement functions.
skill-verdict: implementation-performance-data-structure-choice — applied: this is exactly the skill's trigger condition (a performance cliff / algorithm-choice concern).
canonical: `spawn.py` lines 8208-8254 (_bm25_cross_family_scores)
The function tokenizes once per call and does a linear scan over an
already-small cross-family corpus with no per-call I/O, which is why it
measured at ~9ms (see Measurement table above) rather than needing
algorithmic rework.
skill-verdict: implementation-blueprint — not-applicable: no multi-module/multi-file structure was being designed from scratch; this delivery adds one test file plus a report, not a new architecture.
skill-verdict: observability-phase-trace — applied: cross-checked this phase-2 record's measurement method against the phase-1 methodology it inherits (#2016 survey's file-based-payload approach, per this record's own Basis/Measurement sections) before writing the numbers down.

## Open findings

The 2 pre-existing slow-suite failures noted in Test suite above are
sandbox-environment gaps (no origin/main remote, no live gh auth in
this session's working tree) outside this issue's write-set scope
(on-the-record/hooks/, spawn.py, scripts/, tests/, test/, docs/) to fix
as a behavior change — they are environment prerequisites, not a code
defect this delivery's diff touches.

canonical: `python3 -m pytest -q tests/test_perf_budget_issue_2053.py`
acceptance: `python3 -m pytest -q tests/test_perf_budget_issue_2053.py` — result: 6 passed; all three stages measured under budget and the regression test enforces the budgets going forward.

next steps: none for this issue's own scope.

canonical: `python3 -m pytest -q tests/test_perf_budget_issue_2053.py`
acceptance: `python3 -m pytest -q tests/test_perf_budget_issue_2053.py` — result: 6 passed, delivery ready for PR review.

resolution path: a follow-up session/issue would need to fix this
sandbox's origin/main remote setup and gh auth so the two named
slow-tier spawn tests can be re-verified clean; out of this issue's own
write-set scope.
