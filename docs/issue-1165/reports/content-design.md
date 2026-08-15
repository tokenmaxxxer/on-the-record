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
5. **Pattern family named (amendment 2, added 2026-08-13).** Every
   screen names, in a fixed metadata slot (`convention_family` note),
   which pattern family its primary navigation/form structure follows
   (Material/HIG/common navigation-form patterns). Structural check:
   field non-empty, or `none-applicable` paired with a one-line stated
   reason — the field's presence is checked, not whether the named
   family is the "right" one (that judgment is not automatable, same
   split as rules 1-4). See Amendment 2 below for grounding.

### Tier 2 — new-user checklist

Filed as its own artifact at
docs/issue-1165/reports/content-design/tier2-new-user-checklist.md —
the intuitive-first-screen test, the primary-task-completion test, an
error-recovery test, and (amendment 2, added 2026-08-13) a
convention-conformance test — does the primary flow match imported
Material/HIG/common navigation-form expectations, and if it deviates,
is the deviation stated with a reason — each grounded in a named
source with a stated reject condition and accept shape (requirement
4's anti-nitpick bound: a verdict cites the item, not "feels
confusing").

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

### Amendment 2 — convention-conformance/familiarity (2026-08-13)

Per operator revision request on PR #1170: added
convention-conformance/familiarity as a first-class screen-side
principle, folded into tier 1 (rule 5, `pattern_family_named`) and
tier 2 (checklist item 4) above. Full grounding and the
convention-baseline clause are stated in
`docs/issue-1165/proposals/content-design-screens-comprehensibility.md`
§Amendment 2, mirroring the shape of technical-writing's own amendment
2 (document side) for cross-role consistency, per the review comment's
explicit instruction — canonical: `gh pr diff 1168`, read this turn,
showing the merged document-side amendment-2 clause this section
mirrors. Sources:
Jakob's Law (`https://www.nngroup.com/videos/jakobs-law-internet-ux/`),
principle of least astonishment via platform convention families
(`https://m3.material.io/foundations`,
`https://developer.apple.com/design/human-interface-guidelines`),
Norman's mental models (`https://www.nngroup.com/articles/mental-models/`),
processing fluency
(`https://www.renascence.io/journal/fluency-heuristic-judging-by-ease-of-processing`).

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

## Round 2 (2026-08-16) — human-facing shape of records/PR bodies/reports

Upstream: docs/issue-1165/proposals/2026-08-16-content-design-records-prbodies-reports.md
(filed `status: approved` this turn — the issue thread carries the
exact single-account token `APPROVE issue-1165/content-design`, posted
2026-08-15T15:40:43Z, after the 2026-08-16 research-brief comment and
ahead of this PR).

content_id: docs/issue-1165/reports/content-design/2026-08-16-current-state-survey-records.md
user_need: an implementer (step 2) and any role authoring a record
need a concrete, demonstrated template shape for lead-with-the-point
records/PR bodies/reports, one grain finer than technical-writing's
already-landed paragraph-level rule, so a citation requirement never
has to split the sentence stating the point.
canonical: acceptance: manual review this turn against digital.gov/guides/plain-language/principles — result: UNMEASURED-with-reason: no acceptance command on record for this target
plain_language_check: pass

Decision: mark this section's A/B-variant field not applicable ->
this round ships a review-and-template design, not shipped end-user
copy, so there is no variant to test.

tone-axis check: skipped, reason — this section's output is a
template/checklist design for engineering consumption (step 2's
implementer and future record authors), not shipped end-user product
copy, so NN Group's 4-axis tone check has no applicable audience here.

### What was done

From the content-design lens, designed the human-facing shape of
records/PR bodies/reports for the universal `human_comprehensibility`
criterion, per this session's invocation and the 2026-08-16 research
brief on issue #1165.

1. **Lead-with-the-point template shape for records.** Applied to
   `record-scaffold.sh`'s emitted section order (`## Summary of work`,
   `## Why`, `## What did not work`, `## Open findings`, `## Next
   steps`, `## Resolution path`) -> a design decision adding a lead
   paragraph slot before that first heading, restating what/why/
   so-what in plain prose, with any `canonical:`/citation tag placed as
   a trailing clause or its own line, never interleaved inside the
   point-stating sentence. Structural check (automatable, same framing
   as round 1's tier-1 rules): the sentence immediately preceding a
   `canonical:` tag does not itself contain the string `canonical:`
   mid-sentence (i.e. the tag starts its own sentence or line, never
   sits inside an open parenthetical of the claim sentence).
2. **Enumeration/section bounds for records.** Reuses technical-
   writing's already-landed structural-cap shape (issue requirement 2's
   "consecutive unstructured enumeration cap") one surface over: a
   record section with no sub-heading stays under a stated line bound
   (left as a step-2 tunable, same reasoning as round 1's screen
   length-bound self-critique — no real record corpus was measured this
   round to calibrate a specific number) before it must break into
   named sub-sections. Mirrors round 1's tier-1 screen rule 4 ("no
   raw-context dumps"), applied to prose records instead of screen
   copy.
3. **New-reader test, demonstrated on a real landed record.**
   canonical: `docs/issue-587/reports/implementation.md` lines 15-22,
   read this turn, quoted verbatim in the current-state survey filed
   alongside this section
   (docs/issue-1165/reports/content-design/2026-08-16-current-state-survey-records.md):
   the citation clause sits inside the sentence stating what changed,
   between the proposal reference and its own closing parenthesis —
   a reader must skip mid-sentence to recover the point. Target shape:
   state the point first, move the citation to a trailing clause or its
   own line.
4. **PR-body spec** (added per PR #1616 blocking review comment,
   2026-08-15T15:53:19Z — this item was gap-naming only before that
   comment; it now carries the actual design).
   `gates/pr_reference.py`'s `check_body` (function at line 29, read
   this turn) checks only a phase-appropriate issue-reference trailer
   (`#<n>` phase-1, `Closes/Fixes/Resolves #<n>` phase-2) — no
   content-structure check exists on this surface. Design (still no
   gate implementation, per this round's own scope guard):
   - **First-paragraph shape.** The PR body's first paragraph states
     the change, why, and what happens next (what the merge unblocks
     or what phase-2 will do) before any trailer line (`Part of #<n>`,
     `Closes #<n>`, the sandbox-relay disclosure line). Structural
     check: the first blank-line-delimited paragraph must contain a
     what-changed clause and a why/next clause; a body whose first
     paragraph is only a trailer line fails.
   - **Citation-trailing placement.** Reuses item 1's citation-not-
     mid-sentence structural check verbatim, applied to the PR body's
     first paragraph: a `canonical:`-style or link-shaped citation
     sits as a trailing clause or its own line, never splitting the
     point-stating sentence.
   - **Bounds.** The first paragraph stays within the same section-size
     line bound named in item 2 (same step-2 tunable, no separate
     number chosen here); trailer lines are exempt since they are
     machine-checked fields, not prose.
   - This item still names, not fixes, the gap — `check_body` gains no
     new check this round; wiring stays step 2.

### Reconciliation with required-field record contracts

The template shape above governs the PROSE sections around a record's
required fields, never the fields themselves: `roles/specs/*.spec.json`
`required_fields` (and this role's own `content_id`/`user_need`/
`plain_language_check`) are unaffected. The lead-paragraph-before-
first-heading placement and the citation-not-mid-sentence rule apply
to the body prose that follows the YAML frontmatter block; nothing in
this round's design removes, renames, or reorders a required
frontmatter key.

### Hand-off / relationship to technical-writing's round 2

This round's citation-placement rule is one grain finer than
technical-writing's already-landed paragraph-level `lead_paragraph_present`
rule (a paragraph exists before the first heading) — that rule does not
reach inside the sentence to check where a citation sits; this round's
rule does, and the two compose without conflict (paragraph existence
first, then sentence-level citation placement within it).

### Self-critique note

Same open tunable pattern as round 1: the section-size line bound is
left unset (no real record corpus was measured this round), and the
citation-not-mid-sentence structural check is stated as a rule shape,
not implemented as a runnable script this round (design/spec only, per
this turn's invocation) — step 2 should either implement it against
`gates/record_lint.py`'s existing citation-detection logic or state why
it does not.

## Open findings

None outstanding for round 1's own scope (design of the screens
criterion) or round 2's own scope (design of the records/PR-body/
report shape) — both rounds are design/spec deliverables; the tier-1
length bounds (screens and records) and the tier-3 sampling ratio are
left as named tunables for step 2 to set with a stated reason, per each
round's self-critique note above — configuration choices, not defects
in either round's design. The PR-body content-structure design (item 4
above, added per PR #1616's blocking review comment) is designed but
not fixed, per this round's scope guard — same design/no-gate-
implementation split as items 1-2.
