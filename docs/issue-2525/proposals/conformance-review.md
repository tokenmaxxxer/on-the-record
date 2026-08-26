files:
  - docs/issue-2525/reports/conformance-review.md

## Request

Independently verify that the work landed on `issue-2525/implementation`
(sha `9f0239d1`) actually satisfies #2525's three `check:` bullets —
suite/`pytest.ini`/named-gates deletion and unregistration, no remaining
invocation of the deleted suite, and a plain one-place disclosure that
this removes machine-checking with no replacement — and record the
verdict.

## Constraints

- Phase-2 execution surface (writing the actual verdict into
  `docs/issue-2525/reports/conformance-review.md`) is gated behind a
  human Approve (contract v3 s19; `approval-gate.sh` denied a probe write
  to that path this session, confirming the gate is live for this role).
  No `CORE_BUILD_NOW`/`CORE_CHECKPOINT` env stamp is set this session
  (checked: `env | grep CORE_`, no hits) — default two-session mode
  applies: this PR is phase 1 only.
- The issue's own non-goal binds the *implementation* role, not this
  review, but this review's own checks are all structural (file
  presence, grep, dispatcher/hooks.json registration) — none require
  running the deleted suite or any live-fire demonstration.
- The record for this issue's implementation side
  (`docs/issue-2525/reports/implementation.md`) already self-reports
  `verdict: fail` with five open findings; this review's job is to
  independently confirm (not merely repeat) that verdict against the
  actual tree state, per role-handoff contract's "independent" review
  norm.

## Rationale

Considered staging a live throwaway commit with a fabricated
`acceptance:`/`live-fire:` citation to directly demonstrate
`acceptance-command-real-run-guard.sh` and
`live-fire-claim-real-run-guard.sh` still deny a fabricated result — the
implementation record's own "Open finding 2" names this as unexecuted
work. Rejected for this review: (a) staging any commit is itself an
execution-surface write gated behind the same Approve this proposal is
requesting, so it cannot happen in phase 1 either; (b) it would duplicate
effort — the survey (`docs/issue-2525/reports/conformance-review/survey.md`)
already establishes, by reading both scripts' actual logic at sha
`9f0239d1`, that they are still registered and still executable, which
answers R1c/R1d/R2 without needing to trigger them; a live run would
confirm the same fact these two scripts' own code already discloses; and
(c) the issue's "do not run the suite" non-goal sets the norm this
review's scope stays inside, even though it technically binds the
implementation role rather than this one — running `python3 -m pytest`
via the guard, even once, recreates the exact risk (fixture leakage,
load) #2525 exists to end. Static Inspection of the frozen sha answers
all three acceptance bullets without it.

## What will be done

Phase 2 (after Approve): port the survey's confirmed findings into
`docs/issue-2525/reports/conformance-review.md`'s skeleton — one verdict
per R1a-R1f/R2/R3, each with its file:line/command evidence already
gathered in the survey, an overall verdict (expected: fail, mirroring
but independently re-deriving the implementation record's own
self-reported `verdict: fail`), and `loop_state: reported` (this kind's
terminal state). No new gates, checks, or replacement mechanisms —
review-only, matching #2525's own "no replacement" non-goal.

## Out of scope

- Deleting the three named gates, `pytest.ini`, or rewriting
  `pretooluse_dispatcher.py`/`hooks.json` — that is #2525's
  implementation-role work, not this review's; this review reports the
  gap, it does not close it.
- Staging any live-fire/fabricated-citation demonstration commit (see
  Rationale).
- Re-measuring the `/tmp` fixture-leak numbers the implementation record
  also left open — orthogonal to this review's three acceptance bullets.

## How you'll know it worked

The phase-2 PR's `docs/issue-2525/reports/conformance-review.md` carries
a `verdict:` and `loop_state: reported` in its frontmatter, one entry per
R1a-R1f/R2/R3 in the body each citing file:line/command evidence, and a
plain statement of what remains undone against #2525's acceptance
bullets (gates not deleted, `pytest.ini` not deleted, one live
dead-reference hit, R3's disclosure only partial) — so a reader can tell
apart "reviewed and found incomplete" from "not yet reviewed."
