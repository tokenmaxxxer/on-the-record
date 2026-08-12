---
status: proposed
files:
  - docs/issue-807/reports/product-discovery/step2-current-state.md
  - docs/issue-807/proposals/2026-08-12-role-methodology-depth-audit-step2.md
---

## Request

Issue #807 step 2 (product-discovery): apply step 1's rubric (Gate A
valid judgment, Gate B valid deliverable, Gate C lens-based finding —
canonical: docs/issue-807/proposals/2026-08-11-role-methodology-depth-audit-scope.md,
PR #812, merged) to the priority-one load-bearing roles plus
test-authoring: execution-observation, defect-verification,
architecture, product-discovery, security-threat-model,
test-authoring. Deliver a per-role audit against Gates A/B/C, a
concrete strengthening plan per gap with real citations, and the
connection to #896's invariant-first reframe (which methodology pieces
become a standing always-on invariant vs. judgment residue). No spec
edits — this is scoping/survey only; step 3 does the actual edits.

## Constraints

- Every citation must be a real, checkable source — a named
  standard/book/framework with an identifiable author or issuing body,
  not a paraphrase.
- Compose with step 1's rubric verbatim; do not redefine Gates A/B/C.
- Compose with the existing `axis_evaluation` shared mechanism
  (docs/handbooks/architecture-methodology.md) rather than inventing a
  second finding-method template for the 5 axis-owning roles.
- No role-spec or rulebook file is edited in this step.

## 1. Per-role audit

Read this session: roles/execution-observation.json,
roles/specs/execution-observation.spec.json,
roles/defect-verification.json,
roles/specs/defect-verification.spec.json, roles/architecture.json,
roles/specs/architecture.spec.json,
docs/handbooks/architecture-methodology.md,
roles/product-discovery.json, roles/specs/product-discovery.spec.json,
roles/security-threat-model.json,
roles/specs/security-threat-model.spec.json,
roles/test-authoring.json, roles/specs/test-authoring.spec.json.

### execution-observation

- **Cited standard**: EARL 1.0 Schema (W3C,
  https://www.w3.org/TR/EARL10-Schema/) —
  roles/specs/execution-observation.spec.json `source_standard`.
- **Gate A — pass.** EARL's `earl:TestResult` outcome vocabulary
  (passed/failed/cantTell/inapplicable/untested) is the literal `result`
  enum, and `recomputation.rule` derives the overall verdict as the
  worst-case across that enum's ordering — the standard drives an actual
  derivation rule, not a decorative quote.
- **Gate B — fail (absent).** No stated hollow-instance contrast (e.g. a
  record where every claim resolves to `result: untested` with empty
  `assertedBy` would pass schema conformance while asserting nothing).
- **Gate C — fail/candidate-N/A.** The spec has no investigative
  procedure — it aggregates already-run test claims via the worst-case
  rule; there is no described method for *deciding what to observe*.
  This is a genuine N/A candidate (mechanical aggregation, per step 1
  §4's test), but the spec doesn't say so — an omitted N/A is itself a
  defect per step 1 §4.

### defect-verification

- **Cited standard**: ISO/IEC/IEEE 29119-3 Incident Report (clause 7.12,
  Annex A.2.15) + Bugmon reproduction precedent —
  roles/specs/defect-verification.spec.json `source_standard`.
- **Gate A — pass.** `required_fields` mirror 29119-3's incident-report
  fields, and `reference_resolution.rule` explicitly notes the standard
  leaves severity/status vocabularies open — engagement beyond a quoted
  label. `recomputation.rule` ties verdict to an executed repro log.
- **Gate B — fail (absent).** No contrast for a hollow verdict (e.g.
  `verdict: not-reproduced` with `repro_steps` copy-pasted from the
  original report, never independently executed).
- **Gate C — partial/thin.** `recomputation.rule` requires an attached
  repro log, which is Gate-C-adjacent, but there is no guidance on *how*
  to attempt adversarial reproduction — what inputs to vary, what counts
  as an independent attempt vs. a restatement. roles/defect-verification.json's
  own `use_when` text names "적대적 독립 재현" (adversarial independent
  reproduction) as the role's purpose, but this framing never reaches
  the spec's required fields.

### architecture

- **Cited standard**: MADR (Markdown Any Decision Records),
  https://adr.github.io/madr/ — roles/specs/architecture.spec.json
  `source_standard`.
- **Gate A — borderline fail.** `required_fields`
  (decision_id/context/considered_options/outcome) loosely mirror MADR's
  template fields, and `recomputation.rule` ties `outcome` back to the
  referenced ADR's own status. But the one document this role is meant
  to consult for methodology,
  docs/handbooks/architecture-methodology.md, contains no MADR content —
  it defines a generic axis-evaluation contract shared across 5 roles
  (architecture, security-threat-model, conformance-review,
  capacity-planning, performance-engineering), machine-checked by
  `gates/role_spec_shape.py::check_axis_ownership`. MADR's own guidance
  (how to weigh considered options, use decision drivers, structure
  pros/cons) is never operationalized anywhere.
- **Gate B — fail (absent).**
- **Gate C — incomplete by the handbook's own admission.**
  architecture is one of the 5 `axis_evaluation` owners
  (`judgment_axes: ["maintenance_complexity"]`,
  roles/architecture.json) and the handbook mandates each owner author
  a READ/EXECUTE(mechanical steps)/CRITERIA/CITATION section so "the
  verdict is 'expertise exercised,' not a self-report" — but
  architecture.spec.json does not yet contain that section. The
  mechanism exists; the fill-in doesn't.

### product-discovery

- **Cited standard**: Cagan/SVPG Opportunity Assessment + lean-startup
  pre-registered decision rules (Startup Commons / Kromatic / Startup
  Project) — roles/specs/product-discovery.spec.json `source_standard`.
- **Gate A — pass, strongest of the six audited.**
  `required_fields` reproduce Cagan's opportunity-assessment questions
  (problem_statement, target_market, market_size_rationale,
  competitive_alternatives, differentiator, timing_rationale,
  go_to_market_plan, success_metric, critical_success_factors,
  recommendation) near-verbatim, and lean-startup pre-registration is
  enforced by an ordering constraint in `recomputation.rule`
  (recommendation cannot be asserted before fail_condition/time_box/
  decision_rule are populated).
- **Gate B — fail (absent).** The ordering rule guards *sequence*, not
  *substance* — a `market_size_rationale` filled with boilerplate, or an
  `evidence_log` of trivial/uninformative refs, still passes.
- **Gate C — fail (checklist, not method).** `evidence_log` only
  requires refs resolve to a real path/sha/source; there is no stated
  method for what counts as sufficient evidence-gathering rigor
  (interview count, competitive-scan depth, saturation criteria — the
  kind of standard the `user-discovery` and `market-recon` skills
  already carry in this session's own skill listing, but which is not
  reflected in this role's spec).

### security-threat-model

- **Cited standard**: STRIDE / OWASP Threat Dragon model schema —
  roles/specs/security-threat-model.spec.json `source_standard`.
- **Gate A — pass.** The `type` enum is STRIDE's six categories
  verbatim (Spoofing, Tampering, Repudiation, Information Disclosure,
  Denial of Service, Elevation of Privilege), and
  `reference_resolution.rule` documents a live-fetch confirmation of the
  Threat Dragon schema, resolving a prior open finding (#515).
- **Gate B — fail (absent).**
- **Gate C — incomplete, same gap as architecture.** Only aggregation
  logic exists (`recomputation.rule` derives residual risk per listed
  threat); there is no elicitation procedure — STRIDE's actual method is
  to walk each data-flow-diagram element and test it against all six
  threat categories, and that per-element walk is not present anywhere
  in the spec. security-threat-model is also an `axis_evaluation` owner
  (`judgment_axes: ["attack_potential"]`) missing its
  READ/EXECUTE/CRITERIA/CITATION fill-in, same as architecture.

### test-authoring

- **Cited standard**: IEEE 829 test case specification format —
  roles/specs/test-authoring.spec.json `source_standard` (links to a
  stickyminds.com summary rather than the standard itself).
- **Gate A — fail, the clearest gap of the six.** `required_fields`
  (test_id/test_items/input_spec/output_spec) mirror IEEE 829's
  documentation shape. But roles/test-authoring.json states the role's
  actual `decides` is whether test code is well-designed in isolation
  and fixture strategy, and its `produces` includes a "smell list
  (Meszaros catalog refs)" — this is Gerard Meszaros's *xUnit Test
  Patterns* (2007) territory, specifically the "Test Smells" catalog.
  Meszaros is never named in `source_standard`, and none of the fields
  cover smells, fixture strategy, or isolation quality — the cited
  standard and the role's actual judgment domain are two different
  bodies of methodology, and only the wrong one is operationalized.
- **Gate B — fail (absent).**
- **Gate C — fail.** `recomputation.rule` only re-runs `test_id` against
  `input_spec` (a mechanical check), with no method for judging suite
  architecture, fixture strategy, or smell identification — the role's
  actual stated purpose.

## 2. Cross-cutting findings

- **Gate B fails uniformly across all six roles audited.** No spec
  states a hollow-vs-genuine deliverable contrast; every spec stops at
  `required_fields` + `reference_resolution` (orphan-reference guard) +
  `recomputation` (field-derivation rule) — none of which catches a
  schema-conformant-but-domain-empty instance (real paths cited, no real
  analysis).
- **`recomputation.checked_by` is `"TBD"` in all six roles audited** —
  recomputation enforcement is unimplemented repo-wide, not a per-role
  gap; out of this step's scope, but load-bearing for whether Gate A's
  "operationalized, not decorative" distinction is enforced mechanically
  or only readable by a human auditor.
- **The `axis_evaluation` mechanism
  (docs/handbooks/architecture-methodology.md) is the closest existing
  Gate-C template**, shared across 5 roles, but two of the roles audited
  here (architecture, security-threat-model) have not yet filled in
  their own section under it.

## 3. Strengthening plan per role (for step 3)

| Role | Gate A fix | Gate B fix | Gate C fix |
|---|---|---|---|
| execution-observation | none needed (pass) | add hollow-instance example: a record where every `result` is `untested`/`cantTell` with no cited command output is schema-valid but asserts nothing; require at least one `passed`/`failed` claim with a resolvable command | explicitly mark Gate C = N/A with the mechanical-aggregation justification (step 1 §4 test: any two observers re-running the same test set produce the same worst-case verdict) |
| defect-verification | none needed (pass) | hollow instance: `repro_steps` textually identical to the original bug report with no independent execution log is schema-valid but not verification | add an adversarial-reproduction method: require `repro_steps` to include at least one input/environment variation not present in the original report (operationalizing `roles/defect-verification.json`'s own "적대적 독립 재현" framing into the spec) |
| architecture | fill the READ/EXECUTE/CRITERIA/CITATION section per docs/handbooks/architecture-methodology.md, citing MADR's actual decision-drivers/considered-options weighing method, not just its field names | hollow instance: `considered_options` listing exactly one option, or `decision_drivers` absent/boilerplate, is schema-valid but not a real trade-off decision | the filled axis_evaluation section IS the Gate-C fix — a mechanical EXECUTE procedure for weighing `maintenance_complexity` |
| product-discovery | none needed (pass) | hollow instance: `market_size_rationale`/`competitive_alternatives` filled with generic prose citing no evidence_log entry is schema-valid but not a real assessment | add a rigor floor for `evidence_log`: cite Mom-Test-style evidence discipline (already named in this role's own scout/discovery-skill directives this session) — observation/interview count, date range, no stated-preference-only evidence admissible |
| security-threat-model | none needed (pass) | hollow instance: a threat list covering only 1–2 STRIDE categories for a data flow with an authentication boundary is schema-valid but incomplete elicitation | fill the READ/EXECUTE/CRITERIA/CITATION section: EXECUTE = walk each data-flow-diagram element against all six STRIDE categories explicitly (the standard's actual method, per Shostack, *Threat Modeling: Designing for Security*, 2014, ch. 4) |
| test-authoring | re-scope `source_standard` to add Gerard Meszaros, *xUnit Test Patterns: Refactoring Test Code* (2007) — Test Smells catalog — alongside IEEE 829, and add fields for `smells_identified`/`fixture_strategy`/`isolation_verdict` so the citation matches the role's actual `decides` | hollow instance: `output_spec` mechanically re-derived with no `smells_identified` entries is schema-valid but not a design-quality judgment | add a finding method: enumerate the specific Meszaros smell categories (e.g. Fragile Test, Obscure Test, Test Code Duplication) to check against, evidenced by which lines/fixtures triggered each |

## 4. Connection to #896's invariant-first reframe

For each gate/role above, split the fix into what can be a standing
always-on invariant (a mechanical rule enforceable independent of
per-instance judgment) vs. judgment residue (what still requires a human
or agent's real domain call, no matter how well-specified):

- **Invariant-shaped** (candidates for #896's always-on layer):
  execution-observation's worst-case recomputation rule (already an
  invariant); defect-verification's requirement that `repro_steps`
  include a variation not present in the original report (a checkable
  diff, not a judgment call); product-discovery's pre-registration
  ordering rule (already an invariant) and evidence-log admissibility
  filter (stated-preference-only evidence rejected — mechanically
  checkable by absence of an observation/interview count field);
  security-threat-model's per-element STRIDE coverage check (six
  categories × N data-flow elements is a countable completeness
  invariant, independent of whether each individual threat entry is
  well-reasoned); test-authoring's Meszaros smell-category enumeration
  presence (checkable: did the record cite at least one smell category
  by name, evidenced by file:line).
- **Judgment residue** (cannot be reduced to an invariant, stays a real
  domain call): whether a given `considered_options` entry in an
  architecture ADR is *actually* a live trade-off vs. a straw-man option
  included to satisfy the field; whether a security threat's stated
  severity is *actually* justified given the specific system's exposure,
  not just present; whether a test's identified "smell" is a real design
  problem vs. an intentional, justified pattern; whether
  product-discovery's `differentiator` claim is *actually* differentiated
  from the cited `competitive_alternatives`, not just textually distinct.
- **Pattern**: coverage/presence/ordering/completeness checks
  (did-the-record-do-the-required-motion) are invariant-shapeable across
  all six roles; the substantive correctness of any single judgment call
  inside that motion is not, and stays residue for adversarial review
  (step 1 §3's signal #8 mechanism) to catch.

## 5. Canonical citations (for step 3's edits)

- EARL 1.0 Schema, W3C: https://www.w3.org/TR/EARL10-Schema/
- ISO/IEC/IEEE 29119-3:2021, Software Testing — Test Documentation,
  clause 7.12 / Annex A.2.15 (Incident Report)
- MADR (Markdown Any Decision Records): https://adr.github.io/madr/
- Marty Cagan, *Inspired* (2nd ed., 2017), Opportunity Assessment
  technique (SVPG)
- Eric Ries, *The Lean Startup* (2011), pre-registered
  hypothesis/build-measure-learn decision rules
- STRIDE: Loren Kohnfelder & Praerit Garg (Microsoft, 1999, internal);
  canonical public treatment: Adam Shostack, *Threat Modeling:
  Designing for Security* (Wiley, 2014), ch. 3–4
- OWASP Threat Dragon model schema:
  https://github.com/OWASP/threat-dragon
- IEEE 829-2008, Standard for Software and System Test Documentation
- Gerard Meszaros, *xUnit Test Patterns: Refactoring Test Code*
  (Addison-Wesley, 2007) — Test Smells catalog (part IV)

## Out of scope

- Editing any roles/*.json, roles/specs/*.spec.json, or
  docs/handbooks/*.md file (step 3).
- Building signal #8's grading-agent prompts or filling in the
  `axis_evaluation` READ/EXECUTE/CRITERIA/CITATION sections (step 3).
- Auditing the 35 non-priority roles (deferred by step 1 §2 to step 2's
  normal per-cluster sweep, which this pass does not claim to be —
  this pass covers only the six roles named in this step's task).
- Re-running the #776 harness baseline (step 3, depends on the spec
  edits landing).

## Acceptance

- Each of the six audited roles has a stated Gate A/B/C verdict with
  reasoning tied to the actual spec text (§1).
- Every strengthening-plan cell (§3) names a concrete, checkable change,
  not a restated goal, and cites a real methodology source (§5).
- §4 explicitly separates invariant-shaped fixes from judgment residue
  per role, connecting to #896 as the task requires.
- No roles/*.json, roles/specs/*.spec.json, or handbook file is modified
  by this PR.

## Accumulation

This proposal adds no code. It commits step 3 to editing at minimum the
six roles/specs/*.spec.json files above (Gate B hollow-instance text in
all six; Gate C finding-method additions in architecture,
security-threat-model, defect-verification, product-discovery,
test-authoring; a `source_standard` correction plus new required fields
in test-authoring only) and to filling in two
`axis_evaluation` sections in docs/handbooks/architecture-methodology.md
consumers (architecture, security-threat-model spec files). No standing
maintenance burden is created by this scoping step itself.

## What did not work

None.
