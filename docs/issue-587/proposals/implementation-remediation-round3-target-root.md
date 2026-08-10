---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

## Request

Third e2e re-verification of #587 (PR #610) is still 4/5: `_remediation_merge_sweep`
is invoked with the global `ROOT` constant instead of the caller's
`-C`/`--cwd` target, so it silently no-ops in any repo other than
spawn.py's own checkout — it can never fire event 4 in a real consumer
repo. Thread the resolved target root from the `reconcile
--remediation-merged` CLI path into the sweep, and audit sibling sweeps
for the same `ROOT`-vs-target bug. Test must drive the shipped CLI with
`-C` pointing at a fixture repo outside the checkout and assert the `gh`
comment fires.

## Constraints

- Fix only the assigned call site (`roster_reconcile`'s
  `remediation_merged` branch and its `main()` dispatch) — do not widen
  to the other `ROOT`-hardcoded sites the survey found (`roster_watchdog`,
  `roster_reconcile`'s default mode); those are reported, not fixed, per
  the round's explicit scope.
- No new dependency, env var, migration, or public wire-format change —
  purely an additive keyword-only parameter and one CLI dispatch line.
- The new test must exercise the shipped CLI process
  (`python3 spawn.py reconcile ...`) against a fixture repo that is
  verifiably outside spawn.py's own checkout — not a direct call to
  `_remediation_merge_sweep` or `roster_reconcile`, and not a `spawn.ROOT`
  monkeypatch (that is exactly the coverage gap that let the prior round
  ship green while this bug survived).

## Rationale

Two ways to pass the target root were considered:

1. **Thread `root` as an explicit parameter through `roster_reconcile`
   into `_remediation_merge_sweep`** (chosen). Mirrors the existing
   precedent `drive()` already sets — it resolves `Path(cwd).resolve()`
   once and passes it into the same `_build_observed`/`reconcile`
   machinery `roster_reconcile` uses. No new resolution logic, one new
   optional parameter, default preserves existing non-CLI call sites.

2. **Reassign the module-level `ROOT` global at the top of `main()`
   from `a.cwd` before dispatch** — rejected. `ROOT` is read throughout
   spawn.py (roster paths, watchdog state, workspace index — all under
   `runs/`) as "this orchestrator's own checkout," a meaning that is
   correct and load-bearing everywhere except this one sweep. Overwriting
   the global for the whole process to fix one call site would silently
   redefine every other `ROOT` read for the duration of that CLI
   invocation — exactly the kind of blast-radius surprise the survey's
   audit section flags as a *risk*, not a *fix*: `roster_watchdog`'s
   `ROOT` uses are plausibly intentional (orchestrator-local roster
   state), and clobbering the global would make that ambiguous instead of
   explicit. Passing `root` as a parameter keeps the target-repo meaning
   scoped to exactly the one call site that needs it.

## What will be done

- `roster_reconcile(issue=None, unreported=False, remediation_merged=False,
  root: Path | None = None)`: in the `remediation_merged` branch, resolve
  `target_root = root if root is not None else ROOT` and call
  `_remediation_merge_sweep(target_root, issue)`.
- `main()`'s `reconcile` dispatch: pass `root=Path(a.cwd).resolve()`
  through to `roster_reconcile`.
- New test class in `test_spawn.py` that builds a fixture repo under a
  `tempfile.TemporaryDirectory()` (`git init`, `git remote add origin`,
  an open `docs/issue-587/decisions/remediation-*.md` record), stubs `gh`
  via a `PATH`-prepended executable that logs its argv and returns a
  merged PR for the `pr list` call, an empty comment list for the read
  call, and success for the post call, then invokes
  `subprocess.run([sys.executable, "<spawn.py path>", "reconcile",
  "--remediation-merged", "--issue", "587", "-C", str(fixture_root)])`
  and asserts exactly one `gh api .../comments` call with `-f` fired,
  carrying the expected comment body. The test asserts
  `fixture_root != spawn.py's own checkout dir` up front so a future
  refactor can't quietly make the fixture collapse back into the
  checkout it's supposed to be outside of.
- Existing `RosterReconcileRemediationMergedCLI` (function-level,
  `ROOT`-monkeypatched) stays unchanged — different layer of coverage,
  not superseded.
- Run `python3 test_spawn.py` (full suite) after the change; fenced
  output goes in the phase-2 record.

## Out of scope

- `roster_watchdog`'s `ROOT` uses and `roster_reconcile`'s default-mode
  `ROOT` use (survey's audit section) — same bug class, different call
  sites, not part of this round's assigned fix.
- Any `run.md` orchestration-step change — round 2's proposal already
  established the CLI-verb shape needs no `run.md` edit; this round only
  fixes that verb's `-C` plumbing, no new orchestration surface.
- The fourth e2e re-verification itself — that is execution-observation's
  job on the delivering PR, per prior rounds' precedent.

## Accumulation

The new test adds one more inline `subprocess.run` call plus one more
stub-`gh`-executable fixture to `test_spawn.py`, following the exact same
shape `RosterReconcileRemediationMergedCLI` (prior round) and
`test_help_lists_flag` already use — a per-test tmp `gh` stub, not a
shared helper. If this pattern accumulates further (a fourth or fifth CLI
subprocess test each hand-rolling its own `gh` stub script), the fix is
to extract a shared `_stub_gh(bin_dir, responses)` helper in
`test_spawn.py` once three or more tests duplicate the same
argv-dispatch-and-log shape — not before, since two instances (this one
and the prior round's near-miss `test_help_lists_flag`, which only checks
`--help` and does not stub `gh` responses) don't yet justify the
indirection. No `roles/*.json`-style repeated-file edit is involved —
this is a single call site in `spawn.py` and a single new test class.

## How you'll know it worked

- The new CLI-level test fails on the current `spawn.py` (reproducing the
  bug — sweep runs against spawn.py's own checkout instead of the
  fixture, so the expected `gh` comment call never happens) and passes
  once `root=Path(a.cwd).resolve()` is threaded through.
- `python3 test_spawn.py` full suite passes with no regressions.
- A subsequent e2e drive on a real fixture target repo shows the
  remediation-merged comment (event 4) firing for a branch merged in that
  fixture repo, not spawn.py's own.
