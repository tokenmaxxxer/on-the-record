---
status: proposed
files:
  - docs/issue-573/reports/architecture/survey.md
  - docs/issue-573/reports/architecture/scout-brief.md
  - docs/issue-573/proposals/architecture.md
---

# Proposal — issue #573: delegated-judgment mechanism design (architecture, phase 1)

Phase 1 only: component boundaries and write surfaces, no code. Grounded in
`docs/issue-573/reports/architecture/survey.md` and
`docs/issue-573/reports/architecture/scout-brief.md`; does not re-derive the methodology survey
(Step 1) or the pre-registered hypothesis (Step 2, `docs/issue-573/proposals/product-discovery.md`).
Deployment target throughout: the target/consumer repo running the zero-install plugin surface
(`spawn.py`, `on-the-record/hooks/*.sh`, `on-the-record/commands/run.md`); this repo is the
validation instance, per the issue's stated primary scenario.

## Component boundary

Four components, one direction of dependency, mirroring the existing
`impact-guard.sh -> gates/risk_report.py` split documented in survey.md:

```
roles/*.json + roles/specs/*.spec.json      (schema: axis ownership + record shape)
        |
        v  read at gate time, never written by the gate
on-the-record/hooks/delegated-judgment-gate.sh   (deployed hook, target repo)
        |
        v  imports, target-repo paths only
gates/risk_report.py::classify_axes()  (existing, unmodified)  +  docs/product/*.md corpus
        |
        v  produces
docs/issue-<n>/decisions/auto-<n>.md   (four-field audit record, one per auto-decision)
```

The gate depends on the schema and on the existing classifier; nothing depends on the gate. This
keeps `classify_axes()` reusable by both `impact-guard.sh` (batch-merge denial) and the new gate
(approval-delegation) without either importing the other.

## 1. Axis-role ownership schema

Extend `roles/<role>.json` with one new optional array field, `judgment_axes`, listing which of
the issue's five methodology axes that role is authoritative over (`alignment`,
`maintenance_complexity`, `external_burden`, `attack_potential`, `performance`). Same list shape as
the existing `write_scope` field — no new file format, per the scout-brief's adopted pattern.
A role with no `judgment_axes` field owns none (opt-in, not a default-all).

```jsonc
// roles/architecture.json — illustrative addition, not exhaustive of real ownership
"judgment_axes": ["maintenance_complexity"]
```

Axis-to-role assignment itself (which of the 30 roles owns which axis) is **not** decided in this
phase — it is a per-role content decision belonging to each role's own domain, made when this
schema lands, not invented wholesale by architecture. What this phase fixes is only the field's
shape and the rule that each axis must resolve to exactly one owning role (an axis owned by zero
roles, or by more than one, is a schema error the shape-checker below refuses).

Evaluation-record format lives in the owning role's `roles/specs/<role>.spec.json`, added to
`required_fields` alongside that role's existing fields, reusing the same
`reference_resolution` + `recomputation` mechanism `architecture.spec.json` already has for ADRs:

```jsonc
{
  "name": "axis_evaluation",
  "type": "ref[]",
  "required": false
}
```

with a `reference_resolution` entry stating: each `axis_evaluation` ref must resolve to a real
entry inside that role's own record file, carrying `axis` (one of the five, must be in that role's
`judgment_axes`), `verdict` (`supports` | `contradicts` | `no-opinion`), and `citation` (a
product-corpus entry path — see below). `recomputation`: the gate's four-field audit record
(section 4) must re-derive its per-axis clause from this record, never assert one independently.

Shape enforcement: extend `gates/role_spec_shape.py`'s existing fixed meta-shape check to accept
`judgment_axes` on `roles/*.json` and the `axis_evaluation` required-field shape on
`roles/specs/*.spec.json` — same validator, same test suite pattern already covering the other
30 roles (`gates/test_role_spec_shape_batch*.py`), not a new checker.

## 2. The gate: two-axis AND rule

New deployed hook `on-the-record/hooks/delegated-judgment-gate.sh`, PreToolUse/Bash, matching the
approval act (`gh pr review --approve` / the single-account `APPROVE issue-<n>/<role>` comment
path per contract v3 s19 — both are `gh` invocations the hook can match the same way
`pr-preflight.sh` and `impact-guard.sh` already match `gh` subcommands). Structure mirrors
`impact-guard.sh` exactly: `_checkout_resolve()` unchanged, `TARGET_REPO="$(pwd -P)"` unchanged,
Python heredoc importing `gates.risk_report` plus a new small module for the depth axis.

Inputs the gate computes, both against the target repo:
- **Impact axis**: `classify_axes()`, unmodified, exactly as `impact-guard.sh` already calls it.
  Low impact means `reversibility < AXIS_MAX` and the other three axes not individually forcing
  escalation (same dominant-axis rule, reused verbatim — no new impact logic).
- **Depth axis**: whether the candidate decision's write-set/description matches a recorded entry
  under the target repo's product corpus (per #566's capture surface). A match means the decision
  follows from an operator judgment already on record, not a new one. Matching logic is a new,
  small module sized similarly to `risk_report.py`'s existing per-axis grade functions —
  deliberately out of this phase's design detail per the pre-registered hypothesis's own pivot
  rule ("widen the depth axis's match vocabulary" is explicitly named as the tuning lever,
  implying the matcher's precise algorithm is expected to iterate after H1's first measurement
  window, not be frozen at design time).

AND rule: the gate auto-decides only when both axes independently clear (depth axis matches AND
impact axis grades low) **and** at least one owning role's `axis_evaluation` record exists citing
that same product-corpus entry with `verdict: supports`. Any one of the three missing means
escalate (no partial credit, no OR fallback) — this is the same non-averaging, non-overridable-
by-the-other composition #511 already chose for its own four axes (survey.md), applied one level
up.

## 3. Contradiction-only auto-reject

Auto-reject requires the same three preconditions as auto-approve, plus: the citing
`axis_evaluation` record's `verdict` must be `contradicts`, not merely absent-of-support. A
`verdict: no-opinion`, an ambiguous match to more than one corpus entry, or no `axis_evaluation`
record at all — all escalate. The gate never infers contradiction from the absence of a
supporting record; it only reads an explicit `contradicts` verdict the owning role already wrote.
This is a read-only check on an existing field, not new gate logic beyond the verdict-value branch
in the AND rule above.

## 4. Audit record: write path and four-field format

Write path: `docs/issue-<n>/decisions/auto-<sequence>.md` in the target repo (parallel to
architecture's own `docs/decisions/*.md` convention, scoped per-issue since an auto-decision is
about a specific issue's proposal). Written by the gate itself at decision time (matches
`record-scaffold.sh`'s existing pattern of a hook writing a record file, not a role authoring it
after the fact) — this is what makes the record re-derivable rather than self-reported, per
product-discovery's gaming-resistance argument.

Four fields, each independently re-checkable (mirrors the `reference_resolution`/`recomputation`
shape, not free text):

```yaml
derivation_source: <product-corpus file>#<entry-id>       # depth axis match
impact_grade: {reversibility: 2, blast_radius: 1, propagation: 1, existing_signals: 1}  # classify_axes() output, verbatim
evaluating_roles:                                          # >=1 entry, each resolving to a real axis_evaluation record
  - role: <owning-role>
    axis: maintenance_complexity
    verdict: supports
decision: approve   # or reject; contradiction-only per section 3
timestamp: <RFC3339>
```

`gates/role_spec_shape.py`'s extension (section 1) is reused to validate this record's own shape
if it is expressed as a `roles/specs`-governed record type; alternatively a small dedicated
checker in `gates/` — left to implementation to pick whichever avoids duplicating the existing
`reference_resolution` walker. Either way: the record must fail closed (denial, not a written
record with a broken reference) if any field cannot resolve, matching every other fail-closed rule
in `gates/risk_report.py` already documented in survey.md.

## 5. Degradation rule

Binding, restated from product-discovery and confirmed still true by survey.md's own re-check:
when the target repo's product corpus is empty or absent, the depth axis cannot match anything, so
the AND rule's first precondition never clears, so **every decision escalates** — this falls out
of the AND rule in section 2 with no special-case branch required. The gate implementation must
not add a separate "corpus empty, skip gate" shortcut; the shortcut is unnecessary and would be
one more code path to keep correct. The existing AND composition already produces the right
behavior when its first input has nothing to match.

## Guardrail alignment

`auto_decision_reversal_rate <= 5%` (product-discovery's registered guardrail) is what section 3's
narrow contradiction-only bar and section 2's three-way AND (not two) exist to hold down — a wider
matcher can be tuned per the pre-registered pivot rule without touching the reject bar or the
axis-role authority requirement, keeping the guardrail's stricter surface stable while the
looser-by-design primary metric iterates.

## Deferred to implementation

Exact Python module boundaries inside `gates/`, the depth-matcher's initial vocabulary, the exact
`gh` subcommand patterns `delegated-judgment-gate.sh` matches, and the `gates/role_spec_shape.py`
diff. This phase fixes the schema shape, the gate's read surface and composition rule, the audit
record's write path and fields, and the degradation behavior — not the implementation's line-level
detail.

## Files (write set — phase 2, not this proposal's own write set)

Implementation's phase-2 write set, per the component boundary above (not built in this phase):
- `roles/*.json` (add `judgment_axes` on owning roles)
- `roles/specs/*.spec.json` (add `axis_evaluation` required field + `reference_resolution` on
  owning roles)
- `gates/role_spec_shape.py` (accept the two new shapes)
- `on-the-record/hooks/delegated-judgment-gate.sh` (new deployed hook, mirrors `impact-guard.sh`)
- `docs/issue-<n>/decisions/auto-<sequence>.md` (new record kind, written by the gate at decision
  time, not a source file implementation edits by hand)

## How success will be judged

This proposal succeeds if implementation can build directly against it without a design gap
surfacing mid-build (the re-scout trigger this role would otherwise need to fire on). Concretely:
- The two-axis AND rule (section 2) and contradiction-only bar (section 3) are checkable purely
  by reading `roles/*.json` + `roles/specs/*.spec.json` + the gate's output — no undocumented
  judgment call left to the implementer.
- The degradation rule (section 5) requires no special-case code, only the AND composition already
  specified — verifiable by inspection once implemented (no separate "corpus empty" branch should
  exist in the merged hook).
- The audit record (section 4) is fail-closed and re-derivable: any field implementation cannot
  make resolve to a real, existing reference should be treated as a design gap in this proposal,
  reported back rather than silently patched, per this role's own hand-off obligation below.
- Downstream, product-discovery's registered guardrail (`auto_decision_reversal_rate <= 5%`,
  measured at step 5) is the eventual test of whether this design's AND/contradiction-only
  restrictions were tight enough; this phase cannot itself measure that, only avoid loosening it.

## Hand-off

Interface-shape detail for the audit-record's field types belongs to whichever role next reviews
`roles/specs/*.spec.json` schema conventions if it diverges from architecture's own ADR fields —
none expected here since section 1 reuses the existing mechanism verbatim. No performance budget
is implicated (hook runs are already the existing per-`gh`-call cost class). Implementation owns
everything under "Deferred to implementation" above.
