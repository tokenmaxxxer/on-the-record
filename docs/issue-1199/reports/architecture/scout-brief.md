# architecture role — tool-landscape scout brief (issue-1199)

## 2026-08-14 rework addendum (Claude Code plugin ecosystem)

Operator amendment (2026-08-14, issue body) redirects the survey target
from general domain architecture tools (below, kept as superseded
context) to the Claude Code plugin/skill ecosystem. Rework mode: 2
parallel WebSearch angles this session (architecture/C4/ADR skills;
dependency-graph/codebase-analysis skills), each followed by one
WebFetch deepening call per ambiguous star count — 4 stages total,
under the 5-stage/3min budget.

1. **blueraai `claude-code-graph`** (listed on LobeHub's skills
   marketplace; cross-listed in the same GitHub search-topic result set
   as other maintained Claude Code skills — search this session,
   https://lobehub.com/skills/blueraai-bluera-base-claude-code-graph;
   exact star count not surfaced, adoption evidence rests on
   marketplace-listing + multi-source corroboration, per the
   adoption-evidence method's alternative signal used for Log4brains in
   the superseded survey below). Parses a plugin's manifest/source into
   a directed dependency graph (DOT/Mermaid + JSON), with cycle
   detection, orphan/unused-module identification, and layer/boundary
   discovery. Replaces dependency-cruiser as `dependency-direction.md`
   rule 14's source: same design move (generate the graph from real
   imports, don't assert it), now evidenced by a Claude Code-native
   skill instead of a general npm CLI tool.
2. **`Egonex-AI/Understand-Anything`** — 79.2k GitHub stars (WebFetch
   this session, https://github.com/Egonex-AI/Understand-Anything).
   Turns a codebase into an interactive knowledge graph across Claude
   Code/Codex/Cursor/Copilot/Gemini CLI; its "Diff Impact Analysis"
   feature shows which parts of the system a change ripples into before
   commit. Replaces CodeScene as `coupling-classification.md` rule 15's
   source: pairs structural coupling severity with an observed-impact
   signal (change ripple, generalizing the git co-change-frequency
   move) instead of a static metric alone.
3. **`cheriftj/c4-model-skill`** — 34 GitHub stars (WebFetch this
   session, https://github.com/cheriftj/c4-model-skill); corroborated
   by a second, independently-maintained C4 skill
   (`bitsmuggler/c4-skill`) and a dedicated architecture-skills blog
   post surfacing the same category (search this session,
   https://skills.thicket.sh/blog/best-claude-code-skills-for-architects) —
   multi-source category corroboration, per the adoption-evidence
   method's alternative signal. Interactive Claude Code skill generating
   C4 diagrams (Mermaid/Structurizr DSL/PlantUML output) from Simon
   Brown's model. Replaces Structurizr as `module-boundary-definition.md`
   rule 15's source: same design move (one text model generates the
   context/container/component views together), now a Claude Code-native
   skill.
4. **`gauravs19/enterprise-architecture-skill`** — 7 GitHub stars
   (WebFetch this session,
   https://github.com/gauravs19/enterprise-architecture-skill),
   corroborated by the same architecture-skills blog listing as #3
   above. Unifies C4/ArchIMate/TOGAF/arc42+ADR; its built-in linter
   checks for "accepted ADRs not linked from any doc." Secondary
   context for the methodology handbook's `supersedes`/`superseded_by`
   decision-lineage requirement — the same underlying problem (a flat
   set of decision records losing track of which supersede which) that
   Log4brains addressed in the superseded survey below, now also solved
   inside a Claude Code-native skill.

Category-level check: none of the four category must-bes from the
superseded survey below changed (executable/CI-checked rules,
diagram-as-code, real-import-graph verification, decision-lineage
tracking, structural-severity-plus-observed-cost pairing) — the Claude
Code plugin ecosystem demonstrably assumes the same must-bes as the
general domain-tool ecosystem did; only the surveyed instrument
changed, per issue-1199's 2026-08-14 amendment.

Sources (rework addendum):
- https://lobehub.com/skills/blueraai-bluera-base-claude-code-graph
- https://github.com/Egonex-AI/Understand-Anything
- https://github.com/cheriftj/c4-model-skill
- https://github.com/bitsmuggler/c4-skill
- https://github.com/gauravs19/enterprise-architecture-skill
- https://skills.thicket.sh/blog/best-claude-code-skills-for-architects

## Superseded survey (pre-2026-08-14, domain-tool basis — kept for record continuity only)

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
