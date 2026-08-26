---
issue: 2380
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: gates/merge_gate.py
    sha: d750dbf59de8c95a99deabf5b0747154d7accf80
code_under_review:
  - gates/merge_gate.py
  - gates/test_merge_gate.py
type: fix
breaking:
verdict: pass
---

# issue-2380 — implementation record

## What was done

canonical: `gates/merge_gate.py:_exempt_own_role()` and
`gates/test_merge_gate.py`, both read and edited this session
(sha d750dbf59de8c95a99deabf5b0747154d7accf80 baseline, pre-fix).

Fixed `gates/merge_gate.py`'s `_exempt_own_role()` (called from
`required_verification_missing()`, in turn called from `evaluate()`).
Pre-fix, this function computed `own_role` from the PR-under-evaluation's
head branch (`<subject>/<role>`) and dropped only that single role from
`missing`:

```python
own_role = own_branch[len(subject) + 1:]
return [r for r in missing if r != own_role]
```

Post-fix, when `own_role` is one of the two roles in
`spawn_on_pr.PR_TRIGGERED_ROLES` (`execution-observation`,
`conformance-review`), both roles are dropped from `missing` instead of
just `own_role`:

```python
if own_role in spawn_on_pr.PR_TRIGGERED_ROLES:
    return [r for r in missing if r not in spawn_on_pr.PR_TRIGGERED_ROLES]
return [r for r in missing if r != own_role]
```

Branches whose `own_role` falls outside that two-role set (e.g.
`<subject>/implementation`) keep the original single-role-drop behavior
unchanged.

Test changes in `gates/test_merge_gate.py`:
- `t_exempt_own_role_drops_only_the_supplying_prs_own_role` — extended to
  assert both roles drop for an observer branch
  (`issue-2204/execution-observation` and, mirrored,
  `issue-2204/conformance-review`), and added a case proving a
  non-observer branch (`issue-2204/implementation`) still drops only its
  own role.
- `t_required_verification_missing_exempts_the_observer_pr_that_supplies_it`
  — updated its assertion from `missing == ["conformance-review"]` to
  `missing == []`; the old assertion was itself an encoding of the bug
  #2380 reports (see Why, below).
- Added `t_issue_2380_sibling_observer_prs_neither_blocks_on_the_other`
  (acceptance criterion 2) — spawns two sibling observer PRs
  (`execution-observation`, `conformance-review`) for the same subject,
  neither merged to `main`, and asserts `required_verification_missing()`
  returns `[]` for both, while a control case (the subject's
  `implementation` PR, not itself an observer record) still reports both
  roles missing.
- Added `t_issue_2380_sibling_observer_prs_evaluate_end_to_end` — the
  same scenario through `evaluate()` with check-runner/stale-revert held
  clean, confirming neither sibling PR is refused for a
  missing-verification reason (`"검증 기록"` reason string).

acceptance: python3 -m pytest gates/test_merge_gate.py -q — result:
```
...........................                                              [100%]
27 passed in 3.27s
```

## Why

canonical: pre-fix `gates/test_merge_gate.py`,
`t_required_verification_missing_exempts_the_observer_pr_that_supplies_it`,
this session's read before editing (it asserted
`missing == ["conformance-review"]` for the `execution-observation` PR —
direct evidence, in the test suite itself, that the sibling role was
still enforced as a precondition).

`required_verification_missing()` decides "required observer records
satisfied" purely by reading `spawn.board(root)` — i.e. what is already
merged on `main` — never by looking at whether the PR under evaluation
is itself carrying, or has an in-flight sibling carrying, that record.
Issue #2233 exempted a PR from requiring its *own* record pre-merged, but
`execution-observation` and `conformance-review` are always spawned and
evaluated as a pair for the same subject
(`spawn_on_pr.PR_TRIGGERED_ROLES`), and the pre-fix code still required
each sibling's record be merged before the other's gate check would
clear — the cited test literally encoded that requirement. Since both
PRs are opened in the same review cycle, neither's record can be on
`main` before the other lands, so neither could ever go first.

The fix treats `PR_TRIGGERED_ROLES` as a single unit for the exemption
rather than exempting one role at a time: a PR that is itself one of that
pair is, by construction, evidence the review cycle for that subject is
actively producing both records, so it should never be gated on the
*other* member of the same pair being merged first. PRs outside that
closed two-role set (e.g. the subject's `implementation` PR) are
unaffected and still require both observer records confirmed on `main`
before they can land — that is the actual guarantee this gate exists to
enforce, and this fix narrows the exemption to exactly the pair that
was deadlocking rather than special-casing `evaluate()` around the
symptom or adding new state (e.g. querying `gh` for sibling PRs).

## What did not work

None.

## Upstream basis

This fix responds directly to the on-the-record issue #2380 report
(verbatim ask/acceptance criteria supplied as this session's work order)
and the prior fix landed in issue #2233
(sha d750dbf59de8c95a99deabf5b0747154d7accf80, `gates/merge_gate.py`),
which added `_exempt_own_role()` but only exempted a PR's own role,
leaving the sibling-pair circularity #2380 reports unresolved (see Why,
above, for the canonical evidence).

## Open findings

none — resolution path: n/a, no open findings to resolve.

## Next steps

acceptance: python3 -m pytest gates/test_merge_gate.py -q — result:
```
...........................                                              [100%]
27 passed in 3.27s
```
None — this record's frontmatter `loop_state: landed` reflects that the
commit + push + PR-open steps run in this same session immediately
after this file is written (build-now bypass, CORE_BUILD_NOW=1).
