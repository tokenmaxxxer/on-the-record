# issue-573 — architecture scout brief

Skip condition invoked: partial skip. The category-level sweep (how comparable systems structure
delegated/scoped authority) was already run at Step 1 by `technical-feasibility` and is not
re-run here — re-searching the same angle would violate "never re-derive" from this repo's own
protocol, not satisfy it. What remained undecided going into this role was architecture-specific:
how to express *machine-checkable ownership + evaluation-record shape* inside a JSON manifest
family, which Step 1's survey did not need to answer for its own scope. One targeted angle below
closes that gap using sources Step 1 already verified (no new web search dispatched).

## Must-bes, reused from Step 1 (`docs/issue-573/reports/technical-feasibility/survey.md`)

- Path/topic-scoped ownership, not diff-size, routes a decision to the party positioned to judge
  it — CODEOWNERS, Chromium OWNERS (Source: technical-feasibility survey section 2).
- OPA/Gatekeeper policies live as versioned files in git, auditable through ordinary source
  control — not a bespoke review workflow (Source: same survey, section 2).
- ITIL Standard-change pre-authorization requires the criterion to be recorded once at
  template-creation time, not decided per instance, and any edit to the template forces
  re-assessment (Source: same survey, section 1).

## Architecture-specific gap and adopted pattern

**Gap**: none of Step 1's exemplars needed to answer "ownership of *which axis*, expressed inside
*this repo's own* role-manifest schema." That is scoped to this repo's existing
`roles/*.json` / `roles/specs/*.spec.json` pair (see current-state.md), not an external field.

**Adopt**: extend `roles/*.json` with a small ownership list (mirrors `write_scope`'s existing
glob-list shape — same file, same pattern, no new file format introduced) naming which of the
issue's five methodology axes that role is authoritative over. Extend the owning role's
`roles/specs/*.spec.json` `required_fields` with the axis-evaluation record shape, reusing the
existing `reference_resolution` + `recomputation` machinery already proven for architecture's own
ADR fields — this is the direct application of the OPA/CODEOWNERS "ownership as a versioned,
git-auditable file" pattern onto a schema family this repo already has, not a new one.

**Skip**: a bespoke axis-ownership registry format, or a single centralized ownership file
decoupled from `roles/*.json`. The issue's own text places ownership "in roles/*.json / roles/
specs" — a separate registry would duplicate source-of-truth and drift from `write_scope`'s
existing per-role convention.

## Segment fit

One line: this is an internal-tooling schema decision inside an already-adopted role/spec family,
not a product-facing surface — the relevant "best-in-class" comparison is how this repo already
extends that family (architecture.spec.json's `reference_resolution`/`recomputation` fields),
which current-state.md documents directly.

Stages used: 1 (targeted, no new search — reused Step 1's verified sources per the skip-and-reuse
justification above). Mode: not applicable (no fan-out dispatched; single targeted synthesis pass
over already-verified sources).

## Re-scout micro-round (2026-08-10, post-PR-581 operator addition)

New decision surfaced mid-build: strict rejection standards + brokered role-to-role remediation +
loop bound, per the operator's PR #581 review comment. No new web search dispatched — the decision
composes entirely with patterns already adopted above and in Step 1's survey, so a fresh sweep
would re-derive sources already cited, not find new ones.

**Adopt**: route a rejection's remediation to the role by *write-set path ownership*
(CODEOWNERS/`write_scope` pattern, same as the axis-ownership routing above), not by a new registry
— the routed-to role is whichever role's `write_scope` covers the path the finding names, reusing
the exact mechanism this brief already adopted for axis ownership. This keeps routing a read over
existing schema fields, not a new ownership concept.

**Skip**: a dedicated remediation-routing registry decoupled from `write_scope`/`judgment_axes` —
same duplication-of-source-of-truth reasoning as the original skip line above.

Stages used: 1 (targeted, reused this brief's own already-adopted pattern; no new search).

Sources: docs/issue-573/reports/technical-feasibility/survey.md (sections 1-2, itself citing
https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners,
https://chromium.googlesource.com/chromium/src/+/main/docs/code_review_owners.md,
https://www.openpolicyagent.org/ecosystem/entry/gatekeeper,
http://www.itilfromexperience.com/How+is+a+Standard+Change+Pre-Approved).
