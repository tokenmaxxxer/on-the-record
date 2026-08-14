# Deviation log

2026-08-14T14:39:00Z filed execution-observation(issue-452): drafted
the full docs/issue-452/reports/execution-observation.md record content
(all checks re-run live, outcome computed) but the Write was denied.

canonical: on-the-record/hooks/approval-gate.sh PreToolUse-hook stderr
this session — result: "no matching 'APPROVE issue-452/execution-observation'
issue comment ... from a docs/specs/approvers.md-listed account was found"

Reported here, not spawned as a new issue and not self-approved: this
role session is authenticated as an approvers.md-listed account, but
posting its own APPROVE comment would defeat the gate's self-approval-
prevention intent even though no deployed hook currently intercepts
that specific Bash `gh issue comment` path (only the "VIA DELEGATION"
citation shape is checked by `delegation-post-gate.sh`).
