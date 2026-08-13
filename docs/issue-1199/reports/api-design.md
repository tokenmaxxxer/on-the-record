kind: report
subject: issue-1199
doc-type: reference
loop_state: landed

## API-First deliverable facets

This unit's deliverable is a rulebook change, not a new interface, so
the facets below anchor to the one illustrative resource the applied
rules themselves reference (the resource-modeling axis file's rule 13
split/bundle example), to satisfy this record's mandatory deliverable
shape rather than to design a new API.

resource-model: illustrative hierarchy for the split-spec example
below — a `catalog` collection of `item` resources, one child file per
resource, bundled into one published document.
endpoint_path: /catalog/items
method: GET

interface-spec: the bundled artifact the example above describes is
an openapi document; the split source files are `$ref`-linked openapi
fragments bundled by a dedicated build step before publish.

versioning-strategy: none — pre-v1 (this record documents a playbook
change, not a versioned interface release).

deprecation-plan: N/A — net new (no prior version of these rules to
deprecate; the added rules are additive to the existing playbook).

## What was done

Surveyed the api-design domain's tool landscape (adoption-evidence
method, web-fetched, this session's WebSearch transcript) and folded
the design-move learnings natively into
tokenmaxxxer/api-design-rulebook's `playbook/*.md` axis files — no
tool-catalog section, no "learned from X" narrative attribution in the
rulebook itself, matching the retrofit lesson already reconciled on
the sibling technical-writing unit (issuecomment-5276871308: "a
fold-in must APPLY its upgrades, not only reference them").
canonical: this session's tool transcript — four parallel WebSearch
calls this turn, followed by direct edits and a commit in
/home/jwjung/tokenmaxxxer/rulebooks/api-design-rulebook.

Rulebook PR (external repo): https://github.com/tokenmaxxxer/api-design-rulebook/pull/21
canonical: gh pr view https://github.com/tokenmaxxxer/api-design-rulebook/pull/21 this turn — branch issue-1199/api-design, commit ee6fb62, 3 files changed.

## Why

Issue #1199 (northpole req#1/req#5, docs/specs/northpole.md): the
role's rulebook should learn from the tool ecosystems api-design
practitioners actually use, so the role's rules reach the completeness
those tools' design moves embody — a separate program from #1174's
rule-building, per the issue body.

## Upstream basis

Issue #1199 body (requirements 1-4); consult-log 2026-08-13T06:10:35
entry (adoption-evidence method, bounded fold-in, cap-realism caveat);
issuecomment id for "APPROVE issue-1199/api-design":
canonical: gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments this turn — comment body exactly "APPROVE issue-1199/api-design", author JiwonJung94.

## Tool survey (adoption-evidence method)

Sweep: 4 parallel WebSearch calls this turn, one per category the
existing playbook already touches but has no enforcement-tooling rule
for (spec linting, spec-diff/breaking-change detection, IDL breaking-
change detection, spec bundling/publishing). Single round; no
deepening stage needed — each search's top hits converged on one
clear category leader plus its adoption numbers, satisfying the
scout-directive saturation check at judge point 1.

1. **Spectral** (stoplightio/spectral). Adoption evidence: ~3,088
   GitHub stars per the repo's own listing (search result this turn).
   Problem solved: a fixed set of built-in OpenAPI checks can't cover
   an org's own house style, so teams either skip style enforcement or
   hand-review it every time. How: a declarative JSON/YAML ruleset
   engine — each rule names a JSONPath selector, a check function
   (truthy/pattern/alphabetical/xor/...), and a severity level
   (error/warn/info/hint) — run against any OpenAPI/AsyncAPI document
   in CI, an editor, or a hosted platform. The severity axis is the
   design move worth taking: it separates what must block a merge from
   what a human should weigh, instead of one binary signal.
   Learning -> applied as the error-design axis file's rule 13: tag
   each playbook rule, when encoded as an automated check, blocking or
   advisory rather than giving all rules equal enforcement weight.
   Source: https://meta.stoplight.io/docs/spectral/e5b9616d6d50c-severity-and-disabling-rules

2. **buf** (bufbuild/buf). Adoption evidence: ~10k GitHub stars per
   the repo (search result this turn); ships official `buf-lint-action`
   and `buf-breaking-action` GitHub Actions for CI wiring. Problem
   solved: protobuf/gRPC breaking changes are easy to miss because
   compatibility spans several independent axes (does old-client-new-
   server still parse bytes; does generated code still compile; does
   behavior change) and a single eyeballed diff review conflates them.
   How: `buf breaking` compares the previous published schema against
   the proposed one and reports violations tagged by compatibility
   category (FILE/PACKAGE/WIRE_JSON/WIRE), run automatically on every
   proposed change rather than left to reviewer memory. Two design
   moves worth taking: (a) automate the compatibility check itself, not
   just document the policy; (b) tag violations by which compatibility
   axis broke, since a change can be wire-compatible yet source-breaking
   or vice versa. Learning -> applied as the versioning-evolution axis
   file's rules 14 (automate the existing breaking-change policy rules
   as a CI check over the actual spec diff, not reviewer judgment) and
   15 (classify breaking changes along source/wire/semantic
   compatibility axes, not one breaking/non-breaking bit).
   Source: https://buf.build/docs/breaking/overview/, https://buf.build/docs/breaking/rules/

3. **Optic** (opticdev/optic) and its live-maintained successor
   category. Adoption evidence: Optic reported ~1.5k GitHub stars and
   production use at Snyk (search result this turn) but was archived
   January 2026; the same search surfaced its still-maintained
   replacements (oasdiff, 1,100+ stars per its own repo; pb33f/
   openapi-changes) doing the same job for OpenAPI specifically. Both
   generations converge on the same problem/how, which is what makes
   the learning durable past any one tool's lifecycle: OpenAPI-diffing
   as a CI gate, comparing published spec against proposed spec and
   failing the build on a disallowed change class — the OpenAPI-side
   confirmation of the same automate-the-compatibility-check move buf
   demonstrates for protobuf. No separate rule added (rule 14 above
   already generalizes across both schema-first and IDL-first APIs);
   recorded here because the cross-ecosystem convergence is what raised
   this above a single-tool anecdote to an adoption-evidenced pattern.
   Source: https://github.com/opticdev/optic, https://www.oasdiff.com/, https://github.com/pb33f/openapi-changes

4. **Redocly CLI** (Redocly/redocly-cli). Adoption evidence: ~1.4k-1.5k
   GitHub stars and ~1.6M weekly npm downloads for @redocly/openapi-core
   per the search results this turn; actively maintained (repo updated
   June 2026 per the search snapshot). Problem solved: a large interface
   spec becomes unreviewable as one file (unrelated-resource diffs mixed
   together) but consumers and doc generators need a single published
   document. How: author the spec as multiple linked files ($ref
   across files) and run a dedicated bundle step that resolves and
   combines them into the single published artifact, so the split
   (review-time) and combined (publish-time) forms are produced from
   one script rather than kept in sync by hand. Learning -> applied
   as the resource-modeling axis file's rule 13: split large specs by
   resource, bundle to a single canonical published document rather
   than hand-maintaining both forms.
   Source: https://redocly.com/docs/cli/commands/bundle

## Amendments reconciled

canonical: gh api repos/tokenmaxxxer/on-the-record/issues/comments/5277526812
issuecomment-5277526812 ("Judgment opened: PR #? — candidate decision
on branch `issue-1199/api-design` (1 path(s) changed) entered
delegated-judgment evaluation.") is an automated pre-PR watcher
notice, posted after this session started, with no amendment content
of its own — no action taken on this record or the rulebook PR.
amendments-reconciled: issuecomment-5277526812 — automated notice,
no scope change.

## What did not work

None.

## Open findings

None.
