---
status: proposed
files:
  - docs/issue-310/proposals/execution-observation.md
  - docs/issue-310/reports/execution-observation.md
---

# Proposal — issue #310: execution-observation

Phase 1 only, per role-handoff contract v3 s19. No verdict language below —
verdict levels (outcome/trajectory/step) are named here as what phase 2 will
check, not decided.

## Intent

Observe PR #311 (`issue-310: phase 1 — survey + proposal for a mechanical
discharge gate`, merged `2026-08-07T07:52:54Z` as `5669510c`, commits
`766d192f` phase 1 and `e90e079c` phase 2) against issue #310's own
Acceptance section (the four bullets: the contract names the four
non-discharges, closing an issue with a prose-only Acceptance section
fails a check or states `unverifiable:` and why, a stated requirement is
traceable issue → artifact, and #310's own acceptance satisfies the rule
it establishes) — no observation record exists yet for this commit sha.

## Constraints

- Never re-execute or edit `gates/acceptance_gate.py`,
  `gates/pr_reference.py`, `gates/test_acceptance_gate.py`, or
  `on-the-record/commands/run.md` as production code this session — read
  and, where a unit-test command is being reproduced for evidence, run
  read-only (`python3 gates/test_acceptance_gate.py`, `pytest -k
  pr_reference`), never edited.
- Every verdict-bearing sentence in phase 2 must cite a commit sha,
  file:line, or a command actually run this session.
- Implementation's own record already flagged a self-application gap
  (`docs/issue-310/reports/implementation.md`, "Open findings": issue
  #310's real GitHub issue body, at merge time, was prose-only in its
  Acceptance section and would have been blocked by its own gate).
  Phase 2 must check the *current* state of issue #310's body against
  `acceptance_gate.check_issue_body`, not assume the flagged gap is
  still open or was resolved, since the human may have edited the issue
  body after the PR merged.

## What will be done (phase 2, once approved)

Write `docs/issue-310/reports/execution-observation.md` addressing all
three verdict levels against issue #310's four Acceptance bullets:

- **outcome**: whether `gates/acceptance_gate.py::check_issue_body`
  exists, is wired into `gates/pr_reference.py`'s phase-2 `check()` on a
  matched closing keyword, and whether issue #310's own current body
  (re-fetched via `gh issue view 310`) passes or fails it — resolving
  the self-application gap implementation's own record left open rather
  than restating it.
- **trajectory**: whether the phase-1→phase-2 split (survey/proposal
  commit `766d192f`, then implementation commit `e90e079c`) followed the
  approved proposal at `docs/issue-310/proposals/2026-08-07-discharge-gate.md`
  without scope drift.
- **step**: per-artifact result — `acceptance_gate.py`'s
  `_ARTIFACT_REF` regex and CLI entry point, the `pr_reference.py`
  splice point, the 8 `test_acceptance_gate.py` unit tests (re-run, not
  just read), and the `on-the-record/commands/run.md` contract-text
  addition — each tied to a command run this session or a specific
  file:line read.

## Out of scope

- Editing issue #310's GitHub issue body — user-authored, outside any
  role's write set per contract v3.
- Re-running the full `test_gates.py` suite beyond the
  `acceptance_gate`/`pr_reference`-scoped tests already exercised by
  implementation's own record.
- Filing an issue for any deficiency found — findings go into this
  role's own record only.

## How this will be verified

Phase 2 is complete when `docs/issue-310/reports/execution-observation.md`
is committed on this branch with the independence statement preceding
all verdict language, all three verdict levels addressed, and every
claim backed by a cited command output or file:line.
