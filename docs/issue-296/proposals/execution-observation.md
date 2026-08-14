---
status: proposed
files:
  - docs/issue-296/proposals/execution-observation.md
  - docs/issue-296/reports/execution-observation.md
---

# Proposal — issue #296: execution-observation

Phase 1 only, per role-handoff contract v3 s19. No verdict language below —
verdict levels (outcome/trajectory/step) are named here as what phase 2 will
check, not decided.

## Intent

Observe PR #297 (`issue-296: move TTL pull marker out of the managed
clone`, merged `2026-08-07T01:34:30Z` as `11e459e6`) against issue #296's
four Acceptance clauses, and produce the execution-observation record that
does not yet exist for this commit sha
(`roles/specs/execution-observation.spec.json`'s `use_when` condition).

## Constraints

- Never re-execute or edit `spawn.py`, `tests/test_spawn.py`, or
  implementation's own docs paths (`docs/issue-296/reports/implementation.md`,
  `docs/reports/2026-08-07-hunt-issue-296.md`) — read-only evidence.
- Every verdict-bearing sentence in phase 2 must cite a commit sha, file:line,
  or a command actually run this session.
- If a clause cannot be checked against a real artifact in this working tree
  (e.g. no live managed clone exists to run `spawn.py` against end-to-end),
  say so explicitly rather than asserting it was checked.

## What will be done (phase 2, once approved)

Write `docs/issue-296/reports/execution-observation.md` addressing all three
verdict levels against issue #296's four Acceptance clauses:

- **outcome**: whether each Acceptance clause (empty `git status
  --porcelain` on a clean clone, no dirty suffix on clean/dirty distinction
  preserved, `bench/run.py` passes its provenance check, a pinning test
  exists) holds against the current `spawn.py` / `tests/test_spawn.py`.
- **trajectory**: whether implementation's pure-bugfix skip
  (`docs/issue-296/reports/implementation.md`, "Skip record") was a sound
  invocation of contract v3 s19, evidenced from the issue body and PR #297's
  commit.
- **step**: per-artifact result (`_ttl_marker`, `_mark_pulled`, the three
  dirty-suffix computation sites, `bench/run.py`'s check, the pinning test),
  each tied to a command run this session or a specific file:line read.

## Out of scope

- Re-running the full `tests/` suite beyond the TTL-marker-specific tests.
- Standing up a live managed clone (`runs/rulebooks/tokenmaxxxer-core`) to
  exercise `core_version()`/`rulebook_version()` end-to-end — noted as an
  `untested` step-level gap if it cannot be closed within this session.
- Filing an issue for any deficiency found — findings go into this role's
  own record only.

## How this will be verified

Phase 2 is complete when `docs/issue-296/reports/execution-observation.md`
is committed on this branch with the independence statement preceding all
verdict language, all three verdict levels addressed, and every claim
backed by a cited command output or file:line.
