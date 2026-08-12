---
code_under_review:
  - on-the-record/hooks/directive.sh
  - harness/fixture-operator-experience/scenario.py
  - harness/fixture-operator-experience/test_flow.py
  - harness/fixture-operator-experience/seed_vague.json
  - harness/fixture-operator-experience/seed_precise.json
  - gates/operator_experience.py
type: feature
breaking: false
verdict: pending
loop_state: coding
---

Subject: issue-1006

## What was done

canonical: docs/issue-1006/proposals/operator-experience-layer-build.md
(this branch's phase-2 build-authorization, read this session)

Starting the build of blocks A-E named in that proposal's build section.
This record is written first, per phase-2 protocol, and its body is
updated as each block lands.

## Why

Requirement: issue #1006, operator-experience program — full-delegation
default, interaction guidance, elicitation support, progress legibility,
requirement-traceable completion. Design basis: PR #1009.

## Upstream / basis

docs/issue-1006/proposals/operator-experience-layer-build.md

## What did not work

None.

## Rationale for deviations

The approved build proposal names the marker path as "a marker file
under the workspace, e.g. `.orchestrate-greeted`" without pinning which
variable resolves "the workspace." The build used `${CHECKOUT}` (already
in scope from poll-rearm.sh) as the natural read of that phrase, but
`${CHECKOUT}` resolves to the single shared on-the-record clone, not the
target repo per session — an inline fix (swap to `$(pwd -P)`, the cwd
the hook actually fires in) was needed to match the design's actual
intent. Stays inside the frozen write set, mechanical, does not change
what block A claims to do (fire once per workspace) — INLINE-FIX per the
deviation loop, not a design change requiring re-approval.

## Open findings

None.

## Next steps

Add blocks A-D to on-the-record/hooks/directive.sh, then block E
(the harness fixture pair and its gate module), run the fixture
scenario, and update this record's frontmatter to loop_state: landed
before commit.

## Resolution path

N/A — no open findings.
