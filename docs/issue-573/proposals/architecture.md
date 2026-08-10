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

## 6. Strict rejection: the actionable-finding field

Operator addition (PR #581 review comment + issue #573 comment 5234789984): a rejection must name
WHAT needs fixing, actionable enough to spawn a remediation role — not just a `contradicts` verdict.

Extend `axis_evaluation` (section 1) with a conditionally-required field, same `reference_resolution`
mechanism already governing the rest of that record: when `verdict: contradicts`, the record must
also carry a `finding` object —

```jsonc
{
  "verdict": "contradicts",
  "citation": "docs/product/<entry>.md#<id>",
  "finding": {
    "target_path": "on-the-record/hooks/delegated-judgment-gate.sh",  // must match a real write_scope glob
    "required_fix": "one sentence: what must change, not why it's wrong"
  }
}
```

Shape rule: `target_path` must resolve against some role's `write_scope` (existing field, no new
lookup) — a `finding` whose `target_path` matches no role's `write_scope` is a schema error, same
class as section 1's "axis owned by zero roles" refusal. This is what makes the finding routable
(section 7) rather than prose a human must triage. `required_fix` is free text but mandatory and
non-empty; the shape-checker enforces presence and the `target_path` resolution, not fix quality —
fix quality is the receiving role's own judgment, per contract v3's existing role-autonomy line.

`gates/role_spec_shape.py`'s extension (section 1) grows one more conditional-presence check
(`finding` required iff `verdict == contradicts`); same validator, no new checker file.

## 7. Brokered remediation: routing and audit trail

Operator addition: rejections are not dumped on the operator raw — on-the-record routes each
finding to the expert role whose domain fixes it, and records that routing.

Routing rule, reusing the write-scope-ownership pattern already adopted (section 1, scout-brief
re-scout round): the gate resolves `finding.target_path` against `roles/*.json`'s existing
`write_scope` globs (the same lookup `record-scaffold.sh`/role dispatch already performs elsewhere
in this repo per survey.md) and identifies exactly one owning role — the *remediation target*, which
may differ from the role that authored the rejecting `axis_evaluation` (e.g. `security-threat-model`
rejects a hook file it does not own; the finding routes to `architecture`, the file's owner).
Zero or multiple `write_scope` matches is the same schema-error class as section 6 — refused at
write time, not left for the operator to disambiguate.

New audit record, written by the gate (same write-by-hook pattern as section 4, not self-reported):
`docs/issue-<n>/decisions/remediation-<sequence>.md`:

```yaml
finding_source: <decisions/auto-<n>.md>#axis_evaluation   # the rejecting record
routed_to: <role>                                          # resolved write_scope owner
target_path: on-the-record/hooks/delegated-judgment-gate.sh
required_fix: <copied verbatim from finding.required_fix>
round: 1
status: open   # open | resolved | escalated
timestamp: <RFC3339>
```

This record is the audit trail the operator addition asks for: it is git-native (same convention
as every other `docs/issue-<n>/decisions/*.md` record), so `git log`/`grep` over
`docs/*/decisions/remediation-*.md` answers "what got routed where" without a separate index,
matching contract v3's existing `git log --grep` traceability pattern for warrant proposals.

The routed-to role resolves the finding by producing a new `axis_evaluation` entry of its own on
the original axis, citing the remediation record; the gate re-runs the AND rule (section 2) against
this new record on the next approval attempt — remediation re-enters the same gate it exited, not a
side channel.

## 8. Loop bound and escalation condition

Operator addition: bound the role-to-role loop so it cannot ping-pong indefinitely.

`round` (section 7's field) increments once per remediation record chained to the same
`finding_source`. Bound, fixed at design time (not a per-role config, to keep the bound
un-gameable by the roles it constrains — same reasoning as section 3's contradiction-only
narrowness): `MAX_REMEDIATION_ROUNDS = 3`.

Escalation to the operator (`status: escalated`, no further auto-routing) fires on either:
- `round > MAX_REMEDIATION_ROUNDS` for one `finding_source` chain, or
- the routed-to role's new `axis_evaluation` (section 7, closing paragraph) is itself rejected by
  the *same* contradicting role a second time on the *same* `target_path` — a repeat, not merely
  another round, which signals disagreement rather than a fixable gap.

Both conditions are checks on fields the gate already writes (`round`, `verdict`, `target_path`) —
no new state, no new axis. This keeps the bound inspectable the same way section 5's degradation
rule is: by reading the AND/escalation composition, not a separate timeout mechanism. Escalated
records are the *only* remediation records that reach the operator, per the operator addition's
"operator receives only above-threshold escalations" — every `status: open`/`resolved` record stays
role-to-role.

## Guardrail alignment

`auto_decision_reversal_rate <= 5%` (product-discovery's registered guardrail) is what section 3's
narrow contradiction-only bar and section 2's three-way AND (not two) exist to hold down — a wider
matcher can be tuned per the pre-registered pivot rule without touching the reject bar or the
axis-role authority requirement, keeping the guardrail's stricter surface stable while the
looser-by-design primary metric iterates.

## Deferred to implementation

Exact Python module boundaries inside `gates/`, the depth-matcher's initial vocabulary, the exact
`gh` subcommand patterns `delegated-judgment-gate.sh` matches, and the `gates/role_spec_shape.py`
diff (now including the section 6 conditional-presence check and the section 7 `write_scope`
routing lookup). This phase fixes the schema shape, the gate's read surface and composition rule,
the audit record's write path and fields, the degradation behavior, the rejection finding's
required shape, the remediation-routing rule, and the loop bound — not the implementation's
line-level detail.

## Files (write set — phase 2, not this proposal's own write set)

Implementation's phase-2 write set, per the component boundary above (not built in this phase):
- `roles/*.json` (add `judgment_axes` on owning roles)
- `roles/specs/*.spec.json` (add `axis_evaluation` required field + `reference_resolution` on
  owning roles)
- `gates/role_spec_shape.py` (accept the two new shapes)
- `on-the-record/hooks/delegated-judgment-gate.sh` (new deployed hook, mirrors `impact-guard.sh`)
- `on-the-record/hooks/hooks.json` (register the new hook under `PreToolUse`/`Bash`, matching the
  approval-act `gh` invocations named in section 2 — without this edit the new script exists on
  disk but never fires, silently bypassing the gate; caught by warrant-hunter, after-proposal
  transition, `docs/reports/2026-08-10-hunt-architecture.md`)
- `docs/issue-<n>/decisions/auto-<sequence>.md` (new record kind, written by the gate at decision
  time, not a source file implementation edits by hand)
- `docs/issue-<n>/decisions/remediation-<sequence>.md` (new record kind, section 7, written by the
  gate on each remediation routing; `status: escalated` records are what reaches the operator)

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
- Every rejection is routable without a human reading prose: section 6's `target_path` resolves
  against an existing `write_scope`, and section 7's routing is a lookup over that same field —
  no rejection record should exist for which the routed-to role is ambiguous or undefined.
- The remediation loop is bounded by fields the gate itself already writes (section 8) — no
  external timer, no unbounded round count reachable without hitting one of the two escalation
  conditions first.

## Hand-off

Interface-shape detail for the audit-record's field types belongs to whichever role next reviews
`roles/specs/*.spec.json` schema conventions if it diverges from architecture's own ADR fields —
none expected here since section 1 reuses the existing mechanism verbatim. No performance budget
is implicated (hook runs are already the existing per-`gh`-call cost class). Implementation owns
everything under "Deferred to implementation" above.
