---
subject: issue-1958
kind: implementation
code_under_review:
  - docs/issue-1958/reports/implementation.md
  - docs/issue-1958/reports/implementation/survey.md
  - docs/issue-1958/proposals/2026-08-22-retier-spawn-trigger.md
loop_state: landed
type: doc
breaking: false
verdict: accept
---

# Implementation record: re-tiering `.on-the-record/test-tiers.json`

## What was done

Per the approved proposal (`docs/issue-1958/proposals/2026-08-22-retier-spawn-trigger.md`),
carried in PR #1961 — canonical: `gh pr view 1961` read this session,
state: MERGED — `.on-the-record/test-tiers.json`'s `trigger_change_classes`
is left unchanged — `spawn.py`, `tests/test_spawn.py`,
`on-the-record/hooks/*.sh`, `on-the-record/hooks/test_*.py` all stay as
whole-file slow triggers. No `test-tiers.json`, `spawn.py`, or
`gates/test_tier_contract.py` diff was made.

This record is the tiering doc's measured-reason record required by
acceptance check 2's second branch (bare `spawn.py` trigger stays, escape
hatch: "the tiering doc records the measured reason it must stay"). The
measured reason is recorded in
`docs/issue-1958/reports/implementation/survey.md` ("Matcher granularity
(consult caveat)" and "Why `spawn.py` is a monolith, and what the slow
tests cover" sections): `select_tier` in `gates/test_tier_contract.py`
matches only on whole relative file paths via `fnmatch.fnmatch` — no
diff-hunk or symbol-level input exists anywhere in that file (canonical:
full 95-line read of `gates/test_tier_contract.py`, survey.md) — and
`spawn.py` is a single, unsplit 8413-line file whose 63 slow-marked tests
(of 524 total in `tests/test_spawn.py`) cover integration surfaces
scattered non-locally through it (derived: `wc -l spawn.py
tests/test_spawn.py`, `grep -c '@pytest.mark.slow' tests/test_spawn.py`,
survey.md). No JSON-only change can narrow the trigger below the whole
file without either a matcher change (diff-content-aware matching) or a
`spawn.py` module split — both out of this issue's frozen scope
(`.on-the-record/test-tiers.json` + `docs/` only).

Acceptance check 1 (fast tier under 300s) is re-verified this session:

acceptance: `python3 -m pytest -q -m "not slow"` — result: 38.95s wall
clock (real 0m39.563s), versus the declared 300s `budget_seconds` —
canonical: this session's own live run, transcript below.

```
30 failed, 2399 passed, 18 xfailed, 3 xpassed in 38.95s

real	0m39.563s
```

The 30 failures are the same pre-existing set the survey recorded
(`test_spawn_judge.py`, `test_consult_trace_root.py` — gh-quota/
consult-trace/judge-queue tests unrelated to this issue's write set), not a
regression introduced here.

## Why

Trigger refinement below the whole-file `spawn.py` glob requires either
teaching the matcher to read diff content/symbols (a
`gates/test_tier_contract.py` change) or splitting `spawn.py` along module
boundaries so a narrower path glob has something to key on — both are
explicitly out of this issue's scope. Dropping the trigger outright (the
rejected alternative in the proposal's Rationale) would restore fast
iteration but silently lose slow-tier coverage for the 63 slow-marked
integration tests scattered through `spawn.py`, trading a measured,
bounded cost for an unmeasured regression-detection gap. Documenting the
constraint is the accurate outcome for this issue's scope; per issue #1958's
body and this record, trigger refinement (matcher diff-awareness or a
`spawn.py` module split) is deferred until issue #1959's split lands.

## Upstream basis

- `docs/issue-1958/proposals/2026-08-22-retier-spawn-trigger.md` (approved
  via `APPROVE issue-1958/implementation`, posted as an issue-level comment
  by `JiwonJung94`, an approvers.md account — canonical: `gh issue view
  1958 --comments` read this session).
- `docs/issue-1958/reports/implementation/survey.md` — current-state survey,
  measured matcher-granularity finding.
- PR #1961 — canonical: `gh pr view 1961` read this session, state:
  MERGED — phase-1 survey + proposal.

## Deferred work

Trigger refinement (matcher diff-content-awareness, or a `spawn.py` module
split enabling directory-level glob triggers) is deferred until issue
#1959's split lands — out of this issue's frozen scope
(`.on-the-record/test-tiers.json` + `docs/` only).

## What did not work

None.

## Open findings

None — both acceptance checks are satisfied: check 1 measured at 38.95s
(<300s budget); check 2's second branch is satisfied by this record
cross-referencing the survey's measured-reason finding.
