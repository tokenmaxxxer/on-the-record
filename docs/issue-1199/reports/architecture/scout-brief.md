# architecture role — tool-landscape scout brief (issue-1199)

Mode: parallel WebSearch fan-out, one round, 5 angles in one turn (fitness-
function testing, C4-diagram-as-code, dependency-graph linting, ADR
tooling, hotspot/tech-debt analysis), followed by one targeted deepening
round for exact star counts on the two ambiguous hits (ArchUnit's main
Java repo, Structurizr DSL). 2 stages total, well under the 5-stage/3min
budget.

## Must-bes (per category, adoption-evidence gated)

1. **Architecture fitness-function testing** — TNG/ArchUnit, 3.8k GitHub
   stars ("The repository has 3.8k stars, with another source indicating
   3,729 stars on GitHub" — search result summary this session).
   Category must-be: architecture rules must be executable, CI-checked
   assertions, not narrative-only documentation.
2. **C4-model-as-code** — Structurizr DSL, 1,420 GitHub stars ("Structurizr
   DSL has 1,420 stars" — search result summary this session); Structurizr
   is described as "the original 'models as code' tool designed for the
   C4 model... the reference implementation" (search result summary this
   session). Category must-be: a diagram is a rendering of one versioned
   text model, not an independently hand-drawn artifact.
3. **Dependency-graph linting/visualization** — dependency-cruiser, 6,788
   GitHub stars and 2,402,543 weekly npm downloads ("dependency-cruiser
   version 17.4.3 has 2,402,543 weekly downloads and 6,788 GitHub stars"
   — search result summary this session). Category must-be: the
   dependency graph a team reasons about should be generated from actual
   imports, not asserted from memory.
4. **ADR/decision-record tooling** — Log4brains (multi-source signal:
   listed on adr.github.io's "Decision Capturing Tools" page, has its own
   hosted documentation site and multiple derivative/fork repos — search
   result summary this session; exact star count not surfaced in this
   session's search results, so treated as multi-source-corroborated
   rather than star-quantified). Category must-be: decisions need a
   status lifecycle and cross-links (superseded-by), not a flat list of
   one-off files.
5. **Hotspot/tech-debt prioritization** — CodeScene (multi-source signal:
   own product docs, an arXiv industrial case study
   `arxiv.org/pdf/2607.01850` referenced in this session's search results,
   and blog case studies; commercial product, so adoption evidence is
   multi-source citation rather than GitHub stars). Category must-be:
   structural severity alone is not sufficient to prioritize remediation
   — it must be combined with how often code actually changes.

## Performance axes these tools compete on

- Enforcement mechanism: narrative doc vs. executable CI check
  (ArchUnit's axis).
- Diagram provenance: hand-drawn image vs. generated-from-one-model
  (Structurizr's axis).
- Graph fidelity: asserted/remembered vs. generated-from-actual-imports
  (dependency-cruiser's axis).
- Decision navigability: flat file list vs. status+lineage graph
  (Log4brains's axis).
- Prioritization signal: static structural score vs. structure×change-
  frequency (CodeScene's axis).

## Adopt / skip

- **Adopt**: pairing every dependency-direction/module-boundary decision
  with a named, automated verification method (test or generated graph);
  requiring the C4 diagram source be a diffable text model; combining
  coupling severity with change-frequency for remediation order; adding
  a decision-lineage (`supersedes`/`superseded_by`) pointer field.
- **Skip**: adopting any of these tools' own DSL/config format or CLI as
  a dependency of this rulebook — the rulebook stays tool-agnostic
  (issue-1199's fold-in must be native rules, not a tool integration);
  skip Log4brains's hosted static-site publishing feature (out of scope,
  no hosting surface exists here) and CodeScene's org-wide dashboarding
  (out of scope for a per-issue ADR record).

## Segment fit

This deliverable (a per-issue ADR + C4 record, gated by three mechanical
plugins) is closer to a single-team decision-record practice than to an
org-wide platform, so the five tools are read for their underlying
design move (executable check, model-as-code, generated graph,
lineage links, structure×frequency) rather than cloned as integrations.

## Gap line

canonical: `docs/issue-1199/reports/architecture/survey.md` (committed
this session, commit `3ad5cb5`), `## Gap line` section.

Gap-to-tool mapping: no verification-method requirement paired with a
dependency-direction/module-boundary decision -> ArchUnit's fitness-
function move; no combined structure+frequency prioritization rule in
coupling-classification -> CodeScene's hotspot move; no diagram-as-
text-model requirement -> Structurizr's model-as-code move and
dependency-cruiser's generated-graph move; no decision-lineage field ->
Log4brains's status/supersession move.

Sources:
- https://github.com/TNG/ArchUnit
- https://structurizr.com/
- https://github.com/structurizr/dsl
- https://github.com/sverweij/dependency-cruiser
- https://npmtrends.com/dependency-cruiser
- https://adr.github.io/adr-tooling/
- https://github.com/thomvaill/log4brains
- https://codescene.com/blog/manage-technical-debt-with-augmented-code-analysis/
- https://arxiv.org/pdf/2607.01850
