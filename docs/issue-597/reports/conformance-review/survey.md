# Current-state survey — issue-597 conformance-review (phase 1)

## Target artifact and spec

- Target: `on-the-record/hooks/delegated-judgment-gate.sh` (sixth firing
  condition, lines ~85-282), delivered in PR #607, `docs/issue-597/reports/implementation.md`.
- Spec: `docs/issue-597/proposals/architecture.md` (merged architecture,
  sections 1-5), plus issue #597's Acceptance section directly.

## What exists to check against

Architecture sections map to code regions:

| Architecture section | Code region |
|---|---|
| §1 writer = extended gate, not new surface | Same file, no new hook registration (`FRAMING_TRANSITIONS` list appended to existing dispatch) |
| §2 three transitions, one detection mechanism | `FRAMING_TRANSITIONS` regexes (lines 258-260), dispatch loop (263-282) |
| §3 four labeled sections + citation, assembled not free-composed | `build_framing_snapshot` (154-254), `_field_and_citation`/`_first_heading_prose` (107-151) |
| §4 mechanized citation resolvability, fail-closed | `resolve_citation` (88-93), the `for _, citation in elements.values(): if not resolve_citation(...): return None` gate (243-245) |
| §5 baseline behavior, no prior records | `build_framing_snapshot`'s `if not records:` branch (156-175) |

Issue acceptance adds two check items verbatim (mechanically-resolvable
citations at each covered transition; writer-path, not orchestrator prose)
and a non-duplication constraint (framing comment vs. section-12 events).

## Thin/unknown/contested surfaces (what scouting, if any, should aim at)

- Whether "mechanically-resolvable" in the acceptance text is satisfied by
  `resolve_citation`'s three accepted forms (hex sha / baseline marker /
  existing path) — needs direct code read, not inferable from the proposal
  alone.
- Whether the non-duplication constraint is met structurally (distinct
  header, no restated section-12 content) or only by convention/comment —
  needs a direct diff against section-12's writer code, not present in this
  repo snapshot without reading `delegated-judgment-gate.sh`'s pre-existing
  event arms (outside sixth-firing-condition lines, not yet read here).
- Whether the "at least one record path" requirement is satisfied per
  *element* (all four) or per *comment* (any one) — architecture §3's
  example block shows a citation under every element, but the acceptance
  text's exact wording is ambiguous between "each element carries ... a
  citation" (issue body, constraints section) and "citing at least one
  record path" (acceptance item 1) at the comment level. This is a
  contradiction candidate between issue body and acceptance text, to carry
  as a finding per contract §5, not resolve unilaterally.

## Sampling derivation

Full-population check, not a sample: three transition arms
(`delivery-merged`, `issue-reopened`, `issue-closed`) × four architecture
sections (§2 detection, §3 format, §4 citation gate, §5 baseline) is a
population of 12 checkable cells, small enough to check exhaustively
rather than sample. The two acceptance-criteria bullets (framing lands
with citations; written by deployed surface) are checked directly against
this same population, not separately sampled.

## Scout: skipped

Skip condition: the spec (architecture.md, already-merged) leaves no
design decision open for this review to make — conformance-review checks
an already-built artifact against an already-fixed spec, it does not
design anything new. Per scout-directive's two skip conditions, this is
the second one (spec leaves no open design decision) — scouting a review
plan's "what do strong audits check" is also not applicable since the
review method (per-requirement Present/Surface/Absent/Incorrect/
Unverifiable verdict) is fixed by this role's own directive, not a design
choice this session makes.
