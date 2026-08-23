---
code_under_review:
  - spawn.py
  - gates/test_requirement_drift.py
loop_state: landed
type: fix
breaking: false
verdict: pass
---

# issue-2078 — requirement-drift flags already-merged PRs (stale index read)

## What was done
canonical: spawn.py:2597-2611, 2657-2672 (`requirement_drift()`, read before
editing, this session)
`requirement_drift()` in `spawn.py` runs in two modes: full mode (`gh
issue/pr list --state open`) and delta mode (issue #1688). The delta-mode
refetch loop calls `_fetch_issue_or_pr_via_cache()` per changed number and,
before this session's edit, appended every returned item to `all_items`
unconditionally, with no check of the item's `state` field, so a number
whose GitHub state had since changed kept re-entering the index on every
delta refetch.

canonical: spawn.py diff (this session's edit, staged in this commit)
Fix: the loop now checks the refetched item's `state` field and, when it is
present and not `"open"`, skips adding it to `all_items` and evicts it from
the cache instead — so the index self-heals on the next refetch that
includes that number. Full mode already reads live state via `--state open`
list filtering and needed no change.

## Why
canonical: gh issue view 2078 (fetched this session — Acceptance section)
Acceptance criterion (verbatim): "check: drift sweep reads live PR state (or
refreshes its index) so merged/closed PRs are never flagged; test covers a
merged-PR fixture."

## Upstream basis
docs/issue-2078 (this issue); parent #2071 defect 3.

## Test coverage
canonical: gates/test_requirement_drift.py:87-110
(`test_delta_mode_merged_pr_not_flagged`, added this session, staged in this
commit)
Added a fixture test: seeds the on-disk cache with a PR recorded as open,
stubs `_fetch_issue_or_pr_via_cache` to return that same number with a
different GitHub `state` value (a fixture representing a since-resolved
PR), runs `requirement_drift(root, changed_numbers={9})`, and asserts the
output omits that number and the uncited-flag text, and that the cache no
longer holds an entry for it.

canonical: `python3 -m pytest gates/test_requirement_drift.py -q` (executed
this session)
```
$ python3 -m pytest gates/test_requirement_drift.py -q
7 passed in 0.85s
```

## Test-tier note (issue #1518)
`.on-the-record/test-tiers.json` is present.

canonical: `python3 -m pytest -q -m "not slow"` (executed this session)
```
$ python3 -m pytest -q -m "not slow"
2607 passed, 19 xfailed, 2 xpassed in 41.27s
```

`spawn.py` is in the slow tier's `trigger_change_classes`. A full unfiltered
`-m slow` run exceeded this turn's foreground budget; a targeted subset ran
instead.

canonical: `python3 -m pytest -q -m slow -k "requirement_drift or
spawn_pipeline"` (executed this session, background task b0vq1aj2a)
```
$ python3 -m pytest -q -m slow -k "requirement_drift or spawn_pipeline"
16 passed in 125.92s (0:02:05)
```
This subset is narrower than the full slow tier — stated here rather than
treated as equivalent, per the test-tier directive's observe-only clause.

## Open findings
None. See Test coverage and Test-tier note above for what was and was not
run this session.

## What did not work
None.

## Next steps
canonical: `python3 -m pytest gates/test_requirement_drift.py -q` (executed
this session, see Test coverage above — 7 passed)
None — acceptance is met by the passing new fixture test plus the fast-tier
and targeted slow-tier runs cited above.

skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion threshold, accessor chain, or cross-module import direction change involved; this is a single-function state-filter fix.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision; the fix is a straight-line state check inside an existing loop.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no new data structure, algorithm, or connection scheme introduced; existing dict/list usage unchanged.
skill-verdict: implementation-blueprint — not-applicable: single-function, single-file fix with no multi-module structure decision to freeze.
skill-verdict: test-authoring-isolation-and-fixture-strategy — invoked; applied: followed the file's existing pattern of monkeypatching `spawn.subprocess.run`/an injected fetch function per test with `tmp_path`-scoped digest and cache files (no shared state across tests), consistent with the existing `test_requirement_drift.py` fixtures.
