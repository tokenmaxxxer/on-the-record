# Conformance-review proposal — issue-1097 consult verdict-parse fix (phase 1)

## Upstream / basis

Issue #1097. Approved design:
`docs/issue-1097/proposals/consult-verdict-parse-fix.md` (landed PR
#1103). Delivery: `docs/issue-1097/reports/implementation.md` (PR #1104).
Survey: `docs/issue-1097/reports/conformance-review/survey.md`.

## Requirement list (extracted, verdict deferred to phase 2)

1. **R1 — Regression test parses a captured real transcript.** Source:
   issue #1097 Acceptance bullet 1 ("a test in `tests/` or `gates/` runs
   the consult output-parsing path against a captured real transcript and
   asserts the judgment JSON is found"). Check:
   `gates/test_consult_verdict_parsing.py`'s
   `t_parses_captured_real_transcript` exists, uses a transcript captured
   from a real run (not synthesized), and currently passes.

2. **R2 — Live `spawn.py consult` smoke run succeeds end-to-end.** Source:
   issue #1097 Acceptance bullet 1, second clause. Check: the
   implementation report's cited live run and its consult-log.md trace
   are real (not fabricated), and the fix that made it succeed is still
   present and unmodified on `origin/main` today.

3. **R3 — Full regression suite for the fix passes as a whole, today, not
   only at landing time.** Source: issue #1097 Acceptance bullet 1
   (implicit — a fix that regresses after a later unrelated change no
   longer satisfies "asserts the judgment JSON is found" as a durable
   guarantee); the approved proposal's "How you'll know it worked"
   bullet 1 ("gates/test_consult_verdict_parsing.py passes (4/4)").
   Check, already run in survey.md: the standalone script currently fails
   on `t_retries_once_and_recovers_when_first_attempt_has_no_json` against
   `origin/main` HEAD (3rd of 4 cases, AssertionError on call count),
   because issue #1134's later `_commit_consult_trace()` addition adds two
   more `subprocess.run` calls inside the same monkeypatched surface the
   test counts. This is very likely to render **Incorrect** (regressed
   post-landing) rather than Absent or Present — phase 2 confirms.

4. **R4 — Empty-state trace with diagnosable reason.** Source: issue
   #1097 Acceptance bullet 2 ("consult calls that legitimately return no
   verdict still trace to consult-log.md with a diagnosable reason").
   Check: the `finally` block in `consult_cmd()` still writes a trace line
   with the parse-failure excerpt and raw-output path on every no-verdict
   path, unaffected by the #1134 interaction found in R3 (that addition
   only adds commit calls after the trace write, per survey.md's citation
   of spawn.py:4776-4778).

5. **R5 — northpole req#1 fulfilled: consult is a completed, working step
   in orchestration.** Source: `requirement: northpole req#1` (오케스트레이션
   완주 — consult 는 이슈 드래프트의 필수 단계). Check: whether R3's finding
   (regression test now fails) means the *requirement* — not just the
   *script* — is at risk: does a broken `gates/` script block anything
   downstream (CI gate, pre-issue-draft check) that would stall
   orchestration completion, or is it a dangling regression test with no
   live consequence today. Phase 2 traces whether anything invokes
   `gates/test_consult_verdict_parsing.py` as a gate.

## Out of scope (phase 2 will not re-litigate)

- Whether issue #1134's `_commit_consult_trace()` design itself is
  correct — that landed under its own approved proposal and is out of
  this subject's scope; only its *interaction* with issue-1097's test is
  in scope here.
- Code-quality judgment (naming, structure, efficiency) — this role
  renders per-requirement fidelity verdicts only, never a holistic
  quality read.
- Whether the live smoke-run transcript quoted in implementation.md is
  reproducible today (transient model-output nondeterminism is not a
  conformance gap; R2 checks only that the underlying fix is unmodified).

## Method (phase 2, once approved)

Artifact-only review: phase 2 works from `spawn.py`,
`gates/test_consult_verdict_parsing.py`, `tests/test_spawn.py`'s
`ConsultCmd`/`ConsultVerdictParsing` classes, and issue #1097's own text
— the implementation report's `Why`/`What did not work` prose is not read
as evidence for verdicts, only to locate code, consistent with this
role's artifact-only rulebook.

## What did not work

(none yet — phase 1, no verdicts attempted)

## loop_state

kind: proposal
loop_state: scope-proposed

## Open findings

None recorded yet (phase 1 renders no verdicts). R3's live re-run in
survey.md is a strong signal the eventual R3 verdict is Incorrect, but
that judgment is deferred to phase 2 per this role's phase split.

## Next steps

Await approval (`APPROVE issue-1097/conformance-review` per contract v3
s19, single-account mode). On approval: render the phase-2
per-requirement verdicts (R1-R5 above) in
`docs/issue-1097/reports/conformance-review.md`, using
`review-traceability:finding-record` to write one verdict row per
requirement, and `review-severity:severity-classification` for R3 given
its regression-after-landing shape.

## Resolution path

Phase 2 resolves R3/R5 by tracing whether
`gates/test_consult_verdict_parsing.py` is wired into any CI/pre-commit/
pre-issue-draft gate (grep for its path across `.github/`, `gates/`,
`hooks/`) — if wired, R3/R5 verdict is Incorrect with a blocking severity;
if merely a standalone regression script nobody runs automatically, R3 is
still Incorrect but R5 (the northpole requirement) may still verdict
Present, with R3 filed as an open finding addressed to whichever role owns
`gates/test_consult_verdict_parsing.py` and `_commit_consult_trace()`'s
shared surface.
