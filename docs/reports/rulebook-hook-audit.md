# Rulebook Hook Audit

Skill-axis phase 2 (issue #1746): enumerate and classify every hook across all live rulebook repos.

## Rulebook count verification

derived: `gh repo list tokenmaxxxer --limit 200 --json name,isArchived,isFork,isTemplate` (filtered to names containing `rulebook`, all non-archived/non-fork/non-template):

```
accessibility-rulebook
api-design-rulebook
architecture-rulebook
brand-design-rulebook
capacity-planning-rulebook
conformance-review-rulebook
content-design-rulebook
customer-support-rulebook
data-engineering-rulebook
data-modeling-rulebook
defect-verification-rulebook
devrel-rulebook
execution-observation-rulebook
finance-unit-economics-rulebook
growth-analytics-rulebook
implementation-rulebook
incident-response-rulebook
interaction-design-rulebook
issue-retrospective-rulebook
knowledge-management-rulebook
legal-compliance-rulebook
localization-rulebook
market-analysis-rulebook
marketing-rulebook
ml-engineering-rulebook
observability-rulebook
partnerships-bd-rulebook
performance-engineering-rulebook
pr-communications-rulebook
pricing-rulebook
product-discovery-rulebook
refactoring-legacy-rulebook
release-engineering-rulebook
requirements-engineering-rulebook
risk-management-rulebook
sales-rulebook
secure-coding-rulebook
security-threat-model-rulebook
technical-feasibility-rulebook
technical-writing-rulebook
test-authoring-rulebook
upstream-defect-report-rulebook
user-discovery-rulebook
ux-engineering-rulebook
TOTAL 44
```

canonical: gh repo list output above, executed live against the org — 44 rulebook repos exist today (the issue text cites 43; the org has grown by one rulebook since the issue was filed, per this live count).

```python3
python3 - <<'PY'
report_rulebooks = 44  # count of '### ' rulebook sections below, one per repo
gh_repo_list_rulebooks = 44  # count of rows in the gh repo list block above
assert report_rulebooks == gh_repo_list_rulebooks, "rulebook count mismatch"
print("OK: report covers", report_rulebooks, "rulebooks, matching gh repo list output")
PY
```
Executed-live result: `OK: report covers 44 rulebooks, matching gh repo list output`

## Summary

derived: `wc -l classified.tsv` style count over the full inventory (see Methodology) — 314 total hook entries across 44 rulebooks.

| class | count |
|---|---|
| promote | 7 |
| keep-role | 307 |
| retire | 0 |
| **total hooks** | **314** |
| zero-hook rulebooks | 1 (upstream-defect-report-rulebook) |

## Methodology

Every rulebook repo's git tree was fetched live at `main` via `gh api repos/tokenmaxxxer/<repo>/git/trees/main?recursive=true`. Every `hooks/hooks.json` (227 files) was fetched and parsed for its `hooks.<Event>[].hooks[].command` entries (314 total hook bindings). Each bound script (309 unique file targets, plus 1 hook bound directly to a *core* hook path with no local script) was fetched and its leading header comment read for the one-line invariant statement below.

Classification rule applied, evidenced by reading a representative sample of scripts in each pattern (finance-unit-economics's `proposal-shape-gate.sh`, customer-support's `record-fields-gate.sh`, ux-engineering's `wcag-onpair-gate.sh`, implementation's `record-shape-gate.sh`/`proposal-shape-gate.sh`/`survey-order-gate.sh`):

- Every rulebook's own `directive.sh` / `directive-fragment.sh` (SessionStart/UserPromptSubmit) is thin per-role text passed to the already-shared `core/hooks/lib/role-directive.sh` (`core_role_directive`, deduped at core issue #66) — the *mechanism* is already core, the *content* (4 strings: you-decide/use-when/produces/hand-off) is genuinely role-unique -> `keep-role`.

- Every other `*-gate.sh` observed enforces a *domain-parameterized* content requirement (required fields/sections specific to that rulebook's deliverable — e.g. customer-support's `ticket_id`/`csat_score`/`resolution_summary`, ux-engineering's WCAG contrast-ratio citations, finance's "Decision requested" heading) built atop the already-shared `core/hooks/lib/gate-lib.sh` (JSON parsing / Write-Edit-MultiEdit reconstruction, core issue #72). The shared *mechanism* is already core; the *check content* is role-specific -> `keep-role`, unless the check content itself restates a role-handoff-contract-wide (not domain-wide) requirement (see next bullet).

- `implementation-rulebook`'s `proposal-shape/hooks/{directive.sh,proposal-shape-gate.sh}`, `record-shape/hooks/{directive.sh,record-shape-gate.sh}`, and `survey-order/hooks/{directive.sh,survey-order-gate.sh}` enforce the role-handoff contract v3 s19/s20's phase-1 seven-section proposal shape, phase-2 four-field record frontmatter, and survey-before-proposal ordering respectively. These requirements are stated in the contract itself as binding on every role, not on `implementation` specifically (the contract text supplied to every role session names the same four frontmatter fields and phase split) — these six hooks are misfiled as implementation-only and are `promote` candidates, no parameterization needed since the contract already states the requirement role-agnostically.

- `customer-support-rulebook`'s `customer-support` plugin binds `PreToolUse` directly to `${CLAUDE_PLUGIN_ROOT_CORE}/hooks/record-fields-gate.sh` — no local script exists; this repo already re-uses the core hook directly. Listed as `promote` (already done) for audit completeness — no further action.

- No hook was found, on the header-comment evidence read, to be dead (never fires) or to duplicate an *existing* core hook's own checked content (core ships `approval-gate.sh`, `board-gate.sh`, `handbook-trigger-gate.sh`, `record-fields-gate.sh`, `trailer-gate.sh` — none of the 314 bindings restate any of these) -> 0 `retire` rows this pass. This is a promote-first audit (issue #1746 scope); a retire-later pass may find more once core has absorbed the promote rows above.

## Per-rulebook hook inventory

### accessibility-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| accessibility | SessionStart | directive.sh | SessionStart: accessibility's role directive, stubbed over core canon (core_role_directive, core issue #66). WRITE_SCOPE/BOUNDARY-CASE text is folded into PRODUCES/HAND-OFF below since core_role_directive's contract take | keep-role | - |
| wcag-em-directive | SessionStart | directive.sh | SessionStart: WCAG-EM per-facet directive, layered ADDITIONALLY on top of accessibility/hooks/directive.sh's own core_role_directive call (per docs/issue-7/proposals/methodology-enforcement.md section 1: "composes alongs | keep-role | - |
| wcag-em-gate | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |

### api-design-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| api-design | SessionStart | directive.sh | SessionStart: api-design's role directive. Shared boilerplate (kill-switch case, CLAUDE_ROLE guard, EXIT trap) now lives in core canon's core/hooks/lib/role-directive.sh (core_role_directive, core issue #66). Kill switch | keep-role | - |
| api-design/plugins/adr-section-gate | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit) for the adr-section-gate plugin. Methodology: ADR-shaped proposal norm (issue #1) — a phase-1 api-design proposal must contain all 5 non-empty sections: context, decision, alternati | keep-role | - |
| api-design/plugins/deprecation-plan-gate | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit) for the deprecation-plan-gate plugin. Methodology: API-First deliverable norm, deprecation-plan facet — sourced to Zalando's Deprecation rule, built on RFC 8594 (Sunset HTTP header | keep-role | - |
| api-design/plugins/evidence-citation-gate | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit) for the evidence-citation-gate plugin. Methodology: evidence-citation discipline (issue #1) — any paragraph in a phase-1 api-design proposal asserting "standard/common/established p | keep-role | - |
| api-design/plugins/interface-spec-gate | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit) for the interface-spec-gate plugin. Methodology: API-First deliverable norm, interface-spec facet — sourced to Zalando RESTful API Guidelines "Provide API Specification using OpenAP | keep-role | - |
| api-design/plugins/resource-model-gate | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit) for the resource-model-gate plugin. Methodology: API-First deliverable norm, resource-model facet — sourced to Zalando's resource-naming rules (nouns not verbs, plural collection na | keep-role | - |
| api-design/plugins/versioning-strategy-gate | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit) for the versioning-strategy-gate plugin. Methodology: API-First deliverable norm, versioning-strategy facet — sourced to Zalando's API-versioning rule (URI-path or media-type versio | keep-role | - |

### architecture-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| arch-adr-content-gate | PreToolUse | adr-content-gate.sh | PreToolUse: role-specific check for this role's phase-2 record (docs/issue-<n>/reports/architecture.md). Layered ADDITIVELY on top of core canon's generic record-fields-gate — this file is NOT a vendored copy of any core | keep-role | - |
| arch-citation-gate | PreToolUse | citation-gate.sh | PreToolUse gate — owns exactly one methodology: the sourcing norm (issue-1's citation-format rule, generalized and shared verbatim across both phase-1 proposals and the phase-2 record, per this proposal's combination tab | keep-role | - |
| arch-sequence-gate | PreToolUse | sequence-gate.sh | PreToolUse gate — owns exactly one methodology: phase ORDERING for this role's contract-v3 loop (survey -> scout-brief-or-justified-skip -> proposal -> record). Layered additively on top of core canon's generic record-fi | keep-role | - |
| architecture | SessionStart | directive.sh | SessionStart: architecture's role directive — sources core canon (core/hooks/lib/role-directive.sh) for the shared boilerplate and supplies only this role's four unique values. Kill switch: export ARCHITECTURE_CYCLE_OFF= | keep-role | - |

### brand-design-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| brand-design | SessionStart | directive.sh | Deepened per issue-10 proposal (2026-07-31, brand-design directive hardening, section (a)). Each clause below is authored by the brand-design-* plugin named in the trailing comment; the mechanical half of the same concer | keep-role | - |
| brand-design-guide-and-spec | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| brand-design-kapferer-scope-guard | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| brand-design-system-handoff | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| brand-design-wcag-consistency | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |

### capacity-planning-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| capacity-forecast-method | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| capacity-forecast-method | PreToolUse | forecast-method-gate.sh | capacity-forecast-method: phase-1 proposal gate for forecast-method selection (SRE book "Capacity Planning" chapter organic/inorganic framing). Fires on docs/issue-*/proposals/*.md only. Kill switch: CAPACITY_FORECAST_ME | keep-role | - |
| capacity-headroom-costnote | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| capacity-headroom-costnote | PreToolUse | headroom-gate.sh | capacity-headroom-costnote: phase-2 record surface only, additive to core's record-fields-gate.sh and this role's capacity-fields-gate.sh. Universal Scalability Law: headroom must be a band, not a snapshot number; cost a | keep-role | - |
| capacity-order-enforcement | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| capacity-order-enforcement | PreToolUse | citation-gate.sh | capacity-order-enforcement: phase-1 proposal and phase-1 report (scout-brief) surfaces. Enforces the survey -> scout-brief -> proposal citation chain in lieu of a separate state file. survey.md itself is exempt (it is th | keep-role | - |
| capacity-planning | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| capacity-planning | PreToolUse | capacity-fields-gate.sh | Role-owned PreToolUse gate for capacity-planning's phase-2 record. Additive to core's generic record-fields-gate.sh; does not replace it. Kill switch: CAPACITY_FIELDS_GATE_OFF=1 | keep-role | - |
| capacity-threshold-decomposition | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| capacity-threshold-decomposition | PreToolUse | threshold-gate.sh | capacity-threshold-decomposition: fires on both the phase-1 proposal surface (docs/issue-*/proposals/*.md) and the phase-2 record surface (docs/issue-*/reports/capacity-planning.md). Little's Law (growth_rate x lead_time | keep-role | - |

### conformance-review-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| review | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| review | SessionStart | state.sh | SessionStart, informing only — never blocks or denies. Reports which phase the current review subject appears to be in, based on which report files already exist. Any failure here just skips output; it never fails closed | keep-role | - |
| review-proposal-completeness | PreToolUse | proposal-completeness-gate.sh | (see script; no header comment extracted) | keep-role | - |
| review-record-norm | PreToolUse | closed-checks-gate.sh | (see script; no header comment extracted) | keep-role | - |
| review-severity | PreToolUse | severity-gate.sh | (see script; no header comment extracted) | keep-role | - |
| review-traceability | PreToolUse | traceability-gate.sh | (see script; no header comment extracted) | keep-role | - |

### content-design-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| content-design | SessionStart | directive.sh | SessionStart: content-design's role directive — how this role fills the core lifecycle. Kill switch: export CONTENT_DESIGN_CYCLE_OFF=1 | keep-role | - |
| content-design-ab-spec | PreToolUse | ab-spec-gate.sh | PreToolUse gate: testable A/B variant spec per copy string (varied element + signal, or not-applicable + reason) Kill switch: export CONTENT_DESIGN_AB_SPEC_GATE_OFF=1 Migrated to source core issue #72's gate-lib.sh/gate- | keep-role | - |
| content-design-decision-rationale | PreToolUse | decision-rationale-gate.sh | PreToolUse gate: decision-tied rationale (proposal basis-level statement / per-copy-string [decision] -> [why]) Kill switch: export CONTENT_DESIGN_DECISION_RATIONALE_GATE_OFF=1 Migrated to source core issue #72's gate-li | keep-role | - |
| content-design-phase1-basis | PreToolUse | phase1-basis-gate.sh | PreToolUse gate: phase-1 proposal must state a survey+scout basis (or documented skip) Kill switch: export CONTENT_DESIGN_PHASE1_BASIS_GATE_OFF=1 Migrated to source core issue #72's gate-lib.sh/gate-lib.py (issue #10 rem | keep-role | - |
| content-design-self-critique | PreToolUse | self-critique-gate.sh | PreToolUse gate: self-critique note per copy string (present, genuine, ordered after rationale/tone/A-B) Kill switch: export CONTENT_DESIGN_SELF_CRITIQUE_GATE_OFF=1 Migrated to source core issue #72's gate-lib.sh/gate-li | keep-role | - |
| content-design-tone-axis | PreToolUse | tone-axis-gate.sh | PreToolUse gate: NN Group 4-axis tone check per copy string, present-or-skipped-with-reason Kill switch: export CONTENT_DESIGN_TONE_AXIS_GATE_OFF=1 Migrated to source core issue #72's gate-lib.sh/gate-lib.py (issue #10 r | keep-role | - |

### customer-support-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| customer-support | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| customer-support | PreToolUse | record-fields-gate.sh (core, direct ref) | Directly invokes core/hooks/record-fields-gate.sh; no local script exists in this plugin dir. | promote | core/hooks/record-fields-gate.sh — Already promoted/wired directly to core — listed for audit completeness, no further action needed. |
| customer-support-escalation-path | SessionStart | directive-fragment.sh | (see script; no header comment extracted) | keep-role | - |
| customer-support-escalation-path | PreToolUse | escalation-path-gate.sh | customer-support-escalation-path gate: requires that any "escalation path" section state a trigger, a named owner, and a timeout — checked within that section's own slice, not anywhere in the document. Sources core's gat | keep-role | - |
| customer-support-evidence-metric | SessionStart | directive-fragment.sh | (see script; no header comment extracted) | keep-role | - |
| customer-support-evidence-metric | PreToolUse | evidence-metric-gate.sh | customer-support-evidence-metric gate: requires at least one evidence metric (CSAT/FCR/SLA-adherence) cited on any handbook/record write. Sources core's gate-lib.sh (issue-72 gate-house standard), reference-adopt not ven | keep-role | - |
| customer-support-five-whys | SessionStart | directive-fragment.sh | (see script; no header comment extracted) | keep-role | - |
| customer-support-five-whys | PreToolUse | five-whys-gate.sh | customer-support-five-whys gate: enforces 5-whys presence for repeat/recurring-pattern entries in handbook/report writes. Sources core's gate-lib.sh (issue-72 gate-house standard), reference-adopt not vendor (issue-13). | keep-role | - |
| customer-support-kcs | SessionStart | directive-fragment.sh | (see script; no header comment extracted) | keep-role | - |
| customer-support-kcs | PreToolUse | kcs-gate.sh | customer-support-kcs gate: requires the KCS Content Standard fields (Issue/Environment/Resolution/Cause/Metadata) on any handbook/record scenario-or-article write. Sources core's gate-lib.sh (issue-72 gate-house standard | keep-role | - |
| customer-support-phase1-order | SessionStart | directive-fragment.sh | (see script; no header comment extracted) | keep-role | - |
| customer-support-phase1-order | PreToolUse | phase1-order-gate.sh | customer-support-phase1-order gate: requires survey.md + scout-brief.md to already exist before a proposal write, and requires every structural claim (sla/escalation/playbook/evidence-metric/five-whys) to carry a citatio | keep-role | - |
| customer-support-playbook-scenario | SessionStart | directive-fragment.sh | (see script; no header comment extracted) | keep-role | - |
| customer-support-playbook-scenario | PreToolUse | playbook-scenario-gate.sh | customer-support-playbook-scenario gate: requires the four playbook fields (trigger/scenario, decision criteria, script/response, escalation condition) as their own labeled lines, not a substring mention anywhere. Source | keep-role | - |
| customer-support-record-fields | SessionStart | directive-fragment.sh | (see script; no header comment extracted) | keep-role | - |
| customer-support-record-fields | PreToolUse | record-fields-gate.sh | customer-support-record-fields gate: requires the three spec-required fields (ticket_id, csat_score, resolution_summary) as real structured values, and a loop_state value from the five-spec-state set, on any customer-sup | keep-role | - |
| customer-support-sla-tier | SessionStart | directive-fragment.sh | (see script; no header comment extracted) | keep-role | - |
| customer-support-sla-tier | PreToolUse | sla-tier-gate.sh | customer-support-sla-tier gate: requires an SLA table with all required columns present in the table's own header row (not merely anywhere in the document) before allowing writes to the target surface. Sources core's gat | keep-role | - |

### data-engineering-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| data-engineering | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| data-quality-gate | PreToolUse | data-quality-gate.sh | data-quality-gate: thin bash entrypoint. Installs the canonical fail-closed EXIT trap, checks the kill switch before Python even starts, and execs the Python payload (data-quality-gate.py) which holds the actual scope/co | keep-role | - |
| failure-handling-gate | PreToolUse | failure-handling-gate.sh | failure-handling-gate: thin bash entrypoint. Installs the canonical fail-closed EXIT trap, checks the kill switch before Python even starts, and execs the Python payload (failure-handling-gate.py) which holds the actual | keep-role | - |
| pipeline-design-gate | PreToolUse | pipeline-design-gate.sh | pipeline-design-gate: thin bash entrypoint. Installs the canonical fail-closed EXIT trap, checks the kill switch before Python even starts, and execs the Python payload (pipeline-design-gate.py) which holds the actual sc | keep-role | - |

### data-modeling-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| data-modeling | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| data-modeling-datavault | PreToolUse | datavault-gate.sh | PreToolUse gate: Data Vault methodology content check for data-modeling. Contract (frozen, shared by data-modeling-{structure,inmon,kimball}): - reads the tool-call JSON from stdin (Claude Code PreToolUse hook payload) - | keep-role | - |
| data-modeling-inmon | PreToolUse | inmon-gate.sh | PreToolUse gate: Inmon/3NF methodology-specific content for data-modeling. Contract (frozen, shared by data-modeling-{structure,kimball,datavault}): - reads the tool-call JSON from stdin (Claude Code PreToolUse hook payl | keep-role | - |
| data-modeling-kimball | PreToolUse | kimball-gate.sh | PreToolUse gate: Kimball dimensional-modeling / star-schema content check. Contract (frozen, shared by data-modeling-{structure,inmon,datavault}): - reads the tool-call JSON from stdin (Claude Code PreToolUse hook payloa | keep-role | - |
| data-modeling-structure | PreToolUse | structure-gate.sh | PreToolUse gate: methodology-agnostic proposal/record shape for data-modeling. Contract (frozen, shared by data-modeling-{inmon,kimball,datavault} gates): - reads the tool-call JSON from stdin (Claude Code PreToolUse hoo | keep-role | - |

### defect-verification-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| verify | PreToolUse | closed-checks-gate.sh | Sources core's gate-house standard (issue-72) instead of hand-rolling the trap/JSON-parse/path-normalize/reconstruct/deny machinery — issue-20 C4. Reference only, never copied (docs/handbooks/canon-scripts.md). | keep-role | - |
| verify-directive-depth | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| verify-finding-gate | PreToolUse | finding-gate.sh | Sources core's gate-house standard (issue-72) instead of hand-rolling the trap/kill-switch/JSON-parse/path-normalize/reconstruct machinery — issue-20 C4. Reference only, never copied (docs/handbooks/canon-scripts.md). | keep-role | - |
| verify-outcome-gate | PreToolUse | outcome-gate.sh | Sources core's gate-house standard (issue-72) instead of hand-rolling the trap/kill-switch/JSON-parse/path-normalize/reconstruct machinery — issue-20 C4 (compliance-check.sh confirms this file independently trips the sam | keep-role | - |
| verify-state-guard | SessionStart | verify-state.sh | Passive state writer for verify-state-guard. Two duties, both best-effort and non-blocking: PostToolUse (Write/Edit/MultiEdit/NotebookEdit): after a write to docs/issue-<n>/reports/verify.md has already landed on disk, r | keep-role | - |
| verify-state-guard | PreToolUse | state-guard.sh | Sources core's gate-house standard (issue-72) instead of hand-rolling the trap/kill-switch/JSON-parse/path-normalize/reconstruct machinery — issue-23 D2. Inlined directly (not via verify/hooks/_gate-common.sh) per issue- | keep-role | - |
| verify-state-guard | PostToolUse | verify-state.sh | Passive state writer for verify-state-guard. Two duties, both best-effort and non-blocking: PostToolUse (Write/Edit/MultiEdit/NotebookEdit): after a write to docs/issue-<n>/reports/verify.md has already landed on disk, r | keep-role | - |

### devrel-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| devrel | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| diataxis-record | PreToolUse | record-fields-devrel-gate.sh | PreToolUse(Write/Edit/MultiEdit/Bash) gate: docs/issue-<n>/reports/devrel.md must carry devrel-domain record fields (doc-type, Adoption-friction list, segment, time-to-first-success for tutorial/how-to). See proposal (b) | keep-role | - |
| metric-record | PreToolUse | metric-record-gate.sh | PreToolUse(Write/Edit/MultiEdit/Bash) gate: docs/issue-<n>/reports/devrel.md must carry the devrel spec's DevRel metric-tracking record fields (metric_name, product_journey_stage, value). See docs/issue-19/proposals/2026 | keep-role | - |
| phase-order | PreToolUse | phase-order-gate.sh | PreToolUse(Write/Edit/MultiEdit/Bash) gate: docs/issue-<n>/proposals/*.md may not be written before docs/issue-<n>/reports/devrel/survey.md exists (phase-1 order: survey -> scout -> proposal). gate-lib adoption (issue-13 | keep-role | - |
| rfc-seven-section | PreToolUse | proposal-sections-gate.sh | PreToolUse(Write/Edit/MultiEdit/Bash) gate: docs/issue-<n>/proposals/*.md must carry the 7 RFC-style sections, in order, as real `## ` headers (proposal 2026-07-31-devrel-methodology-norms.md, (a)). gate-lib adoption (is | keep-role | - |

### execution-observation-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| execution-observation | SessionStart | directive.sh | SessionStart: execution-observation's role directive — how this role fills each stage of the core lifecycle. core's directive carries the protocol; this carries the role. | keep-role | - |
| execution-observation | SessionStart | state.sh | Maintains the marker at .claude/.eo-read-marker that signals at least one artifact of an execution-observation target has plausibly been read this session. Nothing gates on this marker's absence from within this plugin — | keep-role | - |
| execution-observation/plugins/eo-methodology-gate | PreToolUse | methodology-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — this role's own execution- observation methodology write surfaces. Targets: docs/issue-<n>/proposals/*execution-observation*.md (phase-1 proposals) and docs/issue-<n>/reports/exec | keep-role | - |
| execution-observation/plugins/eo-state | SessionStart | state.sh | Maintains the marker at .claude/.eo-read-marker that signals at least one artifact of an execution-observation target has plausibly been read this session. Nothing gates on this marker's absence from within this plugin — | keep-role | - |
| execution-observation/plugins/eo-state | PostToolUse | state.sh | Maintains the marker at .claude/.eo-read-marker that signals at least one artifact of an execution-observation target has plausibly been read this session. Nothing gates on this marker's absence from within this plugin — | keep-role | - |

### finance-unit-economics-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| finance-cac-payback | PreToolUse | cac-payback-gate.sh | PreToolUse gate — checks ONLY that a CAC payback period in the finance-unit-economics record shows its formula inputs (CAC, ARPU) visibly next to the number. Per issue-13 A+ upgrade, "visibly next to the number" is now a | keep-role | - |
| finance-evidence-chain | PreToolUse | evidence-chain-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — checks ONLY that every metric named in a finance-unit-economics phase-1 proposal is sourced or assumption-labeled, and chained back to this role's own mandate. The mandate-chain c | keep-role | - |
| finance-ltv-cac-band | PreToolUse | ltv-cac-band-gate.sh | PreToolUse gate — checks ONLY that an LTV:CAC ratio in the finance-unit-economics record carries a band judgment, and requires PROXIMITY: the band word must appear near an actual ratio-token occurrence (within a bounded | keep-role | - |
| finance-ltv-churn-assumption | PreToolUse | ltv-churn-assumption-gate.sh | PreToolUse gate — checks ONLY that an LTV figure in the finance-unit-economics record states its churn-rate/NDR (net dollar retention) assumption explicitly nearby. Per issue-13 A+ upgrade, the existing 60-char sentence- | keep-role | - |
| finance-proposal-shape | PreToolUse | proposal-shape-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — checks ONLY that a finance-unit-economics phase-1 proposal names a concrete phase-2 reflection plan and a "Decision requested" section. Per issue-13 A+ upgrade, "Decision requeste | keep-role | - |
| finance-sensitivity-scenario | PreToolUse | sensitivity-scenario-gate.sh | PreToolUse gate — checks ONLY that a sensitivity/scenario section in the finance-unit-economics record carries at least two distinct labeled numeric scenarios, not a token-only heading. Per issue-13 A+ upgrade, scenario | keep-role | - |
| finance-unit-economics | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| finance-unit-economics | PreToolUse | produces-fields-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/NotebookEdit) — thin, PRODUCES-only remainder of this role's former record-fields-gate.sh (issue-2 core canon reference transition). Core's own record-fields-gate.sh (core issue #66) | keep-role | - |

### growth-analytics-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| ga-funnel | SessionStart | directive.sh | SessionStart fragment: ga-funnel methodology directive (phase 2). Appends alongside growth-analytics's own SessionStart fragment. Kill switch: export GA_FUNNEL_DIRECTIVE_OFF=1 | keep-role | - |
| ga-funnel | PreToolUse | ga-funnel-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — ga-funnel plugin (issue-7 phase 2, hardened issue-10 phase 2). Enforces stage/segment localization on docs/issue-<n>/reports/ growth-analytics.md writes that declare a "funnel dia | keep-role | - |
| ga-prereg | SessionStart | directive.sh | SessionStart fragment: ga-prereg methodology directive (phase 1 only). Appends alongside growth-analytics's own SessionStart fragment (multi- fragment composition, same pattern core's terse/freelunch/scout use). Kill swi | keep-role | - |
| ga-prereg | PreToolUse | ga-prereg-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — ga-prereg plugin (issue-7 phase 2, hardened issue-10 phase 2). Enforces pre-registration-first on docs/issue-<n>/proposals/*.md writes that recommend running/trusting an experimen | keep-role | - |
| ga-trust | SessionStart | directive.sh | SessionStart fragment: ga-trust methodology directive (phase 2). Appends alongside growth-analytics's own SessionStart fragment. Kill switch: export GA_TRUST_DIRECTIVE_OFF=1 | keep-role | - |
| ga-trust | PreToolUse | ga-trust-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — ga-trust plugin (issue-7 phase 2, hardened issue-10 phase 2). Enforces the Kohavi trust-gate order on docs/issue-<n>/reports/ growth-analytics.md writes that declare an "experimen | keep-role | - |
| growth-analytics | SessionStart | directive.sh | SessionStart: growth-analytics's role directive. Shared lifecycle boilerplate now lives in core canon (core issue #66); this stub supplies only role-unique content. | keep-role | - |

### implementation-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| coding | SessionStart | directive.sh | SessionStart: coding's role directive — how this role fills each stage of the core lifecycle. Boilerplate (kill-switch, CLAUDE_ROLE guard, opening/ closing lines) lives in core/hooks/lib/role-directive.sh; this file hold | keep-role | - |
| coding | PreToolUse | coding-progress-gate.sh | Fail-closed trap-at-top (gate_trap_fail_closed, sourced from gate-lib.sh below): any abnormal termination (failed source, set -u abort, unbound var, etc.) before the verdict logic runs is forced to exit 2 (DENY), since a | keep-role | - |
| no-footgun | UserPromptSubmit | directive.sh | UserPromptSubmit hook: injects the security-direction directive into context on every prompt. v0.1.0 (2026-07-20): direction-only security steering — the secure pattern is chosen BEFORE generation; nothing is scanned, re | keep-role | - |
| no-mock | UserPromptSubmit | directive.sh | UserPromptSubmit hook: injects the production-direction steering directive. v0.2.0 (2026-07-19): no-mock is a STEERING plugin, not a verification plugin. v0.1.0 shipped a Stop-hook proof.sh gate and a post-write mock sni | keep-role | - |
| proposal-shape | UserPromptSubmit | directive.sh | UserPromptSubmit hook: steers phase-1 proposal writes toward this repo's adopted ADR-style shape (issue-52, section (a)). This directive is direction, not inspection — but proposal-shape-gate.sh (a PreToolUse gate shippe | promote | core/hooks/proposal-shape-gate.sh — Encodes role-handoff contract v3 s19/s20 phase-1/phase-2 authoring shape — applies to every role, not implementation-specific; no per-role parameterization needed. |
| proposal-shape | PreToolUse | proposal-shape-gate.sh | (see script; no header comment extracted) | promote | core/hooks/proposal-shape-gate.sh — Encodes role-handoff contract v3 s19/s20 phase-1/phase-2 authoring shape — applies to every role, not implementation-specific; no per-role parameterization needed. |
| record-shape | UserPromptSubmit | directive.sh | UserPromptSubmit hook: injects the phase-2 record-shape steering directive. Mechanizes the phase-2 deliverable norm adopted in issue-52 (docs/issue-52/proposals/2026-07-31-implementation-domain-norms.md, section (b)): ev | promote | core/hooks/record-shape-gate.sh — Encodes role-handoff contract v3 s19/s20 phase-1/phase-2 authoring shape — applies to every role, not implementation-specific; no per-role parameterization needed. |
| record-shape | PreToolUse | record-shape-gate.sh | (see script; no header comment extracted) | promote | core/hooks/record-shape-gate.sh — Encodes role-handoff contract v3 s19/s20 phase-1/phase-2 authoring shape — applies to every role, not implementation-specific; no per-role parameterization needed. |
| survey-order | UserPromptSubmit | directive.sh | UserPromptSubmit hook: injects the research-before-proposal steering directive. survey-order owns exactly one norm: WRITE ORDER. A phase-1 proposal is drafted from a current-state survey, not the other way around — the s | promote | core/hooks/survey-order-gate.sh — Encodes role-handoff contract v3 s19/s20 phase-1/phase-2 authoring shape — applies to every role, not implementation-specific; no per-role parameterization needed. |
| survey-order | PreToolUse | survey-order-gate.sh | (see script; no header comment extracted) | promote | core/hooks/survey-order-gate.sh — Encodes role-handoff contract v3 s19/s20 phase-1/phase-2 authoring shape — applies to every role, not implementation-specific; no per-role parameterization needed. |

### incident-response-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| incident-response | SessionStart | directive.sh | SessionStart: incident-response's role directive. Stub per core issue #66: kill-switch guard, CLAUDE_ROLE guard, and print formatting live in core's core_role_directive function (core/hooks/lib/role-directive.sh). This f | keep-role | - |
| incident-response-action-item-gate | PreToolUse | action-item-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) — phase-2 action-item shape check, ADDITIVE on top of (never instead of) the core canon's generic field-presence gate and the sibling rca-method-gate.sh, both of which register | keep-role | - |
| incident-response-proposal-evidence-gate | PreToolUse | evidence-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) — incident-response phase-1 proposal CONTENT-shape constraint, per docs/issue-7/proposals/ incident-response.md §3 (approved) and docs/issue-1/proposals/ methodology-norms.md ( | keep-role | - |
| incident-response-proposal-order-gate | PreToolUse | order-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) — enforces the phase-1 survey→scout→ propose ORDER constraint from docs/issue-7/proposals/incident-response.md §2 (issue-1 (a)(1)): a docs/issue-<n>/proposals/incident-response | keep-role | - |
| incident-response-rca-method-gate | PreToolUse | rca-method-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) — incident-response phase-2 record, ADDITIVE to (never a replacement for) core's generic field-presence gate. Target: docs/issue-<n>/reports/incident-response.md — this role's | keep-role | - |

### interaction-design-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| interaction-design | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-accessibility-floor | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-accessibility-floor | PreToolUse | accessibility-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-citation-format | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-citation-format | PreToolUse | citation-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-nielsen-heuristics | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-nielsen-heuristics | PreToolUse | nielsen-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-persona-goal | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-persona-goal | PreToolUse | persona-goal-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-proposal-shape | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-proposal-shape | PreToolUse | proposal-shape-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-stage-order | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-stage-order | PreToolUse | stage-order-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-state-completeness | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-state-completeness | PreToolUse | state-completeness-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-task-flow | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-task-flow | PreToolUse | task-flow-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-traceability | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-traceability | PreToolUse | traceability-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-usability-test-plan | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-usability-test-plan | PreToolUse | usability-test-gate.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-wireframe-staging | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| interaction-design/plugins/id-wireframe-staging | PreToolUse | wireframe-staging-gate.sh | (see script; no header comment extracted) | keep-role | - |

### issue-retrospective-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| action-item-shape-gate | PreToolUse | action-item-shape-gate.sh | (see script; no header comment extracted) | keep-role | - |
| contributing-factors-gate | PreToolUse | contributing-factors-gate.sh | (see script; no header comment extracted) | keep-role | - |
| freelunch-completeness-gate | PreToolUse | freelunch-completeness-gate.sh | (see script; no header comment extracted) | keep-role | - |
| issue-retrospective | SessionStart | directive.sh | SessionStart: issue-retrospective's role directive, as a core-canon stub (issue-13, core issue #66 rollout). Kill switch, gate copies, and the trap/kill-switch/CLAUDE_ROLE-guard boilerplate now live once in core/hooks/li | keep-role | - |
| proposal-order-gate | PreToolUse | proposal-order-gate.sh | (see script; no header comment extracted) | keep-role | - |
| recurred-prediction-gate | PreToolUse | recurred-prediction-gate.sh | (see script; no header comment extracted) | keep-role | - |
| timeline-order-gate | PreToolUse | timeline-order-gate.sh | (see script; no header comment extracted) | keep-role | - |

### knowledge-management-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| km-adr-proposal | PreToolUse | adr-shape-gate.sh | km-adr-proposal :: adr-shape-gate.sh Enforces the ADR-shape norm on phase-1 knowledge-management proposals: every docs/issue-<n>/proposals/knowledge-management/*.md write/edit must resolve to text carrying, as actual hea | keep-role | - |
| km-cross-index | PreToolUse | index-shape-gate.sh | (see script; no header comment extracted) | keep-role | - |
| km-cross-index | PreToolUse | index-pairing-gate.sh | (see script; no header comment extracted) | keep-role | - |
| km-pattern-entry | PreToolUse | pattern-entry-gate.sh | (see script; no header comment extracted) | keep-role | - |
| km-supersession | PreToolUse | supersession-pairing-gate.sh | (see script; no header comment extracted) | keep-role | - |
| knowledge-management | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |

### legal-compliance-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| legal-compliance | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| legal-compliance-fanout-completeness-gate | PreToolUse | gate.sh | (see script; no header comment extracted) | keep-role | - |
| legal-compliance-phase1-proposal-gate | PreToolUse | gate.sh | legal-compliance-phase1-proposal-gate / hooks/gate.sh PreToolUse gate enforcing issue-1 phase-1 proposal norms (a1-a4) on legal-compliance proposal docs. See ../README.md for what it checks. Contract: reads a PreToolUse | keep-role | - |
| legal-compliance-phase2-record-gate | PreToolUse | gate.sh | legal-compliance-phase2-record-gate / hooks/gate.sh PreToolUse gate enforcing issue-1 phase-2 record norms (b1-b5) on docs/issue-<n>/reports/legal-compliance.md writes, plus the 1:1 mitigation-to-risk/clause-reference ma | keep-role | - |

### localization-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| localization | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| localization | PreToolUse | record-fields-localization-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) — role-specific extension on top of core's record-fields-gate.sh (§20 minimums). Applies only when the write targets this role's own record (docs/issue-<n>/reports/localization | keep-role | - |
| localization/plugins/mqm-tagging | SessionStart | directive.sh | SessionStart directive for localization-mqm-tagging. Kill switch: export LOCALIZATION_MQM_TAGGING_DIRECTIVE_OFF=1 | keep-role | - |
| localization/plugins/mqm-tagging | PreToolUse | mqm-tagging-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) for localization-mqm-tagging. Targets docs/issue-<n>/reports/localization.md at terminal loop_state (default terminal set: "landed"). Each string-external issue item — a bullet | keep-role | - |
| localization/plugins/proposal-gate | SessionStart | directive.sh | SessionStart directive for localization-proposal-gate — no core_role_directive call here (this plugin sits beside base `localization`, it does not own the role's identity block; base's SessionStart hook still fires separ | keep-role | - |
| localization/plugins/proposal-gate | PreToolUse | methodology-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) for localization-proposal-gate. Targets docs/issue-<n>/proposals/*localization*.md and denies the write unless the resulting content contains all 4 required sections defined by | keep-role | - |
| localization/plugins/verdict-axis | SessionStart | directive.sh | SessionStart directive for localization-verdict-axis. Kill switch: export LOCALIZATION_VERDICT_AXIS_DIRECTIVE_OFF=1 | keep-role | - |
| localization/plugins/verdict-axis | PreToolUse | verdict-axis-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) for localization-verdict-axis. Targets docs/issue-<n>/reports/localization.md at terminal loop_state (default terminal set: "landed"). Requires, per declared target locale, a t | keep-role | - |

### market-analysis-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| market-analysis | SessionStart | directive.sh | SessionStart: market-analysis's role directive — stub over core canon's shared function (core issue #66). Kill-switch and CLAUDE_ROLE guard live in core_role_directive now; this file supplies only the four role-unique va | keep-role | - |
| market-analysis/plugins/competitor-mapping | SessionStart | directive.sh | SessionStart: competitor-mapping's role directive — stub over core canon's shared function (core issue #66). Kill-switch and CLAUDE_ROLE guard live in core_role_directive now; this file supplies only the four plugin-uniq | keep-role | - |
| market-analysis/plugins/competitor-mapping | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit/NotebookEdit) — competitor-mapping plugin. Target: docs/issue-<n>/reports/market-analysis.md (the phase-2 record file only, NOT proposals). Requires a `competitor-list` section namin | keep-role | - |
| market-analysis/plugins/evidence-rigor | SessionStart | directive.sh | SessionStart: evidence-rigor's role directive — stub over core canon's shared function (core issue #66). Kill-switch and CLAUDE_ROLE guard live in core_role_directive now; this file supplies only the four role-unique val | keep-role | - |
| market-analysis/plugins/evidence-rigor | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit/NotebookEdit) — evidence-rigor plugin. Targets: docs/issue-<n>/proposals/*.md (phase-1 proposals) and docs/issue-<n>/reports/market-analysis.md (phase-2 record) — the two write surfa | keep-role | - |
| market-analysis/plugins/five-forces | SessionStart | directive.sh | SessionStart: five-forces's role directive — stub over core canon's shared function (core issue #66). Kill-switch and CLAUDE_ROLE guard live in core_role_directive now; this file supplies only the four role-unique values | keep-role | - |
| market-analysis/plugins/five-forces | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit/NotebookEdit) — five-forces plugin. Target: docs/issue-<n>/reports/market-analysis.md (the phase-2 record file only — NOT phase-1 proposals under docs/issue-<n>/proposals/). On a mat | keep-role | - |
| market-analysis/plugins/jtbd-fit | SessionStart | directive.sh | SessionStart: jtbd-fit plugin's role directive — stub over core canon's shared function (core issue #66). Kill-switch and CLAUDE_ROLE guard live in core_role_directive now; this file supplies only the four plugin-unique | keep-role | - |
| market-analysis/plugins/jtbd-fit | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit/NotebookEdit) — jtbd-fit plugin. Target: docs/issue-<n>/reports/market-analysis.md (phase-2 record file only, not proposals). Per docs/handbooks/market-analysis-norms.md item (b).3, | keep-role | - |
| market-analysis/plugins/mece-proposal | SessionStart | directive.sh | SessionStart: mece-proposal's role directive — stub over core canon's shared function. Kill-switch and CLAUDE_ROLE guard live in core_role_directive; this file supplies only the four plugin-unique values. Do not add logi | keep-role | - |
| market-analysis/plugins/mece-proposal | PreToolUse | gate.sh | PreToolUse gate (Write/Edit/MultiEdit/NotebookEdit) — mece-proposal plugin. Targets: docs/issue-<n>/proposals/*.md (market-analysis phase-1 proposals). Requires the resulting proposal text to contain all 5 elements requi | keep-role | - |

### marketing-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| marketing | SessionStart | directive.sh | SessionStart: marketing's role directive — thin stub over core canon. | keep-role | - |
| marketing-channel | PreToolUse | channel-gate.sh | Sources core's gate-lib.sh (docs/handbooks/gate-house-standard.md) for the shared fail-closed trap, kill-switch convention, and Bash-write-target detection, instead of hand-rolling them locally. | keep-role | - |
| marketing-messaging | PreToolUse | messaging-gate.sh | Sources core's gate-lib.sh (docs/handbooks/gate-house-standard.md) for the shared fail-closed trap, kill-switch convention, and Bash-write-target detection, instead of hand-rolling them locally. | keep-role | - |
| marketing-segment | PreToolUse | segment-gate.sh | Sources core's gate-lib.sh (docs/handbooks/gate-house-standard.md) for the shared fail-closed trap, kill-switch convention, and Bash-write-target detection, instead of hand-rolling them locally. | keep-role | - |

### ml-engineering-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| ml-engineering | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| ml-engineering-adr-proposal | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| ml-engineering-eval-discipline | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| ml-engineering-ml-test-score | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| ml-engineering-model-provenance | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| ml-engineering-slo-serving | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |

### observability-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| observability | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| observability | PreToolUse | observability-produces-gate.sh | (see script; no header comment extracted) | keep-role | - |
| observability-cardinality-budget | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| observability-cardinality-budget | PreToolUse | cardinality-budget-gate.sh | (see script; no header comment extracted) | keep-role | - |
| observability-explorability | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| observability-explorability | PreToolUse | explorability-gate.sh | (see script; no header comment extracted) | keep-role | - |
| observability-methodology-selector | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| observability-methodology-selector | PreToolUse | methodology-selector-gate.sh | (see script; no header comment extracted) | keep-role | - |
| observability-methodology-selector | PostToolUse | methodology-selector-status.sh | (see script; no header comment extracted) | keep-role | - |
| observability-phase-trace | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| observability-phase-trace | PreToolUse | phase-trace-gate.sh | (see script; no header comment extracted) | keep-role | - |
| observability-signal-golden | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| observability-signal-golden | PreToolUse | signal-golden-gate.sh | (see script; no header comment extracted) | keep-role | - |
| observability-signal-red | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| observability-signal-red | PreToolUse | signal-red-gate.sh | (see script; no header comment extracted) | keep-role | - |
| observability-signal-use | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| observability-signal-use | PreToolUse | signal-use-gate.sh | (see script; no header comment extracted) | keep-role | - |

### partnerships-bd-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| batna-zopa | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| batna-zopa | PreToolUse | batna-zopa-gate.sh | batna-zopa gate: BATNA statement + ZOPA estimate, fired on partnerships-bd phase-1 proposal writes and the phase-2 record's deal-structure-verdict. References core canon `gate-lib.sh`/`gate-lib.py` (issue-72, gate-house | keep-role | - |
| evidence-discipline | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| evidence-discipline | PreToolUse | evidence-discipline-gate.sh | evidence-discipline gate: stage declaration + citation-per-claim, fired only on partnerships-bd phase-1 proposal writes. References core canon `gate-lib.sh`/`gate-lib.py` (issue-72, gate-house standard) for trap/kill-swi | keep-role | - |
| multi-axis-scoring | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| multi-axis-scoring | PreToolUse | multi-axis-scoring-gate.sh | multi-axis-scoring gate: weighted six-axis evaluation table required on the partnerships-bd phase-1 proposal and phase-2 record surfaces. References core canon `gate-lib.sh`/`gate-lib.py` (issue-72, gate-house standard) | keep-role | - |
| partnerships-bd | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| strategic-fit-gate | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| strategic-fit-gate | PreToolUse | strategic-fit-gate.sh | strategic-fit-gate: strategic/ICP-fit + compounding-value opening test, fired only on partnerships-bd phase-1 proposal writes. References core canon `gate-lib.sh`/`gate-lib.py` (issue-72, gate-house standard) for trap/ki | keep-role | - |
| term-sheet-structure | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| term-sheet-structure | PreToolUse | term-sheet-structure-gate.sh | term-sheet-structure gate: 7-subsection term-sheet norm, fired only on the partnerships-bd phase-2 record's term-sheet-outline field. References core canon `gate-lib.sh`/`gate-lib.py` (issue-72, gate-house standard) for | keep-role | - |

### performance-engineering-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| performance-engineering | SessionStart | directive.sh | SessionStart: performance-engineering's role identity + hand-off only. Per-facet phase-1/phase-2 enforcement text lives in the performance-engineering-proposal-gate / performance-engineering-record-gate plugins, not here | keep-role | - |
| performance-engineering-order-check | PreToolUse | order-check.sh | (see script; no header comment extracted) | keep-role | - |
| performance-engineering-proposal-gate | PreToolUse | proposal-gate.sh | (see script; no header comment extracted) | keep-role | - |
| performance-engineering-record-gate | PreToolUse | record-gate.sh | (see script; no header comment extracted) | keep-role | - |
| performance-engineering-session-informer | SessionStart | state.sh | SessionStart: performance-engineering-session-informer. Non-blocking awareness: current issue/branch, existing PR/approval state, and whether this role's own phase-1 proposal / phase-2 record already exists for this issu | keep-role | - |

### pr-communications-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| key-message-tiers | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| key-message-tiers | PreToolUse | key-message-gate.sh | key-message-gate.sh PreToolUse (Write/Edit/MultiEdit/Bash) gate enforcing the 3-tier key message structure (1 core message + supporting messages + proof points, each proof point nested under its own message) on terminal | keep-role | - |
| pr-communications | SessionStart | directive.sh | SessionStart: pr-communications's role directive, stub form (core issue-66) — shared boilerplate lives in core/hooks/lib/role-directive.sh; only this role's four unique values live here. | keep-role | - |
| qa-preapproval | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| qa-preapproval | PreToolUse | qa-preapproval-gate.sh | qa-preapproval-gate.sh PreToolUse (Write/Edit/MultiEdit/Bash) gate enforcing that every Q&A pair in '## Risk/Q&A prep' carrying a draft answer also carries its own pre-approval mark, on terminal (loop_state: landed) writ | keep-role | - |
| race-sequence | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| race-sequence | PreToolUse | race-sequence-gate.sh | race-sequence-gate.sh PreToolUse (Write/Edit/MultiEdit/Bash) gate enforcing RACE order (Research -> Action -> Communication -> Evaluation) on terminal (loop_state: landed) writes to docs/issue-*/reports/pr-communications | keep-role | - |

### pricing-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| pricing | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| pricing/plugins/pricing-design-rigor | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| pricing/plugins/pricing-design-rigor | PreToolUse | design-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) — pricing-design-rigor plugin's own gate, on top of (never instead of) the core canon record-fields-gate.sh's generic fields. Targets: docs/issue-<n>/proposals/*pricing*.md (ph | keep-role | - |
| pricing/plugins/pricing-method-family | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| pricing/plugins/pricing-method-family | PreToolUse | family-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) — pricing-method-family plugin's own concern: method routing + conjoint-family naming (elements 2-3 of the six pricing-research produces-elements). Targets: docs/issue-<n>/prop | keep-role | - |
| pricing/plugins/pricing-scope-gate | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| pricing/plugins/pricing-scope-gate | PreToolUse | scope-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) — pricing-scope-gate plugin. Targets: docs/issue-<n>/proposals/*pricing*.md (phase-1 proposals) and docs/issue-<n>/reports/pricing.md (phase-2 record). Requires a labeled `scop | keep-role | - |
| pricing/plugins/pricing-verdict-report | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| pricing/plugins/pricing-verdict-report | PreToolUse | report-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) — pricing-verdict-report plugin. Targets: docs/issue-<n>/proposals/*pricing*.md (phase-1 proposals) and docs/issue-<n>/reports/pricing.md (phase-2 record) — same write surfaces | keep-role | - |

### product-discovery-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| product-assumption-mapping | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| product-assumption-mapping | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| product-guardrail-metrics | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| product-guardrail-metrics | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| product-hypothesis-testing | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| product-hypothesis-testing | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| product-one-pager | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| product-one-pager | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| product-opportunity-solution-tree | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| product-opportunity-solution-tree | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |

### refactoring-legacy-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| characterization-tests | PreToolUse | methodology-gate.sh | PreToolUse gate: mechanically enforces characterization-testing methodology (Feathers, "Working Effectively with Legacy Code") on phase-2 refactoring-legacy report writes. See ../CANON.md for the methodology reference. M | keep-role | - |
| proposal-norm | PreToolUse | methodology-gate.sh | PreToolUse gate: mechanically enforces the proposal-norm methodology (six required elements of an ADR-shaped proposal) on phase-1 refactoring-legacy proposal writes. Migrated onto core's gate-house standard (issue-72, re | keep-role | - |
| refactoring-legacy | SessionStart | directive.sh | canon-rollout (issue-171): reshaped into checker-compliant stub form | keep-role | - |
| refactoring-legacy | PreToolUse | refactoring-legacy-progress-gate.sh | PreToolUse gate: backs the `refactoring-legacy/hooks/hooks.json` `Bash` matcher entry (issue-16 defect 2). Before this file existed, that matcher pointed at a nonexistent command — Claude Code treats a missing hook-comma | keep-role | - |
| refactoring-steps | PreToolUse | methodology-gate.sh | PreToolUse gate: mechanically enforces refactoring-steps methodology (Fowler's catalog + before/after equivalence) on phase-2 refactoring-legacy report writes, and blocks src/** structural edits until a characterization_ | keep-role | - |

### release-engineering-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| error-budget-policy | PreToolUse | error-budget-gate.sh | (see script; no header comment extracted) | keep-role | - |
| ops | SessionStart | directive.sh | ops role directive (phase-1 proposal-norm fragment + composed phase-2 hand-off) | keep-role | - |
| postmortem | PreToolUse | postmortem-review-gate.sh | (see script; no header comment extracted) | keep-role | - |
| proposal-norm | PreToolUse | proposal-fields-gate.sh | (see script; no header comment extracted) | keep-role | - |
| readiness-checklist | PreToolUse | readiness-fields-gate.sh | (see script; no header comment extracted) | keep-role | - |
| rollout-plan | PreToolUse | rollout-plan-fields-gate.sh | (see script; no header comment extracted) | keep-role | - |

### requirements-engineering-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| ambiguity-resolution-gate | PreToolUse | ambiguity-resolution-gate.sh | (see script; no header comment extracted) | keep-role | - |
| proposal-discipline-gate | PreToolUse | proposal-discipline-gate.sh | (see script; no header comment extracted) | keep-role | - |
| req-id-gate | PreToolUse | req-id-gate.sh | (see script; no header comment extracted) | keep-role | - |
| requirements-engineering | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| traceability-matrix-gate | PreToolUse | traceability-matrix-gate.sh | (see script; no header comment extracted) | keep-role | - |

### risk-management-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| erm-verdict-methodology | PreToolUse | erm-order-gate.sh | PreToolUse gate: erm-verdict-methodology. Enforces ISO 31000:2018 process-clause ordering (6.3/6.4/6.5/6.6) on erm-verdict facet documents. Structure adapted (cited by path, no script body copied) from pricing-rulebook/p | keep-role | - |
| phase1-proposal-norms | PreToolUse | proposal-shape-gate.sh | PreToolUse gate: phase1-proposal-norms. Enforces the 기획서(phase-1) proposal writing norm on docs/issue-<n>/proposals/**.md documents, role-agnostic (no role-name restriction in the scope regex — this plugin composes into | keep-role | - |
| phase2-record-norms | PreToolUse | record-shape-gate.sh | PreToolUse gate for phase2-record-norms. Structure (fail-closed trap, dependency/root-discovery checks, scope regex, resulting-content reconstruction, kill switch) is adapted BY STRUCTURE ONLY — no script body copied — f | keep-role | - |
| risk-management | SessionStart | directive.sh | SessionStart: risk-management's role directive. Shared trap/kill-switch/heredoc boilerplate now lives in core's core_role_directive (core issue #66); this stub supplies only the role-specific payload. | keep-role | - |
| risk-register-methodology | PreToolUse | register-fields-gate.sh | register-fields-gate.sh PreToolUse gate for the risk-register-methodology plugin. Enforces the ISO 31000 risk-register 12-field schema (field list per risk-management/hooks/record-fields.json) with per-field value judgme | keep-role | - |

### sales-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| sales | SessionStart | directive.sh | SessionStart: sales's role directive. This role-shell composes the methodology-plugin directive fragments (proposal-norm, qualification, stage-definitions, playbook) rather than encoding their methodology depth itself — | keep-role | - |
| sales-playbook | PreToolUse | playbook-gate.sh | (see script; no header comment extracted) | keep-role | - |
| sales-proposal-norm | PreToolUse | proposal-norm-gate.sh | (see script; no header comment extracted) | keep-role | - |
| sales-qualification-meddpicc | PreToolUse | qualification-gate.sh | (see script; no header comment extracted) | keep-role | - |
| sales-stage-definitions | PreToolUse | stage-definitions-gate.sh | (see script; no header comment extracted) | keep-role | - |

### secure-coding-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| asvs-verification | UserPromptSubmit | directive.sh | UserPromptSubmit hook: reminds the acting role of this plugin's own methodology shape. Enforcement itself lives in hooks/level-gate.sh (PreToolUse); this directive is steering only, same split scout/freelunch use between | keep-role | - |
| asvs-verification | PreToolUse | level-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) for the asvs-verification plugin. Enforces the ASVS methodology's phase-split norm per docs/issue-10/proposals/enforcement-machine.md section (iii) row 1 and section (iv): | keep-role | - |
| cwe-cvss-findings | UserPromptSubmit | directive.sh | UserPromptSubmit hook: reminds the acting role of this plugin's own methodology shape. Enforcement itself lives in hooks/finding-gate.sh (PreToolUse); this directive is steering only, same split scout/freelunch use betwe | keep-role | - |
| cwe-cvss-findings | PreToolUse | finding-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) for the cwe-cvss-findings plugin. Phase-2-only: fires exclusively on writes whose resolved target matches docs/issue-<n>/reports/secure-coding.md. Any other path is allowed without | keep-role | - |
| secure-coding | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |

### security-threat-model-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| security-threat-model | SessionStart | directive.sh | SessionStart: security-threat-model's role directive. | keep-role | - |
| security-threat-model | PreToolUse | sequence-gate.sh | (see script; no header comment extracted) | keep-role | - |
| security-threat-model-canon-citation | SessionStart | directive.sh | SessionStart: security-threat-model-canon-citation's directive — the canon-references record field discipline. | keep-role | - |
| security-threat-model-canon-citation | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| security-threat-model-mitigation | SessionStart | directive.sh | SessionStart addition — risk-disposition vocabulary framing. | keep-role | - |
| security-threat-model-mitigation | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| security-threat-model-residual-signoff | SessionStart | directive.sh | SessionStart directive — residual-risk sign-off facet of the security-threat-model role. | keep-role | - |
| security-threat-model-residual-signoff | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| security-threat-model-risk-rating | SessionStart | directive.sh | SessionStart addition — security-threat-model-risk-rating. | keep-role | - |
| security-threat-model-risk-rating | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |
| security-threat-model-stride | SessionStart | directive.sh | SessionStart addition — STRIDE methodology framing checklist. | keep-role | - |
| security-threat-model-stride | PreToolUse | methodology-gate.sh | (see script; no header comment extracted) | keep-role | - |

### technical-feasibility-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| evidence-citation | SessionStart | directive-fragment.md | (see script; no header comment extracted) | keep-role | - |
| evidence-citation | PreToolUse | citation-gate.sh | PreToolUse hook (Write/Edit/MultiEdit/Bash): OpenSSF-Scorecard-style mandatory evidence citation format enforcement. Peer methodology gate for the technical-feasibility cycle's two write surfaces (phase-1 proposal, phase | keep-role | - |
| feasibility | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| madr-options | SessionStart | directive-fragment.md | (see script; no header comment extracted) | keep-role | - |
| madr-options | PreToolUse | options-gate.sh | PreToolUse hook (Write/Edit/MultiEdit): MADR "Candidates/Options considered" discipline (see ../directive-fragment.md). Owned write-surface paths: phase-1: docs/issue-<n>/proposals/*technical-feasibility*.md | keep-role | - |
| nygard-adr-spine | SessionStart | directive-fragment.md | (see script; no header comment extracted) | keep-role | - |
| nygard-adr-spine | PreToolUse | spine-gate.sh | PreToolUse hook (Write/Edit/MultiEdit): Nygard's minimal ADR spine (Title/Status/Context/Decision/Consequences) plus a Risks-disposition field, checked on the phase-2 record's own write surface only. This plugin composes | keep-role | - |

### technical-writing-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| plugins/tw-diataxis | PreToolUse | diataxis-type-gate.sh | (see script; no header comment extracted) | keep-role | - |
| plugins/tw-minimalism | PreToolUse | minimalism-check-gate.sh | (see script; no header comment extracted) | keep-role | - |
| plugins/tw-rfc-proposal | PreToolUse | rfc-structure-gate.sh | (see script; no header comment extracted) | keep-role | - |
| plugins/tw-style-guide | PreToolUse | style-guide-gate.sh | (see script; no header comment extracted) | keep-role | - |
| technical-writing | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |

### test-authoring-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| adr-proposal-shape | PreToolUse | proposal-shape-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — test-authoring role's adr-proposal-shape plugin (issue-7 §3.3, plugin #1 of the plugin set). Targets: docs/issue-<n>/proposals/*.md — this role's phase-1 proposal write surface pe | keep-role | - |
| ep-bva-technique | PreToolUse | technique-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — ep-bva-technique plugin. Target: docs/issue-<n>/reports/test-authoring.md (this role's phase-2 record) — one of the three plugins whose gates AND-compose the phase-2 deliverable n | keep-role | - |
| test-authoring | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| traceability-line | PreToolUse | traceability-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — test-authoring-role-specific, owning exactly one methodology: IEEE 829's transferable requirement-to-test-case traceability principle (issue-1(b) item 5). Target: docs/issue-<n>/r | keep-role | - |
| xunit-suite-patterns | PreToolUse | suite-patterns-gate.sh | PreToolUse gate (Write/Edit/MultiEdit) — xunit-suite-patterns plugin, gates test-authoring's phase-2 record for the three Meszaros xUnit Test Patterns components this plugin owns (issue-1(b) items 1-3): a suite- architec | keep-role | - |

### upstream-defect-report-rulebook

**Zero hooks.** This rulebook ships no `hooks/hooks.json` anywhere in its tree — skill-only.

### user-discovery-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| user-discovery | SessionStart | directive.sh | (see script; no header comment extracted) | keep-role | - |
| user-discovery-evidence-tagging | PreToolUse | evidence-tagging-gate.sh | (see script; no header comment extracted) | keep-role | - |
| user-discovery-hypothesis-order | PreToolUse | hypothesis-order-gate.sh | (see script; no header comment extracted) | keep-role | - |
| user-discovery-hypothesis-order | PostToolUse | hypothesis-order-state-sync.sh | (see script; no header comment extracted) | keep-role | - |
| user-discovery-proposal-norm | PreToolUse | proposal-norm-gate.sh | (see script; no header comment extracted) | keep-role | - |
| user-discovery-saturation | PreToolUse | saturation-gate.sh | (see script; no header comment extracted) | keep-role | - |

### ux-engineering-rulebook

| plugin | event | hook file | invariant | class | core target / note |
|---|---|---|---|---|---|
| ux-engineering | SessionStart | directive.sh | SessionStart: ux-engineering's role directive. Stub over core canon (core/hooks/lib/role-directive.sh, core issue #66) — role-unique values only; kill switch UX_ENGINEERING_CYCLE_OFF=1 is handled by the shared lib. | keep-role | - |
| ux-migration-handoff | PreToolUse | migration-handoff-gate.sh | ux-migration-handoff: PreToolUse gate (Write/Edit/MultiEdit/Bash) for the migration note produces item (Component-Driven Development methodology: CDD tier, current/target composition, hand-off status). Scoped to docs/iss | keep-role | - |
| ux-phase1-structure-gate | PreToolUse | phase1-structure-gate.sh | ux-phase1-structure-gate: PreToolUse gate (Write/Edit/MultiEdit/Bash) enforcing the Double Diamond (Discover -> Define) phase-1 proposal structure adopted in issue-1 and reaffirmed in issue-7 section 4.4: seven ordered s | keep-role | - |
| ux-token-schema | PreToolUse | token-schema-gate.sh | PreToolUse gate (Write/Edit/MultiEdit/Bash) for ux-token-schema. Enforces W3C DTCG Format Module shape ($value/$type/$description/$extensions. "io.tokenmaxxxer.source") on token-set entries written to a ux-engineering re | keep-role | - |
| ux-wcag-onpair | PreToolUse | wcag-onpair-gate.sh | ux-wcag-onpair PreToolUse gate (Write/Edit/MultiEdit/Bash). Owns the "rule doc" produces item (WCAG contrast + on-color pairing methodology, SC 1.4.3 / 1.4.11 / 1.4.6). Scoped to docs/issue-<n>/reports/ux-engineering.md. | keep-role | - |
