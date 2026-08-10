# Current-state survey — issue #609: architecture (phase 1)

Grounded in `docs/issue-609/reports/product-discovery/current-state.md` and
`docs/issue-609/proposals/product-discovery.md` (both merged, PR #614); does not re-derive either.
This survey adds only what architecture needs that product-discovery did not need to inspect:
the deployed-surface mechanics of the machinery being extended.

## The deployed surface being extended (confirmed by inspection)

- `on-the-record/hooks/delegated-judgment-gate.sh` (issue #573, extended #581/#597) is a
  **zero-install** PreToolUse/Bash hook: no `gates/` package import, no on-the-record checkout
  resolution (`_checkout_resolve()` from `impact-guard.sh` is deliberately not reused here) — the
  four-axis reversibility grade is ported inline into the hook's own Python heredoc so it runs
  correctly in a target repo that never clones this repo. This constrains any #609 extension:
  it cannot add a new import from `gates/`, only more inline logic in the same heredoc pattern.
- It fires on `gh pr create` on an `issue-<n>/<role>` branch (architecture proposal section 12's
  "PR opened under judgment" event) — the moment a *candidate decision* enters gate evaluation.
  Open decisions inside a proposal (#609's subject) are not candidate decisions; they exist earlier,
  at proposal-authoring time, inside the PR body/files the gate already sees at that same firing
  point. No new firing event is needed — the existing `gh pr create` trigger already occurs after
  the proposal (and any open decisions it records) exists in the diff.
- `roles/*.json` carries `judgment_axes` (opt-in list field, shape-checked); `roles/specs/*.spec.json`
  carries `axis_evaluation` as a `ref[]` required-field entry, shape-checked by
  `gates/role_spec_shape.py`'s `check_axis_evaluation_entry` (verdict in
  `{supports, contradicts, no-opinion}`, citation required, `finding` required iff `contradicts`).
  All five axes now have exactly one owner per `docs/decisions/2026-08-10-judgment-axis-matrix.md`
  (confirmed): `maintenance_complexity`→architecture, `attack_potential`→security-threat-model,
  `alignment`→conformance-review, `external_burden`→capacity-planning, `performance`→
  performance-engineering.
- The gate's fan-out (which roles are eligible) is computed, never asked: `target_path` resolved
  against every role's `write_scope`, unioned with `judgment_axes`, per #573 architecture proposal
  section 9. This is the exact mechanical lookup product-discovery's resolved question 2 asks
  architecture to reuse for `candidate_axes` — not a new routing algorithm.
- Audit records write to `docs/issue-<n>/decisions/{auto,remediation}-<seq>.md`, written by the gate
  itself at decision time (never self-reported by a role), matching `record-scaffold.sh`'s existing
  hook-writes-the-record pattern. Visibility: a PR comment per synthesis outcome and an issue
  comment per firing event (sections 11-12), posted via `gh pr comment` / `gh issue comment`.
- Degradation (confirmed live, unchanged since #573/#609 product-discovery): the depth axis's
  source (`docs/product/*.md`) has zero entries in this repo. The AND rule's first precondition
  never clears with an empty corpus, so every candidate decision escalates today — no special-case
  branch, this falls out of the AND composition itself (architecture proposal section 5).

## What #609 adds that #573's gate does not have today

- No record shape for an *open, unresolved* item exists anywhere (confirmed: product-discovery's
  grep across docs/, roles/, gates/, on-the-record/ found nothing named `open_decision` or
  `spec-stage`).
- The gate today only ever evaluates one artifact class: a *candidate decision already proposed for
  approve/reject*. It has no code path that reads a proposal's open-decisions list, extracts
  `candidate_axes` per item, or synthesizes an item-level `resolved`/`escalated` outcome distinct
  from the PR-level outcome the existing gate's fixed composition rule already produces
  (`docs/issue-573/proposals/architecture.md`, panel-synthesis section).
- `axis_evaluation` (product-discovery's resolved question 1) is reused verbatim for the *owning
  role's evaluation of an item*, but nothing today lets a role emit the thinner, upstream
  `{item, source_role, source_path, candidate_axes}` shape at proposal-authoring time — this shape
  does not exist in any `roles/specs/*.spec.json` today.

## Where the new shape has to live (confirmed by inspection, not assumed)

- Every phase-1 role proposal in this repo (`docs/issue-<n>/proposals/<role>.md`) already has a
  prose section, "Open questions resolved" (grepped: present in `product-discovery.md`,
  `architecture.md` for #573/#587/#586/#609 alike) — this is the existing free-text home for exactly
  the pattern the issue targets. The new shape does not need a new document location; it needs a
  structured sibling to that existing prose section, machine-readable at the point the gate reads
  the PR diff.
- `roles/specs/*.spec.json`'s `required_fields` mechanism (same one `axis_evaluation` uses) is the
  only existing machine-readable field-shape home in this repo; a role's spec is scoped to that
  role's own record file, which is where `open_decision_item` entries would need to be declared as
  a `ref[]` field, mirroring `axis_evaluation`'s own declaration (issue #573 architecture proposal
  section 1) rather than inventing a second shape-declaration mechanism.

## Degradation, restated

Unchanged from product-discovery: the judgment-capture corpus (`docs/product/*.md`) has zero
entries. Every design decision below must produce the same fail-closed behavior the existing gate
already produces on an empty corpus — full escalation, no special-case branch — for open-decision
items, not only for candidate decisions.
