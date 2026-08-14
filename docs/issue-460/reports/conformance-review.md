# Conformance review — issue-460 GitHub Actions retirement

## Upstream / basis

Requirement list: `docs/issue-460/proposals/2026-08-08-retire-github-actions.md`
(its delivery steps 1-6 and verification bullets), plus issue #460's own
body acceptance bullets. Approved via `APPROVE issue-460/conformance-review`
(issue #460 comment). Reviewed artifact: commit `1340d054` ("feat(issue-460):
retire this repo's own GitHub Actions workflows"), current HEAD (`bc53410e`).
Implementation record: `docs/issue-460/reports/implementation.md`.

## What was done

Artifact-only re-read of the current repo state against the proposal's six
delivery steps and five verification bullets; ran the two gate commands
the proposal names as evidence.

canonical: `ls .github/workflows/`
```
$ ls .github/workflows/
ls: cannot access '.github/workflows/': No such file or directory
```

canonical: `python3 gates/test_boundary.py`
```
$ python3 gates/test_boundary.py
ok - t_a_new_unrecorded_module_is_caught
Traceback (most recent call last):
  ...
  File "gates/test_boundary.py", line 77, in t_all_gates_modules_recorded
    assert not bad, "\n".join(bad)
AssertionError: acceptance_authoring_rule.py 가 docs/specs/enforcement-boundary.md
에 판정(verdict)이 기록된 행으로 없다 — 기록되지 않은 게이트가 조용히 존재한다(#441).
check_runner.py 가 ... 없다(#441).
merge_gate.py 가 ... 없다(#441).
spawn_on_pr.py 가 ... 없다(#441).
tool_learnings_gate.py 가 ... 없다(#441).
tool_learnings_tracker.py 가 ... 없다(#441).
```

canonical: `python3 -m pytest gates/test_boundary_workflow_migration.py -q`
```
$ python3 -m pytest gates/test_boundary_workflow_migration.py -q
...
3 passed in 0.18s
```

Also read `docs/specs/enforcement-boundary.md` (the `.github/workflows/*.yml`
migration table, around line 154), `on-the-record/UNENFORCED-CLAUSES.md`
(rows #369/#383, around line 49), `on-the-record/commands/run.md` (the
pre-merge instruction, around line 294), and `gates/test_boundary_workflow_migration.py`
and `gates/test_boundary.py` (the `__main__` wiring block, around line 328)
directly. One verdict rendered per requirement below.

## Verdicts

canonical: `ls .github/workflows/` run above.
**Item 1 — Delete all four `.github/workflows/*.yml` files: Present.** The
directory itself no longer resolves on disk, not merely emptied. Matches
verification bullet 1.

canonical: `docs/specs/enforcement-boundary.md` (read directly, migration
table around line 154).
**Item 2 — Migration table with `replacement` column, filled per
workflow: Present.** The `mechanism | verdict | replacement` table carries
a non-empty row for all four deleted filenames. Content matches the
proposal's per-workflow breakdown, with one later, unrelated correction:
the `closure-sweep.yml` row's board-wide replacement now names
`spawn.py:roster_watchdog()` (issue #464 ADR) rather than the "out of
scope — operator decision" drop the proposal and `implementation.md`
describe. This is a later, separate issue superseding that row, not a gap
in #460's own delivery — #460's row was non-empty and accurate at the time
it landed.

canonical: `on-the-record/UNENFORCED-CLAUSES.md` (read directly, rows
#369/#383 around line 49).
**Item 3 — No new `UNENFORCED-CLAUSES.md` rows needed, verified not
assumed: Present.** Rows #369 (`gates/ci.py`, full-bundle) and #383
(`gates/closure_sweep.py`, board-wide) already name the two consumer-facing
drops the migration table's `plan-aware-closes-gate.yml` and
`closure-sweep.yml` rows reference, matching `implementation.md`'s claim.

canonical: `gates/test_boundary_workflow_migration.py` and
`gates/test_boundary.py` (both read directly, `__main__` wiring block
around line 328).
**Item 4 — `test_boundary_workflow_migration.py` added with the described
checks, wired into `test_boundary.py`: Present as code.** The file defines
`t_workflows_dir_absent_or_empty`, `t_every_deleted_workflow_has_migration_row`,
and `t_ci_supplement_or_out_of_scope_rows_are_cross_referenced` — the
proposal's described checks (a) and (b), (b) split across the latter two
functions. `test_boundary.py`'s `__main__` block loads this module via
`importlib.util` and appends its `t_*` functions to its own test list,
matching `implementation.md`'s description exactly.

`derived: python3 -m pytest gates/test_boundary_workflow_migration.py -q, reproduced above`
— standalone run: all tests succeed (see fenced output above).

`derived: python3 gates/test_boundary.py, reproduced above`
— combined run: the script raises on `t_all_gates_modules_recorded`, an
unrelated, pre-existing check for six gate modules added by later issues
(`acceptance_authoring_rule.py`, `check_runner.py`, `merge_gate.py`,
`spawn_on_pr.py`, `tool_learnings_gate.py`, `tool_learnings_tracker.py`)
lacking `enforcement-boundary.md` rows, before the migration checks ever
execute — the script's `_run()` helper has no exception handling and stops
at the first raising assertion (`gates/test_boundary.py`, read directly,
around line 320). This is a real, current-HEAD gap in the combined-run
verification bullet, not caused by anything #460 itself changed — see Open
findings.

canonical: `on-the-record/commands/run.md` (read directly, around line
294).
**Item 5 — `run.md` pre-merge instruction corrected: Present.** The
"결과 수용" branch states this repo has no CI (#460), that zero checks is
the expected state on every PR here and is not itself an anomaly to raise,
while the following sentence keeps the "checks exist but none show up"
anomaly-flag rule for consumer repos that do wire CI — matching the
proposal's item 5.

canonical: `docs/issue-460/reports/implementation.md` (read directly,
around line 72).
**Item 6 — Branch-protection required-check names reported: Present.**
The "Branch-protection required checks the operator must remove" section
lists `test`, `closes-gate`, `bundling-gate`, `closure-sweep`, matching the
proposal item 6's four names, with a closing note that no
branch-protection API call was made.

## Why

Per-requirement fidelity verdicts, artifact-only, per the
conformance-review role's rulebook (never a holistic quality read, never a
fix).

## What did not work

None.

## loop_state

kind: review-record
loop_state: draft-reported

## Open findings

`derived: python3 gates/test_boundary.py, reproduced above` — the script
raises before reaching the migration checks.
`derived: python3 -m pytest gates/test_boundary_workflow_migration.py -q, reproduced above`
— all tests succeed standalone (see fenced output above).

- **Verification bullet ("`python3 gates/test_boundary.py` covering the
  wired-in `test_boundary_workflow_migration.py` checks in one run") —
  cantTell at current HEAD.** The combined script raises on
  `t_all_gates_modules_recorded` before reaching the wired-in migration
  checks, because six gate modules landed by later, unrelated issues carry
  no `enforcement-boundary.md` row. The migration checks themselves
  execute cleanly standalone, and are correctly wired in the source per
  the item-4 verdict above. Not a defect in #460's diff — the six
  unrecorded modules were added by other issues after #460 landed.
  Addressed to: whichever role owns `enforcement-boundary.md`'s general
  module-recording hygiene (#441 class), not #460's implementation role —
  #460's own changes are not the cause and this role's write scope does
  not cover `docs/specs/enforcement-boundary.md`'s unrelated rows.

## Next steps

Verdict tally: Present for items 1, 2, 3, 5, 6; Present-as-code with a
cantTell combined-run finding for item 4 (source matches the spec exactly,
but the combined gate run it's wired into currently raises for an
unrelated, later-landed reason — see Open findings). Overall: issue #460's
own delivery substantially conforms to its proposal per the items verified
above; the one open finding is an environmental fact about
`test_boundary.py`'s current combined-run state, not a fidelity gap in
what #460 itself changed, and routes outside this review's write scope.

## Resolution path

Open finding: no action from #460's implementation role — the six
unrecorded modules are outside `docs/issue-460/proposals/2026-08-08-retire-github-actions.md`'s
frozen write set and were added by separate, later issues. Whoever next
touches `docs/specs/enforcement-boundary.md`'s general module-recording
rows, or does a dedicated #441-class hygiene sweep, should add rows for the
six modules named above so `python3 gates/test_boundary.py` can reach and
exercise the already-correct `test_boundary_workflow_migration.py` checks
in a single invocation.
