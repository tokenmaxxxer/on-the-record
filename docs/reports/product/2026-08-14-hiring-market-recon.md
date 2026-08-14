# Hiring-Market Recon: Direction Signals for tokenmaxxxer (2026-08-14)

Decision this feeds: tokenmaxxxer's next roadmap direction, using the hiring
market as the lens — what dev orgs hire for when they agentize themselves
reveals what capability a dev-org-agentization product must supply.

Method: market-recon harness, 5-modality parallel sweep (global AX postings,
Korean AX postings, dev-org role-taxonomy data, competitor surface + their
hiring, org-scale adoption pain signals). Stopped on budget (standard scan,
one pass per modality), not saturation — but the headline finding recurred
independently in 4 of 5 modalities, which is triangulation across
non-shared origins.

## Headline finding (●●●, convergent across 4 independent modalities)

**Verification — not generation — is the bottleneck the market is paying
for.**

- Role-taxonomy data: median PR-review time +441%, PRs merged with no review
  +31%, incidents per PR +242% (Faros/Jellyfish telemetry, 2026); Stack
  Overflow 2025: trust in AI output fell to 29%, 45% lose significant time
  debugging AI code.
- Demand signals: agentic PRs wait 4.6–5.3x longer for pickup (LinearB, 8M
  PRs, 2026); feature-branch throughput +15% while main-branch throughput
  −7% — code enters faster than it lands. METR RCT: −19% actual vs +20%
  perceived productivity.
- Global postings: "evals & observability" and "guardrails/governance" are
  competency clusters #3–#4 across AI-enablement JDs (Tailscale, GM,
  Handshake, Indicium).
- Competitor surface: Cursor bought Graphite because "review is the
  bottleneck once AI writes the code" (Truell); analysts flag verification
  as vendor-self-attested, not independent.

## Competency clusters the market demands (ranked, global postings ●●○)

1. Daily hands-on fluency with agentic coding tools (near-universal)
2. Production agent building: orchestration, MCP, tool use
3. Evals & observability (the trust gate for non-deterministic agents)
4. Guardrails / governance / security (merging INTO the builder role)
5. Measuring adoption & ROI
6. Change management / teaching (behavior change as accountable outcome)
7. Internal platform engineering (paved-road agent platform)

What orgs are building internally: a paved-road internal agent platform +
an eval layer as trust mechanism + a guardrailed SDLC for AI code +
a measurement/change-management function reporting very high (IC reporting
to a co-founder at Tailscale).

## Korea-specific read (●●○)

- Dominant archetype is the embedded FDE / process-discovery consultant
  (Krafton AI FDE, Musinsa AX Engineer) targeting the *whole company's*
  workflows, top-down, not the dev org's own SDLC.
- **Evals are nearly absent from Korean JDs** — validation framed as "PoC
  검증", not systematic evaluation. Korea lags global on exactly the
  cluster the global market ranks #3.
- Wanted 2026 AX report: 92.1% of workers use AI, 5.3% of firms completed
  org-wide AX; #1 blocker = 전문 인력 부족 (53.1%).

## Competitive whitespace (●●○)

Coding (Devin/Factory/Cursor/Codex/Claude Code) and review
(BugBot/CodeRabbit/Greptile/Qodo) are saturated and consolidating into
vertically integrated write+review+ship stacks. Uncovered loop segments:

1. **Independent verification/acceptance** (vendor self-verification has a
   conflict of interest; Graphite's absorption into Cursor removed an
   independent reviewer)
2. **Process governance & per-agent audit records** (KPMG 2026: 75% of
   large enterprises rank auditability top requirement; EU AI Act / IMDA
   creating forced demand; no dev-org product owns it)
3. **Requirements-to-acceptance traceability** (Kiro/Tessl attack from the
   code side, not the org-process side)
4. **Whole-org orchestration** — roles, handoffs, cross-team records;
   MultiDevin/Cursor multitask are intra-task parallelism only

This whitespace maps 1:1 onto tokenmaxxxer's existing architecture:
on-the-record (issue/PR/trace records), acceptance-format gates,
requirement-digest linkage, 43-role orchestration, hooks-enforced process.

## What teams abandoned (graveyard, ●●○)

- Verbose AI review bots (muted within days; 29.6 tokens/LOC vs 4.1 human)
- LLM-auto-generated context files (measured: reduced task success, +20%
  inference cost — human-curated AGENTS.md/CLAUDE.md is what survives)
- Ungoverned broad rollouts (paused to retrofit controls)
- Risk-based routing proxies for human review (tested, failed)
- Standalone IDE-agent plays (Windsurf dismembered; Sweep dormant; Roo Code
  shut down; Aider maintenance mode)

## Direction implications for tokenmaxxxer (findings only — not adopted decisions)

1. **Double down on verification/acceptance as the product's center of
   gravity** — E2E harness-as-judge (northpole), acceptance-format gates,
   real-build-use verification are pointed at the market's #1 revealed
   pain. This is confirmation of current direction, not a pivot.
2. **Records/audit layer is regulation-forced whitespace** — on-the-record's
   trace/record discipline is close to per-agent audit-trail requirements
   (IMDA-style identity + authorization trail); worth an explicit gap
   check against those frameworks.
3. **Eval literacy as a product surface** — the market's trust gate is
   evals; tokenmaxxxer verifies per-change but has no systematic eval
   harness for role/agent quality over time.
4. **Anti-noise is existential** — the graveyard's clearest lesson: noisy
   advisory output gets muted, then killed. Watch/report volume discipline
   is a survival property, not polish.
5. **Measurement/ROI story missing** — orgs hire someone to prove AI
   impact; LinearB/DX can't attribute AI vs human. A product that records
   everything is positioned to measure honestly (subject to the standing
   no-metric-gaming principle).
6. **Korea GTM angle**: the eval/verification gap in Korean JDs means the
   capability tokenmaxxxer embodies is scarce locally (전문 인력 부족
   53.1%) — the product substitutes for talent orgs can't hire.

## Coverage statement

Scanned: EN + KR job postings (Greenhouse/Lever/Ashby/원티드/잡코리아 via
search; some KR pages 403'd — snippets/mirrors used), Indeed Hiring
Lab / LinkedIn / Stack Overflow 2025 / DORA 2025 / METR / LinearB / DX
datasets, competitor sites + careers, practitioner accounts (HN/Reddit/
QCon/blogs). Not reached: paywalled analyst reports (Gartner full text),
LinkedIn posting full-text corpus, JP/CN/EU-language markets, private
salary/ATS data. Stopped on budget after one pass per modality; a deeper
pass would chase Korean enterprise (chaebol SI) JDs and EU AI Act
conformity tooling vendors. Data dates 2024–2026-08; hiring landscape has
a shelf life of months.

## Cheapest next test

The market-derived hypothesis is "teams will adopt a tool whose value is
enforced verification + audit records." Cheapest reversible test: the
already-planned fresh-session real-world install (fresh-session-test
handoff) measured against exactly two questions — does the verification
gate catch a real defect the user would have missed, and does the record
output stay below the mute-threshold noise level. Both are observable in
one session; no new build required.

## Sources

Per-claim source URLs, recovered from the underlying modality briefs (the
synthesis text omitted them):

**Role-taxonomy / verification bottleneck**
- Indeed Hiring Lab, AI & job postings (2026): https://www.hiringlab.org/2026/07/08/ai-and-job-postings-from-destruction-to-creation/ ; https://www.hiringlab.org/2026/01/22/january-labor-market-update-jobs-mentioning-ai-are-growing-amid-broader-hiring-weakness/
- Stack Overflow Developer Survey 2025: https://survey.stackoverflow.co/2025/
- DORA 2025 report: https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
- Faros/Jellyfish PR-telemetry commentary (2026): https://www.faros.ai/blog/key-takeaways-from-the-dora-report-2025
- FDE title growth: https://www.paraform.com/blog/forward-deployed-engineer-demand-quadrupled
- LinkedIn Jobs on the Rise 2026 (via Dice): https://www.dice.com/career-advice/ai-related-jobs-top-linkedins-fastest-growing-roles-list-for-2026
- QA market data: https://www.sqaexperts.com/is-qa-a-dying-career-what-2026-job-market-data-actually-shows

**Demand / adoption pain**
- LinearB 8M-PR dataset (2026): https://linearb.io/blog/8-million-prs-engineering-productivity ; https://www.flowverify.co/blog/ai-code-review-bottleneck-2026-data
- METR RCT (2025): https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- HN/Reddit qualitative analysis: https://www.developersdigest.tech/blog/what-hacker-news-gets-right-about-ai-coding-agents-2026
- Auto-generated context files study (Gloaguen et al. 2026): https://arxiv.org/html/2510.21413v1
- Enterprise rollout controls: https://northflank.com/blog/enterprise-ai-coding-agent-deployment
- DX Q4 2025 impact report: https://getdx.com/blog/ai-assisted-engineering-q4-impact-report-2025/
- Microsoft internal rollout study: https://arxiv.org/html/2607.01418
- Verbose review-bot failure account: https://dev.to/leena_malhotra/i-tried-replacing-human-review-with-ai-heres-where-it-quietly-failed-4jh3

**Global postings**
- Tailscale AI Enablement: https://job-boards.greenhouse.io/tailscale/jobs/4710703005
- Cursor AI Adoption Engineer: https://jobs.accel.com/companies/cursor-2-379534b5-1a2a-49fd-86d0-ccd3e256c4f0/jobs/83960644-ai-adoption-engineer
- Cognition Applied AI Engineer: https://builtin.com/job/ai-enablement-engineer/7470703
- GM Staff SWE AI Dev Productivity: https://search-careers.gm.com/en/jobs/jr-202612378/staff-software-engineer-ai-for-developer-productivity/
- Indicium Sr FDE: https://job-boards.greenhouse.io/indiciumai/jobs/4944657101
- Handshake Agentic Infrastructure: https://jobs.ashbyhq.com/handshake/747bd14b-b957-4fca-b5bd-12d571f6886e
- AI platform leader spec: https://www.augmentcode.com/guides/ai-platform-engineering-leader-job-spec

**Korea**
- 크래프톤 AI FDE: https://www.sedaily.com/article/20024771
- 무신사 AX Engineer: https://www.musinsacareers.com/ko/o/187901
- 원티드 2026 AX report (via 테크월드): https://www.epnc.co.kr/news/articleView.html?idxno=401038
- 잡코리아 AI-tool coding-test policy: https://www.jobkorea.co.kr/goodjob/tip/view?News_No=22546

**Competitor surface**
- Cognition/Devin: https://research.contrary.com/company/cognition
- Factory GA: https://factory.ai/news/factory-is-ga
- Cursor 3.2 analysis: https://futurumgroup.com/insights/cursor-3-2-reframes-the-ide-as-an-agent-execution-runtime/
- Cursor–Graphite: https://cursor.com/blog/graphite ; https://techcrunch.com/2025/12/19/cursor-continues-acquisition-spree-with-graphite-deal
- Review-tool comparison: https://particula.tech/blog/greptile-vs-coderabbit-vs-qodo-ai-code-review-2026
- Governance gap notes: https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-agent-governance-framework-gap-20260403/ ; https://zylos.ai/research/2026-05-01-ai-agent-governance-compliance-2026/
- Consolidation/graveyard: https://rywalker.com/research/ai-coding-assistants

## What was done

Transcribed the 2026-08-14 hiring-market recon report — the first comment
on issue #1314 — verbatim into this file, per the acceptance criteria on
the issue.

## Why

canonical: gh issue view 1314 --comments — issue #1314's first comment is
the report source text; the issue asks for it to be recorded as
docs/reports/product/2026-08-14-hiring-market-recon.md.

## Upstream basis

Based on: issue #1314 first comment (JiwonJung94, 2026-08-14).

## Kind / loop_state

kind: report
loop_state: final

## Open findings

None.
