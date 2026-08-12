---
proposal: docs/issue-1077/proposals/implementation.md
---

# Hunt record — implementation

## after-proposal — stance 0: assume the gate/fix just proposed is bypassable — find the bypass

Verdict: NO FINDING
Seed: tests/test_flows.py DecisionQueueSessionScope.setUp addCleanup swap (lines 187-189)
cap_seconds: 60
tier: default
diff_stat_lines: 2
started_at: 2026-08-12T15:54:23+09:00
ended_at: 2026-08-12T15:54:23+09:00

Searched the whole repo (grep -rn "addCleanup" --include=*.py . | grep -i environ) and found only
the single occurrence in tests/test_flows.py:188-189 that the proposal already fixes. No other
addCleanup-based os.environ mutation exists anywhere in tests/ or gates/ (other os.environ["..."] = ...
assignments in tests/test_spawn.py, tests/test_gates.py, gates/test_test_env_resolve.py all use
try/finally, not addCleanup, so they are outside this LIFO-ordering bug class). Also confirmed
old_env = dict(spawn.os.environ) is captured after all other patches in setUp, and none of those
prior patches (`_patch` calls) touch os.environ, so nothing is missed from the restore snapshot.
Reproduced the LIFO bug generically (clear() before update() wipes state; swapped order restores it
correctly), confirming the fix is correct and its one-line write set is sufficient — no bypass found.
