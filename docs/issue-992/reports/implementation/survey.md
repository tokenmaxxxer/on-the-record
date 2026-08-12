Subject: issue-992

# Current-state survey (implementation role, phase 1)

## Scope

Phase A of the approved plan — cluster A (axis owners:
`conformance-review`, `capacity-planning`, `performance-engineering`) +
cluster B (`requirements-engineering`, `risk-management`).

canonical: `git log --oneline --all | grep 996` (run this session) shows
commit `643eb32 issue-992 phase-1: role expertise deepening program
survey + proposal (#996)` on this branch's history.
canonical: `gh issue view 992 --json comments` (run this session) shows
the exact-string comment `APPROVE issue-992/product-discovery`.
canonical: as above — the proposal file
`docs/issue-992/proposals/2026-08-12-role-expertise-deepening-program.md`
landed via that merged PR.

## Axis-owner gap (cluster A)

canonical: `docs/handbooks/architecture-methodology.md` (read this
session)

```
derived: grep -c '^## Axis evaluation procedure' docs/handbooks/architecture-methodology.md
3
```

Only `maintenance_complexity` (architecture) and `attack_potential`
(security-threat-model) sections exist. `alignment`
(conformance-review), `external_burden` (capacity-planning), and
`performance` (performance-engineering) have no section in the handbook.

```
derived: python3 gates/role_spec_shape.py --roles-dir roles
```
canonical: command output above (run this session, exit 0). This gate
operates on `roles/*.json` judgment_axes wiring, not handbook prose
section presence, so it does not enforce the gap above one way or the
other — it is the pre-edit baseline for §5's guardrail-metric check
(post-edit run must also exit 0).

## roles/*.json judgment_axes wiring

```
derived: python3 -c "
import json,glob
for f in sorted(glob.glob('roles/*.json')):
    d=json.load(open(f))
    if 'judgment_axes' in d:
        print(f, d['judgment_axes'])
"
roles/architecture.json ['maintenance_complexity']
roles/capacity-planning.json ['external_burden']
roles/conformance-review.json ['alignment']
roles/performance-engineering.json ['performance']
roles/security-threat-model.json ['attack_potential']
```

canonical: command output above (run this session). All 5 axes each
resolve to exactly one role in `roles/*.json`. The remaining gap is the
handbook's per-axis `axis_evaluation` procedure section — `capacity-planning`,
`conformance-review`, `performance-engineering` lack theirs.

## Cluster B specs (requirements-engineering, risk-management)

Both `roles/specs/requirements-engineering.spec.json` and
`roles/specs/risk-management.spec.json` (read this session) already carry
a real `source_standard` (EARS + ISO/IEC/IEEE 29148; NIST SP 800-161r1)
and a `recomputation.rule` tied to that standard's own logic (EARS
pattern-grammar match; NIST-lineage treatment/owner completeness). Per
#996 §2/§1(b), the template-B gap is specifically: no `finding_method`
senior-practitioner checklist field and no `anti_pattern`/failure-catalog
field.

```
derived: python3 -c "
import json
for f in ['requirements-engineering','risk-management']:
    d=json.load(open(f'roles/specs/{f}.spec.json'))
    print(f, 'finding_method' in d, 'anti_pattern' in d)
"
requirements-engineering False False
risk-management False False
```

canonical: command output above (run this session).
`gates/role_spec_shape.py` does not validate either field name (read this
session, no `finding_method`/`anti_pattern` reference in the file), so
adding them is additive JSON, not a schema change requiring a gate edit.

## Rulebook-repo access (unchanged from #996)

canonical: `docs/issue-992/reports/product-discovery/current-state.md`
(read this session).
Rulebook prose repos (loaded at spawn, separate from this tree) remain
unreadable this session — same constraint #996's own current-state.md
recorded. Handbook `axis_evaluation` sections and
`roles/specs/*.spec.json` additive fields are the only in-repo write
surfaces available for Phase A; this survey does not claim access to
rulebook-repo prose it did not read.

## Live-fire fixture surface

canonical: `ls docs/issue-992/reports/implementation/` (run this
session, directory absent before this turn's `mkdir`)

No `docs/issue-992/reports/implementation/` seed-task fixtures exist yet.
#996 §5 requires 2 seed tasks per Phase-A role (10 fixtures minimum) plus
an independent-grading-agent design; neither exists in-repo yet.

## What did not work

None.
