# issue-1160: scout brief (requirements-engineering, phase 1)

kind: scout-brief
subject: issue-1160

mode: parallel (3 angles, 1 sweep round, no deepening — saturation reached
at judge point 1: all three angles converged on artifact lists already
implied by each spec's existing `source_standard`, so no build decision
would change with another round)

## Must-bes per domain (Kano floor)

- brand-design: an applied visual identity artifact set — logo usage
  rules (clear-space/min-size), an approved color palette with exact
  values, typography rules, and application rules distinguishing
  correct/incorrect usage — not a review memo.
- content-design: a voice-and-tone style guide plus content
  patterns/templates and microcopy — strategic guidance (voice/tone)
  paired with tactical rules (error-message/label wording), matching
  GOV.UK's own structure already cited in the spec's `source_standard`.
- market-analysis: the five-forces assessment already in the spec's
  `required_fields` (force/assessment/evidence) IS the standard
  deliverable shape for this framework — no gap between what the spec
  already requires and what the field produces as its real output.

## Performance axes

- brand-design: exactness (numeric values, not descriptions) and
  cross-surface application coverage (does the guide show correct AND
  incorrect usage, or only correct).
- content-design: tactical usability (does the guide give an
  answerable rule for an actual UI moment — an error message, a button
  label — or only abstract tone description).
- market-analysis: evidence traceability (each force's assessment
  tied to a named, checkable source) vs. bare opinion.

## Adopt / skip

- Adopt: brand-design's applied-artifact framing (palette/type/
  logo-usage/component-theming) directly matches the issue body's own
  example — no invention needed.
- Adopt: content-design's tone+tactical-rule pairing, since the spec
  already cites GOV.UK/GDS as `source_standard`.
- Skip: full agency-style deliverables package (stationery, social
  assets, brochure) for brand-design — out of proportion to a repo
  role; the mission_deliverables set stays scoped to what a software
  project consumes (tokens, usage rules, component theming).

## Gap line (field must-be vs. current spec state)

- brand-design: already meets "exact values" (its `write_scope`
  includes `design-tokens/*.json`); missing usage-rule/theming
  artifacts beyond the raw token file.
- content-design: missing entirely — `write_scope` is report-only, no
  style-guide artifact path exists.
- market-analysis: required_fields already ARE the deliverable shape;
  missing only the explicit `outcome_mission`/`mission_deliverables`
  declaration tying the existing fields to the real-world goal.

## Stage count / mode

One sweep stage (three parallel WebSearch angles), zero deepening
stages (saturation at judge point one).

Sources:
- https://www.brandedagency.com/blog/visual-brand-guidelines
- https://thebrandstrategylab.com/blog/ultimate-guide-to-creating-brand-guidelines/
- https://uxcontent.com/how-to-create-style-guide/
- https://www.gov.uk/government/publications/govuk-content-principles-conventions-and-research-background/govuk-content-principles-conventions-and-research-background
- https://en.wikipedia.org/wiki/Porter%27s_five_forces_analysis
