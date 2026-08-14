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

## Phase-2 re-observe (2026-08-15, new head)

canonical: `gh pr view 1503 --json commits` (this turn) — PR #1503 now
carries a third commit, `9e16671ed9d24cc2237a422724314f6f2e96603d`
("issue-1490: slow-tier real-subprocess spawn tests, add pre-merge
tier..."), authored 2026-08-14T17:10:34Z, after the two commits
(`9c28c221`, `49aa3161`, both ~15:0x) the sections further below (the
original "Outcome verdict" / "Step-level finding") were written
against. canonical: `git log --oneline -3` (this turn) — `a3e84f90`
"Merge pull request #1495 from tokenmaxxxer/issue-1490/conformance-review"
is on `main`, ahead of this rework's authored timestamp. This is a
rework responding to that merged conformance-review's blockers
(`docs/issue-1490/reports/conformance-review.md`, read this turn on
`main`): Acceptance 1 Incorrect (428.76s independent measurement, over
budget) and Requirement 2's third clause Absent (no pre-merge tier
policy). This section supersedes the original sections' verdicts with
the new head's content; nothing below re-runs pytest — this session's
mandate is unchanged (see Independence statement above).

canonical: `gh pr diff 1503` (this turn, full diff of the current
head, including the record's new "Rework (2026-08-15)" section as a
diff hunk) — the rework commit:

1. moved `EventReporting` and `ProgressEvents` in `tests/test_spawn.py`
   into the `slow` tier (`@pytest.mark.slow` above each class), citing
   these as the four slowest default-tier cases in a
   `--durations=40` run (105.66s/103.90s/103.65s/66.98s), matching the
   `slow` marker's own stated definition.
2. added the "머지 전 회귀 정책 / Pre-merge regression policy — tier
   required per change class" table pair to
   `docs/handbooks/operations.md`, naming the required tier
   (`-m "not slow"`, `-m slow`, both, or none) per change class
   (spawn-lifecycle code, gate scripts, docs-only, other logic).

mode: asserted for every number in this section — the record's own
fenced output, unverified independently by this session, per the role
directive's EVIDENCE MODE clause (re-running to check is prohibited by
this role's mandate).

- Req 3 (<300s default tier, measured): canonical: `gh pr diff 1503`
  (this turn) — the rework section's fenced output shows three
  back-to-back post-fix runs: `run 1: ... in 33.05s`, `run 2: ... in
  26.65s`, `run 3: ... in 27.14s` (all `-m "not slow"`), replacing the
  prior 248.92s/317.56s/288.83s spread that had one run over budget.
  canonical: same `gh pr diff 1503` read (this turn) — all three
  post-fix numbers land under 300s per that fenced output, content now
  present on all three measured runs, not two-of-three as the
  pre-rework head showed.
- Req 2 third clause (pre-merge tier policy per change class):
  canonical: `gh pr diff 1503` (this turn) — the
  `docs/handbooks/operations.md` hunk in that diff adds the bilingual
  table pair described above; content now present in this diff, absent
  from the pre-rework head's diff.
- Acceptance item 2 (combined-tier outcome-set matches baseline):
  canonical: `gh pr diff 1503` (this turn) — the rework section shows
  a before/after fix comparison of `FAILED` lines: `17 failed, 1825
  passed` (before the `@pytest.mark.slow` fix, still on old tiering)
  vs `18 failed, 1787 passed` x3 (after). canonical: same `gh pr diff
  1503` read (this turn) — the one new ID in the after-set,
  `t_rulebook_version_is_recorded` (`tests/test_gates.py`, asserted
  line 95 per that same record text), is attributed by the record to
  this session's own uncommitted edit making the checkout git-dirty at
  measurement time, not a new product failure. canonical: same `gh pr
  diff 1503` read (this turn) — the record's excluding-diff (sorted
  before/after `FAILED` sets, `t_rulebook_version_is_recorded`
  filtered out) shows no output, i.e. identical sets, per that fenced
  text; this is an asserted claim only, not reproduced by this
  session.

**Updated outcome verdict:** still capped at "not yet landed" —
canonical: `gh pr view 1503 --json state,mergedAt` (this turn) — state
OPEN, mergedAt null; PR #1503 is not merged per that same command's
output. canonical: `gh pr diff 1503` (this turn) — on content alone,
worst-case across the step-level results just above: Req 3 and Req 2's
third clause, previously partial/absent per the original section
below, now read content-present on the new head's own asserted numbers
cited above; the only remaining open item is the
`t_rulebook_version_is_recorded` artifact and its un-reproduced
excluding-diff, both mode: asserted and not independently re-run by
this session (see the updated step-level finding immediately below).

**Updated step-level finding**, superseding the original one further
below (dated to the two-commit head): canonical: `gh pr diff 1503`
(this turn, rework section) — that original finding ("Req 3's <300s
target held on two of three runs, cantTell") is superseded by the new
head's own reported numbers cited above (three-of-three under budget)
— downgraded from a live concern to informational, since the
underlying numbers remain mode: asserted, never independently
reproduced by this session. A new, narrower step-level finding
replaces it:

- subject: PR #1503's rework section (`gh pr diff 1503`, this turn),
  specifically its "no other failure ID changed" / empty-diff claim.
- test: whether the combined-tier outcome-set, after excluding the
  git-dirty artifact, is identical to the pre-rework baseline set.
- result: cantTell. canonical: `gh pr diff 1503` (this turn) — the
  record states the excluding `diff` produced no output (cited above),
  but the underlying command was run by the implementation role, not
  reproduced by this session (mode: asserted). canonical: `gh pr diff
  1503` (this turn, same rework section) — an asserted-mode claim
  supports cantTell or untested, never a passed result, per the role
  directive's EVIDENCE MODE clause, so this finding is reported as
  cantTell.
- assertedBy: execution-observation (this role).

Four-part blameless shape for this finding:
- impact: canonical: `gh pr diff 1503` (this turn) — a reviewer
  trusting the record's "no other failure ID changed" line without
  independent reproduction could merge PR #1503 on an unverified
  outcome-set-equality claim.
- timeline: canonical: `gh pr view 1503 --json commits` (this turn) —
  the rework commit is authored 2026-08-14T17:10:34Z, after the
  original two commits (~15:0x, same command's output) and after
  conformance-review's blockers landed on `main` (`git log --oneline
  -3`, this turn, commit `a3e84f90`, cited above).
- root cause: session-start role directive (this turn's system
  context, "never re-run the observed role's code") states this role's
  own mandate prohibits re-executing the observed role's task.
  canonical: `gh pr diff 1503` (this turn, same rework section cited
  throughout this update) — because of that mandate, this role can
  only quote the outcome-set-equality claim from that diff, not
  independently reproduce it.
- action item: canonical: `gh pr view 1503 --json reviews` (this
  turn) — empty result, no reviews yet on PR #1503. canonical: `gh pr
  diff 1503` (this turn, same rework section) — before merge, a human
  reviewer (or a fresh conformance-review pass carrying its own
  independent-execution mandate) should reproduce that section's
  excluding-diff once, outside the implementation role's own session.

## Original head (pre-rework, two-commit) sections below

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

Superseded by the "Phase-2 re-observe (2026-08-15, new head)" section
above: canonical: `gh pr diff 1503` (this turn) — the original
two-of-three-runs finding no longer applies to the current head
(three-of-three under 300s, cited above); the current open finding is
the updated step-level finding above (outcome-set-equality claim is
mode: asserted, not independently reproduced by this session).

## Next steps

canonical: `gh pr view 1503 --json state` (this turn, still OPEN) —
none for this role beyond this update. canonical: `gh pr diff 1503`
(this turn, "Phase-2 re-observe" section above) — the action item
there belongs to a human reviewer or a fresh conformance-review pass
on PR #1503, not to a further execution-observation pass.

## Resolution path

canonical: `gh pr view 1503` (this turn, cited above) — human review
on PR #1503: accept the rework's three-of-three timing measurement and
asserted outcome-set-equality claim as sufficient, or request one more
independently-reproduced run before merge.
