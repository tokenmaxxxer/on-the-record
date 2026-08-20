# Contract v3 s19 amendment: conditional auto-approval (shadow-mode first)

Status: shadow-mode delivered (issue #1739). Real bypass activation is a
separate, future human decision — not made by this amendment.

## What this amendment adds

Contract v3 s19 requires phase 2 to open only via a human PR-review
Approve or an issue-level `APPROVE issue-<n>/<role>` comment from a
`docs/specs/approvers.md` account. This amendment describes an
additional, still-human-gated path under evaluation: a classifier
(`gates/auto_approval_class.py`) that labels low-risk PR classes
(docs-only, test-only) and records a `would_auto_approve` shadow
verdict, without changing what `on-the-record/hooks/approval-gate.sh`
actually requires.

## Shadow mode (this delivery)

- `docs/specs/auto-approval-config.json` absent, or absent
  `shadow_mode`/`quota_per_24h` fields, means the feature is off:
  `approval-gate.sh` behavior is byte-identical to today, and
  `gates/auto_approval_class.py` is not invoked as part of the approval
  path — it exists as a standalone module callable for its own tests
  and audit-log recording, not wired into the hook.
- When invoked, `shadow_verdict()` composes the classifier's own
  classification with `scope_adherence`, `stale_revert_guard`, and
  `requirement_met`'s existing PASS/ALLOW/YES results, plus a quota
  (default 5/24h) and a circuit breaker (any recorded revert of an
  auto-approved PR within a rolling 28 days suspends that class).
- Every `shadow_verdict()` call appends exactly one line to
  `docs/reports/auto-approval-audit-log.md`, whether or not the verdict
  would auto-approve.
- `approval-gate.sh` is not edited by this delivery. The human
  `APPROVE issue-<n>/<role>` requirement (or PR-review Approve) is
  unaffected by any value `shadow_verdict()` returns.

## Circular-trust ban

Any diff touching `on-the-record/hooks/`, `gates/`, or `docs/specs/` —
or any file that itself defines approval/gate semantics — is always
`not_eligible`, independent of the rest of the diff. Auto-approval logic
can never approve a change to itself or a peer file in these
directories. This is enforced inside `classify()` itself, not as a
config option.

## Runtime state

Quota and circuit-breaker state persist in
`.on-the-record/auto-approval-state.json` (repo-root runtime state, kept
out of `docs/specs/` because it is not spec text — it is data the
running system reads and writes). An absent state file reads as
zero-consumed and zero-suspended, never as unlimited.

## Path to real bypass activation (not part of this delivery)

Flipping `shadow_mode` to `false` and wiring `approval-gate.sh` to
actually skip the human APPROVE step for a `would_auto_approve` verdict
requires a separate human decision, made after the shadow-mode sample
window (>= 10 samples or 4 weeks, whichever is later) closes with zero
human-overturned would-approve verdicts. That decision, and the
`approval-gate.sh` edit it would require, are out of scope for issue
#1739.
