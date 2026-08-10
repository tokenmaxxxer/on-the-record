status: proposed
files:
  - docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md
  - docs/issue-587/reports/execution-observation.md

## Request

Step 3 of #587: run the end-to-end judgment-loop verification against a DISPOSABLE FIXTURE
TARGET REPO per the architecture already approved in PR #589. Construct the fixture, drive one
full cycle — issue -> judged PR -> per-role verdict records -> synthesized rejection with a
finding -> remediation record -> gates/remediation_spawn.py generates the task -> (simulated)
remediation PR -> re-judgment -> closure — and verify all five issue-timeline firing events and
the in-place PR comments land on the git surface. Independent execution only: run the shipped
code (on-the-record/hooks/delegated-judgment-gate.sh, gates/remediation_spawn.py) as-is; do not
accept prior records' claims about what it does.

## Verdict levels this step checks, and against what evidence

Per this role's phase-2 contract (execution-observation spec), all three levels will be
addressed in the eventual record:

- outcome — did the shipped code (delegated-judgment-gate.sh + remediation_spawn.py, as merged
  in PR #595) actually fire all five #573 §12 timeline events and produce in-place PR comments,
  checked against the fenced output this step captures by driving the fixture repo directly —
  never against PR #595's own claims.
- trajectory — was #587's phase-1-to-phase-2 path sound for steps 1-2 (did architecture survey
  before proposing, did implementation get real APPROVE before building), checked against the
  PR #589/#592/#595 records and the `APPROVE issue-587/architecture` /
  `APPROVE issue-587/implementation` issue comments already read this session.
- step — which specific artifact, if any, is deficient (e.g. a timeline event that does not
  fire, an idempotency check that misfires, a comment that never lands), checked per-event
  against the fixture repo's actual git/GitHub state after each drive step.

## Constraints

- Fixture repo only — never this repo's own board (architecture's explicit boundary).
- No edits to gates/remediation_spawn.py, on-the-record/hooks/delegated-judgment-gate.sh, or any
  other observed-role src/ path — independence per this role's directive; a confirmed deficiency
  goes into this role's own record as a finding, not a fix applied here.
- Effect absent or any of the five events missing -> the record recommends a remediation round,
  not closure; it does not paper over a gap to reach a clean verdict.

## What will be done

1. Build the fixture target repo: a fresh temp-dir git repo with a minimal roles/*.json pair (one
   role owning the judged axis, one owning the file the rejecting finding names) and an
   approvers.md, per architecture's scenario design section 4.
2. Drive step 1-2 of the scenario: open a candidate PR, run delegated-judgment-gate.sh against it
   to a reject verdict with a routable finding; capture whether timeline events 1-2 fire.
3. Drive step 3: run gates/remediation_spawn.py against the resulting remediation-1.md and
   confirm it returns exactly one task derived from that record's fields (never free-authored);
   capture whether timeline event 3 (routed) and its comment fire.
4. Drive step 4: simulate the remediation PR (a fix commit satisfying the finding) and merge it;
   capture whether timeline event 4 fires via the existing merge-detection path.
5. Drive step 5 twice: once re-running the gate on the original candidate to confirm closure, and
   once as a separate fixture path driving 4 rejection rounds to confirm status: escalated fires
   timeline event 5.
6. Record the fenced end-to-end output and an explicit per-event fired/not-fired table in the
   phase-2 files listed above; state a recommendation (close, or remediation round) based on
   what actually fired, not what the design intended.

## Rationale

Architecture PR #589 (`APPROVE issue-587/architecture`) already fixed the scenario's shape; this
proposal does not re-decide it. The one call this proposal makes that architecture left open is
sequencing: run all five steps in one continuous fixture-repo session (steps 2-5 share one
fixture) plus a second, separate fixture for the 4-round escalation path, since escalation and
the primary happy-path closure are mutually exclusive outcomes for a single candidate PR and
cannot both be observed on one candidate.

## What did not work

- After-proposal hunt (stance 4, docs/reports/2026-08-10-hunt-issue-587-execution-observation.md)
  found the declared write set named only the two report paths, with no location for the
  fixture repo or a driver script phase 2 will actually create. Resolved by declaring it here:
  the fixture repo lives entirely under the session scratchpad
  (/tmp/claude-*/.../scratchpad, per this session's scratchpad-directory instruction), never
  under a tracked docs/issue-587 path, and is torn down after the run — matching architecture's
  "created fresh under a temp dir per test run, torn down after" design. Any driver script used
  to construct/drive the fixture also lives in that scratchpad, not in gates/ or another tracked
  path, since it is a one-shot harness for this record, not new shipped code. Nothing outside
  the two declared report paths is committed to the repository by phase 2.

## Hand-off

Phase 2 (the actual fixture construction, drive, and record) opens only on
`APPROVE issue-587/execution-observation` per contract v3 s19 — this session is headless and
single-shot, so that approval cannot land in the same turn as this proposal. This proposal and
its survey are committed and pushed as this turn's complete phase-1 deliverable.
