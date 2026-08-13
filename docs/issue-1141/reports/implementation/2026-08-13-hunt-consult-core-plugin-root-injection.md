---
proposal: docs/issue-1141/proposals/consult-core-plugin-root-injection.md
---

# Hunt record — consult-core-plugin-root-injection

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned hermetic test cannot exercise consult_cmd()'s real env construction as scoped, so a broken/missing CLAUDE_PLUGIN_ROOT_CORE injection inside consult_cmd() can pass the test undetected
Kind: composition
Seed: docs/issue-1141/proposals/consult-core-plugin-root-injection.md ("What will be done" + "How you'll know it worked" sections)
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only proposal, no code diff yet)
started_at: 2026-08-13T00:00:00Z
ended_at: 2026-08-13T00:01:00Z

### Reproduce
```
grep -n "def spawn_cmd" -A5 spawn.py | head -8
grep -n "def consult_cmd" -A80 spawn.py | grep -n "subprocess.run"
```
`spawn_cmd()` (spawn.py:4241) returns `(cmd, env)` — a pure builder, never
calls subprocess itself, so a test can call `spawn_cmd(...)` directly and
assert on the returned `env` dict.

`consult_cmd()` (spawn.py:4368) is structured differently: it builds `env`
(spawn.py:4409) and then calls `subprocess.run(cmd, cwd=..., input=...,
env=env, ...)` (spawn.py:4441) *inline, in the same function, in the same
try block* — there is no separate function that returns the constructed
`env` without also spawning the real `claude` binary.

The proposal's "What will be done" section describes only adding the
one-line `core_dir = next(...)` / `env["CLAUDE_PLUGIN_ROOT_CORE"] = ...`
injection inside `consult_cmd()`; it does not mention extracting an
env-builder function, nor monkeypatching `subprocess.run`. Yet "How you'll
know it worked" claims the test will assert "the env `consult_cmd()`
constructs for its subprocess" hermetically, "no live claude process".
As `consult_cmd()` is currently structured, the only way to get that env
dict without actually invoking `claude` is for the test to reimplement the
injection logic itself (as `gates/test_env_resolve.py`'s `resolve_core()`
already does for the bash side) rather than calling the real
`consult_cmd()`. A test built that way passes or fails on its own
reimplementation, not on `consult_cmd()`'s actual behavior — so if the
real injection inside `consult_cmd()` is later broken, misplaced outside
the `try` block, guarded by a typo'd condition, or dropped in a refactor,
the test keeps passing while the regression it exists to prevent recurs
silently. This is exactly the class of gap the proposal explicitly says
this fix protects against ("pins the exact same acceptance shape
`spawn_cmd()` already has to meet, and cannot silently re-diverge") — but
the structural difference between the two functions means that guarantee
does not actually hold without an explicit refactor or mock the proposal
never specifies.

### Observed
Proposal text commits to a hermetic, no-live-process test of
`consult_cmd()`'s real env construction, but `consult_cmd()`'s env
construction is not separable from its live `subprocess.run` call as
currently written, and no refactor/mock is scoped to make it separable.

### Expected
The proposal should either (a) scope a refactor extracting `consult_cmd()`'s
argv/env construction into its own return-only helper (mirroring
`spawn_cmd()`'s shape) so the test can call the real code path, or (b)
explicitly scope monkeypatching `subprocess.run` inside the test so the
assertion runs against the real `env` dict `consult_cmd()` builds — otherwise
the test is scoped to end up as a second reimplementation that can drift
from the actual fix exactly like the bug it is meant to catch.
