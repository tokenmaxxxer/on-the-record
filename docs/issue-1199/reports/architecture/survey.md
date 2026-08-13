# architecture role — tool-landscape current-state survey (issue-1199)

## Current state (this rulebook's own write surfaces)

canonical: `docs/handbooks/architecture-methodology.md` in
`tokenmaxxxer/architecture-rulebook` (read this session, mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/architecture-rulebook`), Phase 2
facet §"Stages" step 1.

That step requires "the four required ADR sections plus a C4-level
diagram" for a phase-2 record. Its text names no requirement for how the
diagram is produced (image vs. text model) and no requirement to name an
automated check for a dependency-direction or module-boundary decision.

canonical: `playbook/*.md` in the same rulebook checkout, git log entry
`d4d0529 Add operational playbook: 5 decision axes, 71 rules, 22
REMOVAL (issue-1174)` (read this session via `git log --oneline -5`).

The five `playbook/*.md` axes (`module-boundary-definition`,
`dependency-direction`, `coupling-classification`,
`interface-contract-shape`, `decomposition-strategy`) encode 71
condition/choice/why/source rules per that commit. Gaps relevant to this
issue's tool-landscape sweep, read directly from each file this session:

- `dependency-direction.md` rule 8 (canonical: that file, rule 8 text,
  read this session) covers CI-enforced layering tests citing ArchUnit's
  `layeredArchitecture()`, but no rule in the file addresses verifying
  the actual import graph against a declared direction — only the
  CI-test angle, not the graph-generation angle.
- `coupling-classification.md` rule 14 (canonical: that file, rule 14
  text, read this session) warns against gating on a structural metric
  alone, but no rule in the file combines structural severity with
  observed change-frequency to order remediation.
- `module-boundary-definition.md` rule 13 (canonical: that file, rule 13
  text, read this session) separates C4 container vs. component levels,
  but no rule in the file requires the diagram itself be a versioned,
  diffable text model rather than a pasted image.
- No rule anywhere in the five playbook files or the methodology
  handbook (canonical: full-text read of both this session) addresses
  ADR decision-lineage (supersession links) across issues for the same
  boundary.

## Gap line

The current state has the narrative ADR/C4 methodology and the 71
structural/coupling/dependency rules cited above, and is missing the
four gaps listed — the tool-landscape sweep (`scout-brief.md`) fills
them, mapped one tool per gap.
