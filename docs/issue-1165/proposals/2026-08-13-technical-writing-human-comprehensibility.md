---
status: proposed
files:
  - docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md
---

# issue-1165 (technical-writing, step 1): human-comprehensibility criterion — document side

kind: proposal
subject: issue-1165

Proposal: docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md

## Background

Issue #1165 asks for `human_comprehensibility` as a universal
quality-bar criterion (northpole req#4/req#2), operationalized in three
tiers per the issue's own validity-consult finding (2026-08-13T03:58):
tier-1 automatable structure rules, tier-2 a named new-reader checklist,
tier-3 a sampled deep review. This is the document-side design (step 1,
technical-writing), running in parallel with content-design's
screen-side design. Read basis: `docs/issue-1165/reports/
technical-writing/current-state-survey.md` and `docs/issue-1165/
reports/technical-writing/scout-brief.md` (both read/written this
turn). It reuses #1156's already-landed `quality_bar`
`{criterion, verification_method}` decomposition shape (canonical:
`docs/issue-1156/proposals/per-role-quality-bars.md` §0, read this
turn) rather than inventing a new mechanism.

## Target reader

A phase-2 implementing session (this role or another) that will copy
§ "Proposed structure" into a `quality_bar` entry on
`roles/specs/technical-writing.spec.json` and into on-the-record's
record-scaffold/report-framing surfaces, with no further design
judgment needed — the same "phase 1 proposal, phase 2 copies verbatim"
relationship #1156 already established. Secondarily, any role or human
reviewer checking whether a document/record meets the new criterion.

## Amendment 2 — convention-conformance/familiarity (2026-08-13)

Operator amendment 2 requires familiarity/convention-conformance as a
first-class comprehensibility principle, web-verified per the same
THOROUGH standard as amendment 1. Document-side grounding, each with
its source:

- **Jakob's Law** — "users spend most of their time on other sites"
  and transfer expectations built on familiar products to a new one;
  meeting imported expectations reduces cognitive load (Nielsen Norman
  Group, canonical: `https://www.nngroup.com/videos/jakobs-law-internet-ux/`,
  `https://lawsofux.com/jakobs-law/`). Document-side reading: a
  reader who has seen one README/CHANGELOG/API-reference before
  arrives at the next one with a shape already in their head; a
  document that departs from that shape spends the reader's attention
  on re-orientation instead of content.
- **Processing fluency** — information that is easier to process is
  judged more reliable, truthful, and trustworthy; familiarity and
  fluency (repetition, readability, structural predictability) are a
  documented driver of this effect (canonical:
  `https://www.renascence.io/journal/fluency-heuristic-judging-by-ease-of-processing`,
  Schwarz et al., `https://dornsife.usc.edu/norbert-schwarz/wp-content/uploads/sites/231/2023/12/21_CPR_Schwarz_et_al_Metacognitive_experiences_review.pdf`).
  Evidence grade: validated (peer-reviewed cognitive-psychology
  literature, not practitioner consensus) — a document in a
  recognizable genre shape is not just easier to read, it is judged
  more credible for the same content.
- **Inverted pyramid** — the default structural convention of
  hard-news writing: most important information first, descending
  detail after, so a skimming or interrupted reader still gets the
  essential facts (canonical: `https://www.nngroup.com/articles/inverted-pyramid/`,
  which explicitly ports the convention to web/document writing for
  comprehension, not just journalism). Directly grounds this role's
  existing lead-with-the-point rule (§1 rule 1, §Rationale) and
  extends it: leading with the point is *also* conformance to a named,
  widely-recognized genre convention, not only a minimalism choice.
- **Keep a Changelog** — a named, web-published standard document
  skeleton (canonical: `https://github.com/olivierlacan/keep-a-changelog`,
  keepachangelog.com) with fixed section categories (Added, Changed,
  Deprecated, Removed, Fixed, Security), reverse-chronological
  versions, ISO 8601 dates. Cited here as the worked example of what
  "conforms to a convention family" cashes out as for one concrete
  document genre; on-the-record does not currently produce
  user-facing changelogs, so this is grounding, not a new required
  artifact.
- **Norman's mental models** — users build a mental model from prior
  exposure to similar artifacts and expect a new artifact to match it
  (least-astonishment corollary); already the same source this
  session's `prose-modes` skill grounds reader-knowledge routing in,
  extended here to document *shape* rather than only sentence-level
  style.

**Where amendment 1 and amendment 2 could conflict, and the
resolution**: amendment 1's cognitive-load/minimalism principles
(Sweller, ISO 24495-1 plain language) could in principle push toward
a novel, maximally-minimal structure per document; amendment 2 pushes
toward the *familiar* structure even when a bespoke one might be
marginally more minimal for one specific document. Resolution: convention
wins by default (a familiar-but-slightly-denser structure costs the
reader less than a novel-but-locally-optimal one, because the
processing-fluency literature above shows the orientation cost of an
unfamiliar shape is paid on every read, not once) — amendment 2's own
"deviation-with-reason, never silent novelty" clause is the release
valve for the cases where a document's content genuinely does not fit
any named convention family; the deviation must be *stated*, not
silently defaulted to a bespoke shape.

**Deliverable addition — convention baseline clause**, folded into
tier 1 and tier 2 below:

- **Tier 1 (new checkable rule, `convention_family_named`)** — every
  document/record names, in a fixed metadata slot (for this role: the
  already-required `doc-type`/`quadrant` field, extended by one
  optional free-text `convention_family` note alongside it — e.g.
  "Diátaxis how-to", "Keep-a-Changelog", "inverted-pyramid status
  report"), which convention family it follows. `verification_method`:
  automated presence check — the field is non-empty, not that the
  named family is the "right" one (that judgment is not automatable,
  same rationale as §1 rule 1's split). A record whose convention
  family is `none-applicable` is legal only alongside a one-line stated
  reason (deviation-with-reason), mirroring the existing `unverifiable:`
  escape-line convention already enforced by `record-claim-guard.sh`.
- **Tier 2 (new checklist item, `genre-shape-match`)** — added as a
  fourth item alongside what-changed/why/what-next: "does this
  document's shape match its named convention family (§ordering,
  headings, what's up top), and if it deviates, is the deviation
  stated with a reason?" A `fail` verdict here follows the same citation
  discipline as the other three items (which convention family, what
  specifically doesn't match, what a passing shape looks like) —
  never a bare "feels off."

This amendment does not touch tier 3 or §4's reconciliation — sampled
deep review and required-field reconciliation already generalize to
the new field without further design.

## Proposed structure

Five subsections follow: tier 1 (structure rules, now including
convention-family-named), tier 2 (new-reader checklist, now including
genre-shape-match), tier 3 (sampled deep review), reconciliation with
required-field record contracts, and the amendment-2 addition above.

### 1. Tier 1 — automatable structure rules (document side)

Five rules, each a checkable predicate over prose content, branched by
the document's own required `quadrant` field (Diátaxis grounding: a
`reference` quadrant tolerates denser enumeration than a `tutorial`):

1. **lead_paragraph_present** — a non-empty prose paragraph exists
   before the first heading, list, or step block in the body (a purely
   structural/positional check: paragraph exists, precedes detail). The
   *semantic* claim that this paragraph actually states what/why/so-what
   is not automatable — a warrant-hunter finding on this proposal (after-
   proposal stance 3, canonical: `docs/issue-1165/reports/
   technical-writing/2026-08-13-hunt-technical-writing-human-
   comprehensibility.md`) confirmed no regex/AST scan can judge whether
   a paragraph "states why it matters," contradicting #1156 principle 3
   (non-automatable → named human-review checklist, never an automated
   proxy). That semantic judgment is therefore not duplicated in tier 1
   at all — it is exactly tier 2's `what-changed`/`why`/`what-next`
   checklist (§2 below), which already carries it as
   `verification_method: human-review-checklist`. Tier 1 only checks the
   positional precondition tier 2's checklist needs to even be
   answerable (no lead paragraph → tier 2 fails trivially on all three
   items, cited together).
2. **enumeration_cap** — no more than 12 consecutive unstructured list
   items (a flat bullet/numbered run with no sub-heading break) in
   `tutorial`/`how-to`/`explanation`; `reference` is exempt from the cap
   itself but must sort/group items under named sub-headings once it
   exceeds 12, rather than one undifferentiated wall.
3. **section_size_bound** — no prose section (text between two
   headings, or the whole body if unheaded) exceeds ~150 lines /
   ~1200 words without a sub-heading break. Named escape: a section may
   exceed it only as a single indivisible artifact (a code listing, a
   full command transcript), and the escape must be stated inline, not
   silent.
4. **no_raw_dump** — a human-facing prose section may not paste an
   unfiltered raw log/diff/tool-output dump in place of authored prose;
   raw material belongs in a fenced block the surrounding prose
   explains, never substituting for the explanation.
5. **convention_family_named** (amendment 2, added 2026-08-13) — the
   document/record names its convention family in a fixed metadata
   slot (this role: `doc-type`/`quadrant` plus an optional adjacent
   free-text `convention_family` note). Non-empty, or `none-applicable`
   paired with a one-line stated reason (deviation-with-reason) — see
   the Amendment 2 section above for grounding and the escape-line
   precedent this mirrors.

`verification_method` for all five: automated structural scan
(regex/markdown-AST over the prose body, plus a field-presence check
for rule 5) — no LLM judgment call, per #1156's automatable-tier bar.
(Corrected post-hunt: rule 1 is now `lead_paragraph_present`, a
positional/structural predicate only — see rule 1's note above for
why the semantic half moved to tier 2 rather than staying a
falsely-automatable proxy.)

**Empty state** (per the issue's acceptance check): a doc_id whose
`content` has no human-facing prose section at all (e.g. scaffold text
still `PLACEHOLDER:`, or a structured-only artifact) is exempt from
tier 1 and must be *listed* as exempt by the check output, never
silently skipped.

### 2. Tier 2 — new-reader checklist (DOCUMENTS/RECORDS)

One pass, no session context assumed:

1. **what-changed** — can the reader state, in their own words, what
   the document/record is about or what changed, from the lead section
   alone?
2. **why** — can the reader state why it matters / why it was done,
   without re-reading the whole body?
3. **what-next** — can the reader state what happens next / what they
   are meant to do with this document, without a follow-up question?
4. **genre-shape-match** (amendment 2, added 2026-08-13) — does this
   document's shape (ordering, headings, what's up top) match its
   named convention family (rule 5, tier 1), and if it deviates, is
   the deviation stated with a reason? See the Amendment 2 section
   above for grounding.

A `fail` verdict must cite which of the four items failed and what a
passing shape looks like for that item (issue requirement 4,
anti-nitpick bound) — e.g. "what-changed fails: lead paragraph opens
with rationale, not the change; passing shape: state the change in
sentence 1, rationale in sentence 2." A bare "unclear" is not a valid
tier-2 verdict.

### 3. Tier 3 — sampled deep review

The owning communication-domain role (technical-writing, for documents)
performs a full read against its landed methodology (Diátaxis quadrant
fit, Google Developer Documentation Style Guide compliance, the
already-required `minimalism check` and `style-guide compliance note`
fields) on a sample of landed documents, not every one. Sampling
frequency is a tunable (consult caveat) — this proposal does not fix a
number; phase 2 should start with a small fixed sample (e.g. 1-in-N
landed docs) and adjust from observed miss rate.

### 4. Reconciliation with required-field record contracts (issue
requirement 3)

Stated per field, using `roles/specs/technical-writing.spec.json`
(canonical, read this turn) as the worked example:

- `doc_id` (ref) — structured reference field, not prose; tiers 1-3
  do not apply. `reference_resolution` already governs it.
- `quadrant` (enum) — structured field, not prose-checked; it is the
  *input* tier 1's rules branch on (§1).
- `content` (string) — the prose body tiers 1-3 govern. A structure-
  rule failure here is a `human_comprehensibility` verdict, additive to
  and separate from `content`'s own required-field presence check: a
  field can be present-and-valid and still fail
  `human_comprehensibility`; the reverse never waives the field's
  required-field status.
- Role-directive record fields not yet in `spec.json`'s schema
  (`target-reader note`, `doc outline`, `minimalism check`,
  `style-guide compliance note`, `accuracy review evidence`) — remain
  required as-is; tiers 1-3 apply only to the free-text prose *within*
  them, never to their required presence.
- On-the-record's own record body sections (`## Summary of work`,
  `## Why`, `## What did not work`, `## Open findings`, `## Next
  steps`, `## Resolution path`, scaffolded by `record-scaffold.sh`) are
  prose sections in scope for tiers 1-3 identically to a document's
  `content` — the "on-the-record's own output surfaces" half of issue
  requirement 1. `## What did not work`'s `None.`-marker convention
  (record-tiering directive, issue #760) is explicitly compatible with
  `no_raw_dump`/`section_size_bound`: a bare `None.` is the terse-and-
  correct shape when nothing real happened, not a violation.

## Rationale

- Diátaxis quadrant-branching (scout brief §Grounding) prevents one
  numeric cap from over- or under-constraining a quadrant with a
  structurally different legibility contour (a reference list is
  supposed to enumerate; a tutorial is not).
- The Google Developer Documentation Style Guide (already this role's
  required `style-guide compliance note` field) is the direct source
  for lead-with-the-point and no-raw-dump — this proposal names an
  existing, already-cited standard rather than inventing a new one, per
  #1156's own decomposition principle 2 (no uncited criterion).
- Reusing #1156's `{criterion, verification_method}` shape means phase
  2 is a copy-in, not a new mechanism design, and the criterion inherits
  `quality_bar.py`'s already-landed anti-circularity and bounded-
  rejection (`REJECT_CAP`) machinery for free.
- Per-field reconciliation (§4) is written explicitly, field by field,
  because the issue names this the one place a structure rule could
  wrongly be read as overriding a required field — spelling it out here
  removes that ambiguity before phase 2 touches any spec file.
- Convention-conformance wins over locally-optimal novelty by default
  (Amendment 2 section, conflict resolution) because processing-fluency
  research shows a familiar shape's comprehension benefit is paid on
  every read, not once — the same reasoning that already grounds
  Diátaxis quadrant-branching above, extended from sentence-level style
  to document-level shape.

## Plan for phase 2

1. Add a `human_comprehensibility` entry (the five tier-1 rules,
   including `convention_family_named`, as `{criterion,
   verification_method}` sub-entries) to
   `roles/specs/technical-writing.spec.json`'s `quality_bar` array —
   new array, since technical-writing was one of #1156's 36
   domain-stub roles, not one of its 7 fully-decomposed roles.
   Corresponding gate fixture tests (a passing lead-summary+bounded-
   section fixture, a failing raw-dump fixture) land in `gates/`.
   provenance target: executed-unit, matching the issue's first
   acceptance check.
2. Apply the tier-1 structure to `record-scaffold.sh`'s body template
   and `report-framing-check.sh`'s framing surface (issue delivery
   order item b, "on-the-record's own record/report templates").
3. Run one tier-2 new-reader checklist review, live, against one real
   landed record, and record the verdict — the issue's second
   acceptance check (provenance: executed-live, one sampled real
   record).
4. Fold the tier-2 checklist into other communication-domain roles as
   #1156/#1163 batches land theirs (issue delivery order item c) —
   this proposal's document-side design is the template; each role
   still owns its own screen/domain wording.

## Out of scope

Scope gate: this proposal is document-side design only — it does not
land any spec/hook/gate/template file, and it does not decide anything
for another role's surface.

- Screen-side tier design (content-design's parallel step; owned on
  content-design's own branch, not here).
- Landing the `human_comprehensibility` entry into
  `roles/specs/technical-writing.spec.json`, any `gates/` check, or
  `record-scaffold.sh`/`report-framing-check.sh` — phase 2, listed
  above, not this PR.
- Fixing the tier-3 sample size/frequency number (left a tunable per
  the issue's consult caveat).
- Any other role's own tier-1/tier-2 wording — #1156/#1163's per-role
  batches own theirs.

## Approval

Per role-handoff contract v3 s19, phase 2 (landing the plan above)
opens on an approvers.md account's PR review Approve, or — single-
account mode — an issue-level comment whose entire body is exactly
`APPROVE issue-1165/technical-writing`. Until then this PR carries only
this proposal and the phase-1 research records under
`docs/issue-1165/reports/technical-writing/`.

## What did not work

None.
