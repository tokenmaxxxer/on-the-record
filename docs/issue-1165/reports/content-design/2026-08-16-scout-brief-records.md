# issue-1165 (content-design, step 1 round 2): scout brief — records/PR bodies/reports

kind: scout-brief
subject: issue-1165

Mode: reuse-with-citation, not a fresh sweep — this round's decision
space (how to phrase a lead-with-the-point template, section bounds,
and a new-reader test for records this repo already produces) is
already covered by sources this role and technical-writing's sibling
step-1 round cited on 2026-08-13.
canonical: `roles/specs/content-design.spec.json` and
`docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md`,
both read this turn. This brief cites those plus the 2026-08-16
orchestration research brief rather than re-running web search on the
same questions. Wall-clock: under 1 stage.

## Sources (already-verified, reused)

- GOV.UK content design plain-language/inverted-pyramid guidance —
  `https://www.gov.uk/guidance/content-design/writing-for-gov-uk`
  (this role's own `roles/specs/content-design.spec.json`
  `source_standard`).
- Halvorson content-strategy quad (audience/purpose/message/structure)
  — this role's `planning_methodology`,
  `roles/specs/content-design.spec.json`.
- digital.gov plain-language checklist —
  `https://digital.gov/guides/plain-language/principles` (this role's
  `feedback_methodology`).
- NN/g inverted pyramid for web comprehension —
  `https://www.nngroup.com/articles/inverted-pyramid/`, already cited
  in technical-writing's landed step-1 proposal
  (`docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md`).
- 2026-08-16 orchestration research brief (issue #1165 comment,
  2026-08-15T15:40:30Z): GitLab/Datadog/Grafana/Meilisearch converge on
  few-rules + changed-lines-only + inline-escape-hatch as the adoption
  pattern for deterministic prose/structure linting; readability
  formulas graded C (soft signal only, never a hard gate); GOV.UK/NN
  point-first + short-sentence structure carries the strongest reader-
  outcome evidence available.

## Must-bes this round adopts

- Point first, citation trailing, never interleaved mid-sentence (this
  round's own finding, current-state-survey above).
- Few rules, not a style-lint pile (2026-08-16 brief's adoption-pattern
  finding, avoids the anti-nitpick bound issue #1165 requirement 4
  already names).
- An escape hatch for the field this design adds (`none-applicable`
  pattern already established by amendment 2's `convention_family`
  field) — reused, not reinvented.

## Adopt / skip

- Adopt: changed-lines-only enforcement framing for any future gate
  (step 2's concern, not this step's; noted here so step 2 does not
  have to re-derive it).
- Skip: readability-formula scoring (Flesch etc.) as a gate signal —
  2026-08-16 brief grades it C, invalid as a hard gate for technical
  text.

## Gap line

Already-met: point-first structure (GOV.UK/NN sourced, already this
role's own methodology). Missing before this round: a concrete
sentence/clause-level rule for where a `canonical:` citation sits
relative to the point it supports — the current-state survey's specimen
finding above is the gap this round's proposal closes.

Stage count: 1 (reuse). Mode: sequential read of already-cited sources,
no parallel web fan-out run this round. Saturation rationale: the
sourcing decision was already made and cited by this same role and
technical-writing on 2026-08-13; re-running search on an already-cited,
converging source set would not change a build decision this round, so
judge-point-2's saturation rule is treated as already satisfied by the
prior round's sweep.
