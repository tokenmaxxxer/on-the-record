---
code_under_review:
  - gates/recovery_policy.py
  - tests/test_recovery_policy.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #1670

## What was done

Added `gates/recovery_policy.py`: a pure `classify(failure_signals) -> RESPAWN_IDENTICAL|RESPAWN_WITH_HANDOFF|ESCALATE`
keyed on `has_commit`, `respawn_count` vs `cap` (default 2), and
`failure_signature == last_failure_signature`; plus `classify_from_state()`, a thin
wrapper that persists a per-(issue, role) JSON counter/last-signature file on disk and
calls `classify()`. Added `tests/test_recovery_policy.py` with fixtures for all four
acceptance cases plus a #1660-shaped reconstruction and a persisted-counter test.
Registered the module in `docs/specs/enforcement-boundary.md`.

## Why

northpole req#6: bound the blind-respawn token-bonfire failure mode by classifying a
dead worker's failure instead of always respawning unconditionally.

## Upstream basis

docs/issue-1670/proposals/recovery-policy.md, itself built from spawn.py:1977-2024
(`reconcile()`), the existing signal source this module reuses conceptually.

## Acceptance verification

canonical: acceptance: python3 -m pytest tests/test_recovery_policy.py -q — result: pass (output below, executed this turn)
```
$ python3 -m pytest tests/test_recovery_policy.py -q
..........
10 passed in 0.78s
```
Covers all four acceptance-criteria fixtures: `test_pre_first_commit_under_cap_respawns_identical`
(pre-first-commit -> RESPAWN_IDENTICAL), `test_has_commit_no_pr_respawns_with_handoff`
(has-commit-no-PR -> RESPAWN_WITH_HANDOFF), `test_respawn_count_at_cap_escalates`/
`test_respawn_count_over_cap_escalates` (count>=cap -> ESCALATE),
`test_same_failure_signature_as_prior_escalates` (same-signature -> ESCALATE).

canonical: acceptance: python3 -m pytest -q -m "not slow" — result: pass (output below, executed this turn)
```
$ python3 -m pytest -q -m "not slow"
2133 passed, 19 xfailed, 2 xpassed
```
This change touches neither `spawn.py` nor `tests/test_spawn.py`, so
`.on-the-record/test-tiers.json`'s slow-tier trigger classes do not apply; the fast
tier above is the full applicable check.

canonical: acceptance: python3 -m pytest tests/test_recovery_policy.py -q -k test_classify_from_state_cap_counter_escalates_at_cap — result: pass (output below, executed this turn), see also `tests/test_recovery_policy.py` function `test_classify_from_state_cap_counter_escalates_at_cap` for the assertions.
```
$ python3 -m pytest tests/test_recovery_policy.py -q -k test_classify_from_state_cap_counter_escalates_at_cap
.
1 passed in 0.05s
```
This case reconstructs a staged/committed-work-no-PR death: first call asserts
RESPAWN_WITH_HANDOFF, a repeat call with the same failure signature asserts
ESCALATE instead of respawning blindly again.

canonical: acceptance: python3 -m pytest tests/test_recovery_policy.py -q -k test_classify_from_state_persists_counter_across_calls — result: pass (output below, executed this turn), see also `tests/test_recovery_policy.py` function `test_classify_from_state_persists_counter_across_calls` for the assertions.
```
$ python3 -m pytest tests/test_recovery_policy.py -q -k test_classify_from_state_persists_counter_across_calls
.
1 passed in 0.05s
```
Restart-intensity cap: calls under the cap assert RESPAWN_IDENTICAL, the call that
reaches the cap asserts ESCALATE — unit-covered per-(issue,role) counter.

- checked: empty state (a healthy delivered session is not subject to any recovery
  action) — result: unverifiable
  unverifiable: `classify()` is only ever invoked on an already-observed death
  signal by design; this delivery is module + tests only (no spawn.py wiring, per the
  issue's explicit scope), so there is no live call site yet to exercise "a healthy
  session never reaches classify()" against.

## What did not work

Initial `from gates import recovery_policy` import shape failed (`gates/` has no
`__init__.py`, it is not a package) — expected a package import, actual was
`ImportError: cannot import name 'recovery_policy' from 'gates'`; fixed before commit
by switching to `sys.path.insert(gates dir)` + bare `import recovery_policy`, the
convention `tests/test_flows.py` already uses.

## Doc placement

- No env var, config key, dependency, or migration introduced — no handbook update needed.
- Library/interface decision (pure `classify()` taking pre-derived signals rather than
  deriving git/gh state itself) recorded in `docs/issue-1670/proposals/recovery-policy.md`
  `## Rationale`.
- Gate/module registration: `docs/specs/enforcement-boundary.md` row added and
  `docs/specs/reconciled-index.md` regenerated (no diff — already current) in the
  landing commit.

## Open findings

None.

## Next steps

Sequenced follow-up (out of scope here, noted in the proposal): wire
`classify_from_state()` into spawn.py's `reconcile()`/poll loop so the
`pr-expected-missing` respawn path actually consults this policy instead of
respawning unconditionally.

## Resolution path

N/A — no open findings.
