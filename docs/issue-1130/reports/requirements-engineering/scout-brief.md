---
name: scout-brief
description: issue-1130 phase-1 scout brief — canonical methodology/artifact/knowledge sources per in-scope role
---

# Scout brief — issue #1130

kind: scout-brief
subject: issue-1130

Mode: parallel Agent-tool fan-out, one message with 5 concurrent research-agent dispatches, split by role cluster (data-domain; content/comms; ML/observability/knowledge; refactoring/discovery; gate-now-unwired). Each agent's brief instructed WebSearch/WebFetch verification of sources. This document synthesizes the five agents' combined output into the sections below.

## Gap line

canonical: docs/specs/role-invariant-coverage.md, read directly in this session. Its coverage matrix's "Invariant" column states a behavioral rule per role (e.g. "hot-path change carries a measurement") but names no methodology, artifact-form standard, or degree-level knowledge source for any of the 43 rows — the gap this proposal fills applies to every cause-d and cause-b role below.

## Must-bes extracted per role cluster

- Data-domain roles (data-engineering, data-modeling, growth-analytics): a named academic/industry standard for judgment (DAMA-DMBOK, Codd normalization, AARRR) plus a named planning framework (Kimball lifecycle/dimensional modeling, Lean Analytics).
- Content/comms roles (content-design, pr-communications, localization): a named style/quality-metric standard (NN/g heuristics, MQM, Conventional Commits/Comments); localization additionally has an ISO standard (ISO 17100).
- ML/observability/knowledge roles (ml-engineering, observability, knowledge-management): publicly documented engineering rulebooks (Google's Rules of ML, the SRE book) and ISO 30401.
- Refactoring/discovery roles (refactoring-legacy, user-discovery): single-author canonical texts (Fowler's Refactoring, Feathers' Working Effectively with Legacy Code, Fitzpatrick's Mom Test) with named techniques (seams, characterization tests, the Mom Test's three failure modes).
- Gate-now-unwired roles (accessibility, api-design, performance-engineering): each has a maintained normative standard (WCAG 2.2, Google's API design guide plus Microsoft's REST guidelines, the USE/RED methods) and a structurally-diffable signal (missing alt/aria-label, a removed/renamed API field with no version bump, a missing perf-measurement trailer).
- Cause-b roles (secure-coding, test-authoring, issue-retrospective, release-engineering, interaction-design, ux-engineering): canonical: roles/specs/secure-coding.spec.json, test-authoring.spec.json, issue-retrospective.spec.json, release-engineering.spec.json, interaction-design.spec.json, ux-engineering.spec.json and on-the-record/hooks/hooks.json, read directly. The gap for this cluster is not missing methodology depth — several already carry a `source_standard` field — it is that each role's landed hook checks a narrower or different condition than its own `use_when.board_condition`, so the role session itself never spawns.

## Adopt / skip

- Adopt: one named primary methodology per activity (judgment/planning/deliverable_production/feedback/review) per role, in the same shape roles/specs/product-discovery.spec.json already uses for `source_standard` and roles/specs/requirements-engineering.spec.json uses for `finding_method`/`anti_pattern`.
- Adopt: a real URL per claim below (Sources list), gathered by the researching agents via WebSearch/WebFetch rather than typed from training-data recall, per #515 req#2.
- Skip: a repo-invented competing methodology where a real one already exists.
- Skip: adding methodology depth to cause-b roles. canonical: docs/issue-1129/reports/product-discovery.md's "Per-role cause classification table", read directly — cause-b there is defined as routing absorption with a working hook, and issue #1130's own body (`gh issue view 1130`, read this session) restricts cause-b to routing-fix proposals, not expertise depth.

## Segment fit

Fit is measured by whether each named source is the founding text, the ISO/W3C/IEEE normative standard, or the most-cited industry framework for that discipline — not by competitive benchmarking against a shipped product.

## Sources

Content-design: nngroup.com/articles/ten-usability-heuristics-for-user-interface-design; digital.gov/guides/plain-language/principles; Halvorson, Content Strategy for the Web (New Riders 2012); Rosenfeld/Morville/Arango, Information Architecture (O'Reilly 4th ed 2015); uxcontent.com/how-to-create-style-guide.

Data-engineering: DAMA-DMBOK 2nd ed (Technics Publications 2017); Kimball & Ross, The Data Warehouse Toolkit 3rd ed (Wiley 2013), kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dw-bi-lifecycle-method; Reis & Housley, Fundamentals of Data Engineering (O'Reilly 2022); google.github.io/eng-practices/review.

Data-modeling: Codd, "A Relational Model of Data for Large Shared Data Banks," CACM 1970; Kimball & Ross (Wiley 2013); NIST FIPS 184 IDEF1X; Chen, "The Entity-Relationship Model," ACM TODS 1976; Silverston & Agnew, The Data Model Resource Book Vol 3 (Wiley 2008).

Growth-analytics: McClure, "Startup Metrics for Pirates" (2007), amplitude.com/blog/pirate-metrics-framework; Croll & Yoskovitz, Lean Analytics (O'Reilly 2013); Rodden, Hutchinson, Fu, "HEART Framework" (Google Research 2010), research.google/pubs/pub36299; Deng, "Causal Inference — Statistical Analysis of A/B Tests," alexdeng.github.io/causal/abstats.html.

Knowledge-management: Nonaka & Takeuchi, The Knowledge-Creating Company (1995); ISO 30401:2018, iso.org/standard/89436.html; APQC KM-CAT and maturity levels, apqc.org/resource-library.

Localization: Lommel et al., MQM framework (2014), themqm.org; ISO 17100:2015, iso.org/standard/59149.html; OASIS XLIFF 2.1, oasis-open.org/committees/xliff; W3C Internationalization glossary, w3.org/TR/i18n-glossary.

ML-engineering: Zinkevich, "Rules of Machine Learning" (Google), developers.google.com/machine-learning/guides/rules-of-ml; CRISP-DM (1999); Mitchell et al., "Model Cards for Model Reporting" (FAT* 2019), research.google/blog/introducing-the-model-card-toolkit-for-easier-model-transparency-reporting.

Observability: Sridharan, Distributed Systems Observability (O'Reilly 2018); the Google SRE book, sre.google/sre-book (monitoring, SLOs, postmortem culture, launch checklist sections); OpenTelemetry semantic conventions, opentelemetry.io/docs/specs/semconv; Gregg, the USE Method, brendangregg.com/usemethod.html; Grafana, "The RED Method," grafana.com/blog/the-red-method-how-to-instrument-your-services.

PR-communications: Beams, "How to Write a Git Commit Message," cbea.ms/git-commit; google.github.io/eng-practices/review/reviewer/standard.html; Conventional Commits v1.0.0, conventionalcommits.org; Keep a Changelog v1.1.0, keepachangelog.com/en/1.1.0; Conventional Comments, conventionalcomments.org; Semantic Versioning 2.0.0, semver.org.

Refactoring-legacy: Fowler, Refactoring 2nd ed (2018), refactoring.com/catalog; Feathers, Working Effectively with Legacy Code (Prentice Hall 2004); Fowler, "StranglerFigApplication," martinfowler.com/bliki/StranglerFigApplication.html; Fowler, "CodeSmell," martinfowler.com/bliki/CodeSmell.html.

User-discovery: Fitzpatrick, The Mom Test (2013), momtestbook.com; Torres, Continuous Discovery Habits (2021), producttalk.org/opportunity-solution-trees; Beyer & Holtzblatt, Contextual Design (Morgan Kaufmann 1998); Christensen and Moesta, JTBD (jobs-to-be-d[o]ne) theory, christenseninstitute.org (theory section); Braun & Clarke, "Using thematic analysis in psychology," Qualitative Research in Psychology, 2006; Guest, Bunce & Johnson, "How Many Interviews Are Enough?," Field Methods, 2006.

Accessibility: W3C WCAG 2.2, w3.org/TR/WCAG22; Deque, "Accessibility Heuristics Evaluation," deque.com/blog/supporting-the-design-phase-with-accessibility-heuristics-evaluations; ITI VPAT and ACR guidance, deque.com/accessibility-compliance/vpat; W3C WAI-ARIA, w3.org/TR/wai-aria-1.2.

Api-design: Google Cloud API Design Guide and Google's AIP series, docs.cloud.google.com/apis/design, google.aip.dev; Microsoft REST API Guidelines, github.com/microsoft/api-guidelines; OpenAPI Specification, spec.openapis.org/oas/latest.html; oasdiff, github.com/oasdiff/oasdiff; RFC 9110, rfc-editor.org/rfc/rfc9110.

Performance-engineering: Gregg, the USE Method, brendangregg.com/usemethod.html; Wilkie, the RED Method, weave.works/blog/the-red-method-key-metrics-for-microservices-architecture; the Google SRE book's monitoring and SLO chapters, sre.google; Dean & Barroso, "The Tail at Scale," Communications of the ACM, 2013, research.google/pubs/pub40801; Azure Well-Architected Framework performance testing guidance, learn.microsoft.com/en-us/azure/well-architected/performance-efficiency/performance-test.

Cause-b routing analysis: docs/specs/role-invariant-coverage.md; roles/specs/secure-coding.spec.json, test-authoring.spec.json, issue-retrospective.spec.json, release-engineering.spec.json, interaction-design.spec.json, ux-engineering.spec.json; on-the-record/hooks/hooks.json — all read directly in this repo.
