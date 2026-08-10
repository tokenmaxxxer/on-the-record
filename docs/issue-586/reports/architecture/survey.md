# Current-state survey — issue #586 (architecture, phase 1)

## Axis vocabulary is already fixed, not open for this proposal
`gates/role_spec_shape.py` (`_JUDGMENT_AXES`) fixes the five methodology
axes: `alignment`, `maintenance_complexity`, `external_burden`,
`attack_potential`, `performance`. These match the operator's five named
axes 1:1 (alignment-with-recorded-judgments -> `alignment`,
maintenance-complexity -> `maintenance_complexity`, external-burden ->
`external_burden`, attack-potential -> `attack_potential`,
performance-impact -> `performance`). No sixth axis is justified below —
see "Why no additional axis" in the proposal.

## Ownership today (role count and axis ownership, derived below)

```
$ python3 - <<'PYEOF'
import json, glob
files = sorted(glob.glob('roles/*.json'))
print(len(files), 'role files')
owned = 0
for f in files:
    d = json.load(open(f))
    if d.get('judgment_axes'):
        owned += 1
        print(f, d['judgment_axes'])
print('owned axes total:', owned)
PYEOF
43 role files
roles/architecture.json ['maintenance_complexity']
roles/security-threat-model.json ['attack_potential']
owned axes total: 2
```

derived: 43=role-file-count, 2=owned-axis-count-from-above-reproduction,
5-2=derived-unowned-axis-count. `alignment`, `external_burden`, and
`performance` are the unowned axes (`_JUDGMENT_AXES` set minus the two
owned above). Ownership was seeded by the #573 architecture proposal
solely to unblock `gates/test_role_spec_shape_batch9.py`, not as a
completed assignment.

## What the schema already enforces
`role_spec_shape.py::check_role_judgment_axes` validates each role's
`judgment_axes` entries against the fixed set. `check_axis_ownership`
walks all `roles/*.json` and flags an axis owned by more than one role —
reading the function body (`gates/role_spec_shape.py`, `check_axis_ownership`),
it appends a "more than one role" reason but never checks `len(names) == 0`,
so a zero-owner axis passes silently today. `check_axis_evaluation_entry`
validates the shape of one `axis_evaluation` record entry
(axis/verdict/citation, and a `finding` object with `target_path` +
`required_fix` iff `verdict == "contradicts"`) — this is the shape the
owning role's rulebook procedure must produce; the procedure itself (what
to read, what criteria to apply) is not specified anywhere yet, per role
or in general.

## Batch precedent (#521-#525)
Realizing all 43 `roles/specs/*.spec.json` templates ran as: #521
(6-role verification family, its own phase-1 proposal + scout brief),
#522 (2-role loop_state fix, docs-only fast path), #523 (2-role
write_scope split), #524 (discovery/design-family batch-2), #525
(batch-3+, remaining roles in one shippable batch after the family-sized
batches established the pattern) — from `git log --oneline` on this repo
(commits `782a81d`, `f6fdd23`, `620b24d`, `88baa3e`, `ca99dc4`
respectively). Each batch: its own phase-1 proposal, its own
after-proposal/before-landing hunt record, one PR. Batch sizing tracked
natural role families first, then consolidated the long tail once the
pattern was proven on smaller batches.

## Deployed-surface constraint
`roles/*.json` carries `repo`/`path` pointing at each role's own
rulebook repo (e.g. `tokenmaxxxer/architecture-rulebook`), fetched
zero-install by consumer repos. This `on-the-record` repo (the `roles`
repo) is not those rulebook repos — content inside
`architecture-rulebook`, `conformance-review-rulebook`,
`capacity-planning-rulebook`, or `performance-engineering-rulebook`
cannot be edited from here. What this repo can ship: the
`judgment_axes` ownership assignment on `roles/*.json` (schema side,
the pattern #573 used), a zero-owner completeness check added to
`gates/role_spec_shape.py`, and a rulebook-side procedure template (the
shape every owning role's rulebook procedure section must match) —
shape-checked the same way #521-#525 shape-checked per-role spec
structure, not authored per-rulebook from this repo.
