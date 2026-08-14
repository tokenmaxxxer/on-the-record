---
code_under_review:
  - gates/spawn_on_pr.py
  - gates/merge_gate.py
  - tests/test_spawn_on_pr.py
  - tests/test_merge_gate.py
  - spawn.py
loop_state: landed
type: feature
breaking: false
canonical: pytest tests/test_spawn_on_pr.py tests/test_merge_gate.py -q
verdict: pass
---

## What was done

canonical: `docs/issue-1323/proposals/2026-08-14-spawn-on-pr-and-merge-gate.md`
(read this session, `files:` frontmatter + body)

Phases 3-4 of #1323, implemented per the proposal named above.

- `gates/spawn_on_pr.py`: `PR_TRIGGERED_ROLES = ("execution-observation",
  "conformance-review")`; `applicable_roles(subject_board, roles=...)` —
  pure function, missing-role subset in `roles` order;
  `missing_verification(root)` — board-wide `{subject: [missing roles]}`,
  built on `spawn._pr_open_or_merged_for_branch` (canonical: `spawn.py`,
  read this session) — kept to subjects a PR already exists for;
  `spawn_missing_for_pr(root, cwd, dry_run=False)` — registers+spawns
  each missing `(subject, role)` via `spawn.roster_register` +
  `spawn._spawn_one`, the same primitives `_respawn_or_cap` already
  calls (canonical: `spawn.py`, read this session); `dry_run=True`
  returns the pairs with no registration/spawn call.
- Wired into `spawn.py`'s `_board_wide_sweep` (canonical: this session's
  own diff to `spawn.py`) — one additive call alongside
  `closure_sweep`/`spawn_coverage`, printing what was spawned; adds to
  the anomaly count only when `spawn_missing_for_pr` itself raises.
- `gates/merge_gate.py`: `parse_check_runner_result(comment_body)` —
  matches `check_runner.format_comment()`'s header shape (canonical:
  `gates/check_runner.py`, read this session), returns a
  `{ok_count, total}`-shaped dict or `None`; `latest_check_runner_comment
  (repo, pr)` — sole `gh`-calling function, `gh pr view <pr> --json
  comments` filtered to the last matching comment;
  `required_verification_missing(root, subject)` — thin wrapper over
  `spawn_on_pr.applicable_roles`; `evaluate(root, repo, pr, subject)` —
  `{"allowed", "reasons"}` — the reasons list stays non-empty when the
  check-runner comment is absent, the tally is mismatched, or a
  required verification entry is absent. CLI: `python3 gates/merge_gate.py
  <pr> <subject> [--repo <path>]`, exit-code convention mirrored from
  `gates/check_runner.py` (canonical: `gates/check_runner.py`, read
  this session).
- Tests: `tests/test_spawn_on_pr.py` and `tests/test_merge_gate.py` —
  local git-fixture boards/repos, no network, `gh`/spawn primitives
  monkeypatched to fixed argv or fake returns, mirroring
  `tests/test_check_runner.py`'s `fixture_pr_branch` + `post_comment`
  argv-assertion style (canonical: `tests/test_check_runner.py`, read
  this session).

derived: `python3 -m pytest tests/test_spawn_on_pr.py --collect-only -q | tail -1`
```
7 tests collected in 0.03s
```

derived: `python3 -m pytest tests/test_merge_gate.py --collect-only -q | tail -1`
```
9 tests collected in 0.02s
```

## Why

canonical: `docs/issue-492/decisions/2026-08-08-reconciliation-step-for-supervision.md`
(read this session; ADR referenced from `reconcile()`'s own docstring
in `spawn.py`)

`reconcile()`'s `expected`/`observed` contract has no field
representing "role never registered for this subject" — extending it
would either overload an existing field with a second meaning or add a
field every existing caller must newly supply. `spawn.py`'s
`_board_wide_sweep` (canonical: `spawn.py`, read this session) already
runs `closure_sweep`/`spawn_coverage` as board-wide observe/spawn
ticks; adding `spawn_on_pr` there composes with the same
respawn-on-divergence machinery, leaving `reconcile()`'s own contract
untouched.

canonical: `roles/conformance-review.json`, `roles/execution-observation.json`,
and the other 8 `roles/*.json` files' `use_when` fields (read this
session)

Scoping the trigger to `execution-observation`/`conformance-review`
keeps it a pure function of "commit landed + no record". The other 8
board_condition roles' `use_when` text needs content classification or
a precondition record — reintroducing that judgment here would
duplicate what `gates/check_runner.py` was built to avoid for
Acceptance checks.

## Upstream

Basis: `docs/issue-1323/proposals/2026-08-14-spawn-on-pr-and-merge-gate.md`,
approved via `APPROVE issue-1323/implementation` on the issue.
commit_sha: 102bbc365b61baa137f1cbc4fe41ba8dba8f5b4a

## Acceptance

canonical: pytest tests/test_spawn_on_pr.py tests/test_merge_gate.py -q
acceptance: `python3 -m pytest tests/test_spawn_on_pr.py tests/test_merge_gate.py -q` — result:
```
16 passed in 0.16s
```

canonical: pytest tests/test_check_runner.py -q
acceptance: `python3 -m pytest tests/test_check_runner.py -q` — result:
```
7 passed in 0.72s
```

acceptance: `python3 -c "import ast; ast.parse(open('spawn.py').read())"` — result: no exception raised, exit 0.

## What did not work

None.

## Open findings

None.
