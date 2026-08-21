---
subject: issue-1958
kind: survey
---

# Survey: re-tiering `.on-the-record/test-tiers.json`

## Scope

Write set for this phase: `.on-the-record/test-tiers.json`, `docs/`. No code
change to the matcher (`gates/test_tier_contract.py`) or to `spawn.py` /
`tests/test_spawn.py` is in scope for this issue.

## Current contract

canonical: read `.on-the-record/test-tiers.json`.

```json
{
  "fast": {
    "command": "python3 -m pytest -q -m \"not slow\"",
    "budget_seconds": 300
  },
  "slow": {
    "command": "python3 -m pytest -q -m slow",
    "trigger_change_classes": [
      "spawn.py",
      "tests/test_spawn.py",
      "on-the-record/hooks/*.sh",
      "on-the-record/hooks/test_*.py"
    ]
  }
}
```

## Fast-tier wall clock (clean checkout)

acceptance: `python3 -m pytest -q -m "not slow"` — result: 39.47s wall
clock, versus the declared 300s `budget_seconds` — canonical: this
session's own live run, transcript below.

```
30 failed, 2399 passed, 18 xfailed, 3 xpassed in 39.47s
real  0m39.797s
```

The 30 failures are pre-existing (unrelated test/gh-quota/consult-trace/
judge-queue tests, not in this issue's write set). Acceptance check 1's
text is a wall-clock-vs-budget comparison; it does not require a zero
failure count.

## Matcher granularity (consult caveat)

canonical: `gates/test_tier_contract.py:78-90` (`select_tier`), full 95-line
file read this session for absence of any other input.

```python
def select_tier(contract, changed_paths):
    if contract is None or not contract.slow_command:
        return "fast"
    for changed in changed_paths:
        for pattern in contract.slow_trigger_change_classes:
            if fnmatch.fnmatch(changed, pattern):
                return "slow"
    return "fast"
```

`select_tier` matches on `changed_paths` (relative file paths) with
`fnmatch.fnmatch` — whole-path glob matching; `changed_paths` plus the
contract are the only inputs anywhere in the file — no diff-hunk or
symbol-level input exists (canonical: full-file read above). This confirms
the consult caveat: matching is whole-file (or whole-glob-pattern), never
finer than "this path changed."

canonical: `find . -name spawn.py -o -name test_spawn.py` — run live this
session.

```
./spawn.py
./tests/test_spawn.py
```

Both are single, fixed-location files, so `fnmatch.fnmatch("spawn.py",
"spawn.py")` is an exact match, and today any diff touching either file —
even a single-line comment or an unrelated dead-code removal, as in issue
#1955's `spawn.py` phase-2 diff (commit `ac4d56a0`) — trips the slow tier.

## Why `spawn.py` is a monolith, and what the slow tests cover

derived: `wc -l spawn.py tests/test_spawn.py` — run live this session.

```
8413 spawn.py
11509 tests/test_spawn.py
```

derived: `grep -c '@pytest.mark.slow' tests/test_spawn.py` — run live this
session.

```
63
```

derived: `grep -cE '^( {4})?def test' tests/test_spawn.py` — run live this
session.

```
524
```

`spawn.py` is a single 8413-line file with no submodule split —
orchestration, judge/consult plumbing, gh CLI wrappers, subprocess spawn
logic, board/queue handling all in one file. Of `tests/test_spawn.py`'s 524
test functions (above), 63 carry `@pytest.mark.slow` (above) — integration-
shaped tests (subprocess spawning, gh CLI call-count budgets, judge daemon
lifecycle) scattered non-locally through the file, not confined to one
function/class range.

Because (a) the matcher only sees file paths, never diff hunks, and (b)
`spawn.py` is one file with no directory/module boundary separating
slow-tested surfaces from untested ones, no glob narrower than the bare
`spawn.py` string can distinguish "this diff touches a slow-integration-
covered surface" from "this diff touches an unrelated section of the same
file" — not without either (i) teaching the matcher to read diff
hunks/symbols (a `gates/test_tier_contract.py` change, out of this issue's
scope) or (ii) splitting `spawn.py` into modules so a path glob can key on
the module boundary (a `spawn.py` refactor, also out of scope — scope here
is `.on-the-record/test-tiers.json` + `docs/` only).

## issue #1955's cost (why this issue exists)

canonical: `gh issue view 1958` (read this session, issue body's own
account) and `git log --oneline -1 -- .on-the-record/test-tiers.json`.
Issue #1955 phase 2 (commit `ac4d56a0`, "retire role-source-allowlist /
rulebook resolution path") edited `spawn.py` to delete dead code unrelated
to any of the 63 slow-marked tests; per issue #1958's own body, that diff
paid ~10 fix-rerun iterations at 4-5 min each under the current whole-file
trigger.

## Options available within this issue's scope

1. **Drop `spawn.py` (and/or `tests/test_spawn.py`) from
   `trigger_change_classes` entirely.** Restores fast iteration for
   `spawn.py` diffs unconditionally, but silently drops slow-tier coverage
   for diffs that *do* touch one of the 63 slow-tested integration paths —
   a real regression-detection gap, not just a doc gap.
2. **Keep the bare `spawn.py` trigger, and record the measured reason it
   must stay** (the path this issue's acceptance check 2 explicitly
   allows): the matcher is whole-path-only and `spawn.py` is a single
   undivided file, so no in-scope JSON-only change can achieve finer
   granularity without either a matcher change or a file split, both out
   of scope here.
3. A hybrid is not achievable in-scope: narrowing the pattern below the
   whole file (e.g. a directory glob) needs an actual directory boundary
   inside `spawn.py`'s codebase to key on, which does not exist yet.

This survey does not resolve the choice between 1 and 2 — that judgment
call, with its rejected-alternative rationale, belongs in the proposal.
