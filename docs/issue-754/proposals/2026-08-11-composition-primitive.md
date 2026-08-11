---
status: proposed
files:
  - docs/issue-754/reports/architecture.md
---

## Intent

Audit (read-only) how a surfaced defect gets turned into a resolution
today, whether a role can compose that resolution itself, and what
primitive is missing — then classify each sub-area MET/PARTIAL/GAP with
ranked, repo-owned proposed fixes. This proposal covers only the
phase-1 homes (this file + the survey); the classification record
itself is phase-2 output per role-handoff contract v3 s19 and is
written only after approval.

## Constraints

- Read-only: no code or gate changes this pass (issue #754 acceptance:
  `provenance: read`).
- Write scope limited to `docs/issue-754/**` (this session's own
  `architecture` role directive and the warrant directive both pin it
  there).
- Never `gh pr merge`.
- Classification must cite file:line evidence and name, per
  PARTIAL/GAP row: the concrete missing mechanism, the repo it belongs
  in, and a rank by northpole-centrality and observed-failure-frequency
  (issue #754 acceptance criteria, verbatim).

## What will be done (phase 2, on approval)

Using the current-state survey (`docs/issue-754/reports/architecture/survey.md`)
as the evidence base, write
`docs/issue-754/reports/architecture.md` classifying each of the
survey's sub-areas MET/PARTIAL/GAP:

- issue authorship automation
- role→role work composition (vs. opinion-only consult)
- step-to-step auto-progression
- crash/stall retry vs. defect-driven re-composition
- merge automation
- a recorded, reusable "resolution recipe" primitive

Each PARTIAL/GAP row will name: the concrete missing mechanism: which
repo it belongs in — `on-the-record` (role/consult/spawn primitives) vs.
this repo's own `spawn.py`/`gates/` (enforcement) — and a rank
combining northpole req #5 centrality with how often the survey found
this exact gap already causing the orchestrator to do the step by hand
(2026-08-11's issue-745/issue-741 cycles as the observed instance).

## Out of scope

- Building the missing primitive itself (that is a future
  `implementation`-role issue, once this audit's proposed change is
  approved separately).
- Any change to `spawn.py`, `gates/`, or role rulebooks — this issue is
  read-only.
- Re-litigating whether "자동 진행 없음" (no auto-progression) is a
  good design choice — the survey records it as a deliberate decision;
  the classification will judge only whether a role-composable
  alternative exists for the sub-cases northpole req #5 actually
  wants automated (research + discuss a fix), not whether human
  merge-gating itself should go away.

## How it will be verified

The written record passes `gates/record_lint.py` (no bare counts
without `derived:`, no orphaned backtick paths, every claim traceable),
carries the required record fields (what/why/upstream/kind/loop_state/
open findings), and every PARTIAL/GAP row is checkable against the
survey's cited file:line evidence by a reader with no other context.

## Hunt record

after-proposal: docs-only, no before-landing dispatch — every path
touched by this transition is under `docs/`, so the after-proposal
warrant-hunter dispatch is skipped per the docs-only fast path.

## What did not work

- First survey draft cited `path:line` inside a single backtick span
  (e.g. `` `spawn.py:3556-3620` ``) — `record-claim-guard.sh`'s
  orphaned-path-reference check (issue #330 mirror) treats the whole
  backtick span as a literal path and refuses it because
  `spawn.py:3556-3620` does not exist on disk. Fixed by moving the line
  number outside the backticks (`` `spawn.py`, line 3556 ``) so the
  backtick span alone resolves.
