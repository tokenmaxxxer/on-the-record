kind: report
subject: issue-1199
doc-type: reference

# accessibility — issue #1199 scout brief

canonical: this turn's tool transcript — four WebSearch calls dispatched
in one message (automated-scanner, screen-reader-share, design-stage-
checker, guided-assessment-tool queries)
Stages used: 1 sweep (4 parallel WebSearch angles), 0 deepening rounds.
Judge point 1: strong cross-angle agreement — each result names a
category-leading, multi-source-evidenced tool/dataset, matching the
domain's real practitioner tool categories (automated scan, AT
testing, design-stage check, guided manual assessment). Judge point 2:
another round would not change any build decision — the four gaps
named in `docs/issue-1199/reports/accessibility/current-state-survey.md`
(committed this session, 3376b6e) already map 1:1 to a sweep angle —
so deepening stopped after the sweep. Mode: parallel (four WebSearch
calls dispatched in one turn).

## Sweep angle 1 — automated scanning (axe-core / Lighthouse / Pa11y / WAVE)

canonical: WebSearch "axe-core vs Pa11y vs Lighthouse accessibility
testing adoption market share 2026", this turn's tool transcript
axe-core has been downloaded 4 billion+ times and powers Lighthouse,
Pa11y, and most other scanners under the hood, spanning 13M+ GitHub
projects — the de facto engine underneath the whole automated-scan
category, not one competing product among several. The tools' own
stated ceiling: free automated tools (axe-core, Lighthouse, Pa11y)
plateau at about 57% of issues by volume; 94.8% of the top one million
homepages still fail basic WCAG checks despite this tooling's
ubiquity. Design-move takeaway: a criterion-level affirmative verdict
resting on automated-scan evidence alone is unsound for any criterion
outside that ~57% ceiling — consistent with this rulebook's existing
directive language, but the checklist does not yet spell out the
evidence-field consequence.
Sources:
- https://www.a11yflow.dev/blog/axe-vs-lighthouse-vs-wave-vs-pa11y
- https://inclly.com/resources/axe-vs-lighthouse

## Sweep angle 2 — assistive-technology usage (WebAIM Screen Reader Survey)

canonical: WebSearch "NVDA JAWS VoiceOver screen reader usage share
survey 2026 WebAIM", this turn's tool transcript
WebAIM's Screen Reader User Survey #10 (2024, the field's own
adoption-evidence source, not a vendor claim) shows NVDA most commonly
used at 65.6% vs. JAWS 60.5%, but primary usage nearly ties (37.7% vs.
40.5%), and regional variance is large: JAWS leads NVDA in North
America (55.5% vs. 24.0%) and Australia, while NVDA dominates in
Europe, Africa/Middle East, and Asia. Design-move takeaway: no single
AT tool represents "the" screen reader across the field, so an AT-
testing evidence entry naming only the generic phrase "screen reader
tested" hides which of two near-equally-used, non-overlapping-by-
region tools actually ran, and cannot be checked for AT diversity
across a multi-market product.
Sources:
- https://webaim.org/projects/screenreadersurvey10/
- https://exceedability.com/screen-readers-compared.html

## Sweep angle 3 — design-stage checking (Stark)

canonical: WebSearch "Stark contrast checker Figma plugin accessibility
design adoption downloads 2026", this turn's tool transcript
Stark (40,000+ designers/developers/PMs across 28,000+ companies, per
its own published adoption figures, corroborated by an independent
plugin-directory listing) runs inside Figma/Sketch/Adobe XD at the
token/component design stage — before any rendered page exists for a
page-scanner to reach — checking contrast ratios, simulating color-
vision deficiency, and drafting AI-suggested alt text for a human to
review before use. Design-move takeaway: (a) a color-token change's
contrast/color-vision check belongs at token-definition time, not
deferred to a later rendered-page scan; (b) a machine/AI-drafted
accessible-name or alt-text candidate stays a draft, not an
`assertedBy`-a-person value, until a human has reviewed and accepted
it.
Sources:
- https://www.getstark.co/figma/
- https://sparkbox.com/foundry/stark_for_figma_accessibility_testing_tool_design_website_accessibility_and_accessible_design_review_tool

## Sweep angle 4 — guided manual assessment (Microsoft Accessibility Insights for Web)

canonical: WebSearch "accessibility-insights-for-web Microsoft GitHub
stars adoption enterprise 2026", this turn's tool transcript
Accessibility Insights for Web (Microsoft, actively maintained, 909
GitHub stars, part of a broader enterprise accessibility program that
now underwrites a GitHub Enterprise Accessibility Advisory Panel
launched 2026) structures its "FastPass" workflow as an automated scan
run together with two named guided manual checks — a tab-stops
(keyboard) walk and a "needs review" list the automated scan alone
cannot resolve — and its full "Assessment" mode extends that same
guided-step shape across all WCAG 2.1 AA criteria. Design-move
takeaway: a standing minimum manual-check pair (keyboard tab-stop walk
+ focus-visible walk) recurs across interaction-heavy evaluations
often enough to name once as a default set, rather than re-derived
from scratch each evaluation.
Sources:
- https://github.com/microsoft/accessibility-insights-web
- https://github.blog/open-source/building-githubs-next-chapter-in-accessibility/

## Adopt / skip

Adopt: (1) evidence-field specificity rule — AT evidence must name
tool(+version), never the bare phrase "screen reader tested"; (2)
machine/AI-suggested accessible-name or alt-text candidates stay
drafts requiring human review before an entry may be `assertedBy` a
person or carry an affirmative verdict; (3) color-token contrast/
color-vision check due at token-definition time, not deferred to a
rendered-page scan; (4) a named standing minimum manual-check pair
(keyboard tab-stop walk + focus-visible walk) for interaction-heavy
patterns.
Skip: cloning any tool's UI/workflow (axe-core's rule-engine
internals, Stark's Figma plugin panel layout, Accessibility Insights'
extension chrome) — this role evaluates screens/tokens against WCAG,
it does not operate scanning tooling; adopting the underlying
judgment, not the tool's surface, per scout-directive.

## Gap line

canonical: `docs/issue-1199/reports/accessibility/current-state-survey.md`
(committed this session, 3376b6e) — "Gap this fold-in targets" section
Existing rulebook state already names WCAG-EM as the governing
methodology and already requires "automated + manual" evidence in the
abstract (met); it has no evidence-field specificity rule, no
machine-suggestion-is-a-draft rule, no token-stage timing rule, and no
named standing manual-check minimum (all four missing) — these four
gaps map 1:1 onto the four adopted learnings above.
