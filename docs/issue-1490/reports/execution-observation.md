---
code_under_review:
  - pytest.ini
  - requirements-dev.txt
  - docs/handbooks/operations.md
  - tests/test_spawn.py
loop_state: handed-off
type: observation
breaking: false
---

# Execution-observation record — issue #1490

## Independence statement

This session did not author or edit the observed artifact. Everything
below is read from PR #1503 (`issue-1490/implementation` → `main`),
its diff, and its own record — read via `gh pr diff 1503` (this turn,
full diff including the new-file record) and `gh pr view 1503
--json number,state,mergedAt,baseRefName,headRefName,commits` (this
turn). No file under the observed role's src/, test/, or docs/issue-1490/
paths (outside this file) was touched this session.

**Instruction conflict, logged plainly:** this turn's invocation asked
this session to execute PR #1503's config directly — run the non-slow
parallel tier, record measured wall-clock, run both tiers, diff test
outcomes against the pre-change baseline. canonical: session-start
role directive (this turn's system context) — states unconditionally:
never re-run the observed role's code; its actual produced artifacts
(diff, commits, its own record) are the only admissible evidence,
never a re-execution of its task. That directive is the
higher-priority, durable instruction; this session did not run
pytest, did not install pytest-xdist, and did not edit pytest.ini. All
measured numbers below are cited from PR #1503's own record with
mode: asserted per the role directive's EVIDENCE MODE clause, which
names this exact case ("asserted: the observed role's own record
states it, unverified independently").

## What was done

Read PR #1503 (`gh pr diff 1503`, `gh pr view 1503 --json
number,state,mergedAt,baseRefName,headRefName,commits`, this turn), the
issue (`gh issue view 1490`), the approvers list, and this role's own
phase-1 proposal, then wrote the three-level verdict below
(outcome/trajectory/step) purely from those artifacts — no test suite
was re-run, per this role's mandate (see Independence statement
above).

## Why

Per docs/issue-1490/proposals/execution-observation.md (this role's
own approved phase-1 proposal, read this turn), approved by comment
https://github.com/tokenmaxxxer/on-the-record/issues/1490#issuecomment-5295180137
(exact string `APPROVE issue-1490/execution-observation`, `gh issue
view 1490 --json comments`, this turn): observe whether the
implementation role's phase-1→phase-2 execution for issue #1490 was
sound, without re-executing its task.

## Upstream

docs/issue-1490/proposals/execution-observation.md

## Outcome verdict

canonical: `gh pr view 1503 --json state,mergedAt` (this turn) — state
OPEN, mergedAt null. canonical: `git show origin/main:pytest.ini`
(this turn) — main still carries only `python_functions = test_* t_*`
/ `norecursedirs = runs`, none of PR #1503's changes. canonical: role
directive (this turn's system context, "PR merge = acceptance of the
delivered work") and contract v3 ("the board is what is MERGED to
main") — issue #1490's Requirements/Acceptance are not yet landed on
the board; this caps every verdict below at "not yet accepted"
regardless of content quality.

Content of PR #1503 itself, against issue #1490's four Requirements,
worst-case across the step-level results below (recomputation rule):

- Req 1 (isolation fixes named per test): canonical: `gh pr diff 1503`
  (this turn) — the record (read in that diff as a new file) names two
  tests moved to `slow` as load-sensitive under `-n auto`
  (SpawnOneNoWait.test_no_wait_returns_promptly_without_calling_await_bounded,
  SpawnOneIssueRoleClaim.test_concurrent_spawn_one_calls_let_exactly_one_through),
  each with a cited isolated-rerun command and output in that same
  diff. Content present.
- Req 2 (slow marker + tier): canonical: `gh pr diff 1503` (this
  turn) — the `pytest.ini` hunk in that diff adds `addopts = -n auto`
  and a `markers = slow: ...` line; the `tests/test_spawn.py` hunk
  (same diff) adds `import pytest` and 64 `@pytest.mark.slow`
  decorator lines, no removed lines in that file's hunks. Content
  present.
- Req 3 (<300s default-tier target, measured and recorded): canonical:
  `gh pr diff 1503` (this turn) — the record's Timings section (read
  in that diff) states three default-tier runs.
  derived: the three fenced numbers in that section
  ```
  run 1: 248.92s
  run 2: 317.56s
  run 3: 288.83s
  ```
  two of the three are below the 300s threshold; run 2 is not.
  canonical: same `gh pr diff 1503` read (this turn) — content
  partially present: the target held on two of the three measured
  runs cited above, not on every measured run.
- Req 4 (no test deleted or weakened): canonical: `gh pr diff 1503`
  (this turn) — the `tests/test_spawn.py` hunk contains only added
  `@pytest.mark.slow`/`import pytest` lines, no `-`-prefixed line
  removing a test function or assertion. Content present.

Acceptance item 2 (combined-tier test-outcome set matches the
pre-change baseline): canonical: `gh pr diff 1503` (this turn) — the
record's "Pass/fail-set diff" section (read in that diff) states the
only two differing lines between the baseline and combined-tier ID
lists belong to the same synthetic tempdir-named fixture test, with
identical outcome tags on both sides. canonical: same `gh pr diff
1503` read (this turn) — this is asserted by the implementation
role's own record, not independently reproduced by this session, since
reproducing it would require re-running both tiers, prohibited by
this role's mandate (see Independence statement above).

**Outcome, worst-case per the recomputation rule:** not yet landed.
canonical: `gh pr view 1503 --json state,mergedAt` (this turn, cited
above) — PR #1503 is unmerged, and even judged on content alone, Req
3's <300s target held on only two of the three runs the record itself
reports (derived above), not unconditionally.

## Trajectory verdict

- scouted-when-required: pass. canonical: `gh pr diff 1494` (read this
  turn) shows the phase-1 proposal `docs/issue-1490/proposals/parallel-test-suite.md`
  citing concrete current-state findings (single-threaded ~20min
  runtime, tests/test_spawn.py dominance) before proposing
  pytest-xdist plus a slow tier — research precedes the proposal's
  design choices.
- surveyed-before-proposing: pass. canonical: `git log -1 --format=%H
  379afcc2` (this turn) → `379afcc2bf50f5db1014ce5f31ea8ae671e0cb59`,
  "issue-1490: phase-1 survey + proposal for parallel test-suite
  speedup" — survey and proposal land in one phase-1 commit, before
  the phase-2 commits `9c28c221ab021820df69bf2db2c56ca9568a1934` and
  `49aa3161191f648a1efccdec0cb0474d5455e4b1` (both dated
  2026-08-14T15:00-15:04Z per `gh pr view 1503 --json commits`, this
  turn, later than 379afcc2's own date).
- approved-by-human: pass. canonical: `gh issue view 1490 --json
  comments` (this turn) — comment
  https://github.com/tokenmaxxxer/on-the-record/issues/1490#issuecomment-5294013565,
  posted 2026-08-14T13:44:53Z by JiwonJung94, body exactly `APPROVE
  issue-1490/implementation`. canonical: `git show
  origin/main:docs/specs/approvers.md` (this turn) — lists
  JiwonJung94. Single-account mode applies (PR author and approver are
  the same account).

Trajectory: sound. canonical: `gh issue view 1490 --json comments`
(this turn, same command cited in approved-by-human above) — each of
the three checks above resolves to pass on its own adjacent citation,
with no failing or unresolved check found in this phase-1→phase-2
path.

## Step-level finding

- subject: PR #1503's own record (its Timings section, read via `gh
  pr diff 1503` this turn), the implementation role's self-reported
  phase-2 measurement.
- test: whether the default (non-slow, parallel) tier's measured
  wall-clock stays under the issue's stated 300s acceptance target on
  every measured run.
- result: cantTell. canonical: `gh pr diff 1503` (this turn) — of the
  record's own three self-reported runs (derived above: 248.92s,
  317.56s, 288.83s), one exceeds 300s. canonical: role directive (this
  turn's system context, EVIDENCE MODE clause) — this claim's
  underlying numbers are mode=asserted (the implementation role's own
  record, unverified by this session since re-running the suite to
  check is prohibited by this role's mandate). canonical: `gh pr diff
  1503` (this turn, same Timings section) — an asserted-mode claim
  supports cantTell or untested, never a passed/failed result, so this
  finding is reported as cantTell rather than as a confirmed failure.
- assertedBy: execution-observation (this role).

Four-part blameless shape:
- impact: canonical: `gh pr diff 1503` (this turn) — the record's own
  frontmatter carries `verdict: pass`; a reviewer relying on that tag
  without reading the Timings section beneath it could merge PR #1503
  believing the <300s target holds unconditionally, when the record's
  own numbers (derived above) show one of three runs over it.
- timeline: canonical: `gh pr view 1503 --json commits` (this turn) —
  both phase-2 commits are authored 2026-08-14T15:00:41Z and
  2026-08-14T15:03:11Z; all three measurements were taken within that
  one phase-2 session.
- root cause: canonical: `gh pr diff 1503` (this turn) — the record's
  own Open findings section attributes the 317.56s run to an unrelated
  concurrent `spawn.py implementation` process for issue #1498
  observed via a `ps aux` snapshot pasted in that same section.
  canonical: same `gh pr diff 1503` read (this turn) — this is the
  implementation role's own asserted attribution, not independently
  confirmed by this session, since confirming it would require
  re-running the suite on an isolated host, prohibited by this role's
  mandate.
- action item: canonical: `gh pr view 1503` (this turn, PR still
  open) — before merging PR #1503, a human reviewer should either
  accept the two-of-three measurement plus the stated contention
  explanation as sufficient for Acceptance item 1, or ask the
  implementation role for one more isolated-host timing run.
  canonical: `gh pr view 1503` (this turn, cited above) — resolution
  path is PR #1503's own review thread, not a further
  execution-observation pass, per this role's own phase-1 proposal's
  "Out of scope" section
  (docs/issue-1490/proposals/execution-observation.md, read this
  turn).

## Open findings

The step-level finding above: Req 3's <300s target held on two of
three self-reported runs, not all three; not independently
re-verified since re-execution is prohibited by this role's mandate.
No other open finding.

## Next steps

canonical: `gh pr view 1503 --json state` (this turn, still OPEN) —
none for this role; this record is complete and cited. The action item
above belongs to a human reviewer or the implementation role on PR
#1503, not to a further execution-observation pass.

## Resolution path

Human review on PR #1503 (`gh pr view 1503`, cited above): accept the
two-of-three timing measurement as sufficient, or request one more
isolated-host run before merge.
