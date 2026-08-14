# issue-1323 phases 3-4 — current-state survey

canonical: files read this session (spawn.py, gates/check_runner.py,
roles/*.json, docs/issue-993/reports/product-discovery/current-state.md,
docs/issue-1323/proposals/2026-08-14-acceptance-authoring-rule-and-check-runner.md).

## board_condition inventory

derived: `grep -n board_condition roles/*.json`
```
roles/accessibility.json: a new interaction pattern or color-token set landed on the branch AND no accessibility record exists yet for it
roles/conformance-review.json: an implementation commit landed on the branch AND no conformance-review record exists yet for this commit sha
roles/defect-verification.json: an execution-observation or conformance-review record's result is disputed by another comment on the same commit sha
roles/execution-observation.json: an executable artifact landed on the branch AND no execution-observation record exists yet for this commit sha
roles/interaction-design.json: a requirements-engineering record landed for a screen/flow-facing requirement AND no interaction-design record exists yet for it
roles/product-discovery.json: an issue's requirement is still at problem/hypothesis level AND no product-discovery record with a validated|invalidated verdict exists yet
roles/requirements-engineering.json: a product-discovery record reached a validated verdict AND no requirements-engineering record exists yet
roles/secure-coding.json: authentication or input-handling code landed on the branch AND no secure-coding record exists yet for that commit sha
roles/security-threat-model.json: a spec or design doc landed that introduces a new trust boundary/auth surface/sensitive-data flow
roles/user-discovery.json: a product-discovery hypothesis requires user-interview validation AND no user-discovery record exists yet
```
canonical: the grep output above (this session).
Only two are decidable from "a commit landed on the branch" + "no
record exists for it" alone, with no code-content classification and no
dependency on another role's record: `execution-observation` and
`conformance-review`. The remaining eight need either content
classification (`accessibility`, `secure-coding`,
`security-threat-model`) or another role's record as precondition
(`interaction-design`, `requirements-engineering`, `user-discovery`,
`defect-verification`, `product-discovery`).

## No mechanical evaluator exists today

canonical: docs/issue-993/reports/product-discovery/current-state.md:57-58
(read this session) plus `grep -rn board_condition --include=*.py .`
(no hits outside `roles/*.json`, this session).
board_conditions today route only through orchestrator judgment; no
code evaluates them.

## reconcile() is single-entry-scoped

canonical: spawn.py:1845-1929 (`reconcile`, `_build_expected`), read
this session.
`reconcile(expected, observed)` compares one roster entry's
expected role/branch/PR against what was observed for that same entry
(`expected.get("role")`/`expected.get("branch")` throughout the
function body). It has no input field for "a role never registered on
this subject yet" — every rule assumes the entry already exists.

## _board_wide_sweep is the board-wide analogue

canonical: spawn.py:2694-2734 (`_board_wide_sweep`), read this session.
`_board_wide_sweep(root)` runs every watchdog tick (called from
`_board_wide_sweep_all` at spawn.py:2659, itself called from
`roster_watchdog` at spawn.py:2737) and already imports/runs
`gates/closure_sweep.py` and `gates/spawn_coverage.py` against the whole
board each tick (spawn.py:2705-2733) — not scoped to one roster entry.
`spawn_coverage.find_uncovered()` (called at spawn.py:2729) does a
similar board-wide "role X is owed and missing" computation for the
first/bootstrap role on an issue — a related but separate concern from
a verification role triggered by a landed commit.

## board() is presence-only, not commit-sha-keyed

canonical: spawn.py:1447-1468 (`board`), read this session, plus `grep
-rn '"commit sha"' spawn.py gates/*.py` (prose references only, no field
name or comparison logic, this session).
`board(root)` reads `docs/issue-<n>/reports/<role>.md` frontmatter per
subject/role and reports presence, not per-commit-sha existence.

## check_runner.py is unwired

canonical: gates/check_runner.py, full file read this session (171
lines); `grep -n check_runner spawn.py` (no hits, this session).
Nothing inside spawn.py calls check_runner.py. Its `format_comment()`
(gates/check_runner.py:113-121) builds a fixed-shape comment:
```
## Acceptance check-runner result: {passed}/{total} passed

- [PASS|FAIL] (<type>) <check>
```
one such line per check — the only structured, greppable check-runner
PR-comment shape in this repo.

## No merge-gate code, no CI workflow file

canonical: `ls gates/*.py` (no merge_gate.py) and `ls
.github/workflows/` (No such file or directory) — both this session.
A merge-gate module is new. A role session is refused from touching CI
config anyway (operational-surface gate, contract §21), so the gate has
to be a script a human/orchestrator runs given a PR number — the same
posture check_runner.py already takes.

## Write-set projection

- New `gates/` module, phase 3: mechanical board_condition-triggered-
  role computation, wired into `_board_wide_sweep`.
- One additive call site inside spawn.py's `_board_wide_sweep`
  (spawn.py:2694-2734), mirroring the existing closure_sweep/
  spawn_coverage calls already there — `reconcile()` itself unchanged.
- New `gates/` module, phase 4: mechanical evaluation of check-runner
  result + required verification records for a PR.
- New test files under `tests/`, mirroring
  tests/test_check_runner.py:19-36's local-fixture, no-network
  `fixture_pr_branch` style (read this session).
- No `.env`, dependency-manifest, or migration touch — stdlib +
  `subprocess` + `gh` CLI, same as check_runner.py.

## Alternatives (feeds the proposal's Rationale)

canonical: spawn.py:1851-1853 (`reconcile` docstring), read this
session.
- Extending `reconcile()`'s per-entry rules directly (a 4th
  `next_action` case) vs. a new board-wide function beside
  `_board_wide_sweep`'s existing checks. `reconcile()`'s input shape has
  no field for "a role not yet in the roster" — changing it means
  altering its documented, fixed contract instead of composing with the
  layer where spawn_coverage/closure_sweep already operate board-wide.
- Covering all 10 board_condition roles vs. only the 2 structurally
  mechanical ones, per the inventory above. The other 8 need judgment
  (content classification or another record as precondition) that
  would make the spawn trigger itself non-mechanical.
