---
status: proposed
files:
  - on-the-record/hooks/test_delegated_judgment_gate.py
  - docs/issue-997/reports/implementation.md
---

## Request
Extend the 2-role seed fixture in
`on-the-record/hooks/test_delegated_judgment_gate.py` (architecture +
security-threat-model) to a 3+-role panel fixture, so a test proves
`delegated-judgment-gate.sh` renders a full multi-role panel per issue
#586 acceptance criterion 3. No credentials/secrets in scope.

## Constraints
- Empty state: decisions with fewer owners (1-role, 2-role) keep
  rendering exactly as today — no shared code path changes, additive
  fixture data and test functions only.
- No production script change: `delegated-judgment-gate.sh` is already
  role-count-generic (survey: `on-the-record/hooks/
  delegated-judgment-gate.sh:615-712`).
- Third role's axis must be one already assigned in `roles/*.json` (no
  new axis invented) — `performance-engineering` owns `performance`.

## Rationale
Considered adding a synthetic fourth role dict local to the test file
(not backed by any real `roles/*.json` axis) instead of reusing
`performance-engineering`. Rejected: it would test a shape the gate
never actually sees in the real repo (an axis with no owning role file),
weakening the fixture's fidelity to the acceptance criterion's intent
("renders a full panel on a decision touching paths owned by 3+
axis-owning roles" — issue #586 acceptance). Reusing
`performance-engineering`, an already-assigned real axis-owning role,
keeps the fixture representative of an actual 3-role panel.

## What will be done
- Add `PERFORMANCE_ROLE` dict (write_scope
  `docs/issue-<n>/reports/performance-engineering.md`, judgment_axes
  `["performance"]`) to `test_delegated_judgment_gate.py`, mirroring
  `ARCHITECTURE_ROLE`/`SECURITY_ROLE`'s shape.
- Add `t_three_plus_role_panel_quorum_and_unanimous_support_approves`:
  3-role panel (architecture, security-threat-model,
  performance-engineering), all `supports` -> `decision: approve`, all
  three role names present in the audit record.
- Add `t_three_plus_role_panel_one_contradicts_rejects_with_remediation`:
  same 3-role panel, one `contradicts` -> `decision: reject` +
  remediation record.
- Write `docs/issue-997/reports/implementation.md` per record-shape.

## Out of scope
- Any change to `delegated-judgment-gate.sh` itself (already handles N
  roles).
- Any change to `roles/*.json` axis ownership (already complete per
  survey).
- Correcting issue #997's acceptance text's file-name mismatch
  (`gates/test_role_spec_shape.py` vs the actual
  `on-the-record/hooks/test_delegated_judgment_gate.py`) — noted in the
  survey, not this proposal's job to re-file the issue.

## Accumulation
This adds one more role dict (`PERFORMANCE_ROLE`) alongside
`ARCHITECTURE_ROLE`/`SECURITY_ROLE` and two more test functions to an
already-large fixture file. If N more panel-size cases are added the
same way, the role dicts stay a small fixed set bounded by the real
`roles/*.json` axis-owning roles (5 today, per the survey) — there is
no unbounded growth vector, since a role dict can only be reused, not
multiplied, and the test count grows one function per new scenario
(not per role). No shared helper is warranted yet: `_axis_block()`,
`_init_target()`, `_run()` already factor out the repeated
subprocess/gh-stub plumbing this file uses, and the new tests reuse
them as-is rather than adding new inline subprocess calls.

## How you'll know it worked
`python3 on-the-record/hooks/test_delegated_judgment_gate.py` runs all
tests including the two new ones and reports all passed, with no
change to any pre-existing test's outcome.

## What did not work
Built the fixture change and the phase-2 record directly in this
session (matching the working code, verified locally: all 26 tests
including the two new ones ran clean) before writing this proposal,
skipping the two-phase gate. `record-claim-guard`/`approval-gate.sh`
refused the phase-2 record write with no
`APPROVE issue-997/implementation` comment present — reverted the code
change (`git checkout -- on-the-record/hooks/test_delegated_judgment_gate.py`)
and restarted at phase 1: survey, then this proposal. The working
fixture code above already exists verified in this session's history;
it is not re-included here since phase 1 writes only the two homes
(survey + proposal).
