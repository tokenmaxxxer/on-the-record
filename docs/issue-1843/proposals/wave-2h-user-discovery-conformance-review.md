---
status: proposed
files:
  - docs/issue-1843/reports/conformance-review.md
---

# Conformance-review proposal — issue-1843 (phase 1)

## Request

Review the phase-2 delivery landed for issue #1843 (procedural-body wave
2h, user-discovery family: 6 skills) against its two acceptance
requirements, and render a per-requirement verdict in
`docs/issue-1843/reports/conformance-review.md`.

## Constraints

- Artifact-only, verify-before-claim: every claim in the phase-2 record
  (`docs/issue-1843/reports/implementation.md`) gets independently
  reproduced against the actual merged `skill-repository` code, not
  accepted from the record's pasted output alone.
- Guidance-only role (per this session's role-source-allowlist mapping):
  no new hooks or enforcement, only a review record.
- Scope is limited to `docs/issue-1843/reports/conformance-review.md`;
  no code or checker changes.

## Rationale

Two candidate review depths were available: (a) trust the phase-2
record's pasted command output as sufficient evidence, since the record
already carries `provenance: executed-live` tags and canonical
citations; or (b) independently re-derive every check from a fresh clone
of the merged `skill-repository` commit. (a) was rejected: the phase-2
record's own pasted output is exactly the artifact under review, not
independent evidence of it — accepting it at face value would make this
review a re-statement of the builder's claims rather than a check on
them. (b) is chosen: this session already re-cloned `skill-repository`
fresh to `/tmp/skill-repo-verify-1843`, re-ran both checker invocations,
re-derived the diff scope and rule-retention sweep by two independent
methods, and additionally ran one check the record did not (an
adversarial test that the checker actually rejects a stripped-heading
skill) — findings are in
`docs/issue-1843/reports/conformance-review/survey.md`.

## What will be done

Render `docs/issue-1843/reports/conformance-review.md` with a
per-requirement verdict for both of issue #1843's acceptance
requirements (Trigger/Procedure/Output-shape sections + derived
descriptions + rule retention, both checkers exit 0; diff-scope
containment to the 6 family paths + manifest), each verdict backed by
this session's own independently-reproduced command output (not the
phase-2 record's pasted output), citing the survey's findings.

## Out of scope

- Re-litigating the phase-1 implementation proposal's design choices
  (recipe reuse, manifest-gated checker approach) — those were approved
  at phase-1 of the implementation role and are not this review's
  target.
- Code-quality judgment (naming, prose style) beyond the two acceptance
  requirements.

## How you'll know it worked

`docs/issue-1843/reports/conformance-review.md` exists with `MEETS` or a
discrepancy verdict for each of the two requirements, each backed by a
`canonical:`-cited, independently-run command whose output this session
captured directly (not copy-pasted from the phase-2 record), matching
the survey already on disk at
`docs/issue-1843/reports/conformance-review/survey.md`.

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

Await approval (`APPROVE issue-1843/conformance-review`, single-account
mode per contract v3 s19). On approval: write
`docs/issue-1843/reports/conformance-review.md` using this proposal's
survey evidence, rendering one verdict per acceptance requirement.

## Resolution path

No open finding requires further resolution before phase 2 — the
survey's verification is already complete; phase 2 is transcription into
the formal verdict record, not further investigation.
