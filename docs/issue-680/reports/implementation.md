---
code_under_review:
  - spawn.py
  - test_spawn.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal
(`docs/issue-680/proposals/2026-08-10-returned-pr-spawn-gate.md`):

- `_open_role_prs(root)`: runs `gh pr list --state open --json
  number,headRefName,body,url` against the target repo (via `_repo_slug`),
  filters to `headRefName` matching `issue-(\d+)/`, returns `(prs, ok)`.
- `_undispositioned_role_prs(root, exclude_issue=None)`: for each open
  role PR, reuses `gates/ci.py`'s `_approved_roles_on_issue` to classify
  phase1 (unapproved) vs phase2 (approved, still open), skips
  `exclude_issue`, returns `(blockers, ok)`.
- Wired the gate into `_spawn_one` itself (not only `main()`), so the
  auto-respawn path (`_respawn_or_cap` -> `_spawn_one`) is covered too —
  per the after-proposal hunt finding
  (`docs/reports/2026-08-10-hunt-returned-pr-spawn-gate.md`). Behavior:
  - `ok=False` (gh failure): stderr warning + `returned_pr_gate_fail_open`
    ledger event, spawn proceeds.
  - `ok=True`, blockers present, no `--despite-returned`: prints each
    blocker (`issue #N (phase1|phase2): <url>`), writes
    `returned_pr_gate_refused` ledger event, returns 1 without spawning.
  - `ok=True`, blockers present, `--despite-returned`: writes
    `returned_pr_gate_bypassed` ledger event, spawn proceeds.
  - No blockers: passes silently.
- Added `--despite-returned` flag to `main()`'s argparser, threaded
  through to the top-level `_spawn_one` call.
- `test_spawn.py`: added a `ReturnedPrGate` test class covering
  `_open_role_prs` filtering/gh-failure, `_undispositioned_role_prs`
  exclude/phase-classification, and `_spawn_one` wiring (refusal, empty
  pass, override bypass, fail-open). Updated one pre-existing test
  (`Ledger.test_entry_carries_the_live_log_path`) to mock the new gate,
  since it asserted exactly one ledger write per `_spawn_one` call and
  the unmocked `gh` call in that test environment would otherwise add a
  second (fail-open) entry.

derived: `python3 -m pytest test_spawn.py -k "ReturnedPrGate" -q`
```
........
8 passed, 373 deselected in 0.25s
```

derived: `python3 -m pytest test_spawn.py -q`
```
381 passed in 33.16s
```

## Why

Reuses `_approved_roles_on_issue` instead of a new disposition predicate
(avoids drift between two "is phase-1 approved" implementations);
fails open on `gh` lookup failure with an auditable ledger event, mirroring
`contract-guard.sh`'s existing fail-open stance for the same reason
(gate runs on every spawn, not a single deliberate action). Full
rationale in the proposal's `## Rationale`.

## Upstream

Basis: docs/issue-680/proposals/2026-08-10-returned-pr-spawn-gate.md

## What did not work

None.

## Open findings

None.
