# Survey — issue #1670 recovery policy

derived: `grep -n "pr-expected-missing" spawn.py`
```
spawn.py:2024:            "kind": "pr-expected-missing",
spawn.py:7747:                                    f"health-repair:{issue}:{role}:pr-expected-missing")
```

`reconcile(expected, observed)` at spawn.py:1977 is the existing signal source. It is
a pure function comparing roster-expected state vs. observed session/PR/git state and
returning `[{"kind": ..., "detail": ..., "next_action": ...}]`. Relevant branch (spawn.py:2016-2024):
`expects_pr and pr_number is None and verdict != "in-progress"` -> emits
`{"kind": "pr-expected-missing", "next_action": "respawn"}` — an unconditional respawn,
no classification of why the worker died, no cap, no signature comparison.

Write set for #1670: gates/recovery_policy.py (new, pure module) + tests/test_recovery_policy.py (new).
No change to spawn.py/reconcile — issue explicitly scopes this to the policy module only,
wiring is a sequenced follow-up (avoids collision with concurrent spawn.py work).

Design decision: `classify()` takes a `failure_signals` dict already carrying
`has_commit`, `has_pr`, `respawn_count`, `cap`, `failure_signature`,
`last_failure_signature` — i.e. it consumes reconcile()'s kind of output (a
`pr-expected-missing`-shaped death signal) plus session state, rather than
re-deriving git/gh state itself, matching "REUSE that signal source" instruction.
Alternative considered: have classify() call into spawn.py's git/gh helpers directly —
rejected, since the issue calls for a pure function testable on fixtures with no
network, and spawn.py's helpers shell out to git/gh.
