# refactoring-legacy operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file (docs/issue-1174/reports/refactoring-legacy.md)
is gated behind an "APPROVE issue-1174/refactoring-legacy" comment per
contract v3 s19. This file carries the evidence trail as allowed
phase-1 material, matching the technical-writing/api-design/
observability/data-engineering precedent for this issue
(docs/issue-1174/reports/technical-writing/evidence-trail.md,
docs/issue-1174/reports/api-design.md,
docs/issue-1174/reports/observability/evidence-trail.md,
docs/issue-1174/reports/data-engineering/evidence-trail.md).

## What was done (delivered to the rulebook repo, outside this repo's gate)

Authored the refactoring-legacy role's operational playbook and opened
it as a pull request against tokenmaxxxer/refactoring-legacy-rulebook,
branch issue-1174/operational-playbook.
canonical: `gh pr create` output this turn, returning
https://github.com/tokenmaxxxer/refactoring-legacy-rulebook/pull/26,
commit 2172bcba51b4450f003d5f554b8cb1d02d5fe2e8 on that branch.

Per the approved proposal (docs/issue-1174/proposals/operational-playbook-program.md
sections (a) axis-derived N floor, (b) sparse-tier N_min formula,
(b-revised) fan-out unit, (c) depth-gate shape, amendment 4
removal-category requirement), the PR adds 5 axis files under
playbook/, one per this role's decision axis (derived from this role's
own directive: seam identification, characterization-test scope,
Fowler-catalog step decomposition, strangler-fig migration for
too-large-for-one-step changes, and the run-tests-every-step/verdict
cadence):

- playbook/seam-selection.md
- playbook/characterization-test-scope.md
- playbook/refactoring-step-decomposition.md
- playbook/strangler-fig-migration.md
- playbook/verification-cadence.md

Each axis file's rule count:
derived: `grep -c '^[0-9]\+\.' /home/jwjung/tokenmaxxxer/rulebooks/refactoring-legacy-rulebook/playbook/*.md`
```
seam-selection.md:6
characterization-test-scope.md:6
refactoring-step-decomposition.md:6
strangler-fig-migration.md:6
verification-cadence.md:6
```
30 rule blocks authored total, each condition -> choice -> source, each
axis file carrying at least one rule marked **REMOVAL** (amendment 4).

canonical: `python3 gates/playbook_depth_gate.py /home/jwjung/tokenmaxxxer/rulebooks/refactoring-legacy-rulebook/playbook --role refactoring-legacy --floor 5 --axes seam-selection,characterization-test-scope,refactoring-step-decomposition,strangler-fig-migration,verification-cadence` run this turn, output:
```
REJECT #0: 'When writing a characterization test, assert on the actual observed output of a ' — no choice/action verb
REJECT #6: 'No distinct academic/theory-layer source was located for characterization-test s' — no source citation
REJECT #8: 'When applying any catalog step, run the full test suite immediately after that o' — no choice/action verb
REJECT #10: 'When deciding what to refactor first in a legacy area with many candidate improv' — no choice/action verb
REJECT #25: 'When completing each individual refactoring step (not each larger task or each d' — no choice/action verb
role=refactoring-legacy accepted=26 floor=5 count_ok=True
PASS
```
derived: the 5 REJECT lines above (from the same tool run) — 4 of the
30 authored blocks were rejected on the gate's "no choice/action verb"
heuristic (they open with "assert", "run", "treat", "scope" — real
imperative verbs the regex did not match, the same heuristic gap the
observability evidence trail already recorded for a bolded-noun lead),
and 1 (the characterization-test-scope.md "Open findings" note, not a
rule block) was correctly rejected as carrying no source citation. The
accepted count (26) sits well above the floor (5); the floor
derivation (b): sparse tier, N_min = max(5, axes x 1) = max(5, 5) = 5,
from this role's assignment in the proposal's batch 9 (sparse) listing.

## Research protocol (amendment 1, three layers)

canonical: this session's own WebSearch tool-call transcript, this
turn — every query below and its returned source list.

```
Layer one (practitioner decision knowledge — condition -> choice -> source, not definitions):
- "Michael Feathers seams legacy code definition finding a seam without touching code"
  -> martinfowler.com/bliki/LegacySeam.html
  -> informit.com/articles/article.aspx?p=359417&seqNum=2
  -> mike-bland.com/2023/08/23/legacy-code-seams-and-the-most-important-design-guideline.html
  (seam taxonomy and seam-narrowing guidance)
- "Feathers sprout method wrap method minimal seam legacy code when preferable to full seam"
  -> codably.dev/code-quality/breaking-dependencies-in-legacy-code-sprout-wrap-seam-patterns
  -> gist.github.com/birdofpray70/8a42b05e2dd1a2f19922d0d92e9e4e06
  (sprout-vs-wrap-vs-full-seam decision order)
- "strangler fig pattern legacy migration when to use feature toggle branch by abstraction"
  -> learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig
  -> docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/branch-by-abstraction.html
  -> simranchawla.com/unlocking-legacy-systems-strangler-fig-branch-by-abstraction-and-parallel-run-explained
  (Strangler Fig vs. Branch-by-Abstraction selection criteria)

Layer two (named methodology/standard, verified at source):
- "Fowler refactoring catalog choosing which refactoring step small safe steps"
  -> understandlegacycode.com/blog/key-points-of-refactoring/
  -> silab.fon.bg.ac.rs/wp-content/uploads/2016/10/Refactoring-Improving-the-Design-of-Existing-Code-Addison-Wesley-Professional-1999.pdf (the catalog's own PDF)
  (test-small-change-test rhythm, catalog-entry granularity)
- "characterization test legacy code how much behavior to capture golden master testing"
  -> en.wikipedia.org/wiki/Characterization_test
  -> chicio.medium.com/golden-master-testing-aka-characterization-test-a-powerful-tool-to-win-your-fight-against-legacy-1ca590f219a1
  (Feathers' characterization-test definition, golden-master scoping)
- "run tests after every refactoring step continuous verification rollback trigger regression"
  -> circleci.com/blog/regression-testing-and-how-to-automate-it-with-ci/
  -> harness.io/blog/regression-testing-in-ci-cd-deliver-faster-without-fear
  (fast-gate-first pipeline ordering, canary rollback triggers)

Layer three (distinct academic-theory layer, amendment 4's subtraction-neglect requirement):
- "subtraction neglect people overlook subtractive changes Adams Converse Hales Klotz Nature 2021 simplification"
  -> nature.com/articles/s41586-021-03380-y
  (Adams, Converse, Hales & Klotz, Nature 592, 2021, "People systematically overlook subtractive changes" —
  the same academic anchor amendment 4 names, cited as the rationale layer behind this playbook's
  REMOVAL-category rules, e.g. strangler-fig-migration.md rule 6 and
  refactoring-step-decomposition.md rule 6's dead-code/duplicate-removal guidance)
```

Per-rule mapping: each of the 26 accepted rule blocks carries its own
`source:` line resolving to one of the URLs above — see the playbook
files in the open PR for the full per-rule citations (not reproduced
here to avoid duplicating primary content across two repos).

## Open findings

canonical: playbook/characterization-test-scope.md's own "Open
findings" section, this turn's write (see the fenced excerpt below).
```
No distinct academic/theory-layer source was located for
characterization-test scope specifically (as opposed to testing
methodology generally); the searches run this session surfaced only
practitioner blogs and the Feathers/Fowler canon. A later pass should
search software-testing-effectiveness literature (e.g. mutation-testing
coverage studies) for an independent academic anchor.
```

- The methodology-layer and academic-layer source pages above were read
  via WebSearch result summaries, not individually WebFetched — a
  stated risk, not a claim about current state, so no canonical
  citation applies to this item; a later session should fetch each
  cited page directly to check for summarization drift against the
  live text.
- The role's spec file has not gained a playbook-pointer field yet (out
  of scope for this fan-out unit) — Acceptance check 2 (a live session
  citing a playbook rule) is not yet satisfiable.
  canonical: `grep -c playbook_refs roles/specs/refactoring-legacy.spec.json`
  in this working tree this turn, returning 0.

## PR status (main repo)

canonical: docs/issue-1174/reports/observability/evidence-trail.md's
own "PR not opened (main repo)" section, read this turn.
```
observability, market-analysis, and data-engineering all hit the same
pr-preflight/approval-gate deadlock: pr-preflight.sh requires an
amendments-reconciled line inside the phase-2 record path before
opening a PR, but approval-gate.sh refuses any write to that exact
path pre-approval — no phase-1-legal way to satisfy pr-preflight.
```
This repo's own PR for branch issue-1174/refactoring-legacy is
attempted next, in this same turn; if it hits the same deadlock, this
record and the pushed rulebook branch stand as the phase-1-legal
delivery and PR creation is left for external relay.

## Next steps

- On receiving "APPROVE issue-1174/refactoring-legacy", promote this
  file's content into the phase-2 record
  (docs/issue-1174/reports/refactoring-legacy.md) with the full
  required-field set, including the amendments-reconciled line
  pr-preflight requires.
- Get a human review/merge decision on
  https://github.com/tokenmaxxxer/refactoring-legacy-rulebook/pull/26.
- Parent-repo units this work depends on for full Acceptance: the
  spec's playbook-pointer field and one live session citing a playbook
  rule — both out of scope for this fan-out unit.

## basis

- docs/issue-1174/proposals/operational-playbook-program.md
- tokenmaxxxer/refactoring-legacy-rulebook branch
  issue-1174/operational-playbook (commit
  2172bcba51b4450f003d5f554b8cb1d02d5fe2e8), PR #26
  (https://github.com/tokenmaxxxer/refactoring-legacy-rulebook/pull/26)

## kind

report

## loop_state

awaiting_approval

## why

Records this session's research-and-delivery work for issue #1174's
operational-playbook program (refactoring-legacy fan-out unit) while
the phase-2 record file stays gated pending human approval.
