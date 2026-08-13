---
status: proposed
files:
  - roles/specs/ux-engineering.spec.json
  - roles/specs/interaction-design.spec.json
  - roles/specs/accessibility.spec.json
  - roles/specs/api-design.spec.json
  - roles/specs/performance-engineering.spec.json
  - roles/specs/secure-coding.spec.json
  - roles/specs/test-authoring.spec.json
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/quality-bar-gate.sh
  - on-the-record/hooks/test_quality_bar_gate.py
  - gates/quality_bar.py
  - gates/quality_bar_test.py
  - gates/spec_schema_five_activities_test.py
  - docs/specs/role-invariant-coverage.md
  - docs/specs/reconciled-index.md
---

# issue-1156: per-role quality bars with rejection teeth (proposal, phase 1)

kind: proposal
subject: issue-1156

Proposal: docs/issue-1156/proposals/per-role-quality-bars.md

## Intent

Scope is ALL 43 roles (issue body requirement 5, amended 2026-08-13:
the operator's scope-amendment comment states the 7 are landing ORDER,
not scope). Give the 7 landing-order-first roles (ux-engineering,
interaction-design, accessibility, api-design,
performance-engineering, secure-coding, test-authoring) a decomposed,
individually checkable `quality_bar` drawn from the standard each spec
already cites in `source_standard`
(canonical: `docs/issue-1156/reports/requirements-engineering/current-state-survey.md`,
"What exists today"), add a `bar-not-met` verdict/refusal state to each
spec's `loop_state`, and design (proposal only — no landing this PR) a
merge-blocking hooks-only gate that reads the owning role's own
bar-met/bar-not-met record, refuses a self-graded pass, and bounds
repeated rejection with an escalation path. For the remaining 36 roles,
this phase-1 proposal names each role's bar domain and source standard
(§7) so every one of the 43 ends with a declared bar per the amended
requirement 5 — full per-criterion decomposition for those 36 is
phase-wise, landing in later issues that reuse this proposal's
decomposition principles (§0) rather than re-litigating them. Read
basis:
`docs/issue-1156/reports/requirements-engineering/current-state-survey.md`.

## Constraints stated so far

- Scope is ALL 43 roles (issue body requirement 5, as amended
  2026-08-13 — the pre-amendment "exactly the 7 roles" reading is
  superseded). The 7 named roles are landing ORDER and full-detail
  validation of the template; the other 36 get, at minimum, a named
  bar domain and source standard in this phase-1 proposal (§7), with
  full decomposition to follow phase-wise.
- Bar level is top-of-industry for all 43, not passing-grade (issue
  body requirement 6, amended): each criterion sits at the line a
  top-tier practitioner in that domain would refuse below. Where a
  domain's bar cannot be automated, the checkable form is a named
  human-review checklist recorded in the spec, explicitly marked as
  such — never a silently lowered bar. This is a decomposition
  principle applying uniformly to all 43 roles, detailed in §0.
- Every `quality_bar` entry's methodology traces to the role's already-
  cited `#1130` `source_standard` (and, for the 3 roles that already
  carry five-activity depth, its `judgment_methodology`/
  `review_methodology` fields) — no new, uncited standard is
  introduced (issue body requirement 1; validity-consult finding cited
  in the issue body: decompose adjectives into automatable
  sub-criteria, avoid self-grading, bound the loop).
- The gate is hooks-only, default-on, target-root-anchored — northpole
  req#7 — reusing `on-the-record/hooks/merge-allow-gate.sh`'s
  established shape (kill switch, pure-function classifier in `gates/`,
  PreToolUse on `gh pr merge`) rather than inventing a new enforcement
  path (canonical: survey "What exists today", `merge-allow-gate.sh`
  citation).
- Anti-circularity is structural, not a norm: the classifier must be
  able to tell the record's authoring role apart from the change's
  producing role and refuse when they're the same account/role,
  serving northpole req#1/req#5 (delegation to a specialist is only
  real if a different specialist — never the producer itself — can
  refuse the work; canonical: `docs/specs/northpole.md` sections 1 and
  5, read this turn).
- The rejection loop must be bounded — a fixed reject cap, then
  escalation to `open_decision_item`/operator, never an unbounded
  ping-pong (issue body requirement 4).
- This is a phase-1 proposal only (role directive, contract v3 s19; and
  the issue body's own "Proposal only — approval opens phase 2") — no
  spec/hook/gate edits land in this PR; they land in phase 2, after an
  approvers.md Approve.

## What will be done

### 0. Decomposition principles (apply to all 43 roles)

These principles govern every role's `quality_bar`, including the 36
detailed only at domain level in §7 — they are what phase-wise
decomposition for those 36 must follow, not new rules invented later:

1. **Top-of-industry, not passing-grade** (requirement 6): each
   criterion is set at the refuse-below line of a top-tier practitioner
   in that domain, not a minimum-viable bar — e.g. not "has tests" but
   coverage+mutation thresholds; not "documented" but a record a reader
   can act on without the author (issue body requirement 6, verbatim
   example).
2. **Decompose the adjective**: no criterion may be the bare word
   "high-quality"/"good"/"top-tier" — each is a named, individually
   checkable sub-criterion with a `verification_method`, drawn from the
   role's own already-cited `source_standard` (validity-consult finding
   cited in the issue body).
3. **Non-automatable → named human-review checklist, never a lowered
   bar** (requirement 6): where a domain's bar criterion cannot be
   automated (e.g. positioning quality, negotiation soundness, content
   voice), the checkable form is a named checklist item requiring a
   human verdict, recorded in the spec's `quality_bar` entry with
   `verification_method: human-review-checklist` (or equivalent) and
   the checklist question stated — the criterion is never dropped or
   replaced with an easier automatable proxy.
4. **No self-grading**: the producing role never grades its own
   deliverable against its bar (§4 anti-circularity design applies
   identically regardless of which of the 43 roles owns the bar).
5. **Bounded rejection**: every role's `bar-not-met` verdict feeds the
   same reject-cap + escalation mechanism (§5), not a per-role bespoke
   loop.

### 1. Per-role `quality_bar` decomposition (7 specs)

Each spec gains a `quality_bar` array of `{criterion, verification_method}`
entries, sourced from the spec's own already-cited standard — this
section is the actual decomposition content phase 2 copies verbatim.

**ux-engineering** (source: DTCG token format, shared lineage with
brand-design — canonical: `roles/specs/ux-engineering.spec.json`
`source_standard` field, read this turn):
1. `token_consistency` — every `rendered_value` a component consumes
   resolves to its declared `token_name` in the current token build,
   with no hardcoded literal standing in for a token. verification_method:
   automated diff against the design-tokens JSON (reuses the spec's own
   existing `reference_resolution`/`recomputation` rules).
2. `wcag_aa_automated_pass` — the component passes an automated WCAG 2.2
   AA ruleset (axe-core or equivalent) with zero violations.
   verification_method: automated accessibility scanner run against the
   rendered component, exit code / violation count asserted.
3. `keyboard_navigability` — every interactive element in the component
   is reachable and operable via keyboard alone (Tab/Shift+Tab focus
   order, Enter/Space activation, no keyboard trap).
   verification_method: automated keyboard-navigation test (e.g.
   Playwright/Testing-Library keyboard simulation) asserting focus
   order and activation.
4. `async_surface_states` — every surface that performs an async
   operation (fetch/mutation) declares and renders a loading state, an
   error state, and an empty state — not just the happy path.
   verification_method: static scan for the three state branches in the
   component's render logic, or a component test asserting each state
   renders distinctly.

**interaction-design** (source: NN/g wireflows + UML state-machine
notation — canonical: `roles/specs/interaction-design.spec.json`
`source_standard` field, read this turn):
1. `closed_node_enum` — every wireflow node's type is drawn from the
   spec's declared closed enum (screen/decision/system-action/end) —
   no free-text node type. verification_method: schema validation
   against the closed enum.
2. `no_orphan_transition` — every transition edge resolves to a
   declared node on both ends (no dangling reference).
   verification_method: reference-resolution check (reuses the spec's
   own `reference_resolution` rule).
3. `error_path_modeled` — every user-input node has at least one
   outgoing error/invalid-input transition modeled, not only the happy
   path. verification_method: graph traversal asserting an error-typed
   outgoing edge exists per input node.
4. `terminal_reachability` — every node is reachable from the flow's
   declared start node, and the flow's terminal node is reachable from
   every node (no dead end, no unreachable node).
   verification_method: graph reachability check both directions.

**accessibility** (source: WCAG-EM 2.0 + ACT Rules Format — canonical:
`roles/specs/accessibility.spec.json` `source_standard` field, read
this turn):
1. `wcag22_aa_automated_pass` — zero automated-rule violations at WCAG
   2.2 level AA across the sampled pages/components (WCAG-EM sampling
   procedure). verification_method: ACT-Rules-conformant automated
   scanner run against the WCAG-EM sample, violation count asserted.
2. `manual_check_coverage` — every WCAG 2.2 AA success criterion that
   ACT Rules mark as not machine-testable is covered by a recorded
   manual check outcome (pass/fail/n-a), not silently skipped.
   verification_method: cross-reference the manual-check log against
   the WCAG-EM criterion list for the sample.
3. `keyboard_and_focus_visible` — full keyboard operability plus a
   visible focus indicator on every interactive element in the sample.
   verification_method: automated keyboard-nav + focus-visibility
   check.
4. `name_role_value_exposed` — every interactive element exposes an
   accessible name, role, and (where applicable) value/state to the
   accessibility tree. verification_method: automated accessibility-
   tree query against the sample, asserting non-empty name/role.

**api-design** (source: Spectral ruleset + OpenAPI schema conformance
— canonical: `roles/specs/api-design.spec.json` `source_standard`
field, read this turn):
1. `spectral_ruleset_pass` — zero Spectral lint errors against the
   project's OpenAPI ruleset. verification_method: `spectral lint`
   exit code / error count.
2. `schema_conformance` — every response the API can emit for a
   documented status code validates against its OpenAPI schema.
   verification_method: schema-conformance test suite run against
   recorded/contract responses.
3. `breaking_change_versioned` — a removed/renamed public field or
   endpoint carries a version bump (reuses the existing
   `api-version-guard.sh` invariant as one bar sub-criterion, not the
   whole bar). verification_method: `api-version-guard.sh`'s existing
   diff check.
4. `error_response_shape` — every documented error status code returns
   a response matching the project's declared error-shape schema (not
   an ad hoc shape per endpoint). verification_method: schema
   conformance test scoped to 4xx/5xx documented responses.

**performance-engineering** (source: Google SRE SLO / error-budget —
canonical: `roles/specs/performance-engineering.spec.json`
`source_standard` field, read this turn):
1. `slo_declared_and_measured` — the changed surface has a declared
   SLO (latency/availability target) and a measured value against it,
   not an unmeasured assertion. verification_method: reuses the spec's
   existing `gate_c_axis_evaluation` measurement rule.
2. `error_budget_not_exhausted` — the change does not consume more than
   the remaining error budget for its declared SLO window.
   verification_method: error-budget calculation (SRE workbook policy)
   against the measured value.
3. `tail_latency_bounded` — p99 (not just mean/p50) latency is measured
   and stated against a bound ("Tail at Scale" — already one of
   performance-engineering's #1130-cited degree-level-knowledge
   sources). verification_method: percentile latency measurement from
   the same load test/measurement run.
4. `capacity_headroom_stated` — the measurement states headroom against
   the current capacity ceiling (USE-method resource utilization), not
   only latency. verification_method: resource-utilization measurement
   (CPU/memory/connections) alongside the latency measurement.

**secure-coding** (source: OWASP ASVS — canonical:
`roles/specs/secure-coding.spec.json` `source_standard` field, read
this turn):
1. `asvs_level_declared_checklist_pass` — every ASVS requirement in the
   declared target level (the spec's existing `target-level-undeclared`
   precondition refusal already requires a level be named) is checked
   off pass/fail, not left blank. verification_method: checklist
   completion cross-reference against the declared ASVS level's
   requirement list.
2. `input_validation_at_boundary` — every external input boundary
   (request body/query/header/file) has a validation check present in
   the diff. verification_method: static scan for a validation call on
   each identified boundary.
3. `authn_authz_path_covered` — every new/changed endpoint states its
   authentication and authorization requirement explicitly (including
   "none, by design"). verification_method: cross-reference endpoint
   list against declared authn/authz requirement per endpoint.
4. `known_vuln_dependency_free` — no newly introduced dependency
   carries a known critical/high CVE at the pinned version.
   verification_method: dependency vulnerability scan (e.g. `npm audit`
   / `pip-audit` / equivalent) on the diff's changed manifest.

**test-authoring** (source: IEEE 829-2008 + xUnit Test Patterns / Test
Smells — canonical: `roles/specs/test-authoring.spec.json`
`source_standard` field, read this turn):
1. `ieee829_case_shape` — every authored test case states its purpose,
   preconditions, inputs, and expected result (IEEE 829 test-case
   specification shape), not a bare assertion with no stated intent.
   verification_method: structural check of the test-case
   documentation/docstring against the four required fields.
2. `no_test_smell` — the authored suite is free of the Test Smells
   catalog's structural smells the spec already reuses for judgment
   (e.g. Eager Test, Mystery Guest, Interacting Tests).
   verification_method: reuses the spec's existing `gate_c_finding_method`
   smell-detection rule.
3. `coverage_of_changed_behavior` — every changed/added
   branch/condition in the code under test has at least one asserting
   test exercising it. verification_method: coverage tool run scoped
   to the diff's changed lines/branches.
4. `suite_passes_clean` — the full suite passes with no skipped test
   left unacknowledged (reuses the existing
   `role-test-claim-guard.sh` SKIPPED-line discipline as one bar
   sub-criterion). verification_method: `pytest`/equivalent run, exit
   code and SKIPPED-line count asserted.

The remaining 36 roles are not out of scope (amended requirement 5) —
their bar domain and source standard are named in §7; full
per-criterion decomposition to this same depth is phase-wise, tracked
per role, not silently dropped.

### 2. `bar-not-met` verdict class

Each of the 7 specs' `loop_state.refusal` array gains `bar-not-met`,
alongside the existing precondition-refusal state — a `bar-not-met`
verdict record additionally carries `failed_criteria: [criterion
name, ...]` (a subset of that spec's own `quality_bar` criterion
names) so the send-back names exactly which sub-criteria failed, not a
bare rejection.

### 3. Landing gate: hooks-only, default-on, target-root-anchored

`gates/quality_bar.py` (pure function, network-free, mirroring
`gates/landing_readiness.py: classify`'s shape): given a PR's changed-
file set, the set of specs whose `quality_bar` scope those files touch
("bar-scoped"), and the most recent bar-met/bar-not-met record per
bar-scoped role for that PR, returns `BAR_MET`, `BAR_NOT_MET`, or
`NO_BAR_SCOPED` (pass-through — repos/PRs with no bar-scoped change
behave as today, per the issue's acceptance "empty state").

`on-the-record/hooks/quality-bar-gate.sh` — PreToolUse on `gh pr merge`,
same shape as `merge-allow-gate.sh` (`ORCHESTRATE_OFF=1` kill switch,
CLAUDE_ROLE-empty orchestrator-only scoping, target-root resolution via
`TOKENMAXXXER_CHECKOUT`/plugin-marketplace fallback — northpole req#7:
hooks only, default-on, no CI/Actions, no explicit invocation). Unlike
`merge-allow-gate.sh` (which only ever adds an "allow"), this hook
emits a `"deny"` `hookSpecificOutput.permissionDecision` with exit code
2 when `gates/quality_bar.py` returns `BAR_NOT_MET` for any bar-scoped
role on the target PR — reusing the existing deny-wins-over-allow
composition `merge-allow-gate.sh`'s own docstring already documents
(canonical: `on-the-record/hooks/merge-allow-gate.sh` lines 1-27, read
this turn).

### 4. Anti-circularity

The bar-met/bar-not-met record's author identity (the role that wrote
`docs/issue-<n>/reports/<owning-role>.md`'s verdict) must differ from
the identity that produced the bar-scoped diff being graded.
`gates/quality_bar.py` takes both identities as explicit inputs (never
inferred from prose) and returns `BAR_NOT_MET` — same as "no record at
all" — whenever they match, so a role cannot satisfy its own gate by
writing its own passing verdict.

A same-operator bypass was found and must be closed in the design, not
left to phase 2 (after-proposal warrant hunt,
`docs/issue-1156/reports/requirements-engineering/2026-08-13-hunt-per-role-quality-bars.md`):
comparing bare `CLAUDE_ROLE` values (the way the sibling gate
`merge-allow-gate.sh` already reads producing/acting identity, per its
`os.environ.get("CLAUDE_ROLE", "")` read) is not sufficient, because
`CLAUDE_ROLE` is a self-declared, operator-controlled env var — one
operator can produce the diff under one `CLAUDE_ROLE`, then re-exec
under a second `CLAUDE_ROLE` value in the same terminal/session and
author a passing verdict, satisfying "identities differ" while being
the same actual account. `gates/quality_bar.py`'s producer/author
identity inputs must therefore each resolve through the same
account-level check the role-handoff contract's own approval gate
already performs — the two-account/single-account distinction
(`approvers.md` account resolution, the SessionStart interaction-
protocol directive) — not a bare env-var string compare: the producer
identity is the account that authored the bar-scoped commit(s) (git
author/committer identity or PR author, matching how
`pr-preflight.sh`/`approval-gate.sh` already resolve "who authored
this"), and the author identity is the account that authored the
verdict record's commit — `BAR_NOT_MET` whenever those two accounts are
the same, regardless of what `CLAUDE_ROLE` each claimed at the time.

### 5. Bounded rejection loop + escalation

`gates/quality_bar.py` also takes a `consecutive_bar_not_met_count` for
the (PR, bar-scoped-role) pair. At a fixed cap (proposed: 3 consecutive
`bar-not-met` verdicts on the same item, matching the reject-cap shape
`docs/specs/role-invariant-coverage.md` and existing gates in this repo
already use for bounded retry logic), the classifier returns
`ESCALATE` instead of `BAR_NOT_MET` on the next evaluation — the gate
hook, on `ESCALATE`, still denies the merge (escalation does not
auto-pass) but additionally instructs opening an
`docs/issue-<n>/decisions/open_decision_item-*.md` for operator
attention, per the issue body's requirement 4 and the existing
`open_decision_item`/`delegated-judgment-gate.sh` escalation pattern
(canonical: `docs/specs/northpole.md` section 5, read this turn).

### 6. Spec-schema test extension

Extend `gates/spec_schema_five_activities_test.py` (or a sibling test
module) to assert: each of the 7 landing-order-first specs carries a
non-empty `quality_bar` array of `{criterion, verification_method}`
entries and `bar-not-met` in its `loop_state.refusal`; every one of the
other 36 specs is recorded in `docs/specs/role-invariant-coverage.md`
(or this proposal's own §7) with at minimum a bar domain and source
standard named — not silently skipped and not marked "out of scope",
since amended requirement 5 puts all 43 in scope (sequencing only
differs).

### 7. Remaining 36 roles: bar domain + source standard (phase-wise decomposition)

Per the amended requirement 5, every one of the other 36 role domains
gets at minimum its bar domain and cited source standard here; full
per-criterion decomposition to §1's depth follows phase-wise in later
issues, applying the §0 principles unchanged (top-of-industry level;
non-automatable criteria become named human-review checklists, never a
lowered bar). Source standards below are each read from the role's own
`source_standard` field this turn (canonical: `roles/specs/<role>.spec.json`).

Tracking, so "phase-wise" cannot silently mean "never": phase 2 of
this issue records all 36 in `docs/specs/role-invariant-coverage.md`
with status `bar: domain-named, decomposition-pending` (not `bar-met`,
not `out-of-scope`) — the same file item 4/§6 already uses to list
scope. Until a role's own decomposition PR lands and its status flips
to a real `quality_bar`, §0 principle 4 (no self-grading) does not yet
have a `quality_bar`/`bar-not-met` field to attach to for that role,
so the anti-circularity gate is not yet enforced for it either — this
is the explicit, recorded gap for the 36, not a silent one, and
`decomposition-pending` status is what the next phase-wise PR for each
role is scoped against.

1. **architecture** — bar domain: decision-record quality and
   traceability. source: MADR (Markdown Any Decision Records),
   `adr.github.io/madr`.
2. **brand-design** — bar domain: design-token consistency and
   cross-surface visual coherence. source: DTCG Design Tokens Format,
   `designtokens.org/tr/2025.10/format`.
3. **capacity-planning** — bar domain: forecast accuracy and headroom
   discipline. source: ITIL Capacity Management practice.
4. **conformance-review** — bar domain: machine-checkable conformance
   evidence completeness. source: EARL 1.0 Schema (W3C).
5. **content-design** — bar domain: microcopy clarity and usability.
   source: GOV.UK Content Design / GDS style guide; judgment lens NN/g
   10 Usability Heuristics.
6. **customer-support** — bar domain: support-center service quality.
   source: HDI Support Center Standard + CSAT.
7. **data-engineering** — bar domain: pipeline data-quality and
   contract stability. source: dbt model contracts; judgment lens
   DAMA-DMBOK data-quality dimensions.
8. **data-modeling** — bar domain: schema correctness and grain
   discipline. source: Kimball dimensional-modeling conventions;
   judgment lens Codd's normalization rules (1NF-3NF/BCNF).
9. **defect-verification** — bar domain: reproducible incident-report
   completeness. source: ISO/IEC/IEEE 29119-3 Incident Report (clause
   7.12, Annex A.2.15) + Bugmon reproduction precedent.
10. **devrel** — bar domain: developer-relations impact measurement.
    source: Keystone DevRel metrics + DevRel-Qualified-Lead concept
    (convergent practice, no single ratified standard — stated as
    assumption per the spec's own scout-brief gap).
11. **execution-observation** — bar domain: machine-checkable
    execution-conformance evidence. source: EARL 1.0 Schema (W3C).
12. **finance-unit-economics** — bar domain: unit-economics metric
    correctness. source: SaaS unit-economics metric set (CAC, LTV,
    LTV:CAC, CAC payback, Rule of 40) — de facto convention, no single
    ratified standards body (stated as assumption per the spec's own
    scout-brief gap).
13. **growth-analytics** — bar domain: funnel-metric attribution
    soundness. source: AARRR Pirate Metrics + North Star Metric
    (original source not independently fetched — stated as assumption
    per the spec's own scout-brief gap).
14. **implementation** — bar domain: commit-message and change
    traceability. source: Conventional Commits v1.0.0.
15. **incident-response** — bar domain: postmortem completeness and
    blamelessness. source: SRE Postmortem Template (Google SRE book).
16. **issue-retrospective** — bar domain: retrospective format
    completeness and blamelessness. source: Blameless retrospective
    format (SRE lineage).
17. **knowledge-management** — bar domain: tacit-knowledge capture
    completeness. source: KCS (Knowledge-Centered Service) Solve loop;
    judgment lens SECI model.
18. **legal-compliance** — bar domain: privacy-impact assessment
    completeness. source: GDPR Article 35(7) DPIA.
19. **localization** — bar domain: translation quality and locale-data
    correctness. source: Unicode CLDR / UTS #35 (LDML); judgment lens
    MQM error typology.
20. **market-analysis** — bar domain: competitive-analysis rigor.
    source: Porter's Five Forces (HBR).
21. **marketing** — bar domain: positioning clarity and
    differentiation. source: April Dunford's positioning framework.
22. **ml-engineering** — bar domain: model documentation and
    build/no-build judgment soundness. source: Model Cards (Mitchell et
    al. 2019); judgment lens Google's Rules of ML.
23. **observability** — bar domain: instrumentation completeness across
    the three pillars. source: OpenTelemetry semantic conventions;
    judgment lens three-pillars framing (logs/metrics/traces).
24. **partnerships-bd** — bar domain: collaborative-relationship
    management discipline. source: ISO 44001:2017.
25. **pr-communications** — bar domain: PR-description and evaluation
    rigor. source: AMEC Integrated Evaluation Framework (Barcelona
    Principles); judgment lens Google eng-practices reviewer standard.
26. **pricing** — bar domain: price-sensitivity research validity.
    source: Van Westendorp Price Sensitivity Meter.
27. **product-discovery** — bar domain: opportunity-assessment rigor
    and pre-registered decision rules. source: Cagan/SVPG Opportunity
    Assessment + lean-startup pre-registered decision rules.
28. **refactoring-legacy** — bar domain: refactor justification against
    a named code smell, not stylistic preference. source: Fowler's
    Refactoring Catalog; judgment lens Fowler's code-smell catalog.
29. **release-engineering** — bar domain: changelog completeness and
    format. source: Keep a Changelog.
30. **risk-management** — bar domain: supply-chain risk assessment
    completeness. source: NIST SP 800-161r1 (C-SCRM) (NIST IR 8286
    lineage cited by secondary sources only — stated as assumption per
    the spec's own scout-brief gap).
31. **sales** — bar domain: qualification-criteria completeness.
    source: MEDDPICC.
32. **security-threat-model** — bar domain: threat-model schema
    completeness. source: STRIDE / OWASP Threat Dragon model schema.
33. **technical-feasibility** — bar domain: spike-record completeness
    and decision traceability. source: ADR-style spike record.
34. **technical-writing** — bar domain: documentation-type correctness
    (tutorial/how-to/reference/explanation). source: Diataxis.
35. **user-discovery** — bar domain: interview-saturation and
    signal-vs-noise discipline. source: Teresa Torres interview
    snapshots + Guest/Bunce/Johnson 2006 and Hennink/Kaiser/Weber 2020
    saturation run-length; judgment lens The Mom Test's three
    failure-mode filter.
36. **requirements-engineering** — bar domain: requirement
    verifiability and bidirectional traceability (this role's own
    domain, subject to the same bar it enforces on others). source:
    EARS (Mavin et al., IEEE RE'09) + ISO/IEC/IEEE 29148 bidirectional
    traceability.

## What is out of scope

- Full per-criterion decomposition (§1-depth) of the 36 roles named in
  §7 this PR — phase-1 names their domain and source standard only;
  the criteria themselves land phase-wise in later issues/PRs.
- Actually wiring the hook/gate/spec edits — phase 1 is proposal-only;
  phase 2 lands them after Approve.
- Redesigning the existing `accessibility-guard.sh`/
  `api-version-guard.sh`/`perf-measurement-guard.sh` presence-invariant
  hooks — they stay as-is; the new `quality-bar-gate.sh` is an
  additional, separate gate reading the role's own verdict record, not
  a replacement.
- CI/GitHub Actions of any kind (northpole req#7 forbids this
  regardless).

## How you will know it worked

- `python3 -m pytest gates/ -q -k spec` exits 0 once phase 2 lands the
  spec-schema extension, asserting all 7 specs carry `quality_bar` +
  `bar-not-met` and no other spec does.
- A `gates/quality_bar_test.py` unit test set exercises: bar-scoped
  change + no record → `BAR_NOT_MET`; bar-scoped change + bar-met
  record from a different role → `BAR_MET`; bar-scoped change + bar-met
  record authored by the producer role itself → `BAR_NOT_MET`
  (anti-circularity); 3rd consecutive `bar-not-met` on the same item →
  `ESCALATE`; no bar-scoped change → `NO_BAR_SCOPED` (pass-through).
- `on-the-record/hooks/test_quality_bar_gate.py` exercises the hook's
  deny-on-`BAR_NOT_MET`/`ESCALATE` and no-op-on-`BAR_MET`/
  `NO_BAR_SCOPED` behavior, target-root-anchored (no repo-specific
  hardcoding), matching the acceptance criteria's three `check:` items
  verbatim.

## Accumulation

This proposal is decomposition-shaped, not accumulation-cost-shaped —
it adds one new field per spec and one new gate script; it does not
add a per-PR or per-item recurring cost that grows with repo size
beyond what `merge-allow-gate.sh`'s existing per-PR classifier call
already costs. No accumulation-cost content applies.

## What did not work

None.
