---
code_under_review: HEAD
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# issue-2088: pre-spawn `spawn.py lint --issue <n>` entry point

## What was done
Added `spawn.lint_issue(cwd, issue)` (spawn.py, next to
`require_acceptance_gate`/`require_requirement_linkage`) — it runs the same
body-only gates those two spawn-time functions run (`gates/acceptance_gate.py`
for phase-2 issues, `gates/requirement_linkage.py` for phase-1 issues,
gated on the same phase predicate and the same already-spawned-branch
retroactive-block exemption), but collects every violation into a list and
returns it instead of `sys.exit`-ing on the first one.

canonical: read spawn.py:722-753 (new lint_issue function, inserted right
after require_requirement_linkage)

Wired a new `spawn.py lint --issue <n> [-C <repo>]` CLI subcommand in
`main()` that calls `lint_issue`, prints every violation with an
`acceptance:`/`requirement-linkage:` prefix, and returns exit code 1 if
any exist, 0 otherwise — no session is spawned either way.

canonical: read spawn.py:7495-7508 (lint dispatch branch added next to
the approve-scope branch in main())

Documented lint-before-spawn as the standard flow in the orchestrate
directive (on-the-record/commands/run.md step 5): before the existing
`spawn.py <role> ... --issue <n>` call, the directive now instructs
running `spawn.py lint --issue <n> -C <repo>` first, fixing the issue body
on violation and re-linting, only spawning once lint is clean.

canonical: read on-the-record/commands/run.md:117-127 (step 5, amended)

Added regression coverage in tests/test_spawn_pipeline.py: a
LintIssueSubcommand class covering lint_issue's no-marker passthrough,
phase-1 dirty/clean requirement linkage, phase-2 dirty/clean acceptance
shape (with requirement-linkage correctly skipped once an issue is
phase-2 approved), the already-spawned-branch retroactive-block
exemption, and the CLI's nonzero-exit-with-violations / zero-exit-when-clean
/ missing-`--issue`-usage-error behavior; and an
OrchestrateDirectiveLintBeforeSpawn class asserting the directive names
the `spawn.py lint --issue` command, names "lint-before-spawn" and "issue
#2088", and that the lint instruction textually precedes the spawn call.

```
$ python3 -m pytest -q tests/test_spawn_pipeline.py -k "Lint or OrchestrateDirectiveLintBeforeSpawn" -v 2>&1 | grep -E "PASSED|FAILED|passed|failed"
tests/test_spawn_pipeline.py::LintIssueSubcommand::test_already_spawned_phase1_issue_not_retroactively_blocked PASSED
tests/test_spawn_pipeline.py::LintIssueSubcommand::test_cli_exits_nonzero_and_prints_violations PASSED
tests/test_spawn_pipeline.py::LintIssueSubcommand::test_cli_exits_zero_when_clean PASSED
tests/test_spawn_pipeline.py::LintIssueSubcommand::test_cli_requires_issue PASSED
tests/test_spawn_pipeline.py::LintIssueSubcommand::test_no_marker_no_violations PASSED
tests/test_spawn_pipeline.py::LintIssueSubcommand::test_phase1_clean_requirement_linkage_has_no_violations PASSED
tests/test_spawn_pipeline.py::LintIssueSubcommand::test_phase1_missing_requirement_linkage_is_reported PASSED
tests/test_spawn_pipeline.py::LintIssueSubcommand::test_phase2_clean_acceptance_shape_has_no_violations_and_skips_requirement_linkage PASSED
tests/test_spawn_pipeline.py::LintIssueSubcommand::test_phase2_missing_acceptance_shape_is_reported PASSED
tests/test_spawn_pipeline.py::OrchestrateDirectiveLintBeforeSpawn::test_documents_lint_before_spawn_as_standard_flow PASSED
tests/test_spawn_pipeline.py::OrchestrateDirectiveLintBeforeSpawn::test_documents_lint_subcommand PASSED
tests/test_spawn_pipeline.py::OrchestrateDirectiveLintBeforeSpawn::test_lint_instruction_precedes_spawn_call_in_text PASSED
12 passed
```
canonical: python3 -m pytest -q tests/test_spawn_pipeline.py -k "Lint or OrchestrateDirectiveLintBeforeSpawn" -v — pasted live run above (executed-unit)
acceptance: python3 -m pytest -q tests/test_spawn_pipeline.py -k "Lint or OrchestrateDirectiveLintBeforeSpawn" -v — result: pass (all 12 listed tests PASSED, pasted above, executed-unit)

Also ran the fast tier (python3 -m pytest -q -m "not slow", per
.on-the-record/test-tiers.json) to check for regressions, after
regenerating docs/specs/reconciled-index.md (python3 gates/spec_index.py
--update) for the run.md content-hash change the spec-index-preflight
gate requires alongside a docs/specs/* commit:

```
$ python3 -m pytest -q -m "not slow" 2>&1 | tail -3
2627 passed, 19 xfailed, 2 xpassed in 42.24s
```
canonical: python3 -m pytest -q -m "not slow" — pasted live run above (executed-unit)
acceptance: python3 -m pytest -q -m "not slow" — result: pass (2627 passed, 0 failed, pasted above)

The diff touches spawn.py and tests/test_spawn_pipeline.py, both of which
are `slow`-tier trigger classes in .on-the-record/test-tiers.json; the
slow tier (python3 -m pytest -q -m slow) was launched in the background
per the test-tier directive's budget guidance and its result is not yet
known at commit time — tiering gap noted here rather than silently
absorbed.

## Why
The issue's reproduction log shows five spawn round-trips refused by
body-only issue-body gates (tm-dicequest#55 x3 acceptance grammar,
tm-dicequest#58 x1 heading corruption, on-the-record#2073 x1 missing
Acceptance) that the gates already check purely from the issue body —
none needed a spawned session to discover. Each refusal costs a full
spawn bootstrap + issue edit + respawn cycle. Exposing the existing gate
logic as a standalone, no-spawn CLI entry point removes that round-trip
cost entirely, and documenting it in the orchestrate directive makes it
the default habit rather than an opt-in tool nobody remembers.

## Upstream basis
spawn.py's existing require_acceptance_gate and require_requirement_linkage
functions (both pre-existing, unmodified); gates/acceptance_gate.py and
gates/requirement_linkage.py's check functions (pre-existing, unmodified);
gates/ci.py's _approved_roles_on_issue phase predicate (pre-existing,
unmodified) — lint_issue reuses these exact phase predicates and check
calls without altering their behavior.

## What will be done
- spawn.py: new lint_issue(cwd, issue) function; new lint CLI branch in
  main().
- on-the-record/commands/run.md: step 5 amended to document
  lint-before-spawn as the standard flow.
- tests/test_spawn_pipeline.py: LintIssueSubcommand and
  OrchestrateDirectiveLintBeforeSpawn test classes.
- docs/specs/reconciled-index.md: regenerated hash for the run.md change
  (mechanical, required by spec-index-preflight.sh).

## Out of scope
No change to the underlying gate logic in gates/acceptance_gate.py or
gates/requirement_linkage.py, and no change to require_acceptance_gate's
or require_requirement_linkage's spawn-time behavior — lint is purely an
additive, non-spawning read path over the same checks.

## What did not work
None.

## Skill verdicts
skill-verdict: implementation-complexity-coupling-management — not-applicable: lint_issue adds no new coupling/cohesion threshold, accessor chain, or cross-module import direction — it re-imports the same two gates/* modules the existing spawn-time gates already import.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision; the change is a straight-line function extracting the same two gate checks into a non-exiting variant.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure, algorithm, or communication-scheme choice; a small fixed-size violation list.
skill-verdict: implementation-blueprint — not-applicable: single-module CLI-subcommand addition mirroring an existing sibling-function pattern (require_acceptance_gate/require_requirement_linkage) plus a doc edit — no multi-module structure decision or parallel-worker fan-out to freeze a contract for.
skill-verdict: technical-feasibility-build-vs-buy-dependency-health — not-applicable: no dependency or vendor candidate involved.
skill-verdict: upstream-defect-report-convention — not-applicable: no upstream project defect being filed; in-repo tooling addition.

## Open findings
None.
