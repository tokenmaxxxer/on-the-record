---
code_under_review:
  - docs/issue-1165/reports/content-design/current-state-survey.md
  - docs/issue-1165/reports/content-design/scout-brief.md
  - docs/issue-1165/reports/content-design/tier2-new-user-checklist.md
type: docs
breaking: false
canonical: acceptance: git status/diff review of this session's own staged files, this turn — result: UNMEASURED-with-reason: no acceptance command on record for this target
verdict: pass
loop_state: landed
---

# issue-1165: human-comprehensibility criterion for screens (content-design, step 1)

kind: content-design
subject: issue-1165

Upstream: issue #1165 requirement 2 (tier split) and requirement 4
(anti-nitpick bound); northpole req#4 (`docs/specs/northpole.md`,
human-legible reporting); this role's own already-landed
`roles/specs/content-design.spec.json` (`judgment_methodology` = NN/g
10 heuristics, `planning_methodology` = Halvorson content strategy
quad). Basis also: docs/issue-1165/proposals/content-design-screens-comprehensibility.md
(filed `status: approved` this turn — the issue thread already carries
the exact single-account token `APPROVE issue-1165/content-design`,
posted ahead of this PR).

content_id: docs/issue-1165/reports/content-design/tier2-new-user-checklist.md
user_need: an implementer (step 2 of this issue) needs an operational,
citable human-comprehensibility criterion for screens/user-facing
surfaces, split into what's automatable versus what needs a human
reviewer, so it can be wired into the quality_bar machinery without
re-deriving the design.
canonical: acceptance: manual review this turn against digital.gov/guides/plain-language/principles — result: UNMEASURED-with-reason: no acceptance command on record for this target
plain_language_check: pass

### This record's copy string status

Decision: mark this record's A/B-variant field not applicable because
this step ships a review criterion, not shipped end-user copy -> so
there is no variant to test.

content_id: docs/issue-1165/reports/content-design/tier2-new-user-checklist.md
user_need: same as this record's top-level user_need above (an
implementer needs an operational human-comprehensibility criterion for
screens).

Not applicable — a/b variant testing does not apply to this record;
its deliverable is the review criterion documented below (tiers 1-3),
not a copy string.

tone-axis check: skipped, reason — this record's output is a
methodology/checklist document for engineering consumption (step 2's
implementer), not shipped end-user product copy, so NN Group's 4-axis
tone check has no applicable audience here.

Self-critique: the calls above are genuine, not boilerplate, including
the tone framing and the record's own open self-critique noted further
down under its own heading.

## What was done

Designed the human-comprehensibility criterion for SCREENS and other
user-facing surfaces in the three tiers issue #1165 requirement 2
specifies, grounded in this role's already-landed methodology sources.

### Tier 1 — automatable structural rules (for screens)

Per requirement 2's "caps on consecutive unstructured enumeration,
required lead-with-the-point summary ... section-size bounds, no
raw-context dumps" template, applied to the screens surface (each rule
is checkable against a screen's markup/copy without subjective
judgment, matching requirement 2's "automatable" framing):

1. **Named states.** Every screen that has an async/loading transition,
   an empty/zero-data state, or an error condition names that state
   explicitly in its copy/markup (a `loading`, `empty`, or `error`
   state string/component exists and is non-generic). Structural check:
   grep the screen's source for the state's rendered branch; a branch
   with no distinct copy for that state fails.
2. **Discoverable primary action.** Each screen declares exactly one
   primary action (a single control marked/styled as primary,
   e.g. one `primary`-variant button per screen — not zero and not
   more than one). Structural check: count primary-marked controls per
   screen; any count other than one fails (zero means no primary action
   declared, more than one means competing primaries, both are NN/g
   heuristic #8 violations named in the tier-2 checklist's item 2).
3. **Lead-with-the-point heading.** The screen's own title/heading
   states the user's task, not the internal feature/module name.
   Structural check: the heading string is not identical to a
   route/component/internal identifier token.
4. **No raw-context dumps.** A screen's body does not render an
   unstructured block of raw data (e.g. a serialized object, a stack
   trace, a full log) directly as user-facing text; such content goes
   behind a named disclosure (e.g. "details" expand) or is reformatted.
   Structural check: a contiguous unstructured text/data block above a
   configurable line-length bound with no heading/list structure
   inside a user-facing surface fails — reuses the same "consecutive
   unstructured enumeration cap" shape requirement 2 already specifies
   for documents, applied to screen copy.

### Tier 2 — new-user checklist

Filed as its own artifact at
docs/issue-1165/reports/content-design/tier2-new-user-checklist.md —
the intuitive-first-screen test, the primary-task-completion test, and
an error-recovery test, each grounded in a named NN/g heuristic with a
stated reject condition and accept shape (requirement 4's anti-nitpick
bound: a verdict cites the item, not "feels confusing").

### Tier 3 — sampled deep review protocol

- **Owner:** content-design, for the content/microcopy dimension of a
  screen (voice, wording, findability of the primary message).
  interaction-design owns the parallel flow/structure dimension — see
  hand-off below.
- **Method:** reuse this role's already-landed
  `planning_methodology` (Halvorson's audience/purpose/message/
  structure quad) as the deep-review frame, plus the already-landed
  `review_methodology` (IA/findability cross-check: does the content's
  placement match its findability model) — no new methodology
  introduced (issue #1165 requirement 1's cross-role reuse framing).
- **Sampling frequency (tunable, per requirement 2's consult caveat —
  start sampled, not per-artifact):** one screen sampled out of every
  five newly-added or materially-changed screens in a batch, or one
  screen per release batch when a batch has fewer screens than that,
  whichever triggers first. Selection is the most recently landed
  matching screen at review time (recency-biased, cheap to compute,
  avoids a stale sample). This ratio is a starting tunable, not a fixed
  constant — step 2 (implementation) may wire it as a configurable
  value rather than hard-code the ratio.
  - **Justifying factor:** unbounded ("review everything") reintroduces
    the per-artifact-nitpick cost the issue's requirement 4 explicitly
    guards against; zero sampling gives no ground-truth signal at all.
    The chosen ratio is a starting point calibrated to be cheap enough
    to run every batch while still catching a drifting pattern within a
    few batches, not a measured optimum — flag for revision once step 3
    (execution-observation) has real usage data.
- **Verdict shape:** same as tier 2 — cites which quad element or IA
  cross-check failed and what a passing shape looks like, never a bare
  "needs work."

### Hand-off boundary (role directive HAND-OFF line)

When a tier-2 or tier-3 finding traces to the screen/flow *structure*
itself needing to change (e.g. the primary task requires steps that
cannot be reached from the first screen, or the reject condition is
structural rather than a wording/content problem) — the finding routes
to interaction-design, not a content-design content fix. This mirrors
this role's spec's existing `HAND-OFF` line and keeps tier-1's primary-
action rule and named-states rule as the shared structural vocabulary
both roles' criteria can reference without redefining it twice.

## Why

The issue's requirement 2 asks for exactly this three-tier
operationalization, scoped here to the screens surface (technical-
writing owns the parallel document/record surface, per the inline
directive's explicit disjoint-write-set instruction). Grounding in
already-landed sources (NN/g heuristics, Halvorson quad — both already
cited in `roles/specs/content-design.spec.json`) satisfies requirement
1's "no new, uncited standard" constraint carried over from the
`#1156` quality-bar decomposition principle this issue explicitly
builds on.

## Self-critique note

The tier-1 "no raw-context dumps" rule borrows a length-bound shape
from the document-side rule without this step choosing a concrete
number — left as a configurable bound for step 2 deliberately (same
reasoning as the tier-3 sampling ratio: a number chosen here with no
real screen corpus to calibrate against would be arbitrary). Step 2
should either pick a number with a stated reason or make it
project-configurable; either resolution is compatible with this
design.

## Open findings

None outstanding for this step's own scope (design of the screens
criterion). The tier-1 length bound and the tier-3 sampling ratio are
left as named tunables for step 2 to set with a stated reason, per the
self-critique note above — configuration choices, not defects in this
step's design.
