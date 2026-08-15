kind: current-state-survey
subject: issue-1202
role observed: implementation
session/PR observed: PR #1242 (branch issue-1202/implementation), commits
0200bbc01f0e04a853d7fe4e073fc73bfc3c0308 and
68f908312b0af8ab121504d38d51353b33d537f3, merge commit
be97b778f9b6e53145dddb118a4c018d04b3f7ae — canonical: gh pr view 1242
--json number,url,mergeCommit,commits (read this session).

## What was read this session

- gh issue view 1202 (full issue body: Problem/Requirements/Acceptance/
  실행 계획, and all 11 comments — the two APPROVE comments for
  requirements-engineering and implementation, and the "Verdict:
  escalate" delegated-judgment lines).
- gates/finding_shape.py (full file, this session): `check_finding`,
  `_parse_frontmatter`, `_section_body`, `session_summary_path`,
  `check_rate_bound` — the shape gate + N=3/session rate bound.
- gates/findings_due.py (full file, this session): `_findings_dirs`,
  `findings_due`, `format_report` — scans
  `docs/reports/findings/<role>/*.md` and
  `docs/issue-*/reports/findings/<role>/*.md`, skips
  `*-session-summary.md` and any finding carrying `relayed_to_issue:`.
- gates/test_findings_due.py (full file, this session) — confirms the
  exact fixture path convention (`docs/reports/findings/<role>/` and
  the per-issue variant) the module expects.
- spawn.py:5482-5489 (this session) — `findings-due` CLI subcommand
  wired to `findings_due.findings_due` / `format_report`, print-only,
  same shape as `roles-due`/`needs-due`.
- docs/issue-1202/reports/implementation.md (full file, this session) —
  the implementation role's own record. States acceptance checks 1-3
  covered by unit tests (`test_finding_shape.py` 9/9,
  `test_findings_due.py` 5/5, `test_consult_siblings.py` 4/4, all
  reproduced in that record's fenced output) and states plainly that
  acceptance check 4 (live role session + orchestrator relay) was
  **not run** that session ("MOCK: not run this session (single
  headless turn, no second turn to relay from)").
- docs/handbooks/record-authoring.md (full file, this session) — used
  as the real domain-rule citation source for the scratch fixture
  finding this session builds (see proposal).

## Scope statement

This session observes role `implementation`, PR #1242 (merged commit
be97b77), issue #1202, specifically the step-3 gap its own record
names: acceptance check 4 ("live — one real role session records a
genuine domain finding on a fixture repo and the orchestrator relays
it") was implemented as unit-tested machinery but never exercised live
against a real fixture repo. This role's job is to close that
executed-live gap for the machinery that IS reviewable this way
(`finding_shape.py`'s gate + rate bound, `findings_due.py`'s
board-reading) — not to re-verify requirements 1-3, which the
implementation record already backs with its own reproduced test runs.

## Scout skip record

Skipped. Condition: "the spec literally leaves no design decision
open" — the acceptance check itself specifies the exact steps (build a
fixture repo, write a finding via the advisory queue, confirm the shape
gate accepts it and the rate bound holds, confirm
`spawn.py findings-due` surfaces it); there is no product-facing or
architectural choice for this role to scout exemplars for.
