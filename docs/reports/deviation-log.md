# Deviation log

2026-08-13T00:00:00Z inline upstream-defect-report(issue-1174): task
brief named an existing rulebook repo target
(tokenmaxxxer/upstream-defect-report-rulebook) that did not yet exist;
created it directly rather than inventing an unenforced docs/playbook/
bucket in the parent repo — see docs/issue-1174/reports/upstream-defect-report.md.

2026-08-17T00:00:00Z filed implementation(issue-1726): warrant-hunter
(dispatched before phase-2 completion) found
gates/test_product_capture_vs_deliverable_guard.py lines 135-159 (test
function t_empty_state_bootstrap_still_works) is an xfail(strict=False)
regression guard whose docstring still frames bootstrap-on-first-flag as
intentional behavior ("(d) regression guard for #566's
bootstrap-on-first-flag: no docs/product/ directory at all -> still
bootstraps and flags") and whose body asserts doc.exists() /
"Requirements" in doc.read_text() — the exact behavior #1726 removed by
design. canonical: gates/test_product_capture_vs_deliverable_guard.py
lines 135-159, read this session. Fixing it needs editing a file
outside issue-1726's frozen write set
(on-the-record/hooks/product-capture-stopgate.sh,
on-the-record/hooks/test_product_capture_stopgate.py), so per
SCOPE-EXCEEDED RULE the frozen write set is finished and this is
reported, not spawned — see docs/issue-1726/reports/implementation.md's
Open findings.

canonical: hunt run this session (subagent warrant:warrant-hunter,
agentId adab5ed76c4eb1a95), reproduction verified against the landed
diff — a 4-tick run (POLL_HEARTBEAT_MAX_TICKS=4, spawn.py always
reporting poll-due not-due) produced zero stdout across all 4 ticks
while the alive marker's mtime stayed pinned at tick 0.
2026-08-18T09:15:00Z filed implementation(issue-1732): a second
warrant-hunter round (dispatched before phase-2 completion, after a
phase-1 no-finding round already on record at
docs/issue-1732/reports/implementation/2026-08-18-hunt-drop-monitoring-active-heartbeat-line.md)
flagged a liveness gap: the alive marker
(`on-the-record/monitors/poll-heartbeat.sh:105-114`) that this issue's
own Resolved-problem text and the approved proposal's Rationale
(rejected alternative #2) both cite as already covering monitor
liveness is written once per session, before the tick loop starts, and
never advances again — it can only show "the Monitor process launched",
not "the tick loop is still alive N ticks later." The per-tick
`runs/poll_heartbeat_alive.json` file does advance every tick but is
consumed only internally by `directive.sh`'s
`_monitor_liveness_check_and_notify` re-arm backstop, never surfaced to
the user. This is a critique of a design trade-off already stated and
approved in issue #1732's own body and the approved proposal
(docs/issue-1732/proposals/2026-08-18-drop-monitoring-active-heartbeat-line.md,
Rationale, rejected alternative #2) — not a defect in this session's
implementation of that approved design, and resolving it needs
product/design judgment outside issue #1732's frozen write set
(`on-the-record/monitors/poll-heartbeat.sh`,
`on-the-record/monitors/test_poll_heartbeat.py`) and outside this
session's authority to re-open an already-approved decision. Per
SCOPE-EXCEEDED RULE the frozen write set stays as-is and this is
reported, not spawned — see docs/issue-1732/reports/implementation.md's
Open findings.

- 2026-08-21T00:00:00Z, inline, shared /tmp/skill-repository checkout carried a concurrent session's uncommitted partnerships-bd edits; staged only issue-1873's 6 paths via git index/hash-object instead of git add -A to avoid touching them, skill-repository working tree during this session
