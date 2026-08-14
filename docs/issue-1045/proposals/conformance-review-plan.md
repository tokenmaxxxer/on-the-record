---
status: proposed
files:
  - docs/issue-1045/reports/conformance-review.md
---

# Conformance review of issue #1045's landed fix (commit 8fe249b5)

## Request

Issue #1045 spawned this conformance-review session because commit
`8fe249b5` (PR #1060, merged, closes #1045) landed on `main` with no
conformance-review record yet on file. The task is to render a per-requirement
verdict (Present/Surface/Absent/Incorrect/Unverifiable) on whether that commit
actually satisfies the two defects' Acceptance text, working from the artifact
(`spawn.py`, `tests/test_spawn.py`) and the spec (issue #1045's own Acceptance
section) — not from the implementation role's own account of what it did.

## Constraints

- Verdicts only; this role never edits `spawn.py`/`tests/test_spawn.py` or
  files a fix itself — any gap found is handed off (addressed_to the owning
  role) in the record, not patched here.
- Working deliberately without the building agent's stated intent: the
  `docs/issue-1045/reports/implementation.md` record is read for context
  (what it claims), but the verdict is derived from the artifact and the
  issue's Acceptance text, not accepted on the implementation record's say-so.
- Record lands only in phase 2 (this proposal must be approved first).

## What will be done

Render a verdict for each of the 5 requirements the survey extracted
(`docs/issue-1045/reports/conformance-review/survey.md`):

- REQ-D2-behavior / REQ-D2-regression: read `_panel_degrade()` and
  `_consult_or_record_error()` in `spawn.py` directly, and the
  `PanelDegradeErrorSafety` test class in `tests/test_spawn.py`, and confirm
  by re-running `python3 -m pytest tests/test_spawn.py -k panel -v` this
  session (not by trusting the implementation record's pasted transcript).
- REQ-D1-fix-or-record: this is the requirement most likely to carry a real
  gap. The phase-1 survey for #1045's own implementation
  (`docs/issue-1045/reports/implementation/survey.md`) explicitly reproduced
  only the bare `ListAgents`/`SendMessage` primitive outside the panel
  prompt, and its own text states "its own effect should be judged against a
  subsequent live `panel_cmd()` run, not assumed from this survey alone."
  The approved proposal's Out of scope section defers that live re-run as "a
  next step, not done here." The phase-2 implementation record
  (`docs/issue-1045/reports/implementation.md`) shows only
  `pytest -k panel -v` (mocked `run_session`, no real `claude -p` process)
  as its acceptance evidence. The verdict here turns on whether that
  mocked-unit-test evidence, plus the phase-1 primitive-only reproduction,
  actually satisfies the issue's explicit disjunction ("a live re-run... or a
  grounded record of why it cannot work") — on its face this looks like
  neither disjunct is closed, but phase 2 will re-read the full artifact and
  both records before finalizing that verdict rather than asserting it here.
- REQ-check: re-run the stated check command and confirm the pasted count in
  the implementation record matches.
- REQ-req5-traceability: read the shipped prompt text in `_run_panel_session()`
  and confirm the live-`SendMessage` path is still primary and the sequential
  `consult_cmd()` degrade is still framed as fallback-only, not swapped.

## Out of scope

- Filing or building the fix for any gap found (hands off to the
  implementation role instead).
- Re-litigating req#5/R001's own wording — those are read as given from
  `docs/specs/northpole.md` and `docs/specs/requirements.md`.

## How you'll know it worked

`docs/issue-1045/reports/conformance-review.md` states a verdict for each of
the 5 requirements in the survey, each backed by a `canonical:`-cited read of
the actual artifact or a re-executed command (not by restating the
implementation record's claims), following review-traceability's
finding-record format.
