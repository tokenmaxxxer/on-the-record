---
name: current-state-survey
description: issue-1130 phase-1 current-state survey — role rulebook depth and hook wiring before this proposal
---

# Current-state survey — issue #1130

kind: survey
subject: issue-1130

## Scope input

canonical: `gh issue view 1130`, read directly this session — the issue scopes remediation to exactly the four cause groups issue #1129 classified, not all 43 roles.
canonical: docs/issue-1129/reports/product-discovery.md's "Per-role cause classification table", read directly.

- cause (a), 13 roles — out of scope for #1130 (workload never triggers domain).
- cause (b), 6 roles (secure-coding, test-authoring, issue-retrospective, release-engineering, interaction-design, ux-engineering) — in scope for a routing-fix proposal, not expertise depth.
- cause (c), 0 roles — no action.
- cause (d), 14 roles (content-design, data-engineering, data-modeling, growth-analytics, knowledge-management, localization, ml-engineering, observability, pr-communications, refactoring-legacy, user-discovery, accessibility, api-design, performance-engineering) — in scope for full expertise-realization (judgment/planning/deliverable_production/feedback/review + degree-level knowledge).

## Current rulebook depth (cause-d roles)

derived:
```
python3 -c "
import json
roles = ['content-design','data-engineering','data-modeling','growth-analytics','knowledge-management','localization','ml-engineering','observability','pr-communications','refactoring-legacy','user-discovery','accessibility','api-design','performance-engineering']
for r in roles:
    d = json.load(open('roles/specs/%s.spec.json' % r))
    print(r, 'source_standard' in d, 'finding_method' in d)
"
```
```
content-design False False
data-engineering False False
data-modeling False False
growth-analytics False False
knowledge-management False False
localization False False
ml-engineering False False
observability False False
pr-communications False False
refactoring-legacy False False
user-discovery False False
accessibility False False
api-design False False
performance-engineering False False
```
canonical: the command output directly above (this session's own execution against the working tree). None of the 14 cause-d role specs carry a `source_standard` or `finding_method` field today — the depth roles/specs/product-discovery.spec.json and roles/specs/requirements-engineering.spec.json already have (both read directly in this session) is present in none of the 14 in-scope specs.

## Current rulebook depth (cause-b roles)

derived:
```
python3 -c "
import json
roles = ['secure-coding','test-authoring','issue-retrospective','release-engineering','interaction-design','ux-engineering']
for r in roles:
    d = json.load(open('roles/specs/%s.spec.json' % r))
    print(r, d.get('use_when', {}).get('board_condition'))
"
```
```
secure-coding an authentication or input-handling code change lands on the branch AND no secure-coding record exists yet for that commit
test-authoring None
issue-retrospective a non-incident issue closes AND no issue-retrospective record exists yet for that issue
release-engineering a release is cut AND no release-engineering record exists yet for that version
interaction-design a requirements-engineering record lands for a screen/flow-facing requirement AND no interaction-design record exists yet for it
ux-engineering a UI component consumes a design token AND no ux-engineering record exists yet for that token
```
canonical: the command output directly above. Each `board_condition` names a distinct event; cross-referencing this output against on-the-record/hooks/hooks.json (read directly this session) — none of the landed hooks for these six roles (credential-network-guard.sh, credential-record-guard.sh, test-authoring-invariant-guard.sh, role-test-claim-guard.sh, deviation-log-guard.sh, pr-preflight.sh, merge-allow-gate.sh, spawn-allow-gate.sh, design-rationale-guard.sh) evaluates any of the board_condition strings shown above.

## Wiring status (gate-now roles named by the issue)

canonical: docs/specs/role-invariant-coverage.md's coverage matrix, read directly this session — the "accessibility" row, the "api-design" row, and the "performance-engineering" row are each classified `gate-now` with an "Invariant (proposed if none exists)" cell but carry no `(landed)` marker, and the matrix's own "Landing status" section names these rows as left for a follow-up issue.

derived:
```
grep -c "accessibility\|api-design\|performance-engineering" on-the-record/hooks/hooks.json
```
```
0
```
canonical: the command output directly above. No hook in on-the-record/hooks/hooks.json references any of the three role names — this cross-check against the live hook registry agrees with the coverage matrix's own classification.

## Empty-state note

canonical: on-the-record/hooks/hooks.json, read directly this session, cross-referenced against docs/specs/role-invariant-coverage.md's "Landing status" section. The cause-b roles' hooks are each named "already landed" in that matrix, and this survey's own hooks.json check (above) confirms all six named hook scripts exist and are wired — but wired-and-firing is not the same as evaluating the specific role's board_condition; the gap for cause-b is a routing gap (see the scout-brief's "Must-bes" section), distinct from the not-yet-landed wiring gap the accessibility/api-design/performance-engineering rows have.
