# auto-approval shadow-mode audit log

Append-only. One line per `shadow_verdict()` call (`gates/auto_approval_class.py`):
`<timestamp-iso> | issue=<n> | pr=<n> | class=<class> | would_auto_approve=<bool> | reason=<reason>`

This file has no lines yet — `gates/auto_approval_class.py` is not wired
into `on-the-record/hooks/approval-gate.sh` in this delivery (shadow-only
scope, issue #1739); calls to `shadow_verdict()` happen only from its own
test suite and any future manual/CI invocation, each of which appends a
line here at call time.
