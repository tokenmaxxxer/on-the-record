---
status: approved
files:
  - gates/recovery_policy.py
  - tests/test_recovery_policy.py
---

# #1670 — bounded-retry recovery policy

## Request

When a spawned worker dies, decide whether to respawn identically, respawn with a
handoff brief, or escalate to a human — instead of the current unconditional respawn
on `pr-expected-missing`. Bound retries per (issue, role) with a cap (default 2) and
stop retrying into a repeated identical failure.

## Constraints

- Pure function, no network, unit-testable on fixtures (issue acceptance criterion).
- Reuse spawn.py's existing `reconcile()` signal source (`pr-expected-missing` kind) —
  do not re-derive git/gh state inside this module.
- Module + tests only; no spawn.py/directive wiring in this delivery (sequenced
  follow-up, avoids collision with concurrent spawn.py work per the issue).

## Rationale

Chosen: a pure `classify(failure_signals: dict) -> str` taking already-observed state
(`has_commit`, `has_pr`, `respawn_count`, `cap`, `failure_signature`,
`last_failure_signature`), plus a thin `classify_from_state()` wrapper that reads a
per-(issue,role) JSON counter file on disk for the wrapper path only.

Alternative considered: have the policy module call spawn.py's git/gh helpers
directly (mirroring how `_build_expected`/`reconcile` are wired into the poll loop)
so the wrapper reads live git/PR state itself. Rejected — the issue's acceptance
criterion requires a pure function tested on fixtures with no network, and spawn.py's
own helpers shell out to `git`/`gh`; folding that into `classify()` would make the
core decision function untestable without a live repo/network, which is exactly what
the acceptance check forbids.

## What will be done

- `gates/recovery_policy.py`: `classify(failure_signals) -> Literal["RESPAWN_IDENTICAL", "RESPAWN_WITH_HANDOFF", "ESCALATE"]`
  and `classify_from_state(issue, role, has_commit, has_pr, failure_signature, cap=2, state_dir=...)`
  wrapper that persists/reads respawn counts and last signature per (issue, role).
- `tests/test_recovery_policy.py`: fixtures for pre-first-commit→RESPAWN_IDENTICAL,
  has-commit-no-PR→RESPAWN_WITH_HANDOFF, count>=cap→ESCALATE, same-signature→ESCALATE,
  cap-counter unit coverage, and the #1660 live-shaped reconstruction (2 failed
  same-signature respawns → ESCALATE, not a 3rd blind respawn).

## Out of scope

- Wiring `classify()` into spawn.py's `reconcile()`/poll loop.
- Any change to `reconcile()` itself or to `pr-expected-missing` emission.

## How you'll know it worked

`python3 -m pytest tests/test_recovery_policy.py -q` passes, covering all four
acceptance-criteria fixtures plus the cap-counter and #1660 reconstruction cases.
