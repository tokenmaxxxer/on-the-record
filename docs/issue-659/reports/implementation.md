---
code_under_review:
  - gates/risk_report.py
  - gates/flows.py
  - on-the-record/hooks/impact-guard.sh
  - on-the-record/hooks/plan-order-guard.sh
  - on-the-record/hooks/hooks.json
  - gates/test_batch_eligible_groups.py
  - gates/test_plan_order_blocked.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation report — issue #659 phase 2

## What was done

Delivered exactly the phase-1 proposal's write set
(`docs/issue-659/proposals/implementation.md`):

- `gates/risk_report.py`: `_paths_overlap` (pairwise overlap wrapper around
  `_glob_matches`, bidirectional so either side can be the glob) and
  `batch_eligible_groups(prs, root)` — union-find over write-set overlap,
  returning each connected component as one batch-eligible group. Pure, no
  I/O.
- `gates/flows.py`: `plan_order_blocked(plan)` — for each plan step, finds
  the undone prerequisite step(s) at a strictly lower step number and
  reports the nearest one; steps sharing a step number (parallel `‖`
  entries) never block each other because the comparison is strict `<`.
  Pure, no I/O.
- `on-the-record/hooks/impact-guard.sh`: after the existing `batch_blocked`
  deny-and-exit path, computes `batch_eligible_groups` over the proposals
  that were NOT individually-required, and writes the grouping basis to
  `docs/issue-<n>/decisions/batch-<UTC timestamp>.md` per issue found among
  the grouped proposal paths.
- `on-the-record/hooks/plan-order-guard.sh` (new): matches `spawn.py <role>
  ... --issue <n>` commands (spawn.py's real CLI has no `--step` flag — the
  plan's step numbers map to roles, so the hook resolves role -> step
  itself against the issue's `## 실행 계획` via `gh issue view --json
  body`), calls `plan_order_blocked`, denies if the spawned role's step is
  premature, and writes the refusal basis to
  `docs/issue-<n>/decisions/spawn-refusal-<UTC timestamp>.md`. `gh pr
  merge` is intentionally not matched — see `## What did not work` below
  for why.
- `on-the-record/hooks/hooks.json`: registered `plan-order-guard.sh` under
  the same `PreToolUse`/`Bash` matcher as `impact-guard.sh`, listed right
  after it.
- `gates/test_batch_eligible_groups.py`, `gates/test_plan_order_blocked.py`:
  cover the issue's Acceptance fixtures (overlap grouping, singleton/empty
  states; premature-sequential-refused with parallel-allowed,
  no-dependency-empty-state) plus transitive-overlap and glob-write-scope
  cases.

## Why

Basis: `docs/issue-659/proposals/implementation.md` (approved via
`APPROVE issue-659/implementation`), which itself is grounded in
`docs/issue-659/decisions/2026-08-10-batch-eligibility-and-plan-order-gates.md`.
Both axes make an orchestrator judgment (batch-eligibility, sequential
dependency) machine-derived and audit-recorded instead of unrecorded manual
reasoning (issue #659's Acceptance section, refs #476/#573/#587).

## Test run

```
$ python3 gates/test_batch_eligible_groups.py
Ran 6 tests in 0.000s
OK
$ python3 gates/test_plan_order_blocked.py
Ran 7 tests in 0.000s
OK
$ python3 gates/test_risk_report.py
Ran 31 tests in 0.014s
OK
$ python3 gates/test_hooks_parity.py
4 passed
```

Both new hook shell scripts pass `bash -n`; their embedded Python heredoc
bodies were extracted and `compile()`-checked for syntax, plus a direct
regex-matching smoke test against `spawn.py`'s real invocation shape
(`spawn.py <role> "<task>" --issue <n>`). Not exercised live end-to-end
against `gh` (no live PR/issue fixture in this session) —
`plan-order-guard.sh` fails open (`exit 0`) whenever `gh` lookup fails, the
command isn't a role-naming spawn call, or the plan doesn't mention the
role, matching `impact-guard.sh`'s existing fail-open posture.

## What did not work

The first `plan-order-guard.sh` draft matched spawn/merge commands on a
`\bstep[-\s]?(\d+)\b` regex, assuming the command would name a step number
directly. A before-landing warrant hunt (stance: "assume the gate just
touched is bypassable") found `spawn.py` has no `--step` flag at all — its
real CLI is `spawn.py <role> "<task>" --issue <n>` — so the step-number
regex never matched any real invocation and the hook was dead code against
actual traffic (confirmed: `re.search(r'\bstep[-\s]?(\d+)\b', 'spawn.py
implementation "task" --issue 659')` -> `None`). Effect had it landed
unfixed: every real spawn call for a plan-ordered issue would have
silently bypassed Axis 2 order enforcement, with no denial and no audit
record. Fixed in this same session before landing: the hook now matches
the role token after `spawn.py` plus `--issue <n>`, resolves that role's
step number from the issue's parsed `## 실행 계획`, and gates on that
step. `gh pr merge` matching was dropped in the same fix — a merge command
carries no role/step signal in its text to correlate against the plan, so
there was nothing safe to gate there; Axis 2 enforcement now sits at the
spawn boundary only, not at merge time.

The hunt's own record could not be written to a separate
`docs/issue-659/reports/hunt-*.md` file: this session's role
(`implementation`) is restricted by `board-gate.sh` (contract v3 s11) to
writing only `implementation.md`/`implementation/**`, so the hunt finding
and its resolution are folded into this record instead of a standalone
hunt file — noted here so the absence of a separate hunt-record path is
not mistaken for a hunt that never ran.

## Open findings

None outstanding — the hunt's finding above was fixed in this session
before landing, not deferred.
