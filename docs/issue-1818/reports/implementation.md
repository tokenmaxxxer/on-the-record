---
code_under_review:
  - gates/ci.py
  - spawn.py
  - test/test_convention_equivalence.py
  - test/test_approval_role_field.py
loop_state: landed
type: feature
breaking: false
verdict: pass
---

## What was done

Delivered the approved proposal (docs/issue-1818/proposals/approval-record-carrier.md):
`gates/ci.py:189` `_approved_roles_on_issue` now reads a workspace-local
structured approval record (`.git/gh-read-cache/issue-<n>-approvals.json`,
sibling to the existing `spawn._etag_cache_path` comments-cache
convention) before its comment scan (canonical: gates/ci.py:189-224,
this branch), unions any roles it holds into the result, then — after
the always-run, unmodified comment scan — writes back any newly-scanned
`{role: {actor, timestamp}}` entry not already covered by the record
(write-through cache). `spawn.py` gained the one new helper
`_approval_record_path` (`spawn.py:1334`, next to `_etag_cache_path`)
for the record file path; no read-path signature changed. New
`test/test_approval_role_field.py` covers dual-write shape,
field-read-preferred, fallback for a role the record does not yet
cover, the legacy token-only case, `_ok=False` fail-closed, and a
corrupt record file falling back to the scan. `test/test_convention_equivalence.py`
gained two additions-only cases under `ApproveGrammarEquivalenceTest`
proving the record-present and record-absent paths produce identical
role output.

## Why

Requirements engineering + risk consults on this issue (frozen migration
order entry 4, docs/issue-1792/reports/implementation.md §Migration
order) require: dual-write a structured approval record alongside the
unchanged APPROVE-token comment, with the python needle consumer
(`_approved_roles_on_issue`) reading the record when present and
falling back to the exact-needle scan otherwise, identical outcomes on
both paths, harness green with additions only.

## Upstream / basis

- docs/issue-1818/proposals/approval-record-carrier.md (approved via
  issue comment `APPROVE issue-1818/implementation`)
- docs/issue-1818/reports/implementation/survey.md
- 2b3cccd5 (phase-1 commit, this branch)

## Acceptance evidence

### `python3 -m pytest test/test_convention_equivalence.py -q` (executed live)

```
bringing up nodes...
bringing up nodes...

...............................                                          [100%]
31 passed in 0.85s
```

`git diff HEAD~1 -- test/test_convention_equivalence.py` — additions only
(0 removed/altered lines against the phase-1 baseline commit; `+39` new
lines, no existing golden-case line touched):

```
 test/test_convention_equivalence.py | 39 +++++++++++++++++++++++++++++++++++++
 1 file changed, 39 insertions(+)
```

### `python3 -m pytest test/test_approval_role_field.py -q` (executed live)

```
bringing up nodes...
bringing up nodes...

......                                                                   [100%]
6 passed in 0.81s
```

Covers dual-write shape, field-read, fallback (record-absent role),
and the legacy token-only case (`test_legacy_token_only_issue_resolves_identically_to_today`),
plus `_ok=False` fail-closed and corrupt-record fallback.

## What did not work

Nothing in the delivered scope. See `## Open findings` below for a
test-isolation gap surfaced outside the frozen write set.

## Rationale for deviations

The approved proposal's build-steps section did not anticipate that
delivering the write-through cache would break other, pre-existing
tests outside this issue's frozen write set. Once the cache landed,
`gates/test_closes_gate_ci.py` (not in `files:`) started failing —
documented fully in `## Open findings` and in
docs/issue-1818/reports/implementation/deviation-log.md. Per the
role-handoff contract's scope-exceeded rule, that fix was not made here
(it requires editing `conftest.py` or `gates/test_closes_gate_ci.py`,
outside `files:`); it is reported as a filed deviation with a
resolution path instead, and the delivered code otherwise matches the
approved proposal's build-steps section as written.

## Open findings

canonical: `python3 -m pytest gates/test_closes_gate_ci.py -q` executed
live on this branch's working tree after the implementation edits (full
output and analysis in docs/issue-1818/reports/implementation/deviation-log.md).
Summary: the new write-through cache persists real approval state
across tests in that file that call `_approved_roles_on_issue` with the
real repo checkout (`Path(".")`) and reuse the same literal issue
number (245) across contradictory mocked scenarios within a single
process — those tests assumed the function was memoryless, which stops
holding once it gains a persistent cache. On `main` (pre-issue-1818,
canonical: `git stash` + re-run of the same command on this branch),
the same test file has no such failures. Fixing this needs
test-isolation work in `conftest.py` or `gates/test_closes_gate_ci.py`,
both outside this issue's frozen write set — filed as a deviation, not
fixed here (resolution path below).

canonical: `python3 -m pytest tests/test_gh_quota_guard.py::test_sweep_call_budget
tests/test_spawn.py -k test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts -q`
executed live on this branch, then repeated after `git stash` (pre-issue-1818
main state) with the same result — both failures reproduce identically
without this issue's changes, so they are pre-existing and unrelated to
this delivery.

resolution path: file a follow-up issue scoped to `conftest.py`/
`gates/test_closes_gate_ci.py` adding a `.git/gh-read-cache/*-approvals.json`
cleanup fixture (or switching those specific tests to a tmp repo root)
so the approval-record cache introduced here does not leak state across
unrelated test scenarios that share the real repo checkout and literal
issue numbers.

## Next steps

None for this delivery's own frozen scope — `loop_state: landed`. The
resolution-path issue above (test isolation in `gates/test_closes_gate_ci.py`)
is the only follow-up work identified.
