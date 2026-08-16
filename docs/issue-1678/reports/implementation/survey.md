# Survey — issue-1678: wire recovery_policy into reconcile's respawn path

skip-condition: N/A — scouting was not run; issue #1678 names a
concrete design-research brief inline ("design-research: judgment-layer
brief 2026-08-16 (OTP supervision + Temporal RetryPolicy + agent
self-healing)") already vetted at issue-authoring time, and the target
module (`gates/recovery_policy.py`) already exists with its policy
shape fixed by issue #1670 — the spec leaves no open design decision on
*what* the policy does, only *where* in spawn.py to call it. Treated as
the scout-directive's "spec leaves no design decision open" skip
condition, narrowed to the wiring question this issue actually poses.

## Current state

- `gates/recovery_policy.py` exports pure `classify(failure_signals)`
  returning `RESPAWN_IDENTICAL|RESPAWN_WITH_HANDOFF|ESCALATE`, and a
  stateful wrapper `classify_from_state(issue, role, has_commit, has_pr,
  failure_signature, cap=2, state_dir=DEFAULT_STATE_DIR)` that persists
  a per-(issue, role) `{"respawn_count", "last_failure_signature"}`
  counter as JSON under `.on-the-record/recovery-state/`.
  canonical: gates/recovery_policy.py:1-107 (read this session).

- `classify_from_state`'s `state_dir` parameter is a bare function
  default, evaluated once at module-import time — a caller wanting
  test/root isolation needs to supply `state_dir=` as an explicit
  keyword argument; patching the module attribute after import leaves
  an already-bound default unchanged. canonical: gates/recovery_policy.py:82-107
  (read this session, function signature line
  `state_dir: Path = DEFAULT_STATE_DIR`).

- `spawn.py`'s pure comparison function `reconcile(expected, observed)`
  (issue-492 ADR: docs/issue-492/decisions/2026-08-08-reconciliation-step-for-supervision.md)
  had a `pr-expected-missing` branch (PR expected, none observed,
  session not in-progress) that unconditionally returned
  `next_action: "respawn"` — no cap, no failure-class distinction. This
  is the exact branch issue #1678 names.
  canonical: git show HEAD:spawn.py | sed -n '2021,2028p' (run this
  session, pre-change spawn.py).

- `reconcile()`'s output is only ever printed as a recommendation by its
  three callers — `roster_watchdog()`, `roster_reconcile()`, and
  `drive()` — none auto-executes a respawn from the divergence list;
  `drive()`'s own docstring states this is deliberate (issue #120
  contract: drive never auto-picks/auto-executes a role action).
  canonical: spawn.py:4905-4937 (read this session, `drive()` docstring
  and body).

- `next_action` is documented as a closed set: `respawn`, `resume-watch`,
  `manual-review`, `none` (ADR Decision 3). `manual-review` ("surface to
  human, no automated verb") is the existing member matching ESCALATE's
  "surfaces, does not respawn" semantics — no new `next_action` value is
  needed. canonical: spawn.py:1988-1989 (read this session, `reconcile()`
  docstring, pre-change).

- `tests/test_spawn.py` class `Reconcile` already covers the five
  pre-existing `reconcile()` branches with plain dict fixtures, no
  mocking needed for branches that don't touch recovery_policy — this is
  the "existing test_spawn.py style" issue #1678 points at.
  canonical: tests/test_spawn.py:4739-4860 (read this session,
  pre-change).

- `tests/test_recovery_policy.py` already exercises
  `classify_from_state`'s cap/counter/persistence behavior directly
  against the policy module, using `tmp_path` for state isolation — the
  new spawn.py-side tests should prove the *wiring* (reconcile calls the
  policy with the right signals and acts on its verdict), not re-derive
  that policy-module coverage. canonical: tests/test_recovery_policy.py:107-146
  (read this session).

- `.on-the-record/test-tiers.json` lists `spawn.py`/`tests/test_spawn.py`
  as `slow`-tier trigger paths, so the slow tier
  (`python3 -m pytest -q -m slow`) must run in addition to the fast tier
  for this change. canonical: .on-the-record/test-tiers.json:1-13 (read
  this session).

## Write set (frozen)

- `spawn.py` — `reconcile()`'s `pr-expected-missing` branch calls the
  recovery-policy module's `classify_from_state` function with death
  signals (`has_commit`, `has_pr=False`, `failure_signature`) instead of
  returning an unconditional `respawn`; `_build_expected()` gains an
  `issue` key so the (issue, role) counter key is available; a lazy
  import helper mirrors the repo's existing lazy
  `sys.path.insert(0, str(ROOT / "gates"))` pattern used elsewhere in
  this file for `gates/*` modules. canonical: spawn.py:1667 (read this
  session, an existing lazy-import call site used as the pattern to
  mirror).
- `tests/test_spawn.py` — new test class covering: pre-first-commit
  under cap → respawn identically; has-commit-no-PR → respawn with
  handoff; at-cap/same-signature-repeat → ESCALATE (`manual-review`, no
  respawn); healthy-with-PR → no action (policy function not even
  called); a live-style test reconstructing issue #1660 end-to-end
  through the real policy state function with an isolated tmp state
  dir.
