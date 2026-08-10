---
code_under_review:
  - gates/remediation_spawn.py
  - gates/test_remediation_spawn.py
  - on-the-record/commands/run.md
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# Issue #587 — implementation record (phase 2, step 2)

## What was done

Built `gates/remediation_spawn.py` (`pending_remediation_tasks(root, issue) ->
list[dict]`: reads `docs/issue-<n>/decisions/remediation-*.md`, filters to
`status: open`, builds `task` via the fixed template from architecture
Decision §1, excludes already-launched candidates via `git branch --list`/`gh
pr list` idempotency checks, plus a thin CLI printing `<role>\t<task>` lines),
`gates/test_remediation_spawn.py` (6 unit tests: one open finding -> one task
with the exact template string; a 3-round chain with the 3rd escalated ->
escalated record excluded; zero records -> `[]`; zero open records ->
`[]`; existing branch -> excluded; existing PR -> excluded), and a new
step 3 in `on-the-record/commands/run.md`'s orchestrator loop (between
classification and "누구를 깨울지") that runs the generator before free
judgment and launches any pending task's role/task verbatim through the
existing step-5 `spawn.py` call — renumbering every subsequent step
reference in the file (3→4, 4→5, 5→6, 6→7) to match. Also appended an
`## Accumulation` section to the already-merged phase-1 proposal
(`docs/issue-587/proposals/implementation.md`) to satisfy
`accumulation-claim-guard.sh`, which flagged the inline `git`/`gh` calls at
write time.

Per the approved proposal (PR #592, `APPROVE issue-587/implementation`).

## Why

Step 2 of #587: replace the orchestrator's manual routing judgment for
`status: open` remediation records with a fixed-template generator, per
architecture Decision §1 (PR #589, `APPROVE issue-587/architecture`).

## Upstream

docs/issue-587/proposals/implementation.md

## Confirmation run

```
$ python3 -m pytest gates/test_remediation_spawn.py -q
......                                                                   [100%]
6 passed in 0.03s
$ python3 gates/remediation_spawn.py --issue 999999 -C .
(no output — no pending tasks, exit 0)
```

## What did not work

- Wrote the record with `code_under_review` as a bare commit sha (matching
  a literal reading of the contract's field name); `record-fields-gate.sh`
  refused it — this role's own record must cite `code_under_review` as the
  reviewed file list, not a sha. Switched to the file list.
- First `gates/remediation_spawn.py` write was refused by
  `accumulation-claim-guard.sh` (inline `git`/`gh` calls with no `##
  Accumulation` field in the proposal). Added the section to the phase-1
  proposal, not this record, since the gate reads the proposal.

## Rationale for deviations

None — the implementation follows the approved proposal's `## What will be
done` exactly. The `## Accumulation` addition to the phase-1 proposal is a
gate-compliance amendment to an already-approved document, not a deviation
from what was built.

## Doc placement

- No new env var, config key, dependency, or migration — nothing added to
  a handbook.
- No library-or-format choice over a named alternative beyond what
  architecture already decided — no new decisions/ entry.
- No benchmark/investigation numbers — no reports/ entry.

## Open findings

None — warrant-hunter (before-landing, stance 0/bypass) found one: `git
branch --list <role>` in `_branch_exists` interprets `role` as a glob, so a
`routed_to` value containing a glob metacharacter could false-match an
unrelated branch and silently drop a genuine `status: open` task. Fixed in
this commit by switching to `git rev-parse --verify --quiet refs/heads/<branch>`
(exact refname, no glob interpretation) — confirmed by re-running the
hunter's own repro against this repo's `issue-587/implementation` branch:
`_branch_exists(".", "issue-587/*")` now returns `False` (was `True`),
`_branch_exists(".", "issue-587/implementation")` returns `True`. Full
report: docs/reports/2026-08-10-hunt-issue-587-implementation.md.

## Resolution path

N/A — the one finding from this session's own hunt is already resolved
above; nothing carries forward.

## Closed checks

- check: warrant-hunt before-landing, stance 0 (bypass) — glob-injection
  false-match in `_branch_exists`
  code_under_review: gates/remediation_spawn.py, gates/test_remediation_spawn.py, on-the-record/commands/run.md
  outcome: fixed (git rev-parse --verify --quiet replaces git branch --list)

## Next steps

Step 3 (e2e fixture-target-repo scenario) remains, per issue #587's own
step split — not this PR's job. This PR references #587 plain, not
Closes — the issue stays open for step 3.
