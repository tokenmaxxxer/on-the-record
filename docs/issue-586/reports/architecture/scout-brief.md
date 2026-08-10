# Scout brief — issue #586 (architecture, phase 1)

Mode: parallel WebSearch (2 angles, 1 sweep round, no deepening — saturation
reached at judge point 1: neither result changed a build decision beyond
what the current-state survey already fixed).

## Angles run
1. CODEOWNERS-style single-owner-per-path completeness checkers
2. RBAC/access-control-matrix single-owner-per-resource design patterns

## Must-bes extracted
- Completeness is checked as "no unowned item" AND "no item owned twice" —
  both directions, not just orphan detection. `codeowners-validator` /
  the CODEOWNERS action both report unowned paths as a distinct failure
  class from multi-owner conflicts.
- Ownership is attached to the resource (axis) as a first-class field, not
  inferred from role prose — matches this repo's existing
  `judgment_axes: [...]` array on `roles/*.json`.
- "Owner" as a role is a coarser grain than per-object ACLs; matrices that
  scale keep the axis set small and fixed and let ownership assignment be
  the variable, which is exactly this repo's shape (5 fixed axes, 43 roles).

## Gap line
This repo's `gates/role_spec_shape.py` (function `check_axis_ownership`)
already enforces "no axis owned by more than one role" (the harder
direction). It does not enforce "no axis owned by zero roles" — the
CODEOWNERS precedent's other half is missing. That gap is exactly the
mechanical completeness check issue #586 asks for; the proposal closes it.

## Adopt / skip
- Adopt: two-directional completeness (both zero-owner and multi-owner are
  errors), resource-owner as an explicit field, fixed small axis
  vocabulary.
- Skip: fine-grained per-object ACL/attribute-based ownership — this
  repo's grain is role-level, already correct at that grain, no reason to
  go finer.

## Segment fit
Internal schema/taxonomy design bound to an already-fixed axis vocabulary
(issue #573) and role set (issues #521-#525) — no product-facing exemplar
is a closer analog than access-control completeness tooling.

Sources:
- https://github.com/mszostok/codeowners-validator
- https://github.com/marketplace/actions/codeowners-action
- https://www.lumos.com/topic/access-control-matrix-implementation-guide
