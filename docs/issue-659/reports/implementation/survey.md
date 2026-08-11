# Current-state survey — issue #659 implementation (phase 1)

## Skip condition

Scouting (scout-directive) is skipped: this is a pure implementation task against an already
merged architecture ADR (`docs/issue-659/decisions/2026-08-10-batch-eligibility-and-plan-order-gates.md`)
that fixes the module boundary, function signatures, hook wiring, and audit-record location. No
product-facing or design decision remains open for implementation to make — the ADR states this
explicitly ("hook shell script content is implementation's job", meaning wiring only, not design).

## Write set expected

- `gates/risk_report.py` — add `batch_eligible_groups(prs, root)`, placed next to the existing
  `batch_blocked` function. Reuses `_glob_matches` as the overlap primitive per the ADR.
- `gates/flows.py` — add `plan_order_blocked(plan)`, placed next to the existing `_plan_from_body`
  function. Consumes its `[{step, roles, done}, ...]` output, no new parsing.
- `on-the-record/hooks/impact-guard.sh` — one new stage after the existing `batch_blocked` call,
  calling `batch_eligible_groups` and writing the audit record.
- new file under `on-the-record/hooks/` for the plan-order gate, mirroring `impact-guard.sh`'s
  shape (checkout resolution boilerplate, Python heredoc, env passthrough), gating the
  spawn/merge command surface.
- `on-the-record/hooks/hooks.json` — register the new hook under `PreToolUse` / `Bash`, alongside
  the existing `impact-guard.sh` entry.
- new test file(s) under `gates/` for `batch_eligible_groups` (fixture overlap grouping + audit
  record, singleton empty state) and `plan_order_blocked` (premature sequential refusal, parallel
  allowed, no-dependency empty state) — following this repo's existing per-module test-file
  naming convention (e.g. `on-the-record/hooks/test_impact_guard.py`).
- this issue's phase-2 implementation record (written when phase 2 opens).

## What already exists (reusable, confirmed by reading)

- `_glob_matches(path, pattern)` in `gates/risk_report.py` — currently one-directional (path vs.
  glob pattern), used by `blast_radius_grade` and `propagation_grade`. Axis 1 needs path-vs-path
  exact/glob comparison per the ADR ("a `(list[str], list[str]) -> bool` wrapper around the
  existing `_glob_matches`") — a new wrapper function, not a signature change to `_glob_matches`
  itself, so its existing callers are untouched.
- `batch_blocked(proposals, root)` in `gates/risk_report.py` — risk-permission gate (dominant
  reversibility axis), unrelated to write-set grouping; the ADR confirms Axis 1 runs *after* this
  clears, never merged into it.
- `_plan_from_body(body)` in `gates/flows.py` — already parses the issue's `## 실행 계획` block
  into `[{step, roles, done}]`, with `‖`-joined parallel roles within one step.
  `plan_order_blocked` consumes this list directly.
- `impact-guard.sh` — existing hook shape to mirror: resolve the on-the-record checkout, read the
  stdin JSON payload, deny via a Python heredoc that imports `gates/risk_report.py`, an
  `ORCHESTRATE_OFF` kill switch. Registered in `hooks.json` under `PreToolUse`/`Bash` alongside
  `contract-guard.sh`, `pr-preflight.sh`, etc.
- `docs/issue-<n>/decisions/*.md` — existing convention (this issue's own ADR lives there) that
  both axes reuse per the ADR's deployment-surface section, rather than a new record location.

## Gaps the ADR leaves for implementation to fill (mechanical, not a design decision)

- Exact audit-record filename timestamp format: the ADR names `batch-<timestamp>.md` /
  `spawn-refusal-<timestamp>.md` without specifying the format. This repo's own session-log
  filenames elsewhere in this issue's comment thread use `%Y%m%dT%H%M%SZ`-shaped UTC timestamps —
  implementation follows that existing convention rather than inventing a new one.
- The plan-order hook's exact command-surface match (which `gh` subcommands count as spawn/merge)
  — mirrors `impact-guard.sh`'s own `gh pr merge` regex match, adapted to also catch spawn-shaped
  commands per the ADR's "spawn/merge command point" wording.

## Alternatives considered (for the proposal's Rationale)

- Writing the audit record from inside the pure functions themselves (`batch_eligible_groups` /
  `plan_order_blocked` doing the file write) — rejected: the ADR states both functions are "pure
  ... no I/O, no file writes"; the audit-record write belongs in the hook script, matching how
  `impact-guard.sh` already keeps its own reporting outside `risk_report.py`.
- Extending `impact-guard.sh`'s existing Python heredoc to also call `plan_order_blocked` —
  rejected: the ADR is explicit that Axis 2 is "a new hook, not an extension of
  `impact-guard.sh`", because it gates a different command surface (spawn/merge vs.
  batch-approval framing).
