---
issue: 2241
role: architecture
loop_state: landed
kind: adr
upstream:
  - path: docs/issue-2241/reports/architecture/survey.md
    sha: same-commit
  - path: docs/issue-2241/reports/architecture/scout-brief.md
    sha: same-commit
  - path: docs/decisions/2026-08-25-retire-role-axis-staging.md
    sha: same-commit
decision_id: docs/decisions/2026-08-25-retire-role-axis-staging.md
context: >
  issue #2241 (operator decision, 2026-08-25): role does four unrelated
  jobs at once (concurrency, write-isolation, verification-kind
  tagging, branch naming); retiring role as an identity axis requires
  deciding, per job, whether a sub-key is needed and what it is.
considered_options:
  - "Option A -- decompose into four independently-owned concepts (chosen)"
  - "Option B -- rename role to skill in-place, keep one axis"
  - "Option C -- stop at #1955's scope (guidance-source only)"
  - "Option D -- merge lease and author-identity into one field"
  - "Option E -- big-bang cutover in one PR"
outcome: accepted
axis_evaluation:
  - maintenance-complexity-1
---

# issue-2241 — architecture record

## What was done

Produced the staged proposal set issue #2241's acceptance criterion
names as this issue's own deliverable (no stage-0 code is built by this
session): a current-state survey, a scout brief, one MADR-shaped ADR
naming five considered options, and seven independently-landable stage
proposals (0-6), each with its own `files:` write set, Rationale naming
a rejected alternative, acceptance criteria, and rollback.

- `docs/issue-2241/reports/architecture/survey.md` — current-state
  survey; refutes two of the issue's own claims (open-PR count, and
  "unverified" `roles/specs/*.spec.json` consumer count) and finds
  stage 2's stated goal already mostly landed by #1955.
- `docs/issue-2241/reports/architecture/scout-brief.md` — prior-art
  scout across four angles (lease/claim patterns, append-only
  authorship, check-kind-vs-checker-identity, staged-cutover
  mechanics), batched-sequential fallback mode stated explicitly.
- `docs/decisions/2026-08-25-retire-role-axis-staging.md` — the ADR
  this record's `decision_id` and `considered_options` resolve
  against, including the frozen-decision disposition lines below.
- `docs/issue-2241/proposals/2026-08-25-stage-{0..6}-*.md` — seven
  stage proposals, dependency-ordered per the issue's own staging,
  observer-record-kind rewrite (stage 5) placed second-to-last and
  deletion (stage 6) last, per the issue's explicit rationale about
  incidents #2233/#2238.

## Why

The issue itself supplies the decision (retire role, land lease/author-
identity/record-kind, stage the rollout); this role's job was
evaluating, per issue #2241's own consult request, "which of those jobs
genuinely need a sub-key," and turning that into a concrete,
independently-landable staging plan with real rejected alternatives —
not just restating the issue's own framing. `architecture-coupling-classification`
and `architecture-module-boundary-definition` guidance (both invoked
this session) informed classifying today's role-string coupling as
control/stamp-coupling-shaped across seven-plus files, and choosing to
decompose along the four job boundaries rather than merge any pair of
them back together (Option D's rejection, below). `architecture-decomposition-strategy`
guidance informed choosing a Strangler Fig staged rollout with
observers moved last (Option E's rejection) over a single-PR cutover.

## Upstream basis

`docs/issue-2241/reports/architecture/survey.md`,
`docs/issue-2241/reports/architecture/scout-brief.md`, and
`docs/decisions/2026-08-25-retire-role-axis-staging.md` (all this repo,
this commit — `sha: same-commit` per the frontmatter above); issue
#2241's own body (operator decision, 2026-08-25); prior issues #1758
and #1955 (survey section 6); frozen decisions `single-skill-axis` and
`single-enforcement-surface` (`docs/decisions/2026-08-21-*.md`).

## Axis evaluation

### Axis evaluation procedure — maintenance_complexity

READ: `docs/decisions/2026-08-25-retire-role-axis-staging.md`'s five
considered options and their stated drivers; the modules the accepted
option's `outcome` touches (survey sections 1-6: `spawn.py`,
`board-gate.sh`, `merge_gate.py`/`spawn_on_pr.py`, `roles/*.json`,
`consult.py`/`skills.py`).

EXECUTE: (1) five considered options are listed, each with a stated
driver distinguishing it from the chosen option (collision safety for
B, staging-order risk for C, mutability-invariant conflict for D,
incident-reproduction risk for E). (2) Diffing the chosen option's
scope against option C's (status quo beyond #1955): the accepted
option changes seven-plus coupling points the survey enumerated
one-to-one by job, where option C leaves all seven-plus permanently
coupled to a single 43-name enum.

- axis: maintenance_complexity
  verdict: supports
  citation: `docs/decisions/2026-08-25-retire-role-axis-staging.md`,
    plus MADR (https://adr.github.io/madr/) for the
    >=2-options/stated-drivers requirement.
  id: maintenance-complexity-1

## Open findings

- `roles/specs/*.spec.json`'s `reference_resolution.rule` text names a
  `docs/product/*.md` citation shape for `axis_evaluation.citation` that
  does not match this role's actual domain (an internal-harness ADR, no
  product docs apply); this record's citation instead follows
  `docs/handbooks/architecture-methodology.md`'s axis-specific
  guidance (an ADR path plus the MADR source). `gates/role_spec_shape.py`'s
  `check_axis_evaluation_entry` function only requires the citation be
  a non-empty string, so this substitution satisfies that mechanical
  requirement even though it diverges from the spec's own prose.
  Resolution path:
  a follow-up to this role's own spec text, aligning
  `reference_resolution.rule`'s prose with the methodology handbook's
  per-axis citation guidance.
- `roles/architecture.json`'s `record_fields.loop_state` vocabulary
  (`drafting`, `reviewing`, terminal `landed`) has no state cleanly
  naming "the deliverable is a proposal set, not code" — this record
  uses the existing terminal value `landed` per this repo's own
  precedent (`docs/issue-1199/reports/architecture.md`, which used
  `landed` at PR-open time for a documentation-shaped deliverable too).
  Resolution path: none required unless a future proposal-only
  architecture deliverable finds `landed` misleading in review.
- Stage 3 and stage 6 both depend on a PR against the separate
  `tokenmaxxxer/tokenmaxxxer-core` repository (survey section 2); this
  record's write set never touches that repository, so those two
  stages' own future implementation sessions carry the actual
  cross-repo coordination risk, not this session. Resolution path:
  each stage's own future proposal-round session must re-read
  `board-gate.sh`'s then-current shape before building, since this
  ADR's citations are a point-in-time read.

## Next steps

None for this session — loop_state is terminal (`landed`). The seven
stage proposals are each their own future issue's starting point; no
further action is expected from this architecture-role unit of work on
issue #2241 itself.

## Skill verdicts

skill-verdict: architecture-coupling-classification — applied: invoked;
used to classify today's role-string coupling (rule shapes 1, 4, 5, and
9 — common, control, and stamp coupling across `spawn.py`,
`board-gate.sh`, `merge_gate.py`, and `roles/*.json`) and to reject
Option D (merging lease and author-identity reintroduces stamp
coupling per rule 5's whole-struct-for-one-field shape).

skill-verdict: architecture-decomposition-strategy — applied: invoked;
used to choose a Strangler Fig staged rollout (rule 4) over a
single-PR cutover (Option E, rejected per rule 4's mechanics and the
issue's own #2233/#2238 evidence), and to place the deletion stage
last per rule 13's shared-logic-consolidation-before-deletion shape.

skill-verdict: architecture-module-boundary-definition — applied:
invoked; used to justify drawing four separate concept boundaries
(rule 1 — hide each independently-changing decision inside its own
concept) rather than merging lease and author-identity (rule 9 would
require the boundary to no longer hide anything before merging, which
it still does — see Option D's rejection).

skill-verdict: market-analysis-mece-proposal — applied: invoked; used
to check the seven stage proposals for pairwise content overlap (rule
1) and against the issue's own required coverage (rule 9, substituting
the issue's seven named stages for that skill's native "5 required
elements" checklist, since this proposal isn't the market-analysis role
spec it was originated for) — no stage's `files:`/Rationale content is
restated in another stage's proposal.

other mounted skills: not triggered — `architecture-dependency-direction`
(no import-cycle/layering-direction question arose; the four new
concepts are peers, not layered) and `architecture-interface-contract-shape`
(no sync/async or saga/choreography boundary question arose).
