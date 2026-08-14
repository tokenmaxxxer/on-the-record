---
subject: issue-1021
role: conformance-review
kind: survey
loop_state: survey-written
---

## Board condition

canonical: git log --all --oneline (local clone)
```
b908d5a1 issue-1021 phase-2: bound decision-queue-stopgate re-block loop (#1025)
a6da1b8e issue-1021 phase-1: decision-queue-stopgate bounded re-block proposal (#1022)
```
`b908d5a1` is an implementation commit on `main`.

canonical: git ls-tree -r origin/main --name-only | grep 1021
```
docs/issue-1021/proposals/2026-08-12-decision-queue-stopgate-bounded-reblock.md
docs/issue-1021/reports/implementation.md
docs/issue-1021/reports/implementation/hunt-2026-08-12-decision-queue-stopgate-bounded-reblock.md
docs/issue-1021/reports/implementation/survey.md
```
No conformance-review report path is present in that listing, so no
conformance-review record exists yet for commit `b908d5a1`, satisfying
the marketplace conformance-review role spec's board condition
(issue-521).

## Target artifact

canonical: docs/issue-1021/reports/implementation.md frontmatter, `code_under_review:`
```
code_under_review:
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/test_decision_queue_stopgate.py
```

## Spec

canonical: gh issue view 1021
Issue #1021 ("decision-queue-stopgate: unbounded re-block loop when
decisions are operator-owned"), state CLOSED, cites R001 / northpole
req#4 (autonomy without human intervention must not degenerate into
busy-loops; req#7 no band-aids), and states an explicit Acceptance
section naming a check command and three required test cases.

## Implementation's self-report

canonical: docs/issue-1021/reports/implementation.md frontmatter/body, quoted verbatim
```
loop_state: landed
verdict: pass
canonical: python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py -q — result: 17 passed in 1.21s
```

Independently re-run for this survey:
canonical: python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py -q
```
17 passed in 1.19s
```

## Scout skip

Skipped. Reason: this is conformance-review requirement extraction,
not a product-build — the requirement list is derived directly from
the issue's stated Requirement linkage and Acceptance section (see
Spec above), and there is no product-facing design decision open to
scout.
