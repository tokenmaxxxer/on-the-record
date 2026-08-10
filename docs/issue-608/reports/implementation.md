---
code_under_review:
  - on-the-record/hooks/approval-gate.sh
  - on-the-record/hooks/test_approval_gate.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
type: feature
breaking: false
verdict: pass
loop_state: committing
---

# Issue #608 step 2 — implementation record

## What was done

Added `on-the-record/hooks/approval-gate.sh`, a new `PreToolUse`
(`Write|Edit|MultiEdit`) hook closing the coverage hole step 1's fixture
measurement confirmed: no deployed hook checked phase-2 approval state
for a role session's own writes (its record file, `src/`, `test/`). The
hook no-ops unless `CLAUDE_ROLE` is set, parses `issue-<n>/<role>` off
the branch name, and for a phase-2-shaped target (the acting role's own
`docs/issue-<n>/reports/<role>.md`, or a `src/`/`test(s)/` path) denies
with a refuse-and-instruct message when `docs/specs/approvers.md` is
absent, or denies naming what's missing when present but no matching
`APPROVE issue-<n>/<role>` comment exists from a listed account.
Wired into `on-the-record/hooks/hooks.json`'s existing `Write|Edit|MultiEdit`
`PreToolUse` group. Added `on-the-record/hooks/test_approval_gate.py`
(pytest, subprocess against the real script + a fake `gh` shim) covering
the full matrix: {approvers present, absent} x {approved, unapproved} x
{record path, src path, test path}, plus a phase-1-legal control row
(proposal/survey paths always allowed), an orchestrator-session skip
row, and a `gh`-lookup-failure fail-open row. Added the required
`docs/specs/enforcement-boundary.md` row (verdict `contract`).

## Why

Basis for the fix:
`docs/issue-608/reports/execution-observation/fixture-measurement.md`,
Findings 1-2 (confirmed live): a role session can write its record,
implementation, and tests, and commit them, without ever invoking `gh`
— and therefore without ever reaching either existing approval check
(`contract-guard.sh`, `pr-preflight.sh`), both `Bash`-matcher hooks
gated on `gh pr` verbs only. `deliverable-guard.sh` also fails open
(silent allow) when `approvers.md` is absent, instead of refusing and
instructing, which the issue's acceptance criterion requires be fixed.

## Upstream

Basis: docs/issue-608/proposals/implementation.md

## What did not work

None.

## Rationale for deviations

None — the build matched `## What will be done` in the approved
proposal (`docs/issue-608/proposals/implementation.md`) with no scope
change. One addition beyond the proposal's five numbered steps: an
`## Accumulation` section was added to the proposal itself mid-build
because `accumulation-claim-guard.sh` blocked the test-file write
without it (this repo's own hook, not anticipated in the phase-1
proposal text) — a mechanical requirement satisfied in place, not a
scope or approach change.

## Doc-placement ladder (completed)

- `docs/specs/enforcement-boundary.md` — new `approval-gate.sh` row
  added (verdict `contract`), same commit as the new hook — required in
  the same unit per `gates/test_boundary.py`.
- No new env var, dependency, or migration introduced — nothing else on
  the ladder applies to this unit.

## Test run (fenced, this unit's suite)

```
$ python3 -m pytest on-the-record/hooks/test_approval_gate.py -q
................                                                         [100%]
16 passed in 1.17s
```

Full existing `on-the-record/hooks/` suite, no regression:

```
$ cd on-the-record/hooks && python3 -m pytest . -q
........................................................................ [ 61%]
.............................................                            [100%]
117 passed in 9.38s
```

`gates/test_boundary.py` was also run for the added row's own check; it
has one pre-existing, unrelated failure (`remediation_spawn.py` missing
its own boundary row) not caused by or in this unit's write set — out of
scope, not fixed here:

```
$ python3 -m pytest gates/test_boundary.py -q
F.........                                                               [100%]
1 failed, 9 passed in 0.05s
```

## Hunt

Recorded per warrant directive at after-proposal and before-landing
transitions in `docs/reports/2026-08-10-hunt-implementation.md`
(after-proposal note already present in the approved proposal's own
"Hunt note" section — branch-parse fail-open, accepted, pattern-
consistent with `pr-preflight.sh`/`contract-guard.sh`). Before-landing
hunt dispatched separately per the same directive.

## closed_checks

- full `on-the-record/hooks/` pytest suite (117 passed) —
  code_under_review as listed above.
- new `test_approval_gate.py` fixture matrix (16 passed) —
  code_under_review as listed above.

## Open findings

None.

## Next steps

Commit, push, open PR against main with `Closes #608`.

## Resolution path

N/A — no open finding.
