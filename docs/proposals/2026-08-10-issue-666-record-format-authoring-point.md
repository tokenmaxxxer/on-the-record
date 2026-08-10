---
status: proposed
files:
  - docs/issue-666/reports/architecture/survey.md
  - docs/issue-666/proposals/architecture.md
---

## Intent
Phase-1 architecture proposal for issue #666: today's phase-2 sessions
strand on the last, purely mechanical record-write step (bare sha in
`code_under_review`, unsourced counts, empty `## Accumulation`) because the
correct shape contract lives in this repo's gates/hooks/handbook but is
never surfaced at the point a session starts authoring — that point is
generated in each role's external rulebook repo, out of this checkout's
reach. Survey and ADR trace where the contract already lives and propose
owning it at the one layer this repo controls unconditionally: the shared
`PreToolUse` record-write hook chain, via a new `record-shape-guard.sh`
plus hardened deny messages on the two existing guards.

## Constraints
- This turn only writes the two phase-1 homes
  (`docs/issue-666/reports/architecture/survey.md`,
  `docs/issue-666/proposals/architecture.md`) — no hook code, per
  role-handoff contract v3 s19 (phase 2 is gated on approval).
- No new install/CI dependency; any phase-2 hook must stay zero-install,
  `python3`-only, reusing `gates/record_lint.py` like its siblings.
- Cannot edit the external per-role rulebook repos (out of write scope);
  the proposal must not silently claim to fix the `SessionStart` text
  itself.

## Will do (this turn)
Commit the survey and ADR above, open the phase-1 PR, and stop.

## Out of scope
Any edit to `on-the-record/hooks/*.sh`, `gates/*.py`, or any external
rulebook repo — all deferred to phase 2, pending human Approve.

## Acceptance
Phase-1 PR opens with these two files; a human approver's Approve (per
`docs/specs/approvers.md`) is what opens phase 2.
