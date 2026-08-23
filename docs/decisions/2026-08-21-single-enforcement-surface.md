---
id: single-enforcement-surface
status: frozen
date: 2026-08-21
subject: issue-2104
origin: 2026-08-21 operator decision, after drift incident 2 of 2 that day (hooks-beside-skills)
scope:
  globs:
    - "hooks/**"
    - "on-the-record/hooks/**"
    - "skills/**"
  keywords:
    - "hooks-beside-skills"
    - "hook in the skill repo"
    - "hooks in the skill repository"
    - "skill-side enforcement"
    - "enforcement in skills"
    - "skill repo hook"
---

# Single enforcement surface — hooks live only in core

## Status

Frozen (2026-08-21 operator decision). Recorded here per issue #2104
after a consult recommendation to carry hooks beside skills in the
skill repository was adopted by the orchestrator and caught only by
the operator (second drift incident of 2026-08-21; two drift incidents
in one day motivated the structural guard).

## Decision

Enforcement (hooks) has exactly one surface: **core**. The skill
repository is guidance-only — skills carry instructions and judgment
material, never enforcement hooks. No design may add a second
enforcement carrier (hooks shipped beside skills, skill-repo hook
directories, per-skill enforcement scripts).

## Consequences

- Consult recommendations proposing hooks in the skill repository or
  any skill-side enforcement intersect this decision's scope and
  require an explicit disposition (`reaffirms
  single-enforcement-surface` or `escalated-to-operator: ...`) before
  any issue adopting them is filed (see docs/decisions/README.md).
- Changing this requires an operator decision superseding this record,
  not a consult.
