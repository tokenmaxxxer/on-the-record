---
subject: issue-1669
type: report
loop_state: landed
---

# Requirement list — issue #1669 (conformance-review phase 1)

canonical: gh issue view 1669 (Acceptance + "What to build" sections)

Scout: skipped — this is a conformance check against a fixed spec (the
issue's own Acceptance list), not a design task with an open direction
choice.

Board condition (issue-521 conformance-review contract): implementation
commits landed on `issue-1669/implementation`
(c3dccd18, 420136aa, c48f85ef — `git log issue-1669/implementation --oneline`)
with no prior conformance-review record for this sha.

## Requirements, quoted verbatim from `gh issue view 1669`

canonical: gh issue view 1669 (block below is a direct quote, not a verdict)

```
R1. check: unit test — classify() returns RESPAWN for CHANGES; ALLOW_MERGE
    for MERGE only when merge_gate allows AND tests pass; HOLD for MERGE
    when merge_gate refuses OR tests fail OR verdict unparseable. Pure
    function on fixtures, no network.
    provenance: executed-unit

R2. check: live — a MERGE-verdict PR that fails a deterministic gate
    (e.g. the stale-revert guard, or a failing test) is HELD, not
    merged; a MERGE-verdict PR that passes all deterministic gates
    merges; a CHANGES verdict triggers a respawn.
    provenance: executed-live

R3. check: verdict parsing is fail-closed — a garbled/absent verdict ->
    HOLD (unit-covered with a malformed-verdict fixture).
    provenance: executed-unit

R4. empty state: today's flow for a MERGE verdict that ALSO passes all
    deterministic gates is unchanged (it still merges) — only the
    unsafe 'merge on LLM verdict despite a failing deterministic gate'
    path is newly blocked. Asserted.
    provenance: executed-unit

R5. (from the "What to build" body, not itself listed under Acceptance)
    — wiring classify()'s result into the co-injected orchestrate
    directive.
```

Verdicts for R1-R5 against the code on `issue-1669/implementation` are
recorded in docs/issue-1669/reports/conformance-review.md (phase 2).
