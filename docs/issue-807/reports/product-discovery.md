---
kind: step3-strengthening-delivery
loop_state: validated
subject: issue-807
---

# issue-807 phase-2 step-3: strengthening plan applied to role specs

## What was done

Applied the strengthening plan from the approved step-2 audit
(docs/issue-807/proposals/2026-08-12-role-methodology-depth-audit-step2.md,
section 3) to the six load-bearing role spec files it named, plus the
two `axis_evaluation` procedure sections it left unfilled in the shared
handbook:

code_under_review:
- roles/specs/execution-observation.spec.json
- roles/specs/defect-verification.spec.json
- roles/specs/architecture.spec.json
- roles/specs/product-discovery.spec.json
- roles/specs/security-threat-model.spec.json
- roles/specs/test-authoring.spec.json
- docs/handbooks/architecture-methodology.md

Per role:
- **execution-observation**: added `gate_b_contrast` (hollow-instance
  text: an all-`untested`/`cantTell` record with no cited command
  output is schema-valid but asserts nothing) and `gate_c_status: N/A`
  with the mechanical-aggregation justification from step-2's audit —
  an explicit N/A, not a silent omission, per step-1 sec4's test.
- **defect-verification**: added `gate_b_contrast` (repro_steps
  textually identical to the original report is not verification) and
  `gate_c_finding_method` (repro_steps must include at least one
  input/environment variation not present in the original report),
  operationalizing roles/defect-verification.json's own "적대적 독립
  재현" framing into the spec's checkable content.
- **architecture**: added `gate_b_contrast` (single-option or
  boilerplate-driver ADRs are schema-valid but not a real trade-off)
  and `gate_c_axis_evaluation` pointing at the handbook's new
  `maintenance_complexity` READ/EXECUTE/CRITERIA/CITATION section,
  grounded in MADR's decision-drivers/considered-options weighing
  method (not just its field names).
- **product-discovery**: added `gate_b_contrast` (evidence-log-free
  generic prose is schema-valid but not a real assessment) and
  `gate_c_finding_method` (Mom-Test evidence-admissibility floor —
  observation/interview count + date range, stated-preference-only
  evidence inadmissible).
- **security-threat-model**: added `gate_b_contrast` (1-2 STRIDE
  categories on an authentication-boundary flow is incomplete
  elicitation) and `gate_c_axis_evaluation` pointing at the handbook's
  new `attack_potential` section, grounded in Shostack's per-element
  STRIDE walk (not just the six-category enum).
- **test-authoring**: corrected `source_standard` to add Gerard
  Meszaros's *xUnit Test Patterns* Test Smells catalog alongside IEEE
  829 (previously IEEE 829 only, while the role's actual `decides` per
  roles/test-authoring.json is suite/fixture design quality — a
  citation/domain mismatch step-2 flagged as the clearest Gate-A gap of
  the six); added required fields `smells_identified`,
  `fixture_strategy`, `isolation_verdict`; added `gate_b_contrast` and a
  `gate_c_finding_method` naming the Meszaros smell-category enumeration
  requirement.
- **handbook**: filled the two outstanding `axis_evaluation` procedure
  sections (`maintenance_complexity` for architecture,
  `attack_potential` for security-threat-model) per the shared template
  already defined in docs/handbooks/architecture-methodology.md,
  closing the "mechanism exists, fill-in doesn't" gap step-2 identified
  for both `axis_evaluation`-owning roles audited.

derived: python3 gates/role_spec_shape.py roles/specs/<file>.spec.json (run individually against all six files above)
```
roles/specs/execution-observation.spec.json OK json
roles/specs/execution-observation.spec.json OK shape
roles/specs/defect-verification.spec.json OK json
roles/specs/defect-verification.spec.json OK shape
roles/specs/architecture.spec.json OK json
roles/specs/architecture.spec.json OK shape
roles/specs/product-discovery.spec.json OK json
roles/specs/product-discovery.spec.json OK shape
roles/specs/security-threat-model.spec.json OK json
roles/specs/security-threat-model.spec.json OK shape
roles/specs/test-authoring.spec.json OK json
roles/specs/test-authoring.spec.json OK shape
```
canonical: docs/specs/role-spec-template.schema.json, read directly this
session — its top-level `properties` block has no `additionalProperties`
key at all, so the new `gate_b_contrast`/`gate_c_*` top-level keys added
above are additive and do not break the documented shape contract.

## Why

canonical: gh pr list --search "807" --state all, run this session — PR #926 ("issue-807 step2: per-role methodology audit (6 roles)") shows status MERGED against branch issue-807/product-discovery, and its body is docs/issue-807/proposals/2026-08-12-role-methodology-depth-audit-step2.md.
Upstream basis: that step-2 audit, which explicitly deferred all
spec/handbook edits to step 3 ("No spec edits — this is scoping/survey
only; step 3 does the actual edits").

canonical: gh issue view 807 --comments, run this session — the comment
body is the exact string `APPROVE issue-807/product-discovery`, posted
by JiwonJung94 (approvers.md-listed), the same account as this branch's
PR author — single-account-mode approval, satisfied.

Every citation added above is the exact source step-2's section 5
canonical-citations list names (MADR, Shostack 2014 ch.3-4, Meszaros
2007 Test Smells catalog, Mom Test) — no new, unaudited standard was
introduced in this step; step-3's job was to operationalize step-2's
already-verified citations into the actual spec text, not to re-derive
them.

## Pre-registered check and measured result

Registered rule (inherited from step-2's deferred delivery obligation):
metric = count of the six named spec files passing
`gates/role_spec_shape.py` after the strengthening-plan edits land;
threshold = all six of the six named files must pass (a single failing
file is a kill for that file's edit).

derived: python3 gates/role_spec_shape.py roles/specs/<file>.spec.json (see the code-fenced command block in "What was done" above)
Measured value: all six of the six named files passed — threshold met,
per the code-fenced output cited above (every line ends `OK shape`).

Guardrail metric (must not regress alongside the primary count above):
whether every citation added is one of the pre-verified sources in
step-2's section 5 canonical-citations list, not a newly invented one.
Guardrail status: not breached — every citation used above (MADR,
Shostack 2014, Meszaros 2007, Mom Test, EARL, 29119-3) traces to that
list; no new unaudited source was introduced this step.

ITWWS follow-up (pre-committed): if this strengthening lands cleanly, we
should extend `gates/role_spec_shape.py` to mechanically require
`gate_b_contrast` and the relevant `gate_c_*` field non-empty per role
(see Open finding 1) — deferred to issue #807's own step-3 harness
sub-task rather than actioned in this commit, because that sub-task is
explicitly named in the issue's execution plan as "harness signal for
methodology-validity; re-measure" and depends on all six roles' fields
existing first, which is what this commit delivers.

## Opportunity-solution-tree update

Outcome: role deliverables that survive adversarial review, not surface
imitation (issue #807's stated stake). Opportunity: the six priority-one
load-bearing roles' specs currently pass schema shape but admit
hollow/schema-conformant-but-domain-empty instances (Gate B) and, for
three of them, have no lens-based finding method at all (Gate C).
Candidate solution executed this step: add explicit hollow-instance
contrasts and finding-method fields, grounded in the already-cited real
standards, directly into the spec files (as opposed to leaving the fix
as prose-only guidance in scattered docs). Discriminating assumption
tested: that this fix is expressible as additive spec fields checkable
by the existing hand-rolled shape gate, without inventing new enums or
a new validator dependency.

canonical: gates/role_spec_shape.py, read directly this session — its `_TOP_REQUIRED` tuple and `check()` body accept unknown top-level keys.
derived: python3 gates/role_spec_shape.py roles/specs/<file>.spec.json (see the code-fenced command block in "What was done" above)
Confirmed true — the shape gate passes unmodified against all six
edited files, per that output. Branch promoted (go): the six specs now
carry Gate B contrasts and Gate C finding methods; two `axis_evaluation`
sections that blocked architecture/security-threat-model's Gate C are
filled per the shared handbook template. Branch not yet promoted,
deferred to the issue's step 3 harness sub-task: turning
`gate_b_contrast`/`gate_c_*` fields into a mechanically *enforced* check
(today they are structured spec content an adversarial reviewer or the
eventual #776 methodology-validity signal can read, but no gate script
parses them yet — see Open findings).

#896 invariant-first alignment: per step-2 section 4, the fields added
this step are the invariant-shaped half of each fix (presence/coverage/
ordering checks: does a `gate_b_contrast` exist, does `repro_steps`
diff from the original report, does `evidence_log` carry a count+date,
does the STRIDE walk cover all six categories per element, does
`smells_identified` name a real Meszaros category) — none of them
encode the judgment-residue half (whether a given considered_options
entry is a real trade-off, whether a threat's severity is actually
justified, whether an identified smell is a real problem vs. an
intentional pattern), which step-2 correctly left to adversarial review,
not to a spec field.

## Open findings

1. `gate_b_contrast` and `gate_c_finding_method`/`gate_c_axis_evaluation`/
   `gate_c_status` are new spec fields with no dedicated shape-check yet.

canonical: gates/role_spec_shape.py, read directly this session — the
`check()` function only enforces the top-level keys already required by
`_TOP_REQUIRED`; it does not reject unknown keys and does not reference
`gate_b_contrast` or any `gate_c_*` name, so it cannot yet catch a role
that carries an empty-string `gate_b_contrast`. Resolution path: issue
#807 step 3's harness sub-task ("re-measure" in the issue's execution
plan) should extend `gates/role_spec_shape.py` and
`docs/specs/role-spec-template.schema.json` to require these fields
non-empty, the same way `reference_resolution` and `recomputation` are
required today.
2. `recomputation.checked_by` remains `"TBD"` in all six specs (step-2's
   cross-cutting finding, out of this step's scope per the step-2
   proposal) — recomputation enforcement is still unimplemented
   repo-wide; this step did not change that.
3. This step covers only the six priority-one roles step-2 audited; the
   35 non-priority roles remain unaudited, as step-2's Out-of-scope
   section already stated.

## Next steps

Issue #807 step 3's remaining harness sub-task (mechanical enforcement
of `gate_b_contrast`/`gate_c_*` non-emptiness, and re-running the #776
harness baseline against the strengthened specs) is the open follow-on;
resolution path for Open finding 1 above is to extend
`gates/role_spec_shape.py` accordingly in that follow-on work.

## What did not work

None.
