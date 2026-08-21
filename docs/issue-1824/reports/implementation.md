---
code_under_review: HEAD
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# issue-1824 implementation record

## What was done

`gates/flows.py`'s `_pr_approved` function now dual-reads the #1818
structured approval record, per the approved proposal
(docs/issue-1824/proposals/rsb-dual-read.md).
canonical: git show 8e534e63 -- gates/flows.py

1. `_pr_approved` gained a new `root: Path = spawn.ROOT` parameter
   (defaulted so the two existing golden-case tests in
   test/test_convention_equivalence.py, which call it with only 5
   positional args, keep working unchanged).
2. Before the existing needle scan, it derives `issue_n` from `subject`
   (same idiom already used elsewhere in the file) and reads
   `.git/gh-read-cache/issue-<n>-approvals.json` via gates/ci.py's
   `_read_approval_record`, called on `spawn._approval_record_path(root,
   issue_n)`. If `role` is a key in that record, it returns True
   immediately — matching the proposal's chosen option 1 (role-exact
   short-circuit), not the issue-wide `_approved_roles_on_issue` union
   the proposal's Rationale explicitly rejected.
3. gates/ci.py's read helper is imported inside `_pr_approved`'s
   function body, not at module top (see "What did not work").
4. Both existing call sites in flows.py (the `pr_by_branch` loop and the
   `all_subjects` loop) thread the already-in-scope `root` through to
   the new parameter.
5. The fallback path (record absent/empty/missing the role) falls
   through unchanged to today's needle scan and PR-review loop.

Tests added/changed:
- test/test_convention_equivalence.py: no edit.
  canonical: git diff test/test_convention_equivalence.py (empty output)
- test/test_flows_role_field.py (new): three cases per the proposal —
  record-hit, fallback, and no-carrier-legacy (matching result across
  default-root and empty-root calls).
  canonical: git log -- test/test_flows_role_field.py

## What did not work

A module-top-level `from gates.ci import _read_approval_record` in
gates/flows.py raised a circular-import error.
canonical: python3 -c "import gates.flows" (ImportError: cannot import name '_read_approval_record' from partially initialized module 'gates.ci' — gates/ci.py already does `import flows` at its own top level)

A corrected absolute-import form still broke the test suite, because
test/test_convention_equivalence.py imports `flows` as a bare
top-level module, not `gates.flows`.
canonical: python3 -m pytest test/test_convention_equivalence.py -q (prior attempt: ModuleNotFoundError: No module named 'gates.ci'; 'gates' is not a package)

Both were resolved by moving the import inside `_pr_approved`'s
function body as a bare `import ci`, resolved via the `gates/`
directory flows.py already puts on `sys.path` at flows.py:14.

## Rationale for deviations

The approved proposal's build-steps section, item 1, specified
importing `_read_approval_record` from `gates.ci` without specifying
module-top vs. function-local placement, and its survey checked
gates/ci.py's own imports only, not flows.py's reverse dependency on
it. The circular import surfaced during this build (see "What did not
work" above) needed the function-local placement instead. This changes
only where the import statement sits, not what is read, how the record
path is derived, `_pr_approved`'s role-exact semantics, or
`flows_payload()`'s output shape — all of which match the proposal.

## Why

Issue #1824 (frozen migration order entry 6, docs/issue-1792/reports/
implementation.md §Migration order): gates/flows.py's `_pr_approved`
was the last remaining site deriving approval state via its own
needle-only scan, never touching the #1818 structured approval record
that on-the-record/hooks/approval-gate.sh (#1821) and gates/ci.py
(#1818) already dual-read.

## Upstream

Based on docs/issue-1824/proposals/rsb-dual-read.md, approved via
`APPROVE issue-1824/implementation` on the #1824 issue thread; building
on #1818's gates/ci.py `_read_approval_record`/spawn.py
`_approval_record_path` and #1821's dual-read shape for the same record
file.

## Acceptance verification

Requirement 1 — equivalence harness green, additions-only diff:

canonical: python3 -m pytest test/test_convention_equivalence.py -q

```
bringing up nodes...
bringing up nodes...

.................................                                        [100%]
33 passed in 0.81s
```

canonical: git diff test/test_convention_equivalence.py (empty output — no edits at all, a strict subset of additions-only)

Requirement 2 — flows output matching across carrier/fallback/no-carrier paths:

canonical: python3 -m pytest test/test_flows_role_field.py -q

```
bringing up nodes...
bringing up nodes...

...                                                                      [100%]
3 passed in 0.80s
```

canonical: python3 -m pytest test/test_convention_equivalence.py -q
checked: python3 -m pytest test/test_convention_equivalence.py -q — result: 33 passed, 0 skipped

canonical: python3 -m pytest test/test_flows_role_field.py -q
checked: python3 -m pytest test/test_flows_role_field.py -q — result: 3 passed, 0 skipped

## Test-tier note (issue #1518)

`.on-the-record/test-tiers.json` is present in this repo.
canonical: cat .on-the-record/test-tiers.json

This change (gates/flows.py, test/test_convention_equivalence.py
untouched, test/test_flows_role_field.py new) does not match any
`trigger_change_classes` entry (`spawn.py`, `tests/test_spawn.py`,
`on-the-record/hooks/*.sh`, `on-the-record/hooks/test_*.py`), so only
the `fast` tier applies.

canonical: python3 -m pytest -q -m "not slow" (2434 passed, 18 xfailed, 3 xpassed, 2 failed; budget 300s, actual 37.92s)

Two of those failures — a `test_sweep_call_budget` case and a
`PollHeartbeatMarkerRelocationTest` board-wide-sweep case — reproduce
the same way with this issue's diff fully removed via `git stash`.
canonical: git stash && python3 -m pytest -q tests/test_gh_quota_guard.py tests/test_spawn.py -k "test_sweep_call_budget or test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts" && git stash pop (same two failures reproduced before this change was applied — pre-existing, unrelated)

## Open findings

None.
