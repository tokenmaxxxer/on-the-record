---
status: proposed
files:
  - docs/issue-751/reports/defect-verification.md
---

## Intent

Issue #751 asks for a read-only audit of inter-agent communication —
consult (#699), board record read paths, spawn-time context, PR-comment
relay — against the northpole requirements (#748), pinning gaps as
verified findings mapped to the requirement each blocks. The
architecture role already delivered a merged phase-1 survey covering
those four channels (docs/issue-751/reports/architecture/survey.md,
OF-1..OF-4). This role's assignment for #751 is defect-verification:
independently attempt reproduction rather than re-litigate that survey's
verdicts, with the operator's stated focus on req#5's CONCURRENT
multi-agent judgment clause specifically.

## Constraints stated so far

- Read-only: no code or mechanism changes.
- Write set is docs/issue-751/reports/defect-verification.md only.
- Findings must be reproduced (not asserted) and carry an evidence
  pointer, never a paraphrase.
- Severity assigned strictly by band lookup (Critical/High → blocking,
  Medium/Low/Unknown → advisory), never freehand.
- Phase-2 record writes are gated by contract v3 s19 behind an
  `APPROVE issue-751/defect-verification` comment from a
  docs/specs/approvers.md-listed account — none exists yet as of this
  proposal (canonical: `gh issue view 751 --comments`, run this session).

## What will be done

Phase-1 research is complete:
docs/issue-751/reports/defect-verification/survey.md re-derives
OF-1..OF-3 against current spawn.py (line numbers had drifted from the
merged survey's citations) and adds two attempts that survey did not
test: (a) whether req#5's literal "simultaneously... discussing" clause
is served by either mechanism docs/specs/northpole.md cites for it
(`consult_cmd()`, `panel-unanimous-support-v1`) — reproduced as a gap,
since both are single-shot/static, never live-concurrent; (b) whether the
harness's own `SendMessage`/`ListAgents` live-messaging tools are used or
even considered anywhere in on-the-record — reproduced as a gap, 0 grep
matches.

Phase-2 (on approval) writes docs/issue-751/reports/defect-verification.md
per contract v3 s19's required record shape: the five re-derived/reproduced
attempts with outcomes, the two findings (Finding 1: req#5's literal
clause unserved, blocking; Finding 2: harness-native concurrent-messaging
tools unaudited, advisory) each addressed to architecture with an
evidence pointer and band-lookup severity, and the record's required
fields (what was done, why, upstream basis, kind, loop_state, open
findings, next steps, resolution path).

## Out of scope

- Fixing either finding — this is a verify-record, not a remediation.
- Re-litigating architecture's OF-1..OF-4 verdicts as if they were
  wrong — they were re-confirmed, only their line citations needed
  re-deriving against current spawn.py.
- Auditing the board's write side or the orchestrator-relay/board schema
  themselves — out of scope per issue #751's own text ("beyond the
  orchestrator relaying and the board").

## How you will know it worked

docs/issue-751/reports/defect-verification.md exists, states outcomes
(reproduced/not-reproduced/blocked) for every attempt taken, and every
reproduced finding carries an addressed_to, an evidence pointer, and a
band-lookup severity — matching the defect-verification role's phase-2
quality bar and issue #751's acceptance criteria for the sub-area this
role covers (req#5 concurrency).

## What did not work

None.
