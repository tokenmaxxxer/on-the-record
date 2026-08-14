Subject: issue-1006

## Current-state survey

canonical: `git log --all --oneline | grep -i 1006`, output pasted below (read this session)

```
fafa01f4 issue-1006 phase-2: operator-experience layer blocks A-E (#1018)
c8d2d08e issue-1006 implementation phase-2: register operator_experience.py gate
2e40068b issue-1006 implementation phase-2: operator-experience layer blocks A-E
87243590 issue-1006 implementation phase-1: build-authorization proposal referencing merged operator-experience design (#1010)
5c72ab66 issue-1006 implementation phase-1: build-authorization proposal referencing merged operator-experience design
9c048791 issue-1006 product-discovery phase-1: operator-experience layer survey + proposal (#1009)
6d039588 issue-1006 product-discovery phase-1: operator-experience layer survey + proposal
```

Landed implementation commit under review: fafa01f4 (PR #1018,
issue-1006/implementation).

canonical: `find docs/issue-1006 -iname "*conformance-review*"`, no output (read this session)

No prior conformance-review record exists for this commit — board
condition per the marketplace conformance-review role spec (issue-521)
is satisfied.

### Spec sources read this session

canonical: `gh issue view 1006` (read this session, quoted in full earlier this session)

- Issue #1006 (closed, 5 sub-requirements req#1-req#5, constraints,
  acceptance criteria).

canonical: docs/issue-1006/proposals/operator-experience-layer.md (read this session, file:1-120)

- Its "What will be" heading (block-A-through-E section) names blocks
  A-E as the requirement decomposition, each tagged inline with the issue
  sub-requirement it targets (req#1/#3/#4/#5).

canonical: docs/issue-1006/proposals/operator-experience-layer-build.md (read this session, file:1-100)

- Restates blocks A-E and adds the frozen files: write set, which
  includes a docs/handbooks/ operator-experience handbook page alongside
  the code/harness files.

canonical: docs/issue-1006/reports/implementation.md (read this session, file:1-60)

- Frontmatter carries verdict: pending, loop_state: coding — read only to
  locate the write set actually touched, not as a source for phase-2
  verdicts (role directive requires verdicts rendered independent of the
  building agent's own narrative).

### What the landed commit touched

canonical: `git show fafa01f4 --stat`, output pasted below (read this session)

```
 docs/issue-1006/reports/implementation.md          |  66 +++++++++++
 .../implementation/2026-08-12-hunt-operator-experience-layer-build.md |  45 +++++++
 .../reports/implementation/deviation-log.md        |   1 +
 docs/specs/enforcement-boundary.md                 |   1 +
 gates/operator_experience.py                       |  69 +++++++++++
 harness/fixture-operator-experience/scenario.py    | 132 +++++++++++++++++++++
 .../fixture-operator-experience/seed_precise.json  |   7 ++
 .../fixture-operator-experience/seed_vague.json    |   7 ++
```

canonical: `git show fafa01f4 -- on-the-record/hooks/directive.sh harness/fixture-operator-experience/test_flow.py | head -5`, non-empty output (read this session)

on-the-record/hooks/directive.sh and
harness/fixture-operator-experience/test_flow.py both carry diffs in this
commit; they are truncated from the `--stat` excerpt above but present.

canonical: `find docs/handbooks -iname "operator-experience.md"`, no output (read this session)

The handbook path named in the frozen files: write set of both merged
phase-1 proposals is absent from this commit's diff and from the current
working tree — a candidate gap for phase-2 to verdict.

## Requirement list (phase-1 deliverable, no verdicts)

Nine items to be checked in phase 2, extracted from the design's block
decomposition and the issue's own acceptance/empty-state lines; verdicts
deferred to that phase:

1. Block A — first-contact guidance appended to directive.sh's heredoc,
   gated by a per-workspace marker so it fires once, not every turn
   (issue req#3).
2. Block B — elicitation branch before issue drafting: when the ask lacks
   a testable Acceptance-shaped criterion, ask 1-3 clarifying questions
   via requirements-quality/user-discovery; a precise ask skips straight
   to drafting (issue req#4, empty-state acceptance line).
3. Block C — one narration sentence at the TURN-BUDGET RULES arming point
   (issue req#5).
4. Block D — a clause in AUTONOMOUS ASYNC COMPLETION's verify step citing
   which requirement the PR under merge review corresponds to (issue req#1).
5. Block E — the fixture-operator-experience harness pair plus
   gates/operator_experience.py, mirroring the fixture-requirement-digest
   pairing shape.
6. Issue acceptance line: the harness test_flow.py runs the seeded
   conversation end-to-end.
7. Issue acceptance/empty-state line: a precise requirement skips
   elicitation and goes straight to delegation.
8. Frozen write-set item: the operator-experience handbook page named in
   both proposals' files: frontmatter — whether it exists and, if not,
   whether its absence is disclosed in the phase-2 build record.
9. gates/operator_experience.py's row in
   docs/specs/enforcement-boundary.md, claimed as part of block E's
   delivery in the phase-2 build commit's message.

## What did not work

None.
