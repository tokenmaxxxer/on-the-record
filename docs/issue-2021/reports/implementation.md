---
code_under_review:
  - on-the-record/hooks/approval-gate.sh
  - on-the-record/hooks/test_approval_gate.py
loop_state: landed
type: fix
breaking: false
verdict: pass
---

# issue-2021: line-anchored APPROVE token match

## What was done

`approval-gate.sh`'s plain-token check (`on-the-record/hooks/approval-gate.sh:255-268`)
changed from whole-body exact match (`body.strip() == needle`) to a
line-anchored match: the comment's first line, whitespace-stripped, must
equal `APPROVE issue-<n>/<role>` exactly. Subsequent lines are no longer
compared, so an approver can post rationale after the token. Leading or
trailing text on the token's own line still fails, since `.strip()` removes
only whitespace, never text. Non-approver authors are unaffected — the
author check (`login in approvers`) is untouched.

Added five tests to `on-the-record/hooks/test_approval_gate.py` (issue
#2021 section, above `test_approvers_absent_approved_still_denies`):
`test_first_line_exact_token_with_rationale_below_allows`,
`test_bare_token_comment_still_allows`,
`test_leading_text_before_token_denies`,
`test_trailing_text_same_line_as_token_denies`, and
`test_non_approver_author_denies`.

## Why

Issue #2021: two real approver comments of the shape "APPROVE issue-N/role
— explanation text" failed the gate's exact-match today (issues #2012 and
skill-repository #50), stranding phase-2 sessions that correctly flagged
the near-miss and stopped. The fix keeps the exact-token security posture
(still approvers.md-listed author, still the exact string) while letting
approvers attach rationale on lines after the token.

## Upstream

Basis: on-the-record/hooks/approval-gate.sh at commit
51cfeecb4320772a43a0e594c596915855ddc5a8 (this branch's parent), specifically
the `needle`/matching block at approval-gate.sh:255 before this change.

## What did not work

None.

## Open findings

None.

canonical: pytest on-the-record/hooks/test_approval_gate.py -q, run this turn in this session's working tree
acceptance: pytest on-the-record/hooks/test_approval_gate.py -q — result: 37 passed
