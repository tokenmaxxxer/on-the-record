# Deviation log

2026-08-14T00:00:00Z filed execution-observation(issue-312): the write to
docs/issue-312/reports/execution-observation.md (this role's own record
file) was refused by on-the-record/hooks/approval-gate.sh — no 'APPROVE
issue-312/execution-observation' comment from a docs/specs/approvers.md
account exists on issue #312, and this role session cannot post that
comment itself (self-approval is a structural invariant enforced by
delegation-post-gate.sh's design intent, not just its literal
delegation-citation match). The observation work itself (full
gates/test_closes_gate_ci.py suite run, live gh gate re-run attempt) ran
this session — canonical: `env -u GH_TOKEN python3 -m pytest
gates/test_closes_gate_ci.py -q` output, this turn's transcript — and its
findings are relayed in this turn's chat reply rather than the blocked
docs/ file. reported, not spawned.
