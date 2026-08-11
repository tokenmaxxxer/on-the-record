---
kind: current-state-survey
loop_state: complete
---

# Current-state survey — issue #787 step 3 (re-run scope)

Scope: role `execution-observation`, session on branch
`issue-787/execution-observation`, subject issue #787, re-running the
issue #776 harness against PR #797 (`dee7119`, merged into `main` as
`df347d3`) — the deliverable-guard H1 widening. Read this session before
any proposal-shaped or verdict-shaped language:

- `gh issue view 787` (full body, 3 comments) — problem statement,
  requirement, three-step plan, acceptance criteria (pre-registered
  threshold language for the H1 metric and the empty-state guardrail
  quoted verbatim in this role's assignment).
- `docs/issue-776/reports/execution-observation.md` (baseline record,
  `provenance: executed-live`, `loop_state: handed-off`) — the exact
  harness invocation, transcript-derived signal table, and 3 open
  findings the baseline left for a future re-run.
- `git show dee7119 --stat` — the merged H1 fix diff (widened
  denylist-of-exemptions classifier in `on-the-record/hooks/deliverable-guard.sh`,
  plus its own before-landing hunt record).
- `docs/specs/northpole-harness.md` — the frozen §3 signal table and §6
  decision rule the baseline and this re-run both apply.
- `harness/driver.py`, `harness/signals.py` — the operator-side
  instantiate/build/run helpers and the pure signal-check functions used
  to interpret the transcript this session captured.

## What is thin/unknown before scouting the re-run

- Whether the H1 widening actually changes live enforcement — the fix
  only widened a path-classifier regex; whether the PreToolUse hook
  fires at all for a headless `claude -p` Edit call under
  `--permission-mode acceptEdits` was never observed live for this
  specific invocation shape.
- Whether the harness's own fixture-instantiation convention (dropping
  a fresh copy under a scratch/tmp-named path) collides with the fix's
  own new exemption list (`scratch`, `tmp`, `.git`, `plugin-cache` path
  segments) — this is a candidate self-defeating measurement bug, not
  yet ruled out before running.
- Whether `CLAUDE_ROLE` (set in this observer session's own shell) leaks
  into a nested `claude -p` subprocess and short-circuits the guard's
  role-session bypass branch before H1 is ever reached — also not yet
  ruled out before running.

These three unknowns directly shaped the re-run's scout-equivalent step
(this is a re-run of a pre-registered mechanical harness, not a
build-direction choice, so the scout-directive's product-scouting stage
does not apply here — the "skip: mechanical re-run of a pre-registered
signal table, no open design decision" record stands in its place).
