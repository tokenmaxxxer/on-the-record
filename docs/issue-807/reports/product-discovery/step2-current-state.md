# Current state — issue #807 step 2 (per-role methodology audit)

## Background/context

canonical: docs/issue-807/proposals/2026-08-11-role-methodology-depth-audit-scope.md (PR #812, merged; read this session)

Step 1 fixed the rubric (Gate A valid judgment / Gate B valid deliverable
/ Gate C lens-based finding) and a load-bearing-role priority table.
Step 2 applies that rubric to the priority roles named in that table's
§2: execution-observation, defect-verification, architecture,
product-discovery, security-threat-model (the priority-one set), plus
test-authoring (named directly in this step's task text, not in step
1's table). No code/spec edits happen here — the edits are step 3.

## Problem stated without a solution attached (JTBD)

- **Job performer**: the role-methodology-depth audit process (issue
  #807), acting through the product-discovery role this session.
- **Job**: determine, for each load-bearing role, whether its written
  methodology (roles/*.json + roles/specs/*.spec.json) would survive
  adversarial scrutiny as domain-real, or is field-shape mirroring that
  passes schema gates while being judgmentally hollow.
- **Circumstance**:

canonical: docs/issue-807/proposals/2026-08-11-role-methodology-depth-audit-scope.md §"Constraints" (read this session)

  Step 1 states all roles already carry a `source_standard` citation;
  the open question here is not "is there a citation" but "is it
  operationalized, and does the spec name a hollow-instance contrast and
  an actual finding method."
- **Desired outcome**: a per-role gap list + concrete strengthening plan,
  each grounded in a real citation, so step 3 has a boundary to edit
  against instead of re-deriving methodology from scratch per role.

If the issue text were read as already embedding a solution ("add
methodology to the specs"), the restated problem above is narrower: the
gap is specifically Gate B (hollow-instance contrast) and, for several
roles, Gate C (finding method) — not a blanket "specs need more text."

## Opportunity-solution tree position

- **Outcome**: northpole reqs #1/#3/#4/#5 do not fail invisibly through a
  role that passes schema gates with a domain-empty deliverable.
- **Opportunity**:

canonical: docs/issue-807/proposals/2026-08-11-role-methodology-depth-audit-scope.md §2 priority table (read this session)

  the priority set of roles above is the highest-leverage subset because
  their failure propagates furthest through the harness's own
  measurement chain.
- **Candidate solutions**: (a) add a stated hollow-vs-genuine contrast
  per role (Gate B fix); (b) add a finding-method section per role (Gate
  C fix, reusing the shared `axis_evaluation` template — canonical:
  docs/handbooks/architecture-methodology.md, read this session — where
  it already exists); (c) for test-authoring, realign `source_standard`
  to the role's actual judgment domain (Gate A fix — a citation
  mismatch, not just a depth gap; canonical: roles/test-authoring.json +
  roles/specs/test-authoring.spec.json, read this session).
- **Discriminating assumption test**: step 3 fills in one role's
  READ/EXECUTE/CRITERIA/CITATION section (architecture or
  security-threat-model — the two `axis_evaluation` owners already
  missing it, per docs/handbooks/architecture-methodology.md) and
  re-runs an adversarial review against it; if the filled section
  survives a deliberate-defect flip test (per step 1 §3's signal #8
  mechanism), the template generalizes to the other axis owners without
  re-deriving it per role.

## Scout skip record

Skipped. Condition met: "the spec literally leaves no design decision
open" for the *sourcing* half of this task — the methodologies audited
(EARL, ISO/IEC/IEEE 29119-3, MADR, Cagan/SVPG + lean-startup,
STRIDE/OWASP, IEEE 829/Meszaros) are all named, canonical,
individually-documented standards/frameworks already cited in the specs

canonical: roles/specs/*.spec.json `source_standard` fields (read this session)

the open decision here (how to strengthen each spec) is answered by
applying step 1's rubric to what step 1 already scouted
(docs/issue-807/reports/product-discovery/scout-brief.md), not by
re-scouting the product-discovery-exemplar category. Re-scouting would
re-survey audit-rubric design (already done in step 1) rather than steer
a new product decision.

## Code under review

- roles/execution-observation.json
- roles/specs/execution-observation.spec.json
- roles/defect-verification.json
- roles/specs/defect-verification.spec.json
- roles/architecture.json
- roles/specs/architecture.spec.json
- docs/handbooks/architecture-methodology.md
- roles/product-discovery.json
- roles/specs/product-discovery.spec.json
- roles/security-threat-model.json
- roles/specs/security-threat-model.spec.json
- roles/test-authoring.json
- roles/specs/test-authoring.spec.json
