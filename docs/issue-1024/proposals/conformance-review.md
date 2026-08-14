---
status: proposed
files:
  - docs/issue-1024/reports/conformance-review/survey.md
  - docs/issue-1024/proposals/conformance-review.md
---

# Conformance-review proposal — issue-1024 (phase 1)

## Upstream / basis

Issue #1024. Requirement linkage: R001 (northpole req#6 — requirements
condensed/managed so work never drifts; req#1 — orchestration from
requirements). Delivered: `7b808d84` (phase-1 proposal, PR #1027),
`e16b04fd` (phase-2 delivery, PR #1030). Proposal:
`docs/issue-1024/proposals/2026-08-12-requirement-intake-validity-consult.md`.
Implementation record: `docs/issue-1024/reports/implementation.md`.
Survey: `docs/issue-1024/reports/conformance-review/survey.md`.

## Request

Board condition met (per role directive, issue-521): `e16b04fd` landed
on `main` and no conformance-review record exists yet for it. This
proposal is the phase-1 half of that review: extract the fixed
requirement list phase 2 will render verdicts against, from the issue's
own Problem/Direction/Acceptance text and the linked R001/northpole
req#6/req#1 requirements.

## Constraints

- Verdicts are deferred to phase 2, gated on approval per role-handoff
  contract v3 s19 — this document extracts requirements only, no
  Present/Surface/Absent/Incorrect/Unverifiable judgment.
- Requirements are drawn only from the issue body and its stated
  linkage (R001/northpole #6/#1) — not from the implementer's stated
  intent in the implementation record, per the role's phase-2 rule
  (deliberately without the building agent's stated intent).

## What will be done

Phase 2 will render one verdict per row below against
`e16b04fd`'s artifacts (`on-the-record/hooks/directive.sh`,
`gates/requirement_intake_consult.py`, its tests) and against
R001/req#6/req#1's own wording.

## Requirement list (extracted, verdict deferred to phase 2)

1. **R1 — Default step at requirement intake.** Source: issue body,
   Direction bullet 1 ("On requirement intake ... the orchestrator
   directive gains a default step: consult `requirements-engineering`
   ... and, for risk-bearing asks, `risk-management`"). Check: does
   `directive.sh`'s REQUIREMENT ELICITATION block contain an
   unconditional (non-opt-in) instruction to route confirmed asks
   through `requirements-engineering`, and route risk-bearing asks also
   through `risk-management`, before drafting.

2. **R2 — Consult results recorded in the drafted issue body.** Source:
   issue body, Direction bullet 1 ("results recorded in the consult
   trace and reflected into the issue body before spawn"). Check: does
   the directive instruct writing a `validity-consult: <ref>` line (or
   equivalent trace reference) into the drafted body before spawn, and
   does any mechanism verify the reference resolves to an actual
   consult trace (vs. an arbitrary string).

3. **R3 — Gate/check that a drafted issue carries the trace reference or
   an explicit skip reason.** Source: issue body, Direction bullet 2
   ("A gate or directive check that a newly drafted issue carries
   either the validity-consult trace reference or an explicit skip
   reason (trivial/mechanical)"). Check: `gates/requirement_intake_consult.py`
   implements this two-path check; does anything actually invoke it
   against a real drafted issue (mechanical enforcement), or does the
   check exist only as an offline-testable function with no call site.

4. **R4 — Skip path is first-class, no added latency for trivial asks.**
   Source: issue body, Direction bullet 3 ("Must not add turn-blocking
   latency for trivial asks — skip path is first-class"). Check: is the
   skip path (`validity-consult-skip: trivial`) reachable without
   running the consult step, and is the skip vocabulary closed (not
   free-text) so it cannot be used to bypass genuinely risk-bearing
   asks.

5. **R5 — Test coverage: intake-with-consult passes, intake-without
   is flagged.** Source: issue Acceptance bullet 1 verbatim ("New/extended
   cases ... covering: intake with validity consult recorded passes;
   intake without consult and without skip reason is flagged") and the
   literal `check:` command (`python3 -m pytest tests/test_spawn.py -k
   intake`). Check: do `tests/test_spawn.py` and/or
   `gates/test_requirement_intake_consult.py` carry cases for both
   named scenarios, and does the named command run and cover them.

6. **R6 — R001/northpole req#6 (requirements condensed/managed so work
   never drifts).** Source: issue's own requirement linkage line. Check:
   does the delivered mechanism, as actually wired (not just as
   directive prose), reduce drift risk — i.e. does it create a
   verifiable record of feasibility/consistency/ordering judgment at
   intake time, or does it rely entirely on an LLM session choosing to
   follow unenforced directive text.

7. **R7 — northpole req#1 (orchestration from requirements).** Source:
   issue's own requirement linkage line. Check: does the delivered
   change tie the validity-consult step to requirement drafting itself
   (not a separate, disconnected process), consistent with req#1's
   framing of orchestration flowing from requirements.
