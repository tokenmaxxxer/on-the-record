---
status: proposed
files:
  - docs/issue-609/reports/architecture/survey.md
  - docs/issue-609/proposals/architecture.md
---

# Proposal — issue #609: spec-stage open-decision triage (architecture, phase 1)

Phase 1 only: component boundaries and write surfaces, no code. Grounded in
`docs/issue-609/reports/architecture/survey.md` and, per product-discovery's four resolved
open questions (`docs/issue-609/proposals/product-discovery.md`, merged PR #614), extends
`docs/issue-573/proposals/architecture.md`'s deployed gate verbatim rather than re-deriving it.

**Scout skip record**: scouting skipped this phase. Reason: the spec (product-discovery's four
resolved open questions) already fixes every design-relevant choice this role would otherwise
scout for — reuse `axis_evaluation` verbatim, reuse the two-axis AND gate verbatim, OR-escalation,
the four-field audit record shape — leaving architecture with a placement/wiring decision inside an
already-scouted, already-merged internal pattern (#573's own architecture, which was itself scouted
at design time), not a new external category needing a fresh field survey.

## Component boundary

Same four-component shape #573 established, one new component inserted upstream of the gate, one
direction of dependency preserved:

```
roles/specs/<role>.spec.json                    (schema: open_decision_item ref[] field, NEW)
        |
        v  declared at proposal-authoring time, read at gate time
docs/issue-<n>/proposals/<role>.md               (PR body/diff: "Open decisions" ref block, NEW)
        |
        v  read by the gate at the same gh pr create firing point #573 already uses
on-the-record/hooks/delegated-judgment-gate.sh   (deployed hook, target repo — EXTENDED, not forked)
        |
        v  triage step reuses, unmodified:
        |    - candidate_axes -> #586's axis-ownership table (mechanical lookup, same table
        |      section 9 of #573's proposal already resolves write_scope/judgment_axes against)
        |    - #573's two-axis AND gate (sections 2/5) as the depth/impact clearance check
        |    - axis_evaluation shape (role_spec_shape.py::check_axis_evaluation_entry, unmodified)
        v  produces
docs/issue-<n>/decisions/triage-<sequence>.md    (four-field audit record, NEW record kind)
```

No new hook file, no new firing event, no new import target. The gate already reads the full PR
diff at `gh pr create` time (#573 architecture proposal section 2/12); triage is a new code path
inside the same Python heredoc that runs *before* the existing candidate-decision AND/panel logic,
over a different input (the proposal's open-decision items instead of a candidate decision), reusing
the same axis-ownership lookup and audit-write pattern. This keeps `classify_axes`-equivalent logic
and the axis-ownership table each defined once, read by both code paths, matching the
non-duplication rule #573's own proposal states for `classify_axes()` itself.

## 1. The thin upstream item shape

Product-discovery's resolved question 1, given a machine-readable home: a new required field on
`roles/specs/<role>.spec.json`, `open_decision_item` (`ref[]`, same declaration mechanism
`axis_evaluation` already uses — section 1 of #573's proposal, not a new field-type). Each ref
resolves to an entry in the role's own proposal document, in a new structured sibling to the
existing free-text "Open questions resolved" section (survey.md, confirmed this prose
section already exists in every role proposal):

```jsonc
// roles/specs/<role>.spec.json — new required_fields entry, same mechanism as axis_evaluation
{ "name": "open_decision_item", "type": "ref[]", "required": false }
```

```yaml
# inside docs/issue-<n>/proposals/<role>.md — structured sibling block, one entry per open item
open_decisions:
  - item: "token storage format"
    source_role: requirements-engineering
    source_path: docs/issue-<n>/proposals/requirements-engineering.md#open-questions-resolved
    candidate_axes: [attack_potential]
```

`source_role`/`source_path` are the self-citation discipline #573 already requires of an
`axis_evaluation` entry's `citation` field, applied one layer upstream — the item states where it
came from, not just what it is, so `role_spec_shape.py`'s existing `reference_resolution` walker
(survey.md) can resolve it the same way it resolves every other `ref` field, no new resolver.
`candidate_axes` is the role's own self-tagging (product-discovery's resolved question 2) — a plain
list of axis names from the fixed five, not free text, so the triage lookup (section 2 below) never
has to parse prose.

Shape enforcement: extend `gates/role_spec_shape.py`'s existing required-field-type check
(`_FIELD_TYPES` already includes `ref[]`) with one conditional-presence rule mirroring section 6 of
#573's proposal (`finding` required iff `verdict == contradicts`): `candidate_axes` required and
non-empty iff an `open_decision_item` entry exists, each value drawn from the same closed
`_JUDGMENT_AXES` set `check_role_judgment_axes` already validates. Same validator file, same test
suite pattern (`gates/test_role_spec_shape_batch*.py`), not a new checker.

## 2. Axis-matrix routing: reuse, not re-derive

Product-discovery's resolved question 2, mapped to the exact existing lookup: the gate's triage
step resolves each `open_decision_item`'s `candidate_axes` against
`docs/decisions/2026-08-10-judgment-axis-matrix.md`'s fixed axis→role table — the same table #573's
panel fan-out already builds via `write_scope ∩ judgment_axes` (architecture proposal section 9),
here entered directly from a stated axis instead of from a resolved `target_path`, because an open
decision has no target path yet (it is an unresolved ambiguity, not a change to a file). One axis
maps to exactly one owning role (the matrix's own invariant, `check_axis_ownership`); `candidate_axes`
with more than one entry yields more than one eligible role, same multi-role panel shape section 9
already handles — no new fan-out algorithm, the *input* to the existing lookup changes, not the
lookup itself.

## 3. Owning-role evaluation: `axis_evaluation` verbatim

Product-discovery's resolved question 1's second half: once triage identifies the eligible role(s),
each records its verdict as a plain `axis_evaluation` entry (`role_spec_shape.py`, unmodified) in
its own spec — `supports`/`contradicts`/`no-opinion`, citation required, `finding` required iff
`contradicts` — with `citation` pointing back to the `open_decision_item`'s `source_path` rather
than a `docs/product/*.md` corpus entry (the item itself is what is being judged, not a candidate
decision derived from a prior operator judgment). No new verdict vocabulary, no new evaluation
record shape — `check_axis_evaluation_entry` needs no change, exactly as product-discovery's
resolved question 1 requires.

## 4. OR-escalation gate

Product-discovery's resolved question 3, wired to existing checks: the gate escalates an
open-decision item to the operator when EITHER condition holds (OR, not #573's own AND — this is a
different gate, at the escalation boundary, not #573's auto-decide boundary):

- (a) **threshold-exceeded**: the item does NOT clear #573's own two-axis AND check (architecture
  proposal sections 2/5, unmodified) — i.e. it fails to be both depth-matched (an operator judgment
  already on record under `docs/product/*.md` covers this exact ambiguity) and impact-low. Reusing
  this check verbatim means the empty-corpus degradation (survey.md, restated in section 6
  below) already applies with no new branch: an empty corpus means depth never matches, so every
  item fails (a) and therefore escalates.
- (b) **panel-conflict**: more than one eligible role evaluates the same item (section 2's
  multi-axis case) and their verdicts disagree — one `supports`, another `contradicts` on the item.
  Detected by the same full-quorum read #573's panel synthesis already performs (section 9 of that
  proposal) before applying `panel-unanimous-support-v1`; triage does not wait for that rule's
  approve/reject output, it inspects the same verdict set directly for disagreement, one comparison,
  no new synthesis rule needed.

An item resolves (does not escalate) only when it clears (a) AND all eligible roles' verdicts are
non-conflicting (unanimous `supports`, unanimous `no-opinion`, or a single role) — the same
asymmetric-conservative shape #573 chose for its own auto-approve gate, applied to the opposite
(escalation) direction, per product-discovery's resolved question 3.

## 5. Four-field audit record

Product-discovery's resolved question 4, given a concrete write path. New record kind
`docs/issue-<n>/decisions/triage-<sequence>.md`, written by the gate at triage time (never
self-reported), reusing #573's derivation-source / impact-grade / evaluating-role / decision+timestamp
shape (architecture proposal section 4) with `decision` re-scoped to this gate's own two outcomes:

```yaml
derivation_source: docs/issue-<n>/proposals/<role>.md#open_decisions[<item>]   # the item itself
impact_grade: {reversibility: 2, blast_radius: 1, propagation: 1, existing_signals: 1}  # section 4(a)'s AND-check output, verbatim
evaluating_roles:                                                             # one per eligible role (section 2)
  - role: security-threat-model
    axis: attack_potential
    verdict: supports
decision: resolved   # or escalated; per section 4's OR gate
timestamp: <RFC3339>
```

When `decision: escalated`, the operator-facing artifact is this record's `evaluating_roles` list
verbatim — the same "arriving WITH the expert evaluations attached" requirement #573's own audit
record satisfies for candidate decisions (issue text, product-discovery section 4). No fresh
operator-facing summary is composed; the PR/issue comment layer (#573 proposal sections 11-12,
reused unmodified) posts this record's fields the same way it already posts `auto-<seq>.md`'s.

`gates/role_spec_shape.py`'s extension (section 1 above) is reused to validate this record's own
shape, matching #573's own choice to extend the same validator rather than add a second checker
file (architecture proposal section 4).

## 6. Degradation

Restated, binding: with `docs/product/*.md` empty (survey.md, confirmed live), section 4(a)'s
reused AND check never clears for any item — every open decision escalates until the corpus is
non-empty, the same fall-out-of-the-existing-composition behavior #573's own gate already exhibits,
no special-case branch added for triage. This matches product-discovery's own restated degradation
clause verbatim.

## 7. Deployment surface

Zero-install, unchanged constraint: the triage step is more inline Python inside
`delegated-judgment-gate.sh`'s existing heredoc (survey.md), not a new hook file and not a
new `gates/`-package import — the same zero-install posture #573's implementation chose for the
identical reason (target repo runs the hook without cloning this repo). `roles/specs/*.spec.json`'s
`open_decision_item` field and `gates/role_spec_shape.py`'s extension are this-repo-side schema/CI
surfaces (validated here, at role-proposal-authoring time, same as `axis_evaluation` today); the
gate's triage logic is the target-repo-side runtime surface. No GitHub Actions, matching #566's
standing constraint (restated from product-discovery).

## Alternatives considered

- **A new hook file, separate from `delegated-judgment-gate.sh`.** Rejected: triage needs the same
  axis-ownership table and the same `gh pr create` firing point the existing gate already reads at;
  a second hook would duplicate both the table lookup and the diff-read, the exact
  non-duplication `classify_axes()` already avoids per #573's proposal. One heredoc, one code path
  added before the existing one, keeps both surfaces reading the same data once.
- **A new checker file for the `triage-<sequence>.md` record shape**, instead of extending
  `gates/role_spec_shape.py`. Rejected for the same reason #573's own proposal (section 4) rejected
  it for `auto-<seq>.md`: the record reuses the same `reference_resolution`/field-shape mechanism
  `axis_evaluation` already has a validator for; a second checker would duplicate that walker for no
  new shape class.
- **AND-only escalation** (both threshold-exceeded and panel-conflict required). Rejected per
  product-discovery's own resolved question 3: it would let a conflicted-but-low-impact item resolve
  without escalation, which the issue's OR wording does not authorize — carried into this proposal
  unchanged rather than re-argued.
- **A new, independent open-decision evaluation vocabulary**, not reusing `axis_evaluation`.
  Rejected per product-discovery's resolved question 1: duplicates machinery #573 already validated
  for the identical judgment shape.

## Consequences

- The triage code path and the existing candidate-decision AND/panel logic now share one heredoc,
  one axis-ownership lookup, and one shape validator (`gates/role_spec_shape.py`) — a defect in
  either shared piece now affects both candidate-decision approval and open-decision triage, so
  changes to `role_spec_shape.py` or the axis-ownership table need to be checked against both call
  sites going forward, not just the one being edited.
- Every role that wants to record open decisions must add `open_decision_item` to its
  `roles/specs/<role>.spec.json` and start emitting the structured `open_decisions:` block alongside
  its existing free-text section — an opt-in migration cost per role, mirroring `judgment_axes`'s own
  opt-in adoption path (currently 5 of the repo's roles).
- With the corpus empty (section 6), every open decision escalates today — the mechanism ships with
  zero measurable throughput benefit until `docs/product/*.md` gains entries, matching the same
  known cold-start property #573's gate already has and product-discovery's pre-registered
  measurement window already accounts for.
- `roles/specs/*.spec.json` grows one more conditional-presence rule
  (`candidate_axes` required iff `open_decision_item` present); the shape-checker's surface area and
  its test suite (`gates/test_role_spec_shape_batch*.py`) grow correspondingly, same increment
  pattern each of #573/#581/#597's extensions already added.

## How success will be judged

This phase's own success criterion (contract v3 s19, phase 1): the proposal is judged by whether it
resolves product-discovery's four open questions into a placement/wiring design without inventing
new machinery beyond what product-discovery's RICE table (candidate 1) authorized — checkable by
diffing this proposal's sections 1-5 against product-discovery's four resolved-question numbering
(1:1 correspondence, confirmed above) and confirming no new record shape, verdict vocabulary, or
hook file was introduced beyond the `open_decision_item` field and the `triage-<sequence>.md` record
kind. Downstream, product-discovery's own pre-registered `open_decision_triage_rate` /
`open_decision_misroute_rate` metrics (measured at step 4, execution-observation) are what judge the
mechanism itself; this phase is not measured against those, only against faithful, non-inventive
extension of the already-approved design.

## Hand-off

Interface-shape detail for the `open_decisions:` YAML block's exact parser/embedding format inside
a Markdown proposal (front-matter vs. fenced block vs. a sibling `.json` file) is api-design's call,
not architecture's — this proposal fixes the field names and the shape contract (section 1) and
hands the serialization choice onward. Implementation owns wiring the triage code path into the
existing heredoc and the `gates/role_spec_shape.py` extension itself.
