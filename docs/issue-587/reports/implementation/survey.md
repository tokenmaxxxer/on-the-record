# Issue #587 — implementation current-state survey (phase 1, remediation round 2)

Skip condition: no new design decision is open. The prior
execution-observation round (`docs/issue-587/reports/execution-observation.md`,
"## Resolution path") already named the two possible shapes for the missing
call site — a `reconcile --remediation-merged` CLI verb (the shape
`_remediation_merge_sweep`'s own docstring documents, spawn.py:2109-2118) or
a `run.md` orchestration step — and left the choice to implementer, "either
way". This survey confirms the exact insertion points for the CLI-verb shape
(it composes with the existing `reconcile` verb family rather than adding a
parallel orchestration-only path, matching how `--unreported` was added in
issue #534) and records that choice; no product-facing surface is involved
(pure CLI wiring against an already-frozen internal contract), so scout's
sweep is not triggered.

## Write surfaces

### 1. spawn.py — CLI verb wiring

- `_remediation_merge_sweep(root: Path, issue: int) -> int` already exists
  and is individually correct (spawn.py:2109-2151, covered by
  `RemediationMergeSweep` in test_spawn.py:4791-4879, called directly there).
  Zero callers anywhere else in spawn.py (confirmed:
  `grep -n "_remediation_merge_sweep(" spawn.py` hits only the def line and
  the four direct-call test cases).
- `roster_reconcile(issue, unreported=False)` (spawn.py:2158-2189) is the
  existing dispatcher for the `reconcile` role verb; `--unreported` already
  demonstrates the pattern of a second bool flag selecting a different sweep
  inside the same verb (spawn.py:2159-2172, added issue #534). Adding a
  third mode (`remediation_merged=False`) here mirrors that precedent
  exactly rather than introducing a new dispatch shape.
- `main()`'s `if a.role == "reconcile":` branch (spawn.py:3495-3496) currently
  reads `return roster_reconcile(a.issue, unreported=a.unreported)` — extends
  to pass the new flag through.
- argparse: `--unreported` is defined at spawn.py:3478-3481 as a
  `store_true`; a sibling `--remediation-merged` flag goes next to it,
  following the same help-string convention (issue number, one-line purpose,
  cross-ref).
- `a.issue` (spawn.py:3454-3455, `type=positive_int`) is already required
  for `_remediation_merge_sweep`'s `issue` param — no new required-arg
  plumbing needed, `roster_reconcile` already receives `a.issue`.

### 2. run.md — no change needed for this wiring choice

Round 2's chosen shape (CLI verb on the existing `reconcile` role, not a new
orchestration step) means `on-the-record/commands/run.md` needs no edit:
`run.md`'s existing step 3 (line 77-82) already tells the orchestrator to
run `remediation_spawn.py --issue <n>` before free judgment, which is a
different generator (routing table -> spawn task), not this sweep (posts a
comment once a routed remediation's branch has merged). No existing run.md
step currently invokes any `reconcile` subcommand at all, so there is no
step to extend for this proposal's actual write set — confirmed via
`grep -n "reconcile" on-the-record/commands/run.md` (zero hits). Adding a
`run.md` step that calls `reconcile --remediation-merged` would duplicate
what a periodic/manual `spawn.py reconcile --remediation-merged --issue <n>`
invocation already covers now that the CLI verb exists, and is out of this
round's write set per the observation record's own "either way" framing —
the CLI verb alone satisfies "an entry point the shipped surface actually
exposes."

### 3. test_spawn.py — drive the shipped entrypoint

`RemediationMergeSweep` (test_spawn.py:4791-4879) currently calls
`spawn._remediation_merge_sweep(self.root, 587)` directly — exactly what the
execution-observation record flagged as insufficient ("called directly
rather than via a shipped entry point"). This round adds a new test class
(or method) that instead calls `spawn.roster_reconcile(issue=587,
remediation_merged=True)` (or drives `main()` via `sys.argv` +
`spawn.main()`, matching how `Reconcile` (test_spawn.py:3660) and
`RosterReconcileUnreported` (test_spawn.py:4884) already test their verbs)
against the same merged-fixture-branch setup already built in
`RemediationMergeSweep.setUp`, asserting the `gh api ... /comments` call
fires. No new fixture-building helpers needed — the existing `setUp` already
constructs an open `remediation-*.md` record with a merged `routed_to`
branch and monkeypatches `subprocess.run`.

## No new state store, no new dependency, no new env var

Same conclusion as round 1's survey: the CLI flag is a `store_true` on the
existing `reconcile` verb, `roster_reconcile` gains one new keyword-only
parameter, and `_remediation_merge_sweep` itself is unchanged. No schema,
migration, dependency-manifest, or `.env.example` entry is implicated.
