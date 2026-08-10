# issue-573 — architecture current-state survey

Scope: only the write surfaces a delegated-judgment mechanism would touch. Does not re-derive
the methodology survey (`docs/issue-573/reports/technical-feasibility/survey.md`) or the
product-discovery hypothesis (`docs/issue-573/proposals/product-discovery.md`); reads them as
given.

## Deployment surface (primary: target/consumer repo, zero-install)

- `spawn.py` (repo root) and `on-the-record/commands/run.md` are the zero-install entry points a
  consumer repo installs as a Claude Code plugin (`on-the-record/.claude-plugin/`).
- `on-the-record/hooks/impact-guard.sh` is the closest existing precedent for a decision-routing
  hook. Its `_checkout_resolve()` walks up from the hook's own path / checks
  `TOKENMAXXXER_CHECKOUT` / falls back to a marketplace or user-home checkout / `git clone` as
  last resort, then runs a Python heredoc that imports the checkout's `gates` package but resolves
  every path against `TARGET_REPO="$(pwd -P)"` — the target repo's own tree, never the checkout's.
  This is the pattern a new delegated-judgment gate must follow: logic ships from the checkout,
  data is read from whatever repo the hook is running in.
- `on-the-record/gates/` mirrors a subset of root `gates/` (`gates.py`, `record_lint.py`,
  `role_spec_shape.py`) for the plugin's own self-checks; it is not the enforcement surface for a
  target repo's decisions — `on-the-record/hooks/*.sh` importing from the checkout's root `gates/`
  package (as `impact-guard.sh` already does) is.
- `on-the-record/hooks/hooks.json` wires hooks to Claude Code lifecycle events.
  `impact-guard.sh` runs on PreToolUse/Bash: it denies a batch `gh pr merge` when any currently-
  open target-repo proposal needs individual approval, using the `classify_axes` function in
  `gates/risk_report.py`, computed against the target repo's own `roles/*.json` and git history.
  A delegated-judgment gate is the same shape one level up — intercepting an *approval* act, not a
  batch-merge act — and should reuse that function rather than re-deriving impact grading.

## Existing mechanical impact classification (issue #319 -> #511, reused not replaced)

The `classify_axes` function in `gates/risk_report.py` (root, mirrored into every target-repo
checkout via the hook pattern above) returns four independently-graded axes (`blast_radius`,
`reversibility`, `propagation`, `existing_signals`), dominant-axis composition
(`reversibility >= AXIS_MAX` forces individual approval, never averaged/summed), fail-closed on
unparseable write-sets or unreadable `roles/*.json`. This is the **impact axis** the two-axis AND
rule from the approved product-discovery proposal must consume as-is — issue #573 adds a
**depth** axis and expert-role evaluation authority on top, not a replacement classifier.

## Role/spec schema (where axis ownership would live)

`roles/<role>.json` (30 roles today) is a flat manifest: `marketplace`, `repo`, `path`, `sandbox`,
`decides`, `use_when`, `produces`, `write_scope` (glob list), `record_fields.loop_state`
(progress/terminal/refusal/error state lists), `spec` (pointer to `roles/specs/<role>.spec.json`).
No field today expresses which of a decision's professional-judgment axes a role is authoritative
over — `write_scope` gates where a role may *write*, not what it may *judge*.

`roles/specs/<role>.spec.json` is the per-role record-format contract: `required_fields` (typed,
with `required: true/false`), `reference_resolution` (how a `ref`-typed field must resolve to a
real file, e.g. architecture's `decision_id` resolving to a real ADR under `docs/decisions/`),
`recomputation` (a field's value must be re-derived from what it references, never asserted
independently — architecture's `outcome` is recomputed from the referenced ADR's own `status`
field). This `required_fields` + `reference_resolution` + `recomputation` shape is exactly the
mechanism the audit-record's four fields (derivation source, impact grade, evaluating role and
verdict, decision) need: each field must resolve to something re-checkable, not a self-report.

Enforcement for spec shape today: `gates/role_spec_shape.py` (root) validates every
`roles/specs/*.spec.json` against a fixed meta-shape; `on-the-record/hooks/role-spec-reference-guard.sh`
enforces `reference_resolution` at record-write time in the target repo (per
`roles/specs/architecture.spec.json`'s own `checked_by` field naming that hook).

## Product corpus (depth axis's evidence base, per #566)

A docs-under-product tree does not exist in this repo yet — confirmed by product-discovery's own
current-state report and independently re-checked here. The product-discovery proposal's
degradation clause is therefore live today, not hypothetical: the depth axis has nothing to match
against, so nothing may auto-decide, in this repo, right now. Any gate design must treat an empty
corpus as the default operating condition, not an edge case.

## Gap this design must close

No file today connects impact classification to any depth signal, to `roles/*.json` axis
ownership, or to an audit-record write path for approval/reject decisions. `impact-guard.sh` reads
impact only, decides nothing about approval delegation, and writes no audit record — it only
denies a batch-merge Bash command. The two-axis AND gate, axis-ownership schema, evaluation-record
format, and audit-record write path are all new.
