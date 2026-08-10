---
code_under_review:
  - on-the-record/commands/run.md
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/test_delegated_judgment_gate.py
  - docs/specs/reconciled-index.md
  - docs/issue-641/proposals/implementation-accumulation-note.md
type: feature
breaking: false
verdict: partially detectable, lexical proxy, fail-open advisory
loop_state: landed
---

# Implementation record — issue #641

## Summary of work

Implemented the approved `docs/issue-641/proposals/architecture.md` design (PR #646,
merged) in PR #648 (merged as `93e3bb7`, commit `2ace9a0`):

- `on-the-record/commands/run.md` step 6 gains the review-is-role-work boundary text at
  the exact insertion point the architecture proposal specifies: decision-support
  summarization for the operator stays orchestrator duty; producing review findings or
  feedback on a deliverable is role work (`conformance-review`, or the judgment-axis panel
  via the shipped #573/#609 `open_decision_item` triage machinery), and the orchestrator
  relays the role's recorded findings rather than authoring its own critique.
- `on-the-record/hooks/delegated-judgment-gate.sh` gains a seventh, advisory-only firing
  condition: it detects an orchestrator-authored (`CLAUDE_ROLE` unset) `gh pr comment` /
  `gh issue comment` whose body carries review-verdict-shaped language with no citation of
  a role record, and posts a fail-open audit comment on a hit — no build-blocking behavior.
- `on-the-record/hooks/test_delegated_judgment_gate.py` gained four tests for the new
  condition: flagged, cited-so-not-flagged, role-session-so-not-flagged,
  non-verdict-so-not-flagged.
- `docs/specs/reconciled-index.md` regenerated via `gates/spec_index.py --update` to
  reflect the run.md change, per the acceptance criterion's "spec-index updated in the
  same unit."
- `docs/issue-641/proposals/implementation-accumulation-note.md`: a small phase-2 proposal
  carrying the `## Accumulation` field required by the shape-1 proposal gate, since the
  already-approved `architecture.md` predates that gate and could not be retrofitted.

## Why

Root-caused in the issue: `run.md` told the orchestrator to summarize deliverables for the
operator but never drew the line between that (legitimate decision-support) and the
orchestrator itself authoring review findings (role work). The architecture proposal
(`docs/issue-641/proposals/architecture.md`) already made every design decision this phase
executes — the exact insertion point and wording for the boundary text, and the exact
firing-condition shape/vocabulary/citation-check for the detector — so phase-2 here is a
direct, undeviating build of that approved design, extending the existing
`delegated-judgment-gate.sh` (which already owns orchestrator-issued `gh` command
inspection via #597's sixth firing condition) rather than adding a new hook.

## Upstream / basis

docs/issue-641/proposals/architecture.md (PR #646, merged, commit `c5879e8`)

## What did not work

None.

## Doc placement (completed)

- [x] run.md boundary text — component handbook, same unit (`on-the-record/commands/run.md`)
- [x] spec-index regenerated in the same unit (`docs/specs/reconciled-index.md`)
- [x] detectability verdict recorded in architecture.md's own text (phase-1) and restated
  in this record's frontmatter `verdict:` field, per the acceptance criterion

## Open findings

None outstanding. PR #648's merge note recorded that this record could not be committed
at merge time because the `APPROVE issue-641/implementation` comment had not yet landed
when the code was pushed; that comment has since been posted, and this file is the
deferred record catching up to the already-merged, already-closed delivery.

## Verification run

```
python3 -m pytest -q
973 passed, 2 failed in 45.79s
```

The 2 failures (in `gates/test_boundary.py` and `test_gates.py`) are dirty-worktree /
environment artifacts (uncommitted `.shallow-check` file and this checkout's own directory
name embedding "implementation"/dirty-tree markers into a version string) — unrelated to
this diff and reproduced identically on a clean `main` checkout per PR #648's own note.
