---
status: proposed
files:
  - gates/design_research_consult.py
  - gates/test_design_research_consult.py
---

# Proposal — design-research consult gate (issue-1653)

Skip condition invoked: spec leaves no design decision open (see
docs/issue-1653/reports/implementation/survey.md). The issue body
prescribes the exact module shape ("mirror `requirement_intake_consult.py`
exactly") and exact tag vocabulary, so this proposal documents the mirror
rather than choosing among design alternatives.

## Request
Build a gate module, `gates/design_research_consult.py`, requiring a
design-bearing issue's body to carry either a `design-research: <ref>`
trace tag or the closed-vocabulary `design-research-skip: mechanical`
skip tag — structurally mirroring the existing `requirement_intake_consult.py`
(issue-1024) gate. Ship red+green unit tests. Module + tests only — no
wiring into spawn.py or hooks (deferred, to avoid colliding with #1652's
spawn.py change).

## Constraints
- Pure `check_issue_body(issue, body) -> list[str]`: no network, no `gh`
  call, unit-testable in isolation.
- `check(root, issue)` wraps it with `gh_rest.fetch_issue_body`, same as
  #1024's gate.
- Closed vocabulary for the skip tag: only the literal `mechanical` is
  accepted — no arbitrary skip reason string.
- No changes to spawn.py, hooks, or any other gate's wiring in this issue.

## Rationale
Considered: writing a fresh, differently-shaped module (e.g. a class-based
checker, or folding this into `requirement_intake_consult.py` as an
additional tag pair) instead of a structural mirror. Rejected because the
issue body explicitly requires "mirror `requirement_intake_consult.py`
exactly" — introducing a different shape would fragment the gate family's
conventions (regex-pair + pure check_issue_body + gh-wrapped check) that
downstream tooling (spawn.py's gate registration, future wiring issues)
already expects to find repeated per gate, and would cost a second design
review with no benefit over reusing the proven, already-hunted shape from
#1024.

## What will be done
- Add `gates/design_research_consult.py`: `_RESEARCH_REF` /
  `_RESEARCH_SKIP` regex pair (`design-research:` / `design-research-skip:
  mechanical`), `check_issue_body`, `check`, `main`.
- Add `gates/test_design_research_consult.py`: four unit tests mirroring
  `test_requirement_intake_consult.py` — trace passes, skip-mechanical
  passes, neither present fails, arbitrary skip reason fails.
- Run the new test file directly (`python3 gates/test_design_research_consult.py`)
  and confirm all cases pass before opening the PR.

## Out of scope
- Wiring this gate into spawn.py or any hook path (follow-up issue).
- The effectiveness-verification trace's *truth* (presence-only, per
  #310's acceptance_gate discipline) — this gate checks tag presence,
  not content correctness.
- Any change to `requirement_intake_consult.py` or `gh_rest.py`.

## How you'll know it worked
- `python3 gates/test_design_research_consult.py` exits 0 with all four
  cases printed `ok`.
- The module has no import-time network calls (verified by reading — it
  imports `gh_rest` but only calls `fetch_issue_body` inside `check()`,
  never at module load).
