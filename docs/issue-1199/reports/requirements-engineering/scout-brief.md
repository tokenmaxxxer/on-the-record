---
name: requirements-engineering-tool-landscape-scout-brief
subject: issue-1199
---

# Scout brief: Claude Code plugin ecosystem, requirements-engineering domain

Mode: batched-sequential (four WebSearch calls issued in one turn, one
stage — no parallel-subagent fan-out available in this session; stated
per the scout directive's fallback-disclosure requirement). Stages
used: 1 sweep + 1 deepening (adoption-verification via `curl` to the
GitHub API) = 2 of the 5-stage budget.

## Sweep (stage 1, 4 angles, one turn)
- "GitHub spec-kit Claude Code plugin specification requirements stars"
- "Claude Code skill requirements gathering EARS spec writing plugin marketplace"
- "Claude Code plugin \"spec-driven development\" agentic skill stars github"
- "awesome-claude-code plugins requirements specification traceability"

## Judge point 1 / deepening
`github/spec-kit` surfaced across all four angles (official GitHub
project) — clear category signal. `Hainrixz/the-architect` surfaced as
a direct-domain match (EARS acceptance criteria natively, matching this
role's own Axis 1). Verified both live via `curl -s
https://api.github.com/repos/<org>/<repo>`.

## Must-bes (Kano) the field assumes
- A spec-authoring tool separates "what/why" (business intent) from
  "how" (implementation) as distinct artifact stages, never mixed in
  one document (spec-kit's `/specify` vs `/plan`).
- Ambiguity gets a dedicated resolution step before the spec is allowed
  to generate downstream artifacts (spec-kit's `/clarify`, "recommended
  before /speckit.plan").
- Acceptance criteria are checkable, not just readable — the-architect
  pairs "a runnable verify command" with every acceptance criterion.

## Performance axes the field competes on
1. How early ambiguity is caught (before vs. after downstream artifacts
   are generated).
2. Whether acceptance criteria are executable or prose-only.
3. Whether cross-artifact consistency (spec vs. plan vs. tasks) gets a
   dedicated mechanical check before handoff (spec-kit's
   `/speckit.analyze`).

## Adopt / skip
- Adopt: pairing a verification condition with a literal runnable check
  when one exists (from the-architect); a mandatory whole-batch
  consistency/coverage review step before requirements hand off
  downstream (from spec-kit's `/analyze`).
- Skip: spec-kit's full 7-phase command surface (constitution through
  implement) — out of this role's WRITE_SCOPE (this role produces the
  spec, not the plan/build/implement stages); adopting the full command
  chain would blur role boundaries this repo's contract already draws.

## Gap line
This role's existing playbook (playbook/rules.md, Axis 2
verification-method selection) already assigns one of four ISO 29148
verification methods per requirement, but never required the assigned
method to resolve to an actually-runnable check, and had no
batch-level (cross-requirement) review step — only per-requirement
rules (Axes 1-4). Both gaps are what the two folded-in rules (11a, 11b)
address.

## Segment fit
Direct fit: both exemplars are spec/requirements-authoring tools in the
same problem space as this role (turning intent into a checkable
spec), not adjacent domain tooling.

Sources:
- https://github.com/github/spec-kit
- https://github.com/Hainrixz/the-architect
- https://api.github.com/repos/github/spec-kit
- https://api.github.com/repos/Hainrixz/the-architect
