---
name: issue-993-product-discovery-current-state
kind: current-state-survey
loop_state: surveyed
---

# Current-state survey — issue #993 (product-discovery)

## Background / context
Issue #993 body (operator, 2026-08-12): 43 `roles/*.json` exist; today's
session used only ~4 roles across 40+ landings. Ask: measure per-role
board utilization, diagnose each unused/rare role into one of 5 classes,
land the first fixes.

## Utilization — read evidence
derived: `find docs -mindepth 1 -maxdepth 1 -type d -name "issue-[0-9]*" -exec sh -c '...' _ {} \;` counting `<issue>/reports/<role>.md` and `<issue>/reports/<role>/*.md` per role, for all 43 `roles/*.json` stems
```
role                       total_records  distinct_issues
implementation             528            248
execution-observation      75             29
product-discovery          64             27
architecture               44             26
defect-verification        23             14
conformance-review         11             6
technical-feasibility      11             6
requirements-engineering   9              3
security-threat-model      3              1
technical-writing          3              1
# all other 33 roles: 0 records, 0 issues
accessibility api-design brand-design capacity-planning content-design
customer-support data-engineering data-modeling devrel
finance-unit-economics growth-analytics incident-response
interaction-design issue-retrospective knowledge-management
legal-compliance localization market-analysis marketing ml-engineering
observability partnerships-bd performance-engineering pr-communications
pricing refactoring-legacy release-engineering risk-management sales
secure-coding test-authoring user-discovery ux-engineering
# => 10 of 43 roles carry any board record at all; 33 of 43 carry zero.
```
canonical: the code-fenced table above (this survey's own `find`
re-derivation over `docs/issue-[0-9]*/reports/`, run this session).

`last-used date`: all 10 used roles have at least one record dated
2026-08-11 or 2026-08-12 per the same `find ... -printf '%T@'` sort — no
per-role staleness gap exists among the used set.

## Per-role trigger text — read evidence
derived: `python3 -c "import json;print(json.load(open('roles/<r>.json'))['use_when'])"` for each of the 33 zero-usage roles
```
accessibility: 신규 인터랙션 패턴·색상 토큰 도입 시 (board_condition: a new interaction pattern or color-token set landed on the branch AND no accessibility record exists yet for it)
interaction-design: product-discovery 스펙 확정 후 (board_condition: a requirements-engineering record landed for a screen/flow-facing requirement AND no interaction-design record exists yet for it)
secure-coding: 인증/입력처리 코드 랜딩 후 (board_condition: authentication or input-handling code landed on the branch AND no secure-coding record exists yet for that commit sha)
user-discovery: 가설 검증을 위해 사용자 인터뷰가 필요할 때 (board_condition: a product-discovery hypothesis requires user-interview validation AND no user-discovery record with a pain-confirmed|not-confirmed verdict exists yet for that hypothesis)
# => only 4 of the 33 zero-usage roles carry a machine-checkable
#    board_condition clause; the remaining 29 carry free-text use_when
#    with no board_condition clause, relying entirely on an
#    orchestrating session's own judgment to route to them.
```
canonical: the code-fenced `use_when` dump above (per-role `roles/*.json`
read, this session).

## Checking the 4 mechanical board_conditions against actual board state
derived: `grep -rn "credential\|authentic" docs/issue-*/reports/implementation.md` (sampled)
```
docs/issue-221/reports/implementation.md:246: Bash invocation ... credential-helper
docs/issue-221/reports/implementation.md:258: ... credential-...
docs/issue-304/reports/implementation.md, docs/issue-289/reports/implementation.md,
docs/issue-285/reports/implementation.md, docs/issue-325/reports/implementation.md: same pattern
# => credential/authentication-adjacent code has landed under implementation's
#    own record at least 5 times; secure-coding's board_condition text
#    ("authentication or input-handling code landed... AND no secure-coding
#    record exists yet for that commit sha") is plausibly satisfied on at
#    least one of these commits, yet 0 secure-coding records exist anywhere
#    (per the Utilization table above).
```
canonical: grep hit inside docs/issue-221/reports/implementation.md (this
session) plus the zero-record row for `secure-coding` in the Utilization
table above.

derived: `head -20 docs/issue-515/reports/requirements-engineering.md` (one of the 3 requirements-engineering records)
```
# requirements-engineering record — issue-515 phase 2
... Structured requirements doc ... Requirement-to-plan trace table ...
Realization template spec ... Verification-family batch-1 realization plan
# => this repo's requirements-engineering work is about role-spec/gate
#    shape (internal tooling), not a screen/flow-facing UI requirement —
#    interaction-design's board_condition ("a requirements-engineering
#    record landed for a screen/flow-facing requirement") has no matching
#    input in any of the 3 records.
```
canonical: docs/issue-515/reports/requirements-engineering.md (read this
session, first 20 lines).

derived: `grep -rl "user-interview\|user interview" docs/issue-*/reports/product-discovery*` (recursive)
```
(no matches)
# => no product-discovery record anywhere states a hypothesis requiring
#    user-interview validation; user-discovery's board_condition has never
#    had a true input.
```
canonical: the empty-match grep result above (this session, over the
full `docs/issue-*/reports/product-discovery*` tree).

accessibility's board_condition (a landed interaction pattern or
color-token set) has no candidate input either. canonical: the
Utilization table's 10-row used-role list above, which contains no
UI-facing role (`ux-engineering`, `interaction-design`), combined with
the `use_when` dump above; this repo ships a bash/python CLI plus git
hooks, not a rendered UI.

## Axis-ownership cross-check (composes with #586/#960, not re-derived)
canonical: prior derivation in
docs/issue-586/reports/product-discovery/current-state.md (the
`_JUDGMENT_AXES` read section), re-verified by the grep re-run below.
derived: `grep -l '"axis_evaluation"' roles/specs/*.spec.json`
```
roles/specs/architecture.spec.json
roles/specs/security-threat-model.spec.json
# => capacity-planning and performance-engineering each own a
#    judgment_axis (external_burden, performance per issue-586's own
#    _JUDGMENT_AXES read) but carry no axis_evaluation rule in their own
#    spec.json — matches this survey's 0-record finding for both.
```

## Problem, stated without a solution (JTBD tuple)
The issue text names its own diagnosis taxonomy and asks for a fix plan
per class — restated without that solution attached:

- **Job performer**: the operator, relying on the 43-role rulebook system
  to surface a role's domain judgment whenever a decision actually needs
  it.
- **Job**: trust that a role's silence on the board means "no work
  existed for it," not "the routing never reached it" or "the role has
  nothing useful to say even when reached."
- **Circumstance**: per the Utilization table above, most of the 43
  roles carry zero board history in a 248-issue-deep board, and the
  operator cannot currently tell, role by role, which of the 5
  explanatory classes each silence belongs to.
- **Desired outcome**: each silent role carries a stated, evidenced
  diagnosis, and the small number that are genuine routing gaps get a
  mechanical fix (a board_condition + gate), not a promise.

## Opportunity-solution tree branch (OST vocabulary)
canonical: the Utilization table above.
- **Outcome**: the 43-role rulebook actually earns its build-time and
  review-time cost — every kept role has a realistic path to
  contributing, and roles that structurally cannot are pruned or
  consolidated rather than carried as silent dead weight.
- **Opportunity**: per the reads above, the zero-usage-role silence
  splits into at least 3 distinct causes needing 3 distinct fixes: (1) 4
  roles carry a board_condition that has plausibly fired at least once
  with no record to show for it (routing gap); (2) 2 roles are axis
  owners with no rulebook procedure (thin rulebook, feeds #992); (3) the
  remaining zero-usage roles' `use_when` names a domain (pricing, sales,
  marketing, brand-design, ML serving, data pipelines, physical
  incidents, UI screens) this repo — a self-hosting CLI/git-hooks
  meta-tool with no end users, no priced product, and no UI surface —
  structurally never produces (genuinely no work yet).
- **Candidate solutions** (see accompanying proposal): (a) add a
  mechanical board_condition check (a hook or gate, per the 4 roles that
  already have condition text) that actually fires the role instead of
  relying on an orchestrator noticing; (b) file the axis-owner rulebook
  gap into #992's deepening priority list rather than duplicating it
  here; (c) record the genuinely-no-work rationale per role, once, so
  future audits don't re-derive it from scratch.
- **Discriminating assumption test**: does adding a mechanical trigger
  for secure-coding (the clearest routing-gap case — auth/credential
  code has landed repeatedly under implementation's own record) actually
  produce a secure-coding record on the next matching commit? Not tried
  in this phase-1 turn; the accompanying proposal's own pre-registration
  names this its ITWWS follow-up and explicitly defers it — a
  role-handoff contract two-phase split keeps phase-1 to survey plus
  proposal, with execution held for phase 2.

## Open findings
- secure-coding: board_condition plausibly satisfied by landed
  credential/auth-adjacent code (docs/issue-221/reports/implementation.md,
  grep hits above) at least once, 0 records exist — routing gap,
  highest-priority fix candidate.
- issue-retrospective: board_condition ("작업이 랜딩되고
  defect-verification/conformance-review가 종결된 뒤") is satisfied
  routinely — defect-verification (14 issues) and conformance-review (6
  issues) both close out landings regularly per the Utilization table
  above — yet 0 issue-retrospective records exist; this also starves
  knowledge-management (its own `use_when` requires "여러 이슈의 회고가
  쌓여", i.e. accumulated issue-retrospective output that never
  accumulates).
- release-engineering: board_condition text ("변경이 머지되어 배포할
  때") matches the merge-heavy board directly (Utilization table), 0
  records exist — routing gap, though this repo's "배포" step may not
  exist as a distinct action from merge-to-main; the proposal below
  defers this one pending a scope check against release-engineering's
  own `write_scope`.
- capacity-planning, performance-engineering: axis owners with no
  axis_evaluation rule — thin-rulebook class, routed to #992 rather than
  duplicated here.
- The remaining zero-usage roles' `use_when` domains (pricing, sales,
  marketing, brand-design, partnerships-bd, finance-unit-economics,
  legal-compliance, localization, growth-analytics, market-analysis,
  customer-support, devrel, ml-engineering, data-engineering,
  data-modeling, api-design, observability, incident-response,
  ux-engineering, interaction-design, accessibility, user-discovery,
  content-design, pr-communications, refactoring-legacy, test-authoring,
  knowledge-management) have no matching input anywhere in this repo's
  board history — genuinely-no-work-yet class, detailed per-role in the
  accompanying proposal's utilization table.
