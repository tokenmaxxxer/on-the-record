---
status: proposed
files:
  - docs/issue-807/reports/product-discovery/current-state.md
  - docs/issue-807/reports/product-discovery/scout-brief.md
  - docs/issue-807/proposals/2026-08-11-role-methodology-depth-audit-scope.md
---

## Request

Issue #807 step 1 (product-discovery): scope the role-methodology-depth
audit across the 43 roles in `roles/specs/*.spec.json`. Deliver: (1) the
rubric for a research-grounded methodology per the three capacities
(valid judgment, valid deliverable, lens-based finding), pass/fail
criteria, and what "named domain methodology literature" means per role
type; (2) which roles are load-bearing for the 7 northpole requirements,
prioritized with reasoning; (3) how #776's harness gains a
methodology-VALIDITY signal beyond "delegation happened"; (4) how
pure-mechanical roles get marked N/A explicitly. No code changes — step 2
(a separate PR) does the per-role audit + rewrite; step 3 re-measures.

## Constraints

- Ground every rubric criterion in a real, named methodology source —
  survey confirms all 43 roles already cite one (`source_standard`); this
  proposal must not re-invent that, only define how to grade what's
  BEHIND the citation.
- Must compose with the existing `role-spec-reference-guard.sh` /
  `record_lint.py` mechanical-guard pattern already in place, not invent
  a parallel enforcement mechanism.
- Must compose with the #776 harness's existing 7-signal table
  (`docs/specs/northpole-harness.md`) as an ADDITIONAL signal, not a
  redesign — #776's step 3 baseline-remeasure depends on the existing
  table staying stable.
- Step 1 is scoping only: this proposal fixes the rubric and priority
  order; it does not itself grade any role pass/fail (that's step 2).

## 1. Rubric: research-grounded methodology per capacity

Each role's methodology definition (core or rulebook) is graded against
three independent pass/fail gates, one per capacity. A role passes the
overall methodology-depth check only if all three gates pass OR the role
is marked N/A per §4.

### Gate A — Valid judgment
- **Pass**: the spec/rulebook names a specific, real domain method for
  reaching a defensible call — not "use good judgment" or a restated
  goal. The method must be attributable to a real, citable source (a
  named standard, book, paper, or established industry framework with a
  live or archival URL) and must be the kind of method a practitioner in
  that domain would recognize as the actual working method, not a
  post-hoc label glued onto generic reasoning.
- **What "named domain methodology literature" means, per role type**:
  - *Standards-body roles* (security-threat-model, accessibility,
    secure-coding, legal-compliance, localization): a formal standard
    document (STRIDE/OWASP, WCAG-EM, ASVS, GDPR Art. 35(7), Unicode
    CLDR/UTS#35) — already present for all of these per the survey.
  - *Named-practitioner-framework roles* (product-discovery, marketing,
    market-analysis, sales, pricing): a named framework with a
    identifiable original author/originating body (Cagan/SVPG, April
    Dunford, Porter/HBR, MEDDPICC, Van Westendorp) — already present.
  - *Engineering-discipline roles* (architecture, performance-engineering,
    observability, data-modeling): an engineering methodology with a
    canonical reference text (MADR, Google SRE workbook, OpenTelemetry
    semconv, Kimball) — already present.
  - *Roles with no settled external canon* (e.g. issue-retrospective,
    devrel): the survey found these citing "convergent industry
    practice" or a named individual's public work rather than a formal
    standard — Gate A still passes IF the source is a specific,
    checkable artifact (a named book/talk/post by an identifiable
    practitioner), not a fabricated or generic label; step 2 must verify
    each such citation resolves to a real, findable source (the same
    check `market-analysis`'s citation-discipline rulebook already
    performs for evidence lines).
- **Fail conditions**: the citation names a real standard but the
  spec/rulebook text never actually operationalizes it (the standard is
  decorative — quoted once, never reflected in `required_fields` /
  `recomputation` / any judgment step); or the citation is a paraphrase
  with no traceable source at all.

### Gate B — Valid deliverable
- **Pass**: the spec states, separately from field-shape conformance,
  what a HOLLOW instance of this role's deliverable looks like (plausible
  field-filling with no real domain content) and what distinguishes it
  from a genuine one — i.e., the spec names its own failure mode, not
  just its success shape. Structural principle from rubric-design
  literature: criteria must be MECE and describe quality LEVELS, not
  presence/absence of fields (a schema-conformant record can still be
  hollow — see scout-brief.md must-bes).
- **Fail conditions**: the spec only defines `required_fields` /
  `reference_resolution` (shape) with no stated hollow-instance
  contrast — this is the CURRENT state for effectively all 43 roles per
  the survey (schema conformance is wired; the hollow-vs-valid
  distinction is not written down anywhere).

### Gate C — Requirement/defect finding from the role's lens
- **Pass**: the spec/rulebook states a FINDING method — how the role,
  given only the current repo/system state (not a pre-handed finding),
  surfaces what its lens uniquely sees — distinct from a generic
  checklist ("check for X, Y, Z"). A finding method names what evidence
  the role gathers and how it reasons from that evidence to a finding,
  the way `security-threat-model`'s STRIDE walks each data-flow element
  through six threat categories, or `defect-verification`'s ISO/IEC/IEEE
  29119-3 incident-report clause structures a reproduction method.
- **Fail conditions**: the role only reacts to findings already handed to
  it by another role (pure downstream consumer) — such roles are
  candidates for Gate C = N/A (§4), not a fail, once confirmed in step 2.

### Cross-cutting: what makes the rubric itself trustworthy
Per scout-brief.md (PReMISE; Adversarial Validation Loop; anti-anchoring
finding), a rubric is only as good as its own adversarial robustness: any
grading of Gates A–C against a real role record must have the grader
commit an independent judgment on the artifact BEFORE reading the
producing role's own self-assessment, and must be tested at least once
against a deliberately-broken version of the same artifact to confirm the
verdict flips. §3 operationalizes this as the harness signal.

## 2. Load-bearing roles for the 7 northpole requirements, prioritized

Mapping northpole reqs to the roles whose judgment/deliverable/finding
failure would make that req fail INVISIBLY (record present, gates green,
substance absent) — canonical: `docs/specs/northpole-harness.md` §3 (req
table read this session) and `roles/specs/*.spec.json` (`use_when` /
`write_scope` fields, read via the script in the survey).

| Priority | Role | Northpole req(s) | Reasoning |
|---|---|---|---|
| 1 | requirements-engineering | #3 (real gap vs requirement) | Every other role's "is this done" call is downstream of this role's traceability judgment (EARS/29148) being real, not decorative. |
| 1 | execution-observation | #1, #4 (bottleneck/risk ID, human-legible reporting) | Sits directly in the harness's own observation path (`docs/specs/northpole-harness.md` §4) — if this role's finding method is hollow, the harness's own signal collection is compromised, corrupting every other role's measurement transitively. |
| 1 | architecture | #3, #5 (real gap, real resolution) | MADR judgment calls (coupling/cohesion trade-offs) are exactly the "plausible-sounding vs domain-valid" failure mode the issue names as its motivating example. |
| 1 | security-threat-model | #1 (bottlenecks/risks) | Already has the deepest existing rubric skeleton (STRIDE categories, `recomputation` rule) — best candidate to pilot Gate A–C grading against a working example before generalizing. |
| 2 | defect-verification | #3, #5 | Gatekeeps whether a "fix" claim is real; ISO 29119-3 reproduction method is a finding method already, but has no stated hollow-instance contrast (Gate B gap). |
| 2 | performance-engineering | #1, #5 | SRE error-budget judgment is a numeric-threshold domain — good second pilot for Gate A (methodology already operationalized via SLO math, easiest to check for decorative-vs-real citation use). |
| 2 | risk-management | #1 | NIST SP 800-161r1 C-SCRM is a finding method by construction (supply-chain risk enumeration) — high leverage for req #1. |
| 3 | product-discovery (this role) | #3 | Self-referential: this proposal is itself an instance of the capacity being audited — step 2 should audit this role's own rulebook stack (5 directives seen at session start) for the same three gates. |
| 3 (remaining 35 roles) | — | varies | Deferred to step 2's per-cluster pass; none showed a Gate-A citation gap in the survey (43/43 have `source_standard`), so the marginal audit value per role is lower than the priority-1/2 set above, where a hollow judgment call propagates furthest through northpole's own measurement chain. |

Reasoning for the ordering: priority 1 roles are those whose OWN failure
corrupts either (a) another role's ability to be measured at all
(execution-observation), or (b) the specific northpole reqs the issue
names as most exposed (#1/#3/#5, architecture and security-threat-model
as the issue's own worked examples). Priority 2 extends to roles with a
strong existing methodology skeleton (cheap to pilot Gate A/B/C grading
against) or high fan-out (risk-management's findings feed multiple
downstream roles). Priority 3 defers the remaining 35 to step 2's normal
per-cluster sweep — the survey found no Gate-A gap among them worse than
the priority-1/2 set, so front-loading effort there is not justified yet.

## 3. Harness methodology-validity signal (beyond "delegation happened")

Add signal **#8** to `docs/specs/northpole-harness.md` (additive, does
not renumber or alter signals #1–#7 — preserves #776 step 3's baseline
comparability):

| # | Requirement | Signal | Pass condition | Empty state |
|---|---|---|---|---|
| 8 | Methodology validity (not just delegation) | For each priority-1 role invoked during the run: (a) an independent same-domain agent renders its OWN verdict on the role's deliverable, seeing only the artifact, not the producing role's reasoning trail; (b) a second same-domain agent runs an adversarial refutation pass against a copy of the deliverable with one substantive, domain-real defect deliberately reintroduced (e.g., for security-threat-model: remove a mitigation for a STRIDE category actually present in the data flow) | (a)'s independent verdict agrees with the role's own verdict on the CLEAN artifact, AND (b)'s refutation verdict flips (correctly rejects) on the DEFECT-injected copy | UNMEASURED if no priority-1 role fired during the run (nothing to grade); INDEPENDENT FAIL (not UNMEASURED) if (a) agrees with a defect-injected copy — that is the hollow-role failure mode the issue names |

This directly implements the issue's own Acceptance check ("an
adversarial review confirms a produced deliverable is domain-valid...the
harness emits a methodology-validity signal that fails on a deliberately
hollow role and passes on the grounded one") using the mechanism the
scout pass converged on independently (Adversarial Validation Loop +
anti-anchoring: independent-verdict-first, then deliberate-flip test —
see scout-brief.md). Step 2 builds signal #8's grading agents per
priority-1 role (their domain differs — a security-threat-model
refutation pass is not the same prompt as an architecture one); step 3
runs it against the existing fixture-target repo, seeding one role's
deliverable with a known defect as the negative control.

## 4. Pure-mechanical roles: explicit N/A

A role (or a single Gate within a role) is marked **N/A**, not silently
passed, when it meets a mechanical test: the role's ENTIRE output is
derivable from its input by a fixed transformation with no domain
judgment call — i.e., given the same input, any two competent
practitioners following the stated method would produce the same
output, not merely a similar one. This is distinct from "the role is
simple" — simplicity alone does not qualify.

Step 2 must run this test per role per gate (a role can be N/A on one
gate and not others — e.g. a role with a real finding method but a fully
mechanical deliverable format is N/A on Gate B only, not the whole role).
Likely N/A candidates surfaced by the survey (to be CONFIRMED, not
assumed, in step 2 — listed here only to make the empty-state pattern
concrete, per the issue's own empty-state requirement):
- `release-engineering` (Keep a Changelog format) — Gate B likely N/A:
  the changelog entry format is a fixed transformation of already-decided
  changes, not a judgment call. Gate A/C likely still apply (deciding
  what counts as Added/Changed/Fixed/Breaking is itself a judgment).
- `localization` (CLDR/LDML plural-rule and locale-format lookup) — Gate
  A/B likely N/A for the mechanical lookup path; Gate C (finding
  under-localized strings) likely still applies.

The record for each role's audit (step 2) must state N/A explicitly per
gate with the one-line mechanical-test justification — an omitted gate
is a defect in the audit record, not evidence of N/A.

## Out of scope

- Grading any specific role pass/fail (step 2).
- Building signal #8's actual grading-agent prompts (step 2/3).
- Re-running the #776 harness baseline (step 3, depends on step 2
  landing the per-role rubric text signal #8 reads).

## Acceptance

- The rubric (§1) gives each of the three capacities a stated pass/fail
  test and names what "grounded" means per role type, citable back to
  real methodology-audit literature (scout-brief.md Sources).
- The priority table (§2) is reasoned, not just listed, and ties each
  priority-1 role to a specific northpole req and failure-propagation
  argument.
- §3 is a concrete, additive harness signal spec, not a restated goal —
  it names the two-agent mechanism, its pass condition, and its empty
  state, matching the existing table's format exactly.
- §4 gives a mechanical N/A test plus candidate examples, so step 2 has
  a boundary to apply rather than inventing one per role.

## Accumulation

This proposal adds no code and no new enforcement surface by itself —
it is scoping only. It DOES commit step 2 to touching all 43
`roles/specs/*.spec.json` files (or their paired rulebooks) at least
once each to record a Gate A/B/C verdict (pass/fail/N/A), and commits
step 3 to extending `docs/specs/northpole-harness.md` with signal #8 plus
new grading-agent code under `harness/`. The accumulation cost is
therefore back-loaded onto step 2 (43-file sweep) and step 3 (new harness
signal + fixture defect-injection support), not this step. No standing
maintenance burden is created by step 1 itself.

## What did not work

None.
