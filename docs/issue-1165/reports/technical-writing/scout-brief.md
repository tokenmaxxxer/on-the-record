kind: scout-brief
subject: issue-1165

# issue-1165 (technical-writing) — scout brief

Mode: internal-methodology-only, 0 external sweep stages. Reason: the
issue body's own validity-consult finding (2026-08-13T03:58) already
fixes the three-tier shape and explicitly directs grounding in "landed
methodologies" — for this role that is Diátaxis (this spec's
`source_standard`) and the Google Developer Documentation Style Guide
(role directive's own mandated `style-guide compliance note` field),
plus the `prose-modes` skill already loaded this session (document-type
× reader-knowledge routing). These are not exemplar products to
benchmark against; they are the fixed standard the criterion must trace
to, per #1156's own decomposition principle ("every criterion traces to
the role's own already-cited source_standard" — canonical:
`docs/issue-1156/proposals/per-role-quality-bars.md` §0.2, read this
turn). An external competitive sweep (what do other doc systems do) does
not change which internal standard a self-hosted governance criterion
must cite, so it is skipped rather than run for its own sake.

## Grounding extracted

- **Diátaxis** (tutorial/how-to/reference/explanation): each quadrant
  has its own legibility contour — a tutorial's structure rule can't be
  a reference's (a reference is *allowed* dense enumeration; a tutorial
  is not). Tier-1 caps must therefore branch on the `quadrant` field
  already required on every technical-writing record, not apply one
  number to all four uniformly.
- **Google Developer Documentation Style Guide** (already a required
  record field: `style-guide compliance note`): its structural
  guidance — front-load the conclusion, one idea per paragraph, second
  person for how-to, minimal words — is the direct source for the
  lead-with-the-point rule and the "no raw-context dumps" rule.
- **prose-modes skill** (session-loaded): reader-knowledge is the
  load-bearing axis — raising cohesion helps low-knowledge readers and
  measurably hurts high-knowledge readers. This is why tier-2's
  new-reader checklist is framed as "a reader with *no session
  context*" specifically, not a generic readability score — the
  checklist target is the low-knowledge end of that axis on purpose,
  because that is the reader on-the-record's own records are written
  for (a new session/person, per northpole req#2).
- **#1156's decomposition pattern** (internal, already landed): adjective
  → named checkable sub-criterion; non-automatable → named human-review
  checklist with the question stated, never a lowered bar; bounded
  rejection via the existing `quality_bar.py` classifier. This is the
  wiring tier-1/tier-2/tier-3 below is written to slot into.

## Gap line

The role's already-required fields (`doc_id`, `quadrant`, `content`,
plus the role-directive's `minimalism check` field) already assume a
minimalism/legibility judgment happens per-document — but nothing
today makes that judgment structural or checkable; it's currently a
self-graded free-text note. The gap #1165 fills is turning that
existing-but-unchecked expectation into tier-1 automatable rules (this
proposal), a tier-2 checklist with a named verdict shape, and a
tier-3 sampled deep review cadence — not inventing a new expectation
from scratch.

Sources: `docs/issue-1156/proposals/per-role-quality-bars.md`,
`roles/specs/technical-writing.spec.json`, `docs/specs/northpole.md`,
Google Developer Documentation Style Guide (role-directive-cited
standard), Diátaxis (`https://diataxis.fr/`, this spec's cited
`source_standard`), `prose-modes` skill description (session-loaded).
