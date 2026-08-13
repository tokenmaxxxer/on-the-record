# Current-state survey — issue-1199 partnerships-bd

derived: `find /home/jwjung/tokenmaxxxer/rulebooks/partnerships-bd-rulebook -maxdepth 2 -not -path '*/.git*'`

Rulebook repo: `tokenmaxxxer/partnerships-bd-rulebook`
(`/home/jwjung/tokenmaxxxer/rulebooks/partnerships-bd-rulebook`), 5
methodology plugins (`strategic-fit-gate`, `multi-axis-scoring`,
`batna-zopa`, `evidence-discipline`, `term-sheet-structure`) plus the
`partnerships-bd` role plugin. Canonical rule content for this issue's
scope lives in `partnerships-bd/reference/deliverable-shapes.md` and
`multi-axis-scoring/reference/axes.md`.

## Write surfaces and their unknowns going into scouting

- `deliverable-shapes.md`'s deal-structure-verdict section: six-axis
  table required, but the strategic/ICP-fit axis is scored as a bare
  number — no sub-structure for *how* fit differs across counterparts.
  Unknown going in: does the field's own tooling model partner fit with
  more structure than a single score?
- `deliverable-shapes.md`'s term-sheet-outline section 4 (governance):
  requires authority thresholds, distinct from KPIs — but does not
  require naming *where* (what surface) an approval actually happens.
  Unknown: do practitioner deal-desk tools treat approval routing as a
  first-class design decision?
- `deliverable-shapes.md`'s term-sheet-outline section 7
  (exit/termination): requires conditions/notice/wind-down, but no
  explicit cure-period or data/IP-handling split. Unknown: do
  practitioner CLM tools structure termination clauses more granularly
  than this?
- `multi-axis-scoring/reference/axes.md`: the six axis *names* are
  fixed by the rulebook repo's own prior maturation proposal and read
  by both the scoring gate script and the role's own directive —
  changing the axis list itself would require a gate-script change and
  is out of this issue's scope; the survey therefore treats this file
  as out of scope, and any upgrade attaches instead to
  `deliverable-shapes.md`'s description of how to fill each axis.

These three gaps (partner-fit structure, approval-routing naming,
termination-clause granularity) framed the scout sweep's three angles
in scout-brief.md.
