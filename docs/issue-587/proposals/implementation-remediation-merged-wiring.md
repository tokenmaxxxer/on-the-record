---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - docs/issue-587/reports/implementation/survey.md
  - docs/issue-587/proposals/implementation-remediation-merged-wiring.md
---

## Request

Round-2 remediation for issue #587's re-verification (PR #604): the
`_remediation_merge_sweep` posting function built in PR #603 posts correctly
when called directly, but nothing on the shipped surface ever calls it — no
CLI flag, no `run.md` step, no automatic sweep — so timeline event 4
("Remediation PR merged") can never fire during real operation. Wire an
actual call site for it, with a test driving the shipped entrypoint (not the
private function directly) against a merged fixture branch.

## Constraints

- No new state store, dependency, or environment variable (confirmed in the
  survey).
- The fix must be reachable through code an operator or the orchestrator
  would actually invoke — not just an importable private function.
- The new test must exercise the shipped entrypoint end to end (fixture
  branch merged -> shipped call -> `gh api ... /comments` fires), not call
  `_remediation_merge_sweep` directly the way the existing
  `RemediationMergeSweep` test class already does.

## Rationale

Two shapes were left open by the prior round's own scoping (execution
observation record, "## Resolution path"): (a) a `reconcile
--remediation-merged` CLI verb, or (b) a new `run.md` orchestration step
that calls `_remediation_merge_sweep` directly.

Chosen: (a), the CLI verb. Rejected: (b), a new `run.md` step, because
`run.md` currently has no step that invokes any `reconcile` subcommand at
all (confirmed zero grep hits) — adding one here would introduce a new
orchestration-step shape for a single sweep, duplicating what a CLI verb
already gives any caller (human, cron, or a future `run.md` step) for free.
The CLI-verb shape also has a direct precedent already in this exact
function family: `--unreported` (issue #534) added a second bool-flag mode
to the same `roster_reconcile` dispatcher rather than a new orchestration
step, and `_remediation_merge_sweep`'s own docstring already names
`reconcile --remediation-merged --issue N` as the intended shape
(spawn.py:2109-2111). Following that precedent keeps the `reconcile` verb as
the single place all roster/board sweeps live, instead of splitting sweep
logic across CLI verbs and prose orchestration steps.

## Accumulation

This adds one more `store_true` flag to the `reconcile` verb's argparse
block and one more `if <flag>: return <sweep>(...)`-shaped branch inside
`roster_reconcile`, following the exact pattern `--unreported` already set
(issue #534). If N more such sweeps get added the same way, `reconcile`'s
argparse block and `roster_reconcile`'s body grow by one flag/branch pair
each time — linear, not compounding, and each branch stays a one-line
delegation to an already-independently-tested sweep function (no inline
`subprocess`/`gh` calls are added here; `_remediation_merge_sweep` already
owns its own `gh api` call from round 1). If this pattern reaches roughly
4-5 flags, the follow-up would be collapsing them into a single
`--sweep=<name>` dispatch table rather than N more bool flags — noted here,
not built now, since round 2 only adds the second such flag.

## What will be done

- `spawn.py`: add a `--remediation-merged` argparse flag (`store_true`,
  next to `--unreported`); add a `remediation_merged: bool = False`
  parameter to `roster_reconcile`; when set, delegate to
  `_remediation_merge_sweep(ROOT, issue)` (mirroring the existing
  `unreported` delegation) before/instead of the default roster-divergence
  sweep, guarded the same way `--unreported` is guarded; update `main()`'s
  `if a.role == "reconcile":` branch to pass the new flag through.
- `test_spawn.py`: add a test that builds the same merged-fixture-branch
  setup `RemediationMergeSweep.setUp` already builds, then drives it through
  `roster_reconcile(issue=587, remediation_merged=True)` (or `main()` via
  `sys.argv`), and asserts the `gh api .../comments` call fires — proving
  the shipped entrypoint, not the private function, produces the comment.
- Run the full `test_spawn.py` suite and any other project suite (`gates/ci.py`
  if applicable) and paste fenced output in the phase-2 record.

## Out of scope

- A `run.md` orchestration step invoking the sweep — no existing step
  currently calls any `reconcile` subcommand, and the CLI verb alone
  satisfies "an entry point the shipped surface actually exposes" per the
  observation record's own "either way" framing. If the orchestrator later
  wants a periodic automatic sweep, that is a separate `run.md`-contract
  decision, not part of closing this gap.
- Any change to `_remediation_merge_sweep`'s own posting logic, message
  format, or idempotency marker — round 1 (PR #603) already verified those
  correct via direct-call tests; this round only adds a caller.
- A third re-verification round's e2e fixture drive — that is
  execution-observation's job on the delivering PR, not this proposal's.

## How you'll know it worked

- `python3 -m pytest test_spawn.py` (or the project's existing test runner)
  passes, including the new test that drives `roster_reconcile(...,
  remediation_merged=True)` (or `main()`) and asserts the `gh api`
  comment-post call fires.
- `python3 spawn.py --help` lists `--remediation-merged` under the
  `reconcile` verb's options.
- `grep -n "_remediation_merge_sweep(" spawn.py` shows a call site inside
  `roster_reconcile` in addition to the existing `def` line.
