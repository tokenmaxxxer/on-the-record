# ADR: judgment-axis ownership matrix completed

Date: 2026-08-10
Status: accepted

## Context
`gates/role_spec_shape.py`'s `_JUDGMENT_AXES` fixes five methodology axes
(`alignment`, `maintenance_complexity`, `external_burden`,
`attack_potential`, `performance`). Two were already owned
(`maintenance_complexity` -> architecture, `attack_potential` ->
security-threat-model, issue #573). The remaining three had no owner.

## Decision
Assign the three remaining axes, one role each, per
`docs/issue-586/proposals/architecture.md` section 1 (merged, PR #590):

| Axis | Owning role |
|---|---|
| `alignment` | `conformance-review` |
| `external_burden` | `capacity-planning` |
| `performance` | `performance-engineering` |

`conformance-review`'s whole domain is checking an artifact against
recorded specs/decisions without reading builder intent — the
definitional shape of "alignment." `capacity-planning` is the only role
whose domain is resource/demand budgeting, and external burden (load
placed on a third party) is the same demand-on-a-finite-resource question
pointed outward. `performance-engineering` is a direct 1:1 match on its
`decides` field.

`check_axis_ownership` (`gates/role_spec_shape.py`) is extended to flag a
zero-owner axis, not only a double-owned one, and is now reachable via
`python3 gates/role_spec_shape.py --roles-dir roles` — previously it,
`check_role_judgment_axes`, and `check_axis_evaluation_entry` were
defined and unit-tested but never invoked by any hook, CI job, or other
entrypoint.

## Why no sixth axis
Considered and rejected:
- A `cost`/`unit-economics` axis — `finance-unit-economics` already
  exists as a full role; folding it into the fixed judgment-axis set
  would duplicate machinery that role already has for no gain.
- A `legal`/`compliance` axis — same reasoning against
  `legal-compliance`; the delegated-judgment panel is scoped to the five
  methodology axes the operator named for exactly this reason. Adding
  axes outside that closed set is a scope decision for the operator, not
  something this ADR assumes.

## Consequences
- `_JUDGMENT_AXES` stays closed at 5; at most 5 `roles/*.json` files will
  ever carry `judgment_axes`.
- Any future axis add/reassignment now fails `--roles-dir` until the
  matrix is complete again.
- Rulebook procedure prose for the three newly-owned axes (batches 2-4)
  and the multi-role panel fixture (batch 5) remain follow-up work, out
  of this ADR's scope.

## Source
`docs/issue-586/proposals/architecture.md` (PR #590, merged),
`docs/issue-586/proposals/implementation.md` (this batch).
