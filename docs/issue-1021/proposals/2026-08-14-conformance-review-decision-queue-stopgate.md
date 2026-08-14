---
status: proposed
files:
  - docs/issue-1021/reports/conformance-review.md
---

## Request

Issue #1021 required `decision-queue-stopgate.sh` to stop producing an
unbounded re-block loop on Stop when decision-queue items age past 4h,
citing R001 / northpole req#4. An implementation commit
(`b908d5a1`, per docs/issue-1021/reports/conformance-review/survey.md)
landed on `main` with no conformance-review record filed against it
yet — this PR's phase 2 will render a per-requirement verdict
(Present|Surface|Absent|Incorrect|Unverifiable) against the artifact
named in that commit's `code_under_review`, worked independently of the
implementation role's stated intent.

## Constraints

- Scout skip: recorded in the survey — pure requirement extraction
  from the issue text, no product-facing design decision to scout.
- Verdicts are per-requirement, never a holistic code-quality judgment,
  and are never a fix — findings addressed_to the implementation role.
- code_under_review in the eventual record must be a file list, never a
  commit sha.

## Rationale

The issue's own Acceptance section already enumerates a check command
and three named test cases, so the requirement list below is a direct
transcription rather than an inferred derivation — no sampling or
judgment call was needed to produce it.

## What will be done (phase 2, gated on Approve)

Requirement list, extracted from issue #1021's body (Problem / Fix
direction / Acceptance sections):

1. R1 — `stop_hook_active=true` on a Stop turn must never yield
   `decision: "block"` from this hook, on any branch the hook contains
   (not just the age-tier branches).
2. R2 — The age>=4h ("tier2") blocking branch fires `decision: "block"`
   at most once per session per queue *content* snapshot: a repeat Stop
   against an unchanged blocking-tier item set must not block again,
   even though `age_hours` itself changes every turn.
3. R3 — The age 1h-4h advisory tier's behavior (trigger condition and
   output shape) is unchanged by this fix.
4. R4 — `on-the-record/hooks/test_decision_queue_stopgate.py` gains the
   three cases named in the issue's Acceptance section:
   `stop_hook_active=true` -> no block; same queue snapshot twice ->
   second Stop not blocked; queue content change -> may block once
   more.
5. R5 — `python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py`
   passes (the issue's stated `check:` command).

Phase 2 will check the artifact at
`on-the-record/hooks/decision-queue-stopgate.sh` and
`on-the-record/hooks/test_decision_queue_stopgate.py` against R1-R5
and record one verdict per requirement in
`docs/issue-1021/reports/conformance-review.md`.

## Out of scope

- Fixing any gap found — findings route to the implementation role.
- Re-litigating the fix's design (e.g. the latch-vs-hash tradeoff
  argued in the implementation proposal) beyond checking it against
  R1-R5 as stated in the issue.

## How you'll know it worked

- Five verdicts (R1-R5), each citing where in the artifact it was
  checked, land in docs/issue-1021/reports/conformance-review.md after
  Approve.
