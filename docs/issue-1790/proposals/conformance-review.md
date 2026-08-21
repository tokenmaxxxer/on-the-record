---
status: proposed
files:
  - docs/issue-1790/reports/conformance-review.md
---

# Conformance-review proposal — issue-1790 (phase 1)

## Request

Review the phase-2 delivery landed for issue #1790 (skill procedural-body
authoring pilot wave: 9 skills, checker extension, wave recipe) against
its two acceptance requirements, and render a per-requirement verdict in
`docs/issue-1790/reports/conformance-review.md`.

## Constraints

- Artifact-only, verify-before-claim: every claim in the phase-2 record
  (`docs/issue-1790/reports/implementation.md`) gets independently
  reproduced against the actual merged `skill-repository` code, not
  accepted from the record's pasted output alone.
- Guidance-only role (per this session's role-source-allowlist mapping):
  no new hooks or enforcement, only a review record.
- Scope is limited to `docs/issue-1790/reports/conformance-review.md`;
  no code or checker changes.

## Rationale

Two candidate review depths were available: (a) trust the phase-2
record's pasted command output as sufficient evidence, since the record
already carries `provenance: executed-live` tags and canonical
citations; or (b) independently re-derive every check from a fresh clone
of the merged `skill-repository` commit. (a) was rejected: a phase-2
record's own pasted output is exactly the artifact under review, not
independent evidence of it — accepting it at face value would make this
review a re-statement of the builder's claims rather than a check on
them, defeating the point of a separate conformance-review role. (b) is
chosen: this session already re-cloned `skill-repository` fresh, re-ran
both checker invocations, re-derived the diff scope, and additionally
ran one check the record did not (an adversarial test that the checker
actually rejects a stripped-heading skill) — findings are in
`docs/issue-1790/reports/conformance-review/survey.md`.

## What will be done

Render `docs/issue-1790/reports/conformance-review.md` with a
per-requirement verdict for both of issue #1790's acceptance
requirements (trigger/procedure/output sections + rule retention;
diff-scope containment + full-tree checker), each verdict backed by this
session's own independently-reproduced command output (not the phase-2
record's pasted output), citing the survey's findings.

## Out of scope

- Re-litigating the phase-1 proposal's design choices (manifest-gated
  checker approach, section placement) — those were approved at
  phase-1 of the implementation role and are not this review's target.
- Reviewing the WAVE RECIPE's proposed partition for follow-up waves as
  a design decision — noted as present, not re-derived, since it is a
  forward-looking recommendation with no acceptance check attached to
  it in issue #1790.
- Code-quality judgment (naming, prose style) beyond the two acceptance
  requirements.

## How you'll know it worked

`docs/issue-1790/reports/conformance-review.md` exists with `MEETS` or
a discrepancy verdict for each of the two requirements, each backed by a
`canonical:`-cited, independently-run command whose output this session
captured directly (not copy-pasted from the phase-2 record), matching
the survey already on disk at
`docs/issue-1790/reports/conformance-review/survey.md`.

## loop_state

kind: proposal
loop_state: scope-proposed

## What did not work

(none yet — phase 1, no verdicts attempted)

## Open findings

None at phase 1. The survey found no discrepancy between the phase-2
record's claims and this session's independent reproduction of every
cited check; phase 2 will restate that finding as formal per-requirement
verdicts.

## Next steps

Await approval (`APPROVE issue-1790/conformance-review`, single-account
mode per contract v3 s19). On approval: write
`docs/issue-1790/reports/conformance-review.md` using this proposal's
survey evidence, rendering one verdict per acceptance requirement.

## Resolution path

No open finding requires further resolution before phase 2 — the survey's
verification is already complete; phase 2 is transcription into the
formal verdict record, not further investigation.
