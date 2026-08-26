---
status: proposed
files:
  - docs/issue-2561/reports/conformance-review.md
---

## Request

Conformance-review PR #2564 (`issue-2561/implementation`, squash-merged
to `main`) against issue #2561's 4 acceptance checks, and land the
verdict in `docs/issue-2561/reports/conformance-review.md`.

## Constraints

- `CLAUDE_ROLE=conformance-review`, no `CORE_BUILD_NOW` — this session
  runs the default two-phase role-handoff contract: this proposal, then
  a human Approve, then the record write in a later session.
- The record file itself (`docs/issue-2561/reports/conformance-review.md`)
  is phase-2 output under this repo's approval-gate — it cannot be
  written this session without an Approve (observed live: this session's
  own git reads against `docs/issue-2561/reports/*` paths were refused by
  `pretooluse-dispatcher.sh`'s approval-gate mid-session, before any
  proposal existed).
- PR #2564 is already merged to `main` — this review has nothing left to
  block; it only records a verdict against already-landed code.

## Rationale

Considered writing the record directly against the pre-written skeleton
at `docs/issue-2561/reports/conformance-review.md` without a phase-1
proposal, since the skeleton was already staged on disk and the spawning
task described it as ready to fill in. Rejected: no `CORE_BUILD_NOW` is
set and no prior PR/approval exists for `issue-2561/conformance-review`
(checked this session via `gh pr list --head issue-2561/conformance-review`
and `gh pr list --search "2561 in:title,body"`), so the default
two-session contract applies unchanged, and the repo's own
`pretooluse-dispatcher.sh` mechanically confirmed this mid-session by
refusing further git reads under `docs/issue-2561/reports/`. Writing the
record anyway would mean vs the same gate a second, harder time at
commit — better to survey now and hand the actual verdict write to phase
2.

The current-state survey (`docs/issue-2561/reports/conformance-review/survey.md`,
already on disk) was built with the heavier bar this role's own precedent
(`docs/issue-2403/proposals/2026-08-26-conformance-review-issue-2403.md`)
sets: every one of the 4 acceptance checks was independently re-derived
against the actual merged `main` commit in throwaway worktrees, not cited
from the implementation record's own pasted numbers — including
re-running the pre-#2561 code three times to characterize the live
skill-judge's run-to-run non-determinism before treating any single
before/after pair as proof.

## What will be done

Once approved, write `docs/issue-2561/reports/conformance-review.md`
carrying a Present/Surface/Absent/Incorrect/Unverifiable verdict for each
of the 4 requirement items already extracted and checked in the survey
(1: `_ROLE_SKILLS`/`resolve_role_source` gone + anti-pattern guard; 2:
spawn before/after skill count; 3: consult skill resolution; 4: empty-task
policy-skill mount), citing the survey's own evidence rather than
re-deriving it, plus the mandatory `skill-verdict:` lines for
`conformance-review-finding-record` and
`conformance-review-traceability-and-evidence` (both invoked this
session, applied when the record itself is written) and
`conformance-review-verdict-assignment` (applied at verdict-render time).
`conformance-review-sampling-derivation` and
`conformance-review-severity-classification` stay not-applicable — full
enumeration was feasible and no risk-weighting pass was requested.

## Out of scope

- No code changes to `skills.py`, `spawn.py`, `consult.py`, or
  `pipeline.py` — this role only reviews and records, it does not patch.
- No action on PR #2564 itself (it is already merged; no review comment,
  no re-review) — this role's write scope is its own record file.
- Re-running the implementation record's full 43-role coverage sweep
  (its own "Open findings" item 1) — independently spot-checked only the
  one exception role it names (`defect-verification`), since none of the
  issue's 4 coded acceptance checks require a full sweep; the survey
  states this explicitly rather than silently narrowing scope.

## Sources

No live web research access was used or needed for this proposal — this
is a review of an internal infra/process refactor with no external
product category to benchmark against (see the survey's own "Skip
conditions checked" section). The only sources consulted were internal:
issue #2561 itself (`gh issue view 2561`), PR #2564 (`gh pr view 2564`),
the implementation record and code diff on the merged `main` commit, and
this role's own prior-precedent proposal
(`docs/issue-2403/proposals/2026-08-26-conformance-review-issue-2403.md`).

## How you'll know it worked

`docs/issue-2561/reports/conformance-review.md` exists, carries a verdict
for each of the 4 acceptance checks with a citation back to this
proposal's survey evidence (not bare assertion), and its own frontmatter
`result:` reflects the worst-case result across the 4 items per this
role's convention.
