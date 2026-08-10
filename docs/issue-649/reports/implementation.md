---
code_under_review:
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/test_delegated_judgment_gate.py
type: fix
breaking: false
verdict: accept
loop_state: landed
---

## What was done

`on-the-record/hooks/delegated-judgment-gate.sh`: before the `origin/main`
diff call, checks `git rev-parse --verify -q refs/remotes/origin/main`. When
it fails, posts an explicit `gh issue comment` naming the missing ref and the
fetch fix (`git fetch origin main`), then exits 0 — instead of silently
exiting 0 with no output (hunt #628 finding). The existing "diff succeeded,
zero changed paths" silent path is untouched.

`on-the-record/hooks/test_delegated_judgment_gate.py`: added the red/green
fixture pair — `t_missing_origin_main_reports_explicit_outcome` (red,
`origin/main` absent → explicit `gh` comment) and
`t_present_origin_main_unchanged_behavior` (green, `origin/main` present →
current behavior unchanged).

Ran `python3 on-the-record/hooks/test_delegated_judgment_gate.py`: 23 passed,
including both new fixtures.

## Why

Approved phase-1 proposal `docs/issue-649/proposals/implementation.md`
(PR #654, merged): refuse-and-instruct was chosen over silently falling
back to a guessed local ref, because a silent fallback is harder to notice
than the no-op it replaces (still produces gate output, just against
unverified data), in exactly the fresh-clone shape hunt #628 flagged.

## Upstream

docs/issue-649/proposals/implementation.md (PR #654, merged)

## What did not work

None.

## Open findings

None.

## Anomaly note

PR #658 (an earlier phase-2 attempt against this same branch) was closed
after finding no phase-2 approval yet: `gh pr view 654 --json reviews`
returned `[]` and no exact `APPROVE issue-649/implementation` issue comment
existed at that time, so `approval-gate.sh` blocked writing this record and
that PR shipped code without one. That approval comment now exists on issue
#649 (posted after #658 closed), which is what opened this session's phase 2.
The code from #658 was already present on this branch (commit 1cb1d4a,
unchanged) and only this record was added to complete the delivery.
