---
subject: issue-223
role: execution-observation
observed_role: implementation
observed_pr: 249
code_under_review: a30f56c65e1166ff72961e9599a3f0400755b513
loop_state: phase-1-proposal
---

files:
- docs/issue-223/reports/execution-observation.md

## Request

Issue #223's `## 실행 계획` step 2: an independent execution observation
of step 1, delivered by the `implementation` role as PR #249 (commits
`2272489` phase 1, `a30f56c` phase 2), merged to `main` as `48266e7` at
2026-08-03T10:56:21Z. Issue #223's three numbered requirements: (1) the
main spawn path (`_spawn_one()`) gets the same claim family the respawn
path already has, rejecting a second concurrent spawn of the same
`(issue, role)`; (2) a stale claim left by a dead session is cleanable;
(3) the rejection message names which session (pid/start-ts) already
holds the claim.

## Verdict levels to be rendered in phase 2

Declared here, before any evidence discussion. All three levels of the
role's three-level verdict will be addressed in
`docs/issue-223/reports/execution-observation.md`; a level found not to
apply will be written as "not applicable, because X" rather than
omitted.

1. **Outcome** — whether PR #249 and
   `docs/issue-223/reports/implementation.md` satisfy issue #223's three
   numbered requirements. Evidence: `a30f56c:spawn.py`'s
   `_acquire_spawn_claim`/`_rewrite_spawn_claim_pid`/
   `_release_spawn_claim` and their wiring into `_spawn_one()`, checked
   against each requirement's own wording, plus the four new
   `SpawnOneIssueRoleClaim` tests' construction in `a30f56c:test_spawn.py`.
2. **Trajectory** — whether the phase-1→phase-2 path met contract v3
   s19: survey before proposal, a real human approval before any
   phase-2 artifact. Evidence: `2272489`'s file membership and
   authored timestamp; the issue-223 comment `APPROVE
   issue-223/implementation` (author, timestamp, `docs/specs/approvers.md`
   membership); `a30f56c`'s authored timestamp relative to that
   approval.
3. **Step** — which specific artifact, if any, carries a deficiency.
   Candidates are enumerated in "What will be done" below (S1-S3). Any
   finding that survives checking will carry the four-part blameless
   shape — impact, timeline, root cause, action item.

## Constraints

- **No re-execution.** `test_spawn.py`'s `SpawnOneIssueRoleClaim` suite,
  `spawn.py`, and `spawn.py clean` will not be run. The four new tests'
  construction (arrange/assert) is checkable by inspection; whether they
  actually pass is the observed role's own claim, not independently
  reproduced here.
- **No reading of `spawn.py` / `test_spawn.py` at HEAD as evidence of
  what PR #249 did**, beyond the two call-site lines
  (`spawn.py:5732`, `spawn.py:3510-3524`) already read in the survey,
  which are unrelated to `a30f56c`'s own diff and unchanged by any later
  commit as of this survey.
- **No edits outside this role's own path.** `spawn.py`,
  `test_spawn.py`, and `docs/issue-223/reports/implementation*` are the
  observed role's; nothing under them is touched.
- **No issue filing.** Contract v3: issues are user-authored only.
  Findings return in this role's own record, on this role's own PR.
- Pre-existing sandbox test failures unrelated to `a30f56c` are outside
  this change's account (transition-based relevance).

## Rationale

The survey found the observed record already names two of its own open
items (rc-discard at `spawn.py:3523`, pid-reuse) — a check plan that
spends itself re-deriving those from nothing would spend itself on an
already-stated point. The scout brief's category must-bes point at two
places the survey has not yet resolved: whether every claim-file mutation
step (not just the create step) is atomic, and whether the delivered fix
still satisfies the proposal's original ask despite its shape changing
from the proposal's literal `O_CREAT|O_EXCL` description. The checks
below are weighted toward those two; C1/C2 are confirmatory against named
artifacts.

## What will be done

Write `docs/issue-223/reports/execution-observation.md` as the first act
of phase 2, with an independence statement (this role did not author or
edit PR #249's artifacts) preceding any verdict language, and
`loop_state` updated at each transition. Into it:

- **C1 (outcome).** Read requirement 1 against
  `a30f56c:spawn.py`'s wiring inside `_spawn_one()` (claim acquired
  before `checkout_issue_branch()`, released after `roster_remove()`);
  requirement 2 against `_acquire_spawn_claim`'s dead-pid branch and
  `test_stale_claim_from_dead_pid_is_cleaned_and_retried`'s
  construction; requirement 3 against the rejection string's content and
  `test_rejection_names_the_live_claimant_pid_and_ts`'s assertions.
- **C2 (trajectory).** Read `2272489`'s file membership and authored
  timestamp, the issue-223 approval comment's author/timestamp against
  `docs/specs/approvers.md`, and `a30f56c`'s authored timestamp relative
  to the approval.
- **S1 — atomicity of every claim-mutation step.** Read
  `_acquire_spawn_claim` (tempfile+`os.link()`), `_rewrite_spawn_claim_pid`
  (tempfile+`os.replace()`), and `_release_spawn_claim` (read-then-
  conditional-unlink, no write) against the TOCTOU class the observed
  record's own "What did not work" section names, to confirm the fix
  closes it at all three mutation points, not only the first.
- **S2 — the proposal-to-delivery shape change.** Read
  `docs/issue-223/proposals/spawn-one-issue-role-claim.md`'s literal
  `O_CREAT|O_EXCL`-then-write description against the delivered
  tempfile+link/replace shape and the observed record's own account of
  why it changed, to confirm the delivered mechanism still satisfies the
  proposal's behavioral ask (single winner, stale-cleanable, pid/ts in
  the rejection) despite the syscall-level shape change.
- **S3 — the discarded return code at `spawn.py:3523`.** Re-confirm by
  independent read (already performed once in the survey) that
  `_respawn_or_cap()` neither assigns nor checks `_spawn_one()`'s return
  value, and read the bookkeeping lines immediately above the call
  (`attempt_n`, `_append_event(..., "respawn-attempt", ...)`,
  `_respawn_state_save(state)`) to state precisely what runs regardless
  of a claim rejection inside that call.

Each of C1, C2, S1-S3 lands as a citation-bearing paragraph; any that
resolve to no finding are recorded as checked, not dropped.

## Out of scope

- Re-running `test_spawn.py`, `spawn.py clean`, or the two-thread
  concurrency repro in any form.
- Any edit to `spawn.py`, `test_spawn.py`, or
  `docs/issue-223/reports/implementation*`.
- Redesigning the claim mechanism or evaluating alternative locking
  primitives (`flock()`, a database row lock, etc.) — the design choice
  was approved by the human and is not this role's to relitigate.
- Re-opening issue #132's respawn-claim mechanism, which this change
  only mirrors, not modifies.
- Filing any issue for anything found. Findings go in the record; the
  human judges them on this PR.

## How you'll know it worked

- `docs/issue-223/reports/execution-observation.md` exists on this
  branch, committed, with the independence statement preceding the
  first verdict-bearing sentence in document order.
- All three levels — outcome, trajectory, step — appear, each either
  rendered or written as "not applicable, because X".
- Every verdict-bearing sentence has its citation (commit SHA,
  `file:line`, or comment URL/timestamp) adjacent to it.
- Each of C1, C2, S1-S3 is accounted for, including any that resolve to
  nothing.
- Any finding carries impact, timeline, root cause, and action item.
- No file outside `docs/issue-223/reports/execution-observation*` and
  `docs/issue-223/proposals/execution-observation-plan.md` is modified
  by this session — checkable with `git show --stat` on this branch's
  commits.
