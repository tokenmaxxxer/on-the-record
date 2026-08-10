---
code_under_review:
  - docs/issue-651/reports/implementation.md
type: fix
breaking: false
verdict: blocked
loop_state: commit-unreachable
---

# Issue #651 — Implementation record

## What was done

The delivery phase opened on `APPROVE issue-651/implementation` (issue
comment, single-account mode). Re-verified the phase-one survey's
cross-repo finding before attempting any edit:

- derived: `ls -la /home/jwjung/tokenmaxxxer-core/core/hooks/board-gate.sh`
  → file exists, readable, executable.
- derived: `echo test > /home/jwjung/tokenmaxxxer-core/.write-test-651`
  → `읽기전용 파일 시스템` (read-only filesystem) — write refused by the
  sandbox, not by file permissions.

The target file `core/hooks/board-gate.sh` and its test harness
`core/hooks/tests/run-board-gate-tests.sh` live in the separate
`tokenmaxxxer/tokenmaxxxer-core` repository, mounted read-only into this
sandbox. This session's write scope is `tokenmaxxxer/on-the-record`,
branch `issue-651/implementation`, which cannot reach those paths no
matter how the edit is expressed — this is the same blocker issue-40's
coding record already documented, confirmed independently here rather
than assumed from the survey's citation of it.

No code change could be attempted against the frozen write set's actual
target (`core/hooks/board-gate.sh`) from this session. The approved
proposal's own closing item anticipated this outcome and scoped this
session's delivery to recording the blocker plainly, which is this
record.

## What did not work

- Attempted a write test into `/home/jwjung/tokenmaxxxer-core/` to confirm
  the survey's read-only claim still held for this session: expected
  either a permission-denied (ownership) or a successful write; actual
  result was a read-only-filesystem error at the mount level, confirming
  the sandbox itself blocks writes into that tree regardless of the
  target file's own permission bits.

## Rationale

Approved approach unchanged from the proposal (root-check only
resolvable absolute-path candidates in `board-gate.sh`'s hit-building
loop; leave relative-token handling untouched). No alternative approach
was substituted — the blocker is one of write-access scope, not of
design.

## Rationale for deviations

The approved proposal's `## What will be done` lists steps that include
the actual edit to `core/hooks/board-gate.sh` and its test harness. This
session executed only the closing step (record the blocker plainly) —
the edit steps target `core/hooks/board-gate.sh` and
`core/hooks/tests/run-board-gate-tests.sh`, both in the separate
`tokenmaxxxer/tokenmaxxxer-core` repository, which this session's
sandbox mounts read-only (confirmed above under `## What did not
work`). This is not a substituted alternative — no other approach was
tried or considered — it is the proposal's own anticipated blocker (its
Constraints section named this possibility in advance) materializing
exactly as predicted. The unexecuted edit design stands unrejected,
pending a session with actual write scope on that repo.

## Upstream basis

- docs/issue-651/proposals/2026-08-10-board-gate-resolved-write-targets.md
- docs/issue-651/reports/implementation/survey.md

## Open findings

None raised in this session. The confirmed fix design (root-check
absolute candidates against `root_of()` before accepting a docs-relative
hit; leave relative-token substring handling as-is) remains available in
the proposal above for whichever session gets write scope on
`tokenmaxxxer/tokenmaxxxer-core`.

## Next steps

A session opened directly against `tokenmaxxxer/tokenmaxxxer-core`, with
its own issue/branch/PR in that repo, must:
- apply the `## What will be done` steps from the linked proposal to
  `core/hooks/board-gate.sh`;
- add the regression scenarios (absolute out-of-repo docs-shaped path
  allowed; foreign-record write still refused; mention-only text still
  allowed) to `core/hooks/tests/run-board-gate-tests.sh`;
- run that suite and confirm the red/green pair issue #651's acceptance
  criterion names, both directions.

## Resolution path

Hand this issue's remaining work off to a session scoped to the
`tokenmaxxxer/tokenmaxxxer-core` repository directly — this
`on-the-record`-scoped session structurally cannot write there, per
`## What did not work` above and issue-40's precedent.

## Doctrine placement

- No env var, config key, dependency, migration, or setup step introduced
  — nothing routes to a handbook.
- No library/format choice or changed public signature — no decision
  record needed.
- No benchmark/investigation numbers produced — nothing routes beyond
  this record itself.

## Hunt

No hunter dispatched this session: no code changed in this repo, so
there is no diff for a hunter to probe. The docs-only fast path does not
apply either, since it presumes a landing diff exists — here the landing
itself did not occur.
