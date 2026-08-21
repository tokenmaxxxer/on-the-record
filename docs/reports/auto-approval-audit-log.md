# auto-approval shadow-mode audit log

Append-only. One line per `shadow_verdict()` call (`gates/auto_approval_class.py`):
`<timestamp-iso> | issue=<n> | pr=<n> | class=<class> | would_auto_approve=<bool> | reason=<reason>`

`gates/auto_approval_class.py` is still not wired into
`on-the-record/hooks/approval-gate.sh` (shadow-only scope, issue #1739);
approval-gate.sh's human-APPROVE requirement is unaffected by any line
below. As of issue #1791, `shadow_verdict()` is wired at the
approval-observation call site (`gates/ci.py:_autodetect_issue_phase()`,
which calls `_phase_from_approval()`) — one line is appended here the
first time a (issue, pr) pair is observed as phase2.
2026-08-21T07:02:37.956502+00:00 | issue=304 | pr=307 | class=not_eligible | would_auto_approve=False | reason=non-docs, non-test paths present: spawn.py
