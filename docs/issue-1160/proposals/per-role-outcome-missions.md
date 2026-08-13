---
status: proposed
files:
  - roles/specs/brand-design.spec.json
  - roles/specs/content-design.spec.json
  - roles/specs/market-analysis.spec.json
  - docs/specs/reconciled-index.md
---

# issue-1160: per-role outcome missions, phase-1 pilot (proposal, phase 1)

kind: proposal
subject: issue-1160

Proposal: docs/issue-1160/proposals/per-role-outcome-missions.md

## Intent

Give a pilot set of roles an `outcome_mission` (the real-world goal the
profession exists to achieve) and `mission_deliverables`
({artifact, fit_criterion}) declaration in their spec, plus a
need-detector predicate with a stated false-positive bound, so the role
performs the profession's actual work instead of only reviewing it —
issue body requirements 1 and 2. Read basis:
docs/issue-1160/reports/requirements-engineering/current-state-survey.md,
docs/issue-1160/reports/requirements-engineering/scout-brief.md.

## Pilot set (confirm/adjust the 2-3 dormant picks, with rationale)

The issue names three dormant-role candidates (brand-design,
content-design, market-analysis) and two operator-named examples
(ux-engineering, interaction-design). This proposal's write set covers
only the three dormant candidates — the ux-engineering/interaction-design
pair is frozen out per the sequencing note below, not dropped from
scope.

Confirmed dormant picks, unchanged from the issue body: brand-design,
content-design, market-analysis. Rationale for keeping all three rather
than trimming to two:

- brand-design already has a real write_scope
  (`design-tokens/*.json`, canonical: roles/specs/brand-design.spec.json
  `write_scope` field, read this turn) — cheapest pilot, artifact path
  exists, only the mission/deliverable declaration and the usage-rule
  extension are new.
- content-design and market-analysis are both currently `report_only`-
  shaped in effect (write only docs/issue-<n>/reports/<role>.md,
  canonical: roles/specs/{content-design,market-analysis}.spec.json
  `write_scope` fields, read this turn) — they are the clearest
  instances of issue #1129's "review but never perform" gap the issue
  body cites, so dropping either would leave the pilot without a
  report-only-to-artifact test case, which is exactly what phase-2's
  live-pilot acceptance check needs to exercise.

market-analysis is the one candidate whose `required_fields`
(force/assessment/evidence) already match the deliverable shape a
five-forces analysis is supposed to produce (canonical: scout-brief.md
"Gap line" section, read this turn) — its mission declaration is
close to a formality, but it stays in the pilot because it is the
cheapest possible instance to validate the schema-extension mechanics
against before content-design's harder write-scope extension.

## Constraints stated so far

- Mission/deliverable declarations live in specs (northpole req#5 —
  survive fresh clones), not in a separate doc, per issue body
  requirement 5.
- Bar verdicts on mission deliverables reuse #1156's anti-circularity
  design (producer-identity vs. author-identity, resolved through
  account-level check, `BAR_NOT_MET` on match) rather than reinventing
  it — canonical: docs/issue-1156/proposals/per-role-quality-bars.md
  section "### 4. Anti-circularity", read this turn. This proposal does
  not redesign that mechanism; it names, per pilot role below, which
  existing role's spec is the author-identity that records the verdict
  on that pilot role's mission_deliverables (§2/§3/§4's "verified by"
  lines) — a producer role never verifies its own mission deliverable,
  matching #1156 §4's no-self-grading rule.
- Need-detectors are advisory-first (issue body requirement 2): a repo
  without the need stays silent, and each detector's false-positive
  bound is stated explicitly, never left implicit.
- Write-set freeze: roles/specs/ux-engineering.spec.json and
  roles/specs/interaction-design.spec.json are NOT in this proposal's
  write set. #1156 phase-2 (in flight, not yet landed) already owns
  edits to those same two files for its `quality_bar`/`bar-not-met`
  addition (canonical: docs/issue-1156/proposals/per-role-quality-bars.md
  frontmatter `files:` list, read this turn). This proposal names the
  ux-engineering/interaction-design mission content (§4) for the record
  but defers landing it until after #1156 phase-2 merges to main, to
  avoid a concurrent-edit collision on the same two spec files.
- Gate-only/mechanical roles are out of scope (§5) — vacuous-spec risk
  named in the issue body requirement 4.
- Proposal only — no spec edits land in this PR; they land in phase 2,
  after an approvers.md Approve (role directive, contract v3 s19).

## What will be done

### 1. Schema addition (applies to all pilot specs)

Each pilot spec gains two new top-level fields:

- `outcome_mission`: string — the real-world goal the profession exists
  to achieve on the target project, independent of on-the-record's own
  process.
- `mission_deliverables`: array of `{artifact, fit_criterion}` — each
  entry names a concrete work product path/shape and the criterion a
  different role checks it against (fit_criterion feeds the #1156 bar
  verdict, it does not replace it).

### 2. brand-design

- `outcome_mission`: "the target project has an applied, consistent
  visual identity a user or another contributor can see and reuse —
  not a description of one."
- `mission_deliverables`:
  1. `{artifact: "design-tokens/*.json (palette + type scale, DTCG
     format)", fit_criterion: "every token resolves to a real DTCG
     entry and covers at minimum color + fontFamily + fontWeight
     categories (reuses the spec's own reference_resolution rule)"}`
  2. `{artifact: "docs/issue-<n>/reports/brand-design/logo-usage.md
     (clear-space, minimum size, correct/incorrect application
     examples)", fit_criterion: "states a numeric clear-space value
     and minimum size, and shows at least one correct and one
     incorrect usage example — not description-only"}`
  3. `{artifact: "component theming: token consumption wired into at
     least one real UI component's stylesheet/theme file",
     fit_criterion: "a component in the target project's source
     resolves a token from (1) at build/render time, checkable the
     same way ux-engineering's reference_resolution already checks
     token_name -> consuming_component"}`

Verified by: ux-engineering records the bar verdict on brand-design's
mission_deliverables (deliverable 3 is by definition a UX-engineering
consumption point; deliverables 1-2 are checked by the same role
since it already reads brand-design's token file as an input to its
own reference_resolution rule) — brand-design never grades its own
deliverable.

### 3. content-design

- `outcome_mission`: "the target project's user-facing copy is
  governed by an applied voice-and-tone standard a contributor can
  follow without re-deriving it — not a one-off review comment."
- `mission_deliverables`:
  1. `{artifact: "docs/issue-<n>/reports/content-design/style-guide.md
     (voice-and-tone entry + before/after example pairs, per the
     spec's existing deliverable_form field)", fit_criterion: "every
     voice/tone rule carries at least one before/after pair drawn from
     real target-project copy, not a hypothetical example"}`
  2. `{artifact: "microcopy patterns for the target project's actual
     UI moments (error message, empty state, button label) that exist
     in the current codebase", fit_criterion: "each pattern names the
     UI moment and gives an answerable rule (exact wording or a
     template), checkable against the plain_language_check field
     already in required_fields"}`
- Write-scope extension needed: add
  `docs/issue-<n>/reports/content-design/*.md` to `write_scope`
  (currently only the single top-level report file).

Verified by: requirements-engineering records the bar verdict on
content-design's mission_deliverables — plain-language/before-after
verification is a documentation-quality check requirements-engineering
already performs on records generally, and it never authors
content-design's own deliverable, so producer/author accounts differ
by construction.

### 4. market-analysis

- `outcome_mission`: "the target project's market position is assessed
  against real, current competitive evidence — not a template filled
  with placeholder judgment."
- `mission_deliverables`:
  1. `{artifact: "the five-forces record itself
     (docs/issue-<n>/reports/market-analysis.md), already required by
     required_fields", fit_criterion: "every force's evidence field
     names a checkable source (a tracked competitor entry, a dated
     external reference) — not a bare assertion; reuses the spec's own
     reference_resolution rule"}`
  2. `{artifact: "docs/issue-<n>/reports/market-analysis/competitor-
     tracking.md (a maintained list of tracked competitor entries the
     evidence field's reference_resolution rule resolves against)",
     fit_criterion: "at least one entry per force where the assessment
     is medium/high, so 'evidence' has something concrete to point at"}`
- Write-scope extension needed: add
  `docs/issue-<n>/reports/market-analysis/*.md` to `write_scope`.

Verified by: requirements-engineering records the bar verdict on
market-analysis's mission_deliverables, same account-differs-from-
producer basis as content-design above (requirements-engineering never
authors a market-analysis record).

### 5. ux-engineering / interaction-design (named for record, deferred landing)

Per the write-set freeze above, this content is recorded here for
continuity but does not land until after #1156 phase-2 merges:

- ux-engineering `outcome_mission`: "a real UI component in the target
  project renders using the design system's tokens — a working
  interface artifact, not an annotation of one." `mission_deliverables`
  reuse the spec's existing `token_name`/`consuming_component`/
  `rendered_value` triple directly — required_fields already names the
  deliverable shape; only the mission-level framing is new.
- interaction-design `outcome_mission`: "a screen/flow's states,
  transitions, and edge cases are mapped completely enough that a
  builder needs no further discovery to implement it." Currently
  `report_only: true` with an empty `write_scope` — issue body
  requirement 1's "working interface artifacts, not annotations" is in
  direct tension with `report_only`; resolving that tension (does
  interaction-design's deliverable stay a wireflow record, or does it
  need a write-scope extension too) is deferred to the sequenced
  follow-up proposal, not decided here.

### 6. Need-detectors (issue body requirement 2)

Each detector is a `board_condition` extension distinct from the
existing `use_when.board_condition` (which fires on upstream artifact
presence) — it fires on absence of the role's own deliverable given a
signal that the target project needs it:

- brand-design: fires when the target project has UI source files
  (`**/*.tsx`, `**/*.jsx`, `**/*.vue`, `**/*.svelte` — the same
  path_patterns ux-engineering's trigger already uses) AND no
  `design-tokens/*.json` file exists anywhere in the repo tree.
  False-positive bound: a backend-only or CLI-only target project has
  no UI source files at all, so the detector never fires — bound is
  "zero UI surface -> silent, unconditionally."
- content-design: fires when the target project has user-facing string
  literals in UI source (heuristic: JSX/template text nodes matching a
  minimum length threshold, not single-word labels) AND no
  `docs/**/content-design/style-guide.md` exists anywhere in the repo
  tree. False-positive bound: a purely programmatic/API-only project
  with no rendered UI text never matches the string-literal heuristic,
  so it stays silent; the threshold on literal length is set
  deliberately conservative (favor false-silence over false-fire, per
  the issue body's "advisory-first" instruction) and is phase-2 tuning
  work, not decided numerically here.
- market-analysis: fires when a product-discovery or pricing record
  exists on the branch (a market-facing decision was made) AND no
  market-analysis record exists yet covering all five forces — this
  reuses the existing `use_when.board_condition` verbatim, because
  market-analysis's existing trigger is already need-shaped (it fires
  on a real market decision, not on artifact presence the way the
  other two's old triggers did). False-positive bound: a repo with no
  product-discovery/pricing record at all never fires — bound is
  "no market-facing decision on the branch -> silent, unconditionally."

## Out of scope: gate-only/mechanical roles

Named explicitly per issue body requirement 4 (vacuous-spec risk):
conformance-review, defect-verification, execution-observation,
issue-retrospective, release-engineering. Each of these already
performs a mechanical check/gate function as its entire job (verifying
a claim, re-running a command, tracking release mechanics) — there is
no separate "real-world outcome" distinct from the gate itself to
declare, so an `outcome_mission` field on these would either restate
the existing `use_when`/`loop_state` verbatim or invent a deliverable
that does not exist. These stay out of the pilot and out of the
template this pilot sets for the later 8 dormant roles.

## Accumulation

None — this is the first outcome_mission/mission_deliverables addition;
no prior per-role mission declarations exist to accumulate against.

## What did not work

None.
