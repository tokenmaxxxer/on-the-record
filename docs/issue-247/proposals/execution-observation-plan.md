---
kind: proposal
loop_state: proposed
---

# Proposal — issue #247, execution-observation of PR #256

## Verdict levels to be checked, and against what evidence

This is a phase-1 proposal; no verdict is rendered here. Phase 2 will
render this role's three mandated verdict levels:

- **outcome** — whether PR #256 (subject issue-247, merged
  `1d7df88329a97c8d2c4d0928e057a07b65a3dbb2`) closes the gap issue #247's
  body describes (headless delegate-and-wait ending with `subtype:
  success`, `is_error: false`, and no commit), checked against a live
  code read of the shipped `_self_trigger_respawn()` call site on the
  current `origin/main` checkout and the targeted `pytest` re-run already
  captured in `docs/issue-247/reports/execution-observation/survey.md`.
- **trajectory** — whether phase 1 -> phase 2 on PR #256 followed contract
  v3 s19 (survey before proposal, a real approval comment before
  phase-two work started, phase-two output confined to the approved write
  set), checked against `gh issue view 247`'s comment trail and the two
  commit timestamps (`cd48c333`, `9d1394f1`).
- **step** — whether each of the two deviations the implementation record
  discloses (the session-end/self-trigger reordering; `time.time()`
  float-precision) is individually sound, checked against the actual
  `spawn.py` diff and code on the current checkout, not the record's own
  narrative of it.

## Skip record (scout-directive)

Scouting is skipped, for the reason already recorded in this phase's
survey ("Skip record (scout-directive)",
`docs/issue-247/reports/execution-observation/survey.md`): this is the
same "audit an executed change to safety-net code, against its own
implementation record's claims" shape this repo has run on comparable
PRs (#265, #267, #633) — no open design decision here needs an external
category sweep.

## What will be done (phase 2, on approval)

1. Re-read the implementation record's outcome claims
   (`docs/issue-247/reports/implementation.md`) against the current
   `spawn.py` on `origin/main` and the targeted `pytest` result already
   captured this phase, and render the outcome verdict.
2. Read `gh issue view 247`'s full comment trail and the two branch
   commit timestamps to check contract v3 s19's phase-1 -> phase-2 gate
   (approval before phase-2 work), and render the trajectory verdict.
   Includes noting, without treating it as a finding against PR #256, the
   process observation already surfaced in the survey: this
   execution-observation session was itself spawned through
   `spawn_missing_for_pr` on a now-closed issue.
3. Judge each of the two disclosed deviations (reordering;
   `time.time()` precision) against the actual diff — the exact
   before/after code shapes and the regression tests that pin them
   (`SessionEndVerdict`'s two new tests) — and render the step verdict.
4. Search `runs/ledger.jsonl` for any real (non-test) firing of
   `_self_trigger_respawn()` in production use since PR #256 merged, to
   report — not require — whether the mechanism has fired for real yet.
5. Write the verdicts and any findings to
   `docs/issue-247/reports/execution-observation.md`.

## Independence

This role did not author PR #256 (`issue-247/implementation`,
`spawn.py`, `test_spawn.py`, `docs/handbooks/operations.md`, or
`docs/issue-247/proposals/self-triggered-abandoned-work-respawn.md`) and
will not edit any of it. This role's only write is
`docs/issue-247/reports/execution-observation.md` (plus this phase's own
`docs/issue-247/proposals/` and
`docs/issue-247/reports/execution-observation/` files).

## Out of scope

- Re-running the implementation record's own `_spawn_one()` integration
  test as this role's evidence — only the shipped code and independently
  re-run tests count.
- Filing an issue for any finding — contract v3: issues are user-authored
  only; findings return in this role's own record for the human to act
  on.
- Judging whether issue #247 itself should be reopened — that is the
  human's call, already exercised once in the closing comment cited in
  the survey.
