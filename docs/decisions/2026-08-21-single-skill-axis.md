---
id: single-skill-axis
status: frozen
date: 2026-08-21
subject: issue-2104
origin: 2026-08-21 operator decision, after drift incident 1 of 2 that day
scope:
  globs:
    - "roles/**"
  keywords:
    - "role concept"
    - "role manifest"
    - "roles/<role>"
    - "separate role axis"
    - "new role type"
    - "role hierarchy"
---

# Single skill axis — no separate role concept

## Status

Frozen (2026-08-21 operator decision). Recorded here per issue #2104
after a consult recommendation to reintroduce `roles/<role>` manifests
as a concept distinct from skills was adopted by the orchestrator and
caught only by the operator (drift incident, 2026-08-21).

## Decision

There is exactly one capability axis: **skills**. What used to be
called a "role" is a heavyweight skill — larger, stateful, dispatched
differently, but on the same axis. No design may reintroduce a
separate role concept (role manifests, role registries, a role/skill
type split) as an architectural primitive.

## Consequences

- Consult recommendations proposing a role concept, role manifests, or
  a role axis distinct from skills intersect this decision's scope and
  require an explicit disposition (`reaffirms single-skill-axis` or
  `escalated-to-operator: ...`) before any issue adopting them is filed
  (see docs/decisions/README.md, disposition contract).
- Changing this requires an operator decision superseding this record
  (`status: superseded` plus a successor record), not a consult.
