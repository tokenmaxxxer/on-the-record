# keep-role classification precision: 20-sample verify (issue #1750)

Phase-2 delivery for issue #1750, implementing the approved proposal
`docs/issue-1750/proposals/keep-role-precision-sample.md` (approved via
`APPROVE issue-1750/implementation`). Measures classification precision on
the 307 `keep-role` rows from `docs/reports/rulebook-hook-audit.md` (issue
#1746) by re-judging 20 of them against their FULL fetched script bodies,
not the header-comment excerpt the original audit used.

## Selection rule

Every 15th row among the 307 `keep-role` rows, counted in report order
(1-indexed among keep-role rows only, not among all 314 table rows),
starting at index 1: `1 + 15*i` for `i = 0..19`, giving indices
`1, 16, 31, 46, 61, 76, 91, 106, 121, 136, 151, 166, 181, 196, 211, 226,
241, 256, 271, 286`. No hand-picking.

derived:
```
$ awk -F'|' '$0 ~ /\| keep-role \|/ && $6 !~ /^[[:space:]]*$/ {print NR"\t"$2"\t"$3}' docs/reports/rulebook-hook-audit.md | wc -l
307
```
(confirms 307 keep-role data rows exist to sample from, matching the
audit's own summary count.)

## Sample table

Each row: original class (from the audit), the hook's identity (repo /
plugin / file), the re-judged class from the fetched full script body, and
a one-line reason. Every script was fetched live via `gh api
repos/tokenmaxxxer/<repo>-rulebook/contents/<path>` (base64-decoded), not
read from the audit's header excerpt.

| # | audit line | repo/plugin | file | original class | re-judged class | reason |
|---|---|---|---|---|---|---|
| 1 | 103 | accessibility-rulebook / accessibility | hooks/directive.sh | keep-role | keep-role | Thin `core_role_directive` stub — mechanism is core (issue #66), the four YOU_DECIDE/USE_WHEN/PRODUCES/HAND-OFF strings are accessibility-specific (WCAG-EM 5-step fields). |
| 2 | 133 | brand-design-rulebook / brand-design-guide-and-spec | hooks/methodology-gate.sh | keep-role | keep-role | Domain-parameterized gate on `docs/issue-<n>/reports/brand-design.md`: checks for a brand-guide-entry (logo usage/typography/voice-tone/imagery/do's-don'ts labels) and an asset-spec (hex/rgb color or file-format token) — brand-design-specific content on a shared `gate-lib.sh` mechanism. |
| 3 | 158 | conformance-review-rulebook / review | hooks/state.sh | keep-role | keep-role | SessionStart informational hook; reads git branch + checks which `docs/issue-<n>/reports/review*.md` files exist and emits a review-phase context string naming this rulebook's own plugin set (`review-traceability`, `review-severity`, etc.) — role-specific content, never blocks. |
| 4 | 184 | customer-support-rulebook / customer-support-evidence-metric | hooks/evidence-metric-gate.sh | keep-role | keep-role | Domain-parameterized gate requiring at least one of CSAT/FCR/SLA-adherence cited on customer-support handbook/record writes — customer-support-specific metric vocabulary on the shared `gate-lib.sh` mechanism. |
| 5 | 204 | data-engineering-rulebook / failure-handling-gate | hooks/failure-handling-gate.sh | keep-role | keep-role | Thin bash entrypoint (fail-closed trap + kill switch) that execs a Python payload holding the actual failure-handling-methodology checks — mechanism from `gate-lib.sh`, the checked content is data-engineering's own failure-handling methodology. |
| 6 | 234 | devrel-rulebook / diataxis-record | hooks/record-fields-devrel-gate.sh | keep-role | keep-role | Domain-parameterized gate requiring `doc-type` (tutorial/how-to/reference/explanation), an Adoption-friction list, `segment`, and (for tutorial/how-to) `time-to-first-success` on the devrel record — devrel-specific Diataxis fields on the shared mechanism. |
| 7 | 259 | finance-unit-economics-rulebook / finance-unit-economics | hooks/directive.sh | keep-role | keep-role | Thin `core_role_directive` stub; PRODUCES field lists CAC/LTV/LTV:CAC/CAC-payback — finance-unit-economics-specific content. |
| 8 | 295 | incident-response-rulebook / incident-response-proposal-evidence-gate | hooks/evidence-gate.sh | keep-role | keep-role | Gate requires 4 elements (survey ref, scout-brief ref or skip, adopt/skip list, rationale tying an adopted item to "장애 후 무엇을 배웠고 재발을 무엇으로 막을 것인가") in incident-response phase-1 proposals — the survey/scout-ref checks overlap contract-wide ordering, but the 3rd/4th elements (adopt/skip list, incident-response's own decision-boundary rationale) are genuinely domain content the gate actually enforces alongside them, so this is not a pure restatement of the contract-wide ordering norm the way #9/#10 below are. |
| 9 | 315 | interaction-design-rulebook / interaction-design/plugins/id-stage-order | hooks/stage-order-gate.sh | keep-role | **promote** | Re-read in full: the gate enforces ONLY file-existence ordering — survey.md exists before a new proposal, a proposal exists before the phase-2 record — with zero interaction-design-domain content checked anywhere in the script. This is exactly the role-handoff-contract v3 s19 survey-before-proposal / phase-1-before-phase-2 ordering, stated role-agnostically, the same pattern the original audit itself flagged as `promote` for `implementation-rulebook`'s `survey-order-gate.sh` (audit Methodology bullet 3) — the header-comment-only method missed this because it never read past the header comment to see the check body has no domain content. |
| 10 | 335 | issue-retrospective-rulebook / proposal-order-gate | hooks/proposal-order-gate.sh | keep-role | **promote** | Re-read in full: the gate reads the subject's own phase-1 proposal off disk and denies the phase-2 record write unless the proposal names a survey path and either a scout-brief path or an explicit scout-skip, citing "Per contract v3 s19" and "the platform scout directive" directly in its own deny messages — again zero issue-retrospective-domain content, purely the contract-wide phase/survey/scout ordering norm. Same misclassification pattern as #9. |
| 11 | 365 | localization-rulebook / localization/plugins/mqm-tagging | hooks/directive.sh | keep-role | keep-role | SessionStart directive requiring MQM's 8 top-level categories (Accuracy/Fluency/Terminology/Locale convention/Style/Verity/Design/Internationalization) tag each string-external issue — localization-specific methodology content, informational only (no gate script). |
| 12 | 385 | market-analysis-rulebook / market-analysis/plugins/mece-proposal | hooks/directive.sh | keep-role | keep-role | Thin `core_role_directive` stub; PRODUCES field lists market-analysis's own 3 frameworks (industry attractiveness / competitive positioning / customer-need fit) — market-analysis-specific content. |
| 13 | 415 | observability-rulebook / observability-cardinality-budget | hooks/cardinality-budget-gate.sh | keep-role | keep-role | Domain-parameterized gate requiring a cardinality mention on phase-1/phase-2 writes and, when high-cardinality dimensions are named, a co-located handling policy — observability-cardinality-specific content on the shared mechanism. |
| 14 | 435 | partnerships-bd-rulebook / batna-zopa | hooks/batna-zopa-gate.sh | keep-role | keep-role | Domain-parameterized gate requiring a substantive BATNA mention and a co-located ZOPA mention (paragraph-proximity checked) — partnerships-bd-specific negotiation-methodology content. |
| 15 | 460 | pr-communications-rulebook / key-message-tiers | hooks/directive.sh | keep-role | keep-role | Phase-2-only directive stating the 1-core/N-supporting/proof-point key-message-tier structure — pr-communications-specific content, paired with its own domain gate (`key-message-gate.sh`, not sampled here). |
| 16 | 480 | pricing-rulebook / pricing/plugins/pricing-verdict-report | hooks/report-gate.sh | keep-role | keep-role | Gate enforcing the 3 required pricing-verdict deliverable fields (per `roles/specs/pricing.spec.json`, issue #19) via a pricing-specific shared helper (`pricing-fields.py`) — pricing-domain content. |
| 17 | 505 | refactoring-legacy-rulebook / refactoring-steps | hooks/methodology-gate.sh | keep-role | keep-role | Gate enforcing Fowler's refactoring-catalog step-name heading + applied-step-sequence field on the phase-2 record, and blocking `src/**` structural edits until `characterization_tests_path` is recorded — refactoring-legacy-specific methodology content. |
| 18 | 535 | risk-management-rulebook / risk-management | hooks/directive.sh | keep-role | keep-role | `core_role_directive` stub whose PRODUCES payload is risk-management's own ISO 31000:2018 ERM-verdict 5-stage shape and 12-field risk-register schema (with an explicitly noted phase1-proposal-norms passage that restates contract-wide survey/phase-gate norms as background context, not as this hook's own checked content) — the bulk of the payload is genuinely risk-management-domain (ISO 31000), and per the audit's own rule 1 every `directive.sh` is classified by "content is role-unique," which the ISO 31000 payload satisfies; agreeing with the original call. |
| 19 | 565 | security-threat-model-rulebook / security-threat-model-canon-citation | hooks/methodology-gate.sh | keep-role | keep-role | Gate scoped to the `canon-references` record field: when present, requires a `docs/`-relative path per cited technique (no bare technique names, no vendored copies) — security-threat-model-canon-citation-specific content. |
| 20 | 585 | technical-feasibility-rulebook / nygard-adr-spine | hooks/spine-gate.sh | keep-role | keep-role | Gate enforcing Nygard's minimal ADR spine (Title/Status/Context/Decision/Consequences) plus a Risks-disposition field on the phase-2 record's own write surface — technical-feasibility(ADR)-specific methodology content. |

## Precision and re-judged class distribution

Agreement: 18 of 20 samples re-judged to the same class the audit assigned.
Disagreements: #9 (`interaction-design/id-stage-order`) and #10
(`issue-retrospective/proposal-order-gate`), both re-judged `keep-role` ->
`promote`.

```
precision = agreed / 20 = 18 / 20 = 0.90 = 90%
```

Re-judged class distribution across the 20 samples: `keep-role`: 18,
`promote`: 2, `retire`: 0.

## Conclusion

**Computed precision: 18/20 = 90%.**

90% >= the 80% threshold stated in the issue's Acceptance criterion 2, so
the **>=80% branch is triggered: the keep-role figure (307) stands**, and
phase 4 must design a carrier for role-specific hooks, per the issue's
stated branch language.

Caveat carried forward for whoever designs phase 3/4, not acted on here
(out of scope per the approved proposal): the 2 disagreements found here
are not random noise — both are the *same* pattern (a `*-gate.sh` that
enforces only the contract-wide survey/scout/phase ordering norm with zero
domain content, misclassified `keep-role` because the header-comment-only
method never read the check body). If that specific pattern recurs
elsewhere in the 307, a targeted grep for ordering-only gates (rather than
a full re-audit) may be worth phase 3 considering — but that judgment call
belongs to phase 3, not this report.
