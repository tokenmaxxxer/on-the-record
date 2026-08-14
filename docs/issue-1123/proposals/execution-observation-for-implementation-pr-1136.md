---
status: proposed
files:
  - docs/issue-1123/reports/execution-observation.md
---

# Proposal: execution-observation record for implementation PR #1136 (issue #1123)

## Intent

Issue #1123's board condition fired: an executable artifact landed on
`issue-1123/implementation` (PR #1136, merged) and no
`execution-observation` record exists yet for that commit sha. This
proposal scopes the phase-2 record that will judge whether that landing
was sound, per `roles/specs/execution-observation.spec.json`.

## Constraints

- Independence: this role never authored or edited the observed
  artifact; the record cites only PR #1136's diff/commits and the
  observed role's own record (`docs/issue-1123/reports/implementation.md`),
  never re-executes `gates/test_consult_json_parse.py` or the live consult
  path itself.
- Every verdict-bearing sentence must carry an adjacent citation (commit
  sha, file:line, or PR comment URL), per this role's directive.
- Test-claim entries whose only source is the observed role's own record
  (e.g. its stated 5/5 test-suite result) are `mode: asserted` and can
  only support `cantTell`/`untested`, never `passed`/`failed`, since this
  role does not re-run them.

## What will be checked

All three verdict levels, named here before any verdict language appears:

- **outcome** — the spec's worst-case recomputation rule applied across
  the step-level `result` entries this record cites (never a standalone
  summary), checked against issue #1123's three named requirements
  (persist raw output on parse failure; extend
  `gates/test_consult_json_parse.py` with both live-recurrence shapes;
  live-smoke a multi-part question) as evidenced by PR #1136's diff
  (`spawn.py`, `gates/test_consult_json_parse.py`,
  `docs/reports/consult-log.md`) and the observed role's own record.
- **trajectory** — three named checks, each pass/fail/not-applicable:
  scouted-when-required (was research done before the phase-1 proposal —
  checked against PR #1126's survey/hunt-record/proposal files),
  surveyed-before-proposing (did PR #1126's scope statement precede any
  proposal-shaped language), approved-by-human (a real `APPROVE` string
  match on both PR #1126 and PR #1136, not an inferred one — checked
  against the two `APPROVE issue-1123/implementation` issue comments).
- **step** — any specific artifact found deficient, each finding stating
  subject/test/result/assertedBy per the spec's EARL vocabulary. One
  candidate already surfaced by the observed role's own record: its
  `resolved_findings` section documents a warrant-hunter finding (unquoted
  raw-output path defeating `record_lint.py`'s untracked-path guard) and
  claims it was fixed — this record will independently verify that claim
  against the actual diff hunk (`spawn.py`'s `attempts_exhausted`
  f-string), not merely restate the observed role's own resolution claim.

## Out of scope

- Re-running `gates/test_consult_json_parse.py` or the live consult path
  — prohibited for this role; the record instead marks those claims
  `mode: asserted`.
- Judging issue #1123's underlying root-cause hypothesis (timeout vs.
  parser vs. retry budget) — that is the `implementation` role's
  substantive scope, not this role's; this role judges whether the
  landed work matches what the issue asked for and whether the
  phase-1→phase-2 path was sound.
- Editing anything under `docs/issue-1123/reports/implementation.md` or
  any other `implementation`-role path.

## How this will be known to have worked

The phase-2 record at `docs/issue-1123/reports/execution-observation.md`
exists, states its independence statement before any verdict language,
addresses all three verdict levels (with "not applicable, because X" for
any that do not apply), cites a source adjacent to every verdict
sentence, and is committed on `issue-1123/execution-observation` with
`loop_state: handed-off`.
