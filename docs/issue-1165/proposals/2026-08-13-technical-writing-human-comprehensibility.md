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

## Proposed structure

Four subsections follow: tier 1 (structure rules), tier 2 (new-reader
checklist), tier 3 (sampled deep review), and reconciliation with
required-field record contracts.

### 1. Tier 1 — automatable structure rules (document side)

Four rules, each a checkable predicate over prose content, branched by
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

`verification_method` for all four: automated structural scan
(regex/markdown-AST over the prose body) — no LLM judgment call, per
#1156's automatable-tier bar. (Corrected post-hunt: rule 1 is now
`lead_paragraph_present`, a positional/structural predicate only — see
rule 1's note above for why the semantic half moved to tier 2 rather
than staying a falsely-automatable proxy.)

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

A `fail` verdict must cite which of the three items failed and what a
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

## Plan for phase 2

1. Add a `human_comprehensibility` entry (the four tier-1 rules as
   `{criterion, verification_method}` sub-entries) to
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
