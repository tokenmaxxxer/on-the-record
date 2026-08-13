# issue-1165: content-design scout brief (phase 1)

kind: scout-brief
subject: issue-1165

Mode: batched-sequential (methodology grounding pulled from this role's
own already-cited, already-landed `source_standard` /
`judgment_methodology` / `planning_methodology` fields in
`roles/specs/content-design.spec.json`, not a fresh web sweep — the gap
this step closes is an *operationalization* gap, not a *which
methodology* gap; the sources were already chosen and landed under
issue-521/#1130's spec-authoring work). Stages used: 1 (source
re-read + extraction), well under the 5-stage/3min budget.

## Must-bes (from the landed sources, applied to screens)

- NN/g heuristic #6, recognition over recall: a new user should not
  need to hold anything in memory to act on a screen — options and
  next steps stay visible.
- NN/g heuristic #2, match between system and real world: labels/copy
  use the user's task language, not internal system vocabulary.
- NN/g heuristic #1, visibility of system status: every async/loading
  transition and every error is named and visible, never silent.
- NN/g heuristic #8, aesthetic and minimalist design: a screen surfaces
  one clear primary action; competing equal-weight CTAs fail this.
- Halvorson content strategy quad (audience/purpose/message/structure):
  a screen's content is reviewable against "who is this for, what is
  it for, what is the one message, how is it structured" — this is the
  quad this role's `planning_methodology` already commits to, reused
  here as the tier-3 deep-review frame rather than invented fresh.

## Performance axes (what strong screens visibly compete on)

1. Time-to-first-successful-action for a new, unaided user (NN/g
   heuristic #6 + #8 combined).
2. Recoverability — can the user tell what went wrong and what to try
   next when a state fails (heuristic #1 + #9, help users recognize/
   diagnose/recover from errors).
3. Findability of the primary task from the first screen (Halvorson
   structure axis, ties to this role's existing `review_methodology`,
   the IA/findability cross-check).

## Adopt / skip

- Adopt: NN/g's heuristic evaluation as the tier-2 checklist's judging
  frame — it is already this role's landed `judgment_methodology`, and
  its heuristics are individually named and citable per finding (issue
  requirement 4's anti-nitpick bound: a verdict must cite which
  checklist item failed).
- Skip: inventing a new scoring rubric (e.g. numeric heuristic-severity
  ratings) — NN/g's own severity scale is a research-usability-test
  instrument calibrated for moderated sessions with real users; this
  role's tier-2 is a fast unaided-reviewer checklist, not a moderated
  study, so a numeric severity import would overstate precision this
  step's protocol doesn't have the data to support.

## Gap line

The landed sources already cover *what to look for* (the heuristics,
the quad). What was missing going into this step was an operational
check — a concrete accept/reject checklist item, a tier split
(automatable vs. human-checklist vs. sampled-deep), and a sampling
protocol; the proposal in this same PR works that gap.

Sources:
- roles/specs/content-design.spec.json (`judgment_methodology`,
  `planning_methodology`, `review_methodology` fields, read this turn)
- nngroup.com/articles/ten-usability-heuristics-for-user-interface-design
  (as cited by the spec's own `judgment_methodology.source`)
- Halvorson, *Content Strategy for the Web*, 2nd ed (New Riders 2012)
  (as cited by the spec's own `planning_methodology.source`)
