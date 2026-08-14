---
status: proposed
files:
  - gates/spawn_on_pr.py
  - gates/merge_gate.py
  - tests/test_spawn_on_pr.py
  - tests/test_merge_gate.py
  - spawn.py
---

## Request

#1323 phases 3-4, sequenced after #1320 (closed) and after phases 1-2
(landed, PR #1325): (3) PR creation auto-spawns the applicable
verification roles per their `board_condition`, extending the reconcile
machinery's respawn-on-divergence; (4) merging requires the
check-runner result (phase 2, landed) plus the required verification
records.

## Constraints

- The spawn trigger must stay mechanical — only board_conditions
  decidable from "a commit landed on the branch" + "no record exists
  for it" qualify, per docs/issue-1323/reports/implementation/survey-
  phase3-4.md's inventory: `execution-observation` and
  `conformance-review`. The other 8 roles' board_conditions need
  content classification or another role's record as precondition and
  are out of scope here.
- No change to `reconcile()`'s existing contract (its `expected`/
  `observed` shape, its 4 `next_action` values) — phase 3 composes at
  the board-wide sweep layer instead, per the survey's alternatives
  section.
- The merge gate is a script invoked with a PR number, mirroring
  `check_runner.py`'s existing posture (no `.github/workflows/` file in
  this repo; a role session is refused from touching CI config, per the
  operational-surface gate).
- New test files stay local-fixture, no-network, mirroring
  `tests/test_check_runner.py`'s `fixture_pr_branch` style.

## Rationale

Considered wiring the new board_condition check directly into
`reconcile()` as a 5th `next_action` value covering "role never
registered". Rejected: `reconcile()`'s documented contract
(spawn.py:1845-1929) takes one roster entry's `expected`/`observed` and
has no field representing "a role not yet in the roster for this
subject" — bolting that on would either overload an existing field with
a second meaning or add a field every existing caller must now pass,
breaking a pure function with a closed, already-referenced contract
(ADR docs/issue-492/decisions/2026-08-08-reconciliation-step-for-
supervision.md). A new function beside `_board_wide_sweep`'s existing
`closure_sweep`/`spawn_coverage` calls (spawn.py:2705-2733) extends the
same respawn-on-divergence machinery (the sweep that already drives
`roster_watchdog`) without touching `reconcile()`'s contract, and
matches how `spawn_coverage.find_uncovered()` already does a related
board-wide "role owed, missing" computation for the bootstrap role.

Considered spawning all 10 board_condition roles on PR creation, since
the issue says "the applicable verification roles per their
board_conditions" without naming a subset. Rejected: 8 of the 10 need
judgment to decide applicability (does this diff introduce a new
interaction pattern? does it touch authentication code? does another
role's record already exist as precondition?) — deciding those
mechanically would mean re-implementing content classification inside a
"strictly mechanical" gate, which is exactly what phase 2's check-runner
was built to avoid doing for Acceptance checks. Scoping to the 2
structurally decidable roles keeps the trigger itself a pure
function of "commit landed + no record" and defers the other 8 to
existing orchestrator judgment, unchanged.

## What will be done

**Req 3 — `gates/spawn_on_pr.py`:**
- `PR_TRIGGERED_ROLES = ("execution-observation", "conformance-review")`
  — the 2 board_condition roles decidable from commit-landing alone.
- `applicable_roles(subject_board: dict, roles=PR_TRIGGERED_ROLES) ->
  list[str]` — given one subject's `board()` entry
  (`{role: frontmatter}`), returns the subset of `roles` missing a
  record, in the order `roles` names them. Pure function, no I/O.
- `missing_verification(root: Path) -> dict[str, list[str]]` —
  `{subject: [missing roles]}` across the whole board, built from
  `board(root)` plus `_pr_open_or_merged_for_branch`-style PR-existence
  checks already used by `reconcile`'s observed-side builder (reuses
  `spawn._pr_open_or_merged_for_branch`, no new `gh` call shape) —
  restricted to subjects that actually have an open/merged PR, since
  the trigger is "PR creation", not "commit exists on any branch".
- `spawn_missing_for_pr(root: Path, cwd: str, dry_run: bool = False) ->
  list[tuple[str, str]]` — for each `(subject, role)` from
  `missing_verification`, registers+spawns that role by calling
  `spawn.roster_register` + `spawn._spawn_one` (the same primitives
  `_auto_respawn_check`/`_respawn_or_cap` already call for respawn —
  extension, not duplication). `dry_run=True` returns the
  `(subject, role)` pairs without registering/spawning, for testing
  without launching a session.
- Wired into `spawn.py`'s `_board_wide_sweep` (spawn.py:2694-2734) with
  one additive call alongside the existing `closure_sweep`/
  `spawn_coverage` calls, printing what it spawned (or would, under
  `--dry-run` parity with the rest of that function) and adding to the
  returned anomaly count only when `spawn_missing_for_pr` itself errors
  (a mechanical "N spawned" line is not an anomaly).

**Req 4 — `gates/merge_gate.py`:**
- `parse_check_runner_result(comment_body: str) -> dict | None` —
  matches `check_runner.format_comment()`'s exact shape (`"## Acceptance
  check-runner result: {passed}/{total} passed"` header); returns
  `{"passed": int, "total": int}` or `None` if the shape doesn't match.
- `latest_check_runner_comment(repo: Path, pr: int) -> str | None` —
  the sole `gh`-calling function here, `gh pr view <pr> --json comments`
  filtered to the last comment matching the header regex.
- `required_verification_missing(root: Path, subject: str) -> list[str]`
  — thin wrapper over `spawn_on_pr.applicable_roles` against
  `board(root)[subject]`, reusing req 3's role list rather than a second
  one.
- `evaluate(root: Path, repo: Path, pr: int, subject: str) -> dict` —
  `{"allowed": bool, "reasons": [str, ...]}`. Blocks when: no
  check-runner comment found; a found comment has `passed != total`;
  or `required_verification_missing` is non-empty. Allows only when all
  three clear.
- CLI: `python3 gates/merge_gate.py <pr> <subject> [--repo <path>]` —
  prints the reasons, exits 0 when allowed, 1 otherwise (same exit-code
  convention as `check_runner.py`).

**Tests** (`tests/`, pytest-collectible, plain `def test_*():` +
`assert`):
- `tests/test_spawn_on_pr.py` — `applicable_roles` against fixture
  board dicts (both roles missing, one missing, none missing);
  `spawn_missing_for_pr(..., dry_run=True)` against a fixture board +
  roster, asserting the exact `(subject, role)` pairs returned and that
  no roster file / subprocess call happens in dry-run mode.
- `tests/test_merge_gate.py` — `parse_check_runner_result` against
  real `check_runner.format_comment()` output (both all-pass and
  partial-fail) and non-matching text (`None`); `evaluate` against
  fixture combinations (comment missing, comment failing, verification
  missing, all clear) asserting `allowed`/`reasons`; `gh` calls
  monkeypatched to fixed argv/return the same way
  `tests/test_check_runner.py:92-106` tests `post_comment`.

## Accumulation

Both new modules add one more `subprocess.run(["gh", ...])` call site to
a codebase that already has several (`check_runner.post_comment`,
`_pr_open_or_merged_for_branch`, `pr_reference.py`, `ci.py`). This
proposal does not add a shared `gh`-call helper — it reuses the exact
convention (`subprocess.run(["gh", ...], cwd=repo, capture_output=True,
text=True)`) each existing site already uses, so a Nth caller looks
like the (N-1)th, not a new pattern. If a 5th/6th such call site lands
after this one, the accumulation point is a `gates/gh_call.py` thin
wrapper — not proposed here because 4 near-identical 1-line
`subprocess.run` calls is still cheaper to read than a wrapper's
indirection; that judgment should flip once a caller needs retry/
rate-limit handling the others don't (`spawn_coverage.py` and `ci.py`
already special-case rate limits independently — a wrapper would need
to reconcile those, out of scope for this proposal).

The role list `PR_TRIGGERED_ROLES = ("execution-observation",
"conformance-review")` duplicates 2 of the 10 role names already
enumerated in `roles/*.json`'s board_condition text. If more
board_conditions become mechanically decidable later (e.g. a future
content-classifier gate), the growth point is this tuple, not a new
file — `merge_gate.py` already imports it from `spawn_on_pr` rather
than keeping its own copy, so a 3rd role added there is a 1-line diff
touching one file, not two.

## Out of scope

- The 8 board_condition roles needing content classification or a
  precondition record (accessibility, secure-coding,
  security-threat-model, interaction-design, requirements-engineering,
  user-discovery, defect-verification, product-discovery) — still
  routed through orchestrator judgment, unchanged.
- Installing `merge_gate.py` as an actual GitHub branch-protection
  check or `.github/workflows/` job — no such CI surface exists in this
  repo and a role session is refused from adding one.
- Any change to `check_runner.py`'s own behavior or to `reconcile()`'s
  existing rules/contract.

## How you'll know it worked

```
python3 -m pytest tests/test_spawn_on_pr.py
python3 -m pytest tests/test_merge_gate.py
```
both exit 0: req 3's applicable-role computation and dry-run spawn
selection verified against fixture boards/rosters with no live
session launched; req 4's check-runner-comment parsing and merge-gate
verdict verified against fixture comments/boards with no live PR
network call (the `gh` call itself tested only for its argv shape, same
convention as the phase-2 `post_comment` test).
