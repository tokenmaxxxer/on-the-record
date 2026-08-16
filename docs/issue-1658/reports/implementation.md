---
code_under_review:
  - gates/scope_adherence.py
  - gates/test_scope_adherence.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue-1658

## What was done
canonical: gates/scope_adherence.py (written this turn, as committed on this branch)
Added gates/scope_adherence.py, mirroring gates/landing_readiness.py in
shape: {scope: frozenset|None, pr_files} pure classify(), gh-wrapped
check(), main(). parse_declared_scope() reads an optional scope field
from an issue body, same spelling/comma-list family as
maintenance-targets.

canonical: gates/test_scope_adherence.py (written this turn, as committed on this branch)
Added gates/test_scope_adherence.py: twelve unit-test cases, no network.

canonical: docs/specs/enforcement-boundary.md (written this turn, as committed on this branch)
Added the required registration row for the new gate module
(gate-registration-guard.sh).

Module + tests only — no wiring into spawn.py or hooks, per the issue's
explicit deferral to avoid colliding with #1652's spawn.py change.

## Why
northpole req#6. The role's static write_scope already blocks writes
outside a role's declared area, but cannot catch intent drift within an
allowed area — a PR wandering into an unrelated module while staying
under src/** is not caught by that static check today. File-path prefixes are deterministic, so a
landing-time trajectory-vs-goal check can block this safely without
touching mid-flight watch-coverage. Advisory-when-undeclared keeps this
consumer-repo friendly.

## Upstream basis
gates/landing_readiness.py (same classify/gh-wrapper shape), per issue
#1658's explicit instruction to reuse that convention.

## Acceptance verification
canonical: acceptance: python3 -m pytest gates/test_scope_adherence.py -q — result: pass (output below, executed this turn)
```
$ python3 -m pytest gates/test_scope_adherence.py -q
12 passed in 0.93s
```

canonical: acceptance: python3 -m pytest gates/test_scope_adherence.py -q — result: pass (same run as above)
Covers the issue's Acceptance list: classify() blocks a pr_file outside
every declared prefix and passes when all files are within
(test_blocks_when_file_outside_every_declared_prefix,
test_passes_when_all_files_within_declared_prefixes); declared_scope=None
is advisory-only, never blocking
(test_declared_scope_none_is_advisory_and_never_blocks); the issue's own
record tree is always in scope, alone, alongside declared-prefix files,
and with an empty pr_files set (test_own_record_tree_always_in_scope,
test_own_record_tree_in_scope_alongside_declared_prefix_files,
test_empty_pr_files_passes_regardless_of_declared_scope); scope: field
parsing for single prefix, comma list, case-insensitivity, absent field,
empty value (test_parse_declared_scope_single_prefix,
test_parse_declared_scope_comma_list,
test_parse_declared_scope_case_insensitive,
test_parse_declared_scope_absent_returns_none,
test_parse_declared_scope_empty_value_returns_none).

canonical: acceptance: cd gates && python3 -c "import scope_adherence as sa; from pathlib import Path; print(repr(sa.parse_declared_scope(sa._issue_body(Path('..'), 1658))))" — result: pass (output below, executed this turn, live gh read against issue #1658's own body)
```
None
```
Issue #1658 itself declares no scope field, so parse_declared_scope
returns None on the live body — the same input classify() takes down
its advisory branch rather than its blocking one. This is the "an
undeclared-scope issue lands byte-identical to today" acceptance item,
checked against the issue's real current state rather than a fixture.

The issue text's illustrative example (a hypothetical issue declaring
scope: src/auth/ whose PR touches a payments path) names paths that do
not exist as a real issue/PR pair in this repo to query live; that
scenario is exercised via the unit-test fixtures cited above instead —
test_blocks_when_file_outside_every_declared_prefix and
test_passes_when_all_files_within_declared_prefixes run the same
classify() code path with equivalent inputs.

## What did not work
None.

## Open findings
None.

## Next steps
Wire gates/scope_adherence.py into the landing gate path (e.g.
landing_readiness.py's blocking_causes) as a sequenced follow-up issue —
deliberately out of scope here, per issue #1658's own text, to avoid a
spawn.py/hook collision.

## Resolution path
Follow-up issue to wire this gate into landing_readiness.py /
spawn.py.
