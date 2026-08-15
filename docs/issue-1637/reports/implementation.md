---
code_under_review:
  - docs/issue-85/reports/coding.md
type: fix
breaking: false
verdict: blocked
loop_state: scope-undeclared
---

# Issue #1637 — Implementation Record

## What was done

Attempted the single cross-issue Edit issue #1637 requires: fix the broken
citation at `docs/issue-85/reports/coding.md:12` from the non-existent path
```
docs/issue-85/reports/current-state-survey.md
```
to
`docs/issue-85/reports/coding/current-state-survey.md`, using the plain
Edit tool directly (no heredoc/python -c/tee), from this issue's own branch
(issue-1637/implementation), invoking the R4 maintenance-targets exception
declared in the issue #1637 body (`maintenance-targets: docs/issue-85/`).

The Edit call was refused by the repo's `board-gate.sh` PreToolUse hook
before any write occurred:

```
board-gate: docs/issue-85/reports/coding.md belongs to another role. implementation writes only implementation.md, implementation/** — never a foreign record. (contract v3 s11)
```

canonical: PreToolUse:Edit hook error returned verbatim by
`${CLAUDE_PLUGIN_ROOT}/hooks/board-gate.sh` on the direct Edit attempt this
session.

No workaround was attempted, per issue #1637's explicit instruction to stop
and report the denial verbatim rather than route around the gate.

## Why

Issue #1637 requires performing the fix "directly ... from your own
issue-1637/implementation branch" and explicitly forbids any indirect-write
workaround if the gate denies the plain Edit. The gate denied it citing
contract v3 s11 (a role writes only its own record file), which the issue's
R4 maintenance-targets exception language did not override at the
mechanical-gate level.

## Upstream basis

- Issue #1637 (this issue).
- Target line: docs/issue-85/reports/coding.md:12, on branch
  issue-1637/implementation at commit_sha 44b912f1 (`main` at session
  start).

## What did not work

- Direct `Edit` on `docs/issue-85/reports/coding.md` — expected: the R4
  maintenance-targets allow would let this issue's session write outside
  its own record; actual: `board-gate.sh` refused the write unconditionally
  for any path outside `implementation.md`/`implementation/**`, citing
  contract v3 s11, with no observed carve-out for maintenance-targets.

## Open findings

- The board gate (`board-gate.sh`) appears to have no maintenance-targets
  carve-out for cross-role writes, even though issue #1637's body declares
  one. Either the gate needs a maintenance-targets exception implemented,
  or the issue's requested approach (direct cross-issue Edit from a role
  session) is not actually permitted under the current gate and the fix
  must be delivered a different way (e.g., by whichever role/session owns
  `docs/issue-85/reports/coding.md`, or via an explicit gate-bypass
  mechanism this session does not have).

next steps: a human or the record's owning role (or a gate change) must
resolve which of the two above is correct before this fix can land.

resolution path: file/escalate to the maintainers of `board-gate.sh` (or
the issue author) to either add the maintenance-targets carve-out to the
gate, or reassign the fix to the record's owning role.
