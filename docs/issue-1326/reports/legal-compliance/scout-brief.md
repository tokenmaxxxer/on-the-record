Subject: issue-1326 (legal-compliance, scout)

## Angles run (parallel WebSearch batch; both resolved in-round, no
snowball needed — saturation reached round 1)

- Angle A: IMDA Model AI Governance Framework for Agentic AI (Jan 2026) —
  primary text location and content.
- Angle B: EU AI Act provisions bearing on autonomous agents (record-
  keeping, deployer log-retention).

## Findings

**IMDA MGF for Agentic AI v1.0 (22 Jan 2026, updated v1.5 20 May 2026)**
is retrievable as a real PDF, not a paywalled/JS-rendered page, at the
official IMDA media URL.
canonical: https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/mgf-for-agentic-ai.pdf — fetched and converted this session
derived: pdftotext -layout <fetched pdf> /tmp/mgf.txt && wc -l /tmp/mgf.txt
```
2480 /tmp/mgf.txt
```
No primary-access failure; the issue's precondition (verify primary text
access, else downgrade source tier) is satisfied at full tier. Structure:
four pillars (assess/bound risk upfront, human accountability, technical
controls, end-user responsibility); the per-agent identity/authorisation
content sits under pillar 1 as an "Agent identity" subsection with two
bulleted lists (Identification, Authorisation); logging is component 8 of
the agent architecture enumeration and recurs under pillar 3 (technical
controls) as a named control category ("Logging and monitoring").
canonical: /tmp/mgf.txt:1008-1073 (this session's pdftotext output of the fetched primary PDF)

**EU AI Act**: the record-keeping article (providers) and the deployer-
obligations article are the two clauses that speak to logging/audit
trails generally.
canonical: fetched this session
```
https://artificialintelligenceact.eu/article/12/
https://artificialintelligenceact.eu/article/26/
```
Neither article names "autonomous software agent" or "agentic AI" — the
Act's high-risk classification predates the agentic wave and turns on
sector/use-case (biometrics, employment, credit, etc.), not on agent
autonomy per se. Whether an internal dev-tooling agent (like
on-the-record's own role agents) falls under "high-risk AI system" at all
is unresolved in the Act's fetched article text — this is the load-
bearing reason nearly every EU-AI-Act row in the eventual gap table needs
[interpretation], not a clause citation: the Act's audit/logging
obligations were written for a different system class and are being
mapped onto agent tooling by analogy.

## Must-bes / gap line

- IMDA's "Agent identity" bullets (Unique, Accounted for, Differentiated-
  by-capacity, Catalogued) plus "Authorisation" bullets (scoped/least-
  privilege/non-transferable, bounded-by-authorising-human) are the
  concrete per-agent-identity requirement set the issue asks to map
  on-the-record against (canonical: /tmp/mgf.txt:1030-1073, this
  session's pdftotext of the fetched primary PDF) — these map to
  specific, checkable trace fields (agent ID, supervising human/role,
  scope, permission bound), which is what makes IMDA gradeable with real
  clause citations, unlike the EU side.
- The EU record-keeping and deployer-obligations articles give a generic
  logs-must-exist / retention-floor / cover-risk-and-monitoring-events
  bar (canonical: fetched this session, see URLs above) that
  on-the-record's mechanisms can be graded against only analogically,
  since no clause names agents.

## Adopt / skip

- Adopt: cite IMDA by section heading + PDF page number (no numbered
  clauses exist in the source; page numbers are the only stable locator
  pdftotext preserves) rather than inventing clause numbers.
- Skip: do not grade the EU record-keeping/deployer-obligations rows at
  the same confidence as IMDA rows — every EU row carries the
  [interpretation] marker per the issue's own instruction, since the
  Act's fetched text has no autonomous-agent-specific provision.

## Segment fit

Framework-reading task, not a product/competitive scout — "top of
category" here means primary legal/regulatory text over secondary
law-firm summaries, which was reachable for both frameworks this
session.

Sources:
```
https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/mgf-for-agentic-ai.pdf (primary, fetched and pdftotext'd this session)
https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/press-releases/2026/new-model-ai-governance-framework-for-agentic-ai
https://artificialintelligenceact.eu/article/12/
https://artificialintelligenceact.eu/article/26/
https://www.bakermckenzie.com/en/insight/publications/2026/01/singapore-governance-framework-for-agentic-ai-launched
```

Stage count: one sweep round (parallel WebSearch calls, angles A/B) plus
one deepening round (parallel WebFetch calls confirming/extracting the
primary texts) — well under the 5-stage/3-minute budget. Saturation
reached: both primary sources were retrieved and clause content
extracted; a further round would not change which rows get cited vs.
[interpretation].
