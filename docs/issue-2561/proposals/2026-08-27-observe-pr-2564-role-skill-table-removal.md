files:
- docs/issue-2561/reports/execution-observation.md

## Request

Issue #2561 asks the implementation role to delete `_ROLE_SKILLS` (the
43-role static role-to-skill dict) and `resolve_role_source()`, the last
role-to-skill table, and prove via four acceptance checks that no session
ever arrives with fewer skills than before. That work landed as PR #2564
(branch `issue-2561/implementation`, still open, not yet merged — see
survey). This role's job is not to build anything — it is to independently
re-derive the PR's own acceptance-check claims (not just re-read them) and
record a verdict in `docs/issue-2561/reports/execution-observation.md`.

## Constraints

- Read-only role: no code, no other role's files. The only path this role
  ever writes is `docs/issue-2561/reports/execution-observation.md` (plus
  the phase-1 homes: this proposal and `reports/execution-observation/`).
- Phase 2 (writing the actual record) is gated behind a human Approve —
  confirmed live this session by `approval-gate.sh` refusing an
  execution-surface write with exactly that reasoning (see survey,
  Subject section). This session cannot self-authorize past that gate.
- Verification must be independent, not a re-statement of the PR's own
  cited commands and outputs — re-run each check from a fresh checkout the
  PR author never touched, per this role's established pattern (see
  `docs/issue-2516/reports/execution-observation.md` for a precedent this
  proposal follows).

## Rationale

Considered treating the PR's own `derived:`-tagged evidence in
`docs/issue-2561/reports/implementation.md` as sufficient and simply
restating it in the eventual record. Rejected: this role exists
specifically because a re-statement of the builder's own claims is not
independent verification — an implementation session's own acceptance
evidence can be honestly reported yet still reflect a single lucky run,
a scope the author unconsciously narrowed, or (as found this session,
below) a claim that isn't actually reproducible on retry. Re-deriving from
a separate scratch clone, as this session already did in the survey, is
the only way to tell the difference between "true" and "reported and
plausible."

The one substantive finding from that independent re-derivation: check
2 (a real spawn, same task text before/after) relies on a live
BM25+LLM-judge subprocess call, which this session found is
non-deterministic — two back-to-back re-runs on the *same*
`issue-2561/implementation` code each returned a different 3-skill
composition, neither matching the PR's claimed 4-skill result. Considered
treating this as a defect finding against the PR (its check 2 evidence
"doesn't reproduce"). Rejected that framing: `spawn.py`'s own diff removes
only one dead re-export line and touches nothing in the actual mount
computation (independently confirmed by reading the diff, survey Check 2),
so the non-reproducibility is a property of the live judge subprocess that
predates this change and is out of this issue's scope (the issue's Scope
boundary explicitly excludes changing task-matched selection) — not
something PR #2564 introduced or could have prevented. The eventual record
will report this as an open finding about check 2's inherent
non-determinism, not as a failure of the PR.

## What will be done

Once the Approve signal exists (PR review Approve from an
`docs/specs/approvers.md` account different from this role's own PR
author, or an issue comment whose entire body is exactly `APPROVE
issue-2561/execution-observation`), a later session will:

1. Read `docs/issue-2561/reports/execution-observation.md`'s pre-written
   skeleton and fill every section using the independent re-derivation
   already performed in `docs/issue-2561/reports/execution-observation/survey.md`
   this session (checks 1, 3, 4, 5, 6 all independently reproduced; check
   2 characterized as non-deterministic-but-not-a-regression).
2. Re-run each check one more time at record-writing time (not just cite
   this session's survey numbers) so the record's own evidence is live,
   per `docs/issue-2561/reports/execution-observation.md`'s own frontmatter
   contract (`test:`, `result:`, `assertedBy:`).
3. Set `loop_state` to the terminal state for an `execution-observation`
   kind (per contract §2's per-kind terminal-state vocabulary) and record
   a `result:` reflecting whether the four acceptance checks, taken
   together, support the PR's own `verdict: pass`.
4. Land the record on this same branch/PR, phase 2, no separate PR.

## Out of scope

- Modifying, re-running, or commenting on `_sp.ROLES` or core's hooks (the
  issue's own Scope boundary excludes both).
- Re-litigating the design judgment PR #2564 made (base layer =
  `resolve_role_family_source()` over a straight `resolve_static_policy_source()`
  swap) — that decision, and its own documented regression evidence, is
  the implementation role's to own; this role verifies the *outcome*
  against the *acceptance checks*, not the design process.
- Writing to `docs/issue-2561/reports/implementation.md` or any other
  role's record area.
- A full-suite `pytest` re-run to reconcile this session's scratch-clone
  test counts against the PR's own claimed absolute counts — the survey
  already established why the absolute counts differ (different `origin`
  remote per sandbox) and that the relative claim (no new failures, 4
  fewer tests) is what's independently checkable and was confirmed.

## How you'll know it worked

`docs/issue-2561/reports/execution-observation.md` exists with
`loop_state` set to a terminal value, every skeleton section filled with
live `derived:`/`canonical:`/`acceptance:`-tagged evidence (not copied from
the PR's own record), an explicit verdict on all four issue acceptance
checks, and an Open findings entry characterizing check 2's live-judge
non-determinism — landed on this role's branch and visible in this PR
after the human Approve.
