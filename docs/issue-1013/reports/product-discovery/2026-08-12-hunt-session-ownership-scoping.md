---
proposal: docs/issue-1013/proposals/session-ownership-scoping.md
---

# Hunt record — session-ownership-scoping

## after-proposal — stance 1: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — the design is keyed entirely on `session_id`, which is populated from `os.environ.get(ORCHESTRATOR_SESSION_ID_ENV)` (spawn.py:5427, 5516), but nothing anywhere in the repository ever sets/exports `ORCHESTRATOR_SESSION_ID` before an orchestrator session runs spawn.py — so in real operation every roster entry's `session_id` is always `None` and the "own entries" filter degenerates to the empty-state/no-op case for every session, not just the single-session machine. The path the build needs (whatever launches an orchestrator session — a wrapper/harness invocation that exports `ORCHESTRATOR_SESSION_ID` per concurrent session) is outside the frozen write set (spawn.py, tests/test_spawn.py) and outside the proposal's scope, so phase-2 cannot make the feature actually distinguish two concurrent sessions even after implementing A-F correctly.
Kind: design-error
Seed: docs/issue-1013/proposals/session-ownership-scoping.md (design section A-F, keyed on `session_id`/`ORCHESTRATOR_SESSION_ID_ENV`)
cap_seconds: 120
tier: default
diff_stat_lines: 2 files changed (proposal + survey), see `git show e1106e5 --stat`
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
grep -n "ORCHESTRATOR_SESSION_ID_ENV\]\|os.environ\[ORCHESTRATOR_SESSION_ID_ENV\]\|environ.setdefault.*ORCHESTRATOR" spawn.py
# -> no output: spawn.py only ever *reads* this var (2 call sites, spawn.py:5427,5516), never sets it
grep -n "ORCHESTRATOR_SESSION_ID" harness/driver.py
# -> no output: the harness driver never exports it either
grep -rn "export ORCHESTRATOR_SESSION_ID\|ORCHESTRATOR_SESSION_ID=" . --include="*.sh" --include="*.py" --include="*.md" | grep -v docs/
# -> no output anywhere in the codebase (only docs describe the var, nothing sets it)
```

### Observed
No process in the repository — not spawn.py, not the harness driver that launches orchestrator sessions, not any hook — ever assigns a value to `ORCHESTRATOR_SESSION_ID`. `os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None` at spawn.py:5427/5516 therefore evaluates to `None` for every roster entry on every real invocation today, and will continue to after phase-2 builds A-F strictly within spawn.py + tests/test_spawn.py, since the proposal's write set cannot touch whatever launches the orchestrator process to set the env var it depends on.

### Expected
For the scoping feature to distinguish two concurrent operator sessions (the proposal's entire stated intent), some process outside spawn.py must generate and export a distinct `ORCHESTRATOR_SESSION_ID` per concurrent orchestrator session before spawn.py runs. That process/path is not named anywhere in the proposal's write set, constraints, or out-of-scope section — it is simply assumed to already exist ("no `ORCHESTRATOR_SESSION_ID_ENV` ever set" is treated only as the single-session degenerate case, not as today's actual universal case).
