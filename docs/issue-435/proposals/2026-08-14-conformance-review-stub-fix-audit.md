---
status: proposed
files:
  - docs/issue-435/reports/conformance-review/survey.md
  - docs/issue-435/proposals/2026-08-14-conformance-review-stub-fix-audit.md
  - docs/issue-435/reports/conformance-review.md
---

## Intent

Conformance-review issue #435's own landed implementation (13
`gates/test_closes_gate_ci.py` stub fixes, the new
`shape_contracts.assert_stub_return_shape` check, and the
`docs/handbooks/operations.md` no-`--ignore=gates` default) against
that implementation record's own falsifiable claims: re-run and
re-read rather than trust the record's narration, per this role's job
of rendering per-claim verdicts against a spec.

## Constraints

- Evidence must be repo actuals re-run this session, not a restatement
  of `docs/issue-435/reports/implementation.md`'s own transcripts.
- No fixes performed here; any open finding routes to its own issue,
  not edited inline.

## What was done

Re-ran every `derived:`/`canonical:` command the implementation record
cites and re-read every file/line it names. Result at
`docs/issue-435/reports/conformance-review/survey.md`: all 6 in-scope
claims reproduce as Present, one (the full-suite `495 passed` figure)
is Unverifiable — not because it is wrong, but because this session's
own full-suite runs did not finish under heavy host contention
(10+ concurrent `pytest` invocations from other sessions observed via
`ps aux`), while the narrower file-scoped run covering the actual
`code_under_review` returned clean in under a second. One off-topic
failure (`gates/test_closure_sweep.py::MainExitCode`) was encountered
while this session briefly investigated the wrong subject
(issue-1360's `spawn_on_pr.py`, before recognizing issue #435 was the
actual target from the literal task string) and confirmed pre-existing
on commit af3dd121 — out of this review's `code_under_review` scope,
not filed as a new finding.

## Out of scope

- Re-running the full suite to completion on an uncontended host —
  left as the resolution path for Claim 6, not performed here.
- Any fix to `gates/closure_sweep.py`'s unmocked rate-limit pre-check —
  that is a different subject's pre-existing gap, out of this issue's
  `code_under_review`.

## How you'll know it worked

`docs/issue-435/reports/conformance-review.md` exists (phase 2),
states a Present/Incorrect/Unverifiable-shaped verdict for each claim
against the implementation record, and carries forward Claim 6's
open resolution path (re-run `python3 -m pytest -q` on an uncontended
host) without treating it as a defect.

## What did not work

This session initially investigated issue #1360's `spawn_on_pr.py`
changes as the review subject, misled by a spawn-template task string
whose shape matched issue #1360's own template text; caught and
discarded before any conformance-review content was written for the
wrong subject — logged in
`docs/issue-435/reports/conformance-review/survey.md`'s own "What did
not work" section.
